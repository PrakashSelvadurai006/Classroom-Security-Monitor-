from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import cv2
import json
import base64
import numpy as np
from datetime import datetime, timedelta
import threading
import time

from config import Config
from models import db, Student, EntryLog, SystemAlert
from ai_service import AIService
from alarm_system import trigger_security_alarm, stop_security_alarm

app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

# Initialize extensions
db.init_app(app)
CORS(app)

# Initialize AI service
ai_service = AIService()

# Global variables for monitoring
monitoring_active = False
monitoring_thread = None
capture_thread = None   # Dedicated camera-read thread
camera = None

# Shared frame buffer — only the capture thread writes; everyone else reads
latest_frame = None
latest_frame_b64 = None
frame_lock = threading.Lock()

def allowed_file(filename):
    """Check if file has allowed extension"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main dashboard page"""
    # Get recent entry logs
    recent_entries = EntryLog.query.order_by(EntryLog.entry_time.desc()).limit(10).all()
    
    # Get active alerts
    active_alerts = SystemAlert.query.filter_by(is_resolved=False).order_by(
        SystemAlert.created_at.desc()
    ).limit(5).all()
    
    # Get student count
    total_students = Student.query.filter_by(is_active=True).count()
    
    # Get today's entries
    today = datetime.utcnow().date()
    today_entries = EntryLog.query.filter(
        db.func.date(EntryLog.entry_time) == today
    ).count()
    
    return render_template('index.html', 
                         recent_entries=recent_entries,
                         active_alerts=active_alerts,
                         total_students=total_students,
                         today_entries=today_entries,
                         monitoring_active=monitoring_active)

@app.route('/students')
def students():
    """Student management page"""
    students = Student.query.filter_by(is_active=True).all()
    return render_template('students.html', students=students)

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    """Add new student"""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            student_id = request.form.get('student_id')
            email = request.form.get('email')
            phone = request.form.get('phone')
            
            # Check if student ID already exists
            existing_student = Student.query.filter_by(student_id=student_id).first()
            if existing_student:
                flash('Student ID already exists!', 'error')
                return redirect(url_for('add_student'))
            
            # Handle file upload
            if 'photo' not in request.files:
                flash('No photo uploaded!', 'error')
                return redirect(url_for('add_student'))
            
            file = request.files['photo']
            if file.filename == '':
                flash('No photo selected!', 'error')
                return redirect(url_for('add_student'))
            
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{student_id}_{file.filename}")
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                # Ensure upload directory exists
                os.makedirs(os.path.dirname(photo_path), exist_ok=True)
                file.save(photo_path)
                
                # Extract face features using AI
                features = ai_service.extract_face_features(photo_path)
                
                # Create new student
                student = Student(
                    name=name,
                    student_id=student_id,
                    email=email,
                    phone=phone,
                    photo_path=photo_path
                )
                
                # Store face features
                if features:
                    student.face_encoding = json.dumps(features)
                
                db.session.add(student)
                db.session.commit()
                
                flash('Student added successfully!', 'success')
                return redirect(url_for('students'))
            else:
                flash('Invalid file format!', 'error')
                
        except Exception as e:
            flash(f'Error adding student: {str(e)}', 'error')
            db.session.rollback()
    
    return render_template('add_student.html')

@app.route('/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    """Delete a student"""
    try:
        student = Student.query.get_or_404(student_id)
        student.is_active = False
        db.session.commit()
        flash('Student deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting student: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('students'))

@app.route('/start_monitoring', methods=['POST'])
def start_monitoring():
    """Start monitoring — browser will supply frames via /analyze_frame."""
    global monitoring_active, monitoring_thread

    try:
        if not monitoring_active:
            monitoring_active = True

            # Start the AI monitoring thread (reads frames posted by the browser)
            monitoring_thread = threading.Thread(target=monitor_faces, daemon=True)
            monitoring_thread.start()

            return jsonify({
                'status': 'success',
                'message': '✅ Monitoring started — camera active in browser'
            })
        else:
            return jsonify({'status': 'info', 'message': 'Monitoring already active'})

    except Exception as e:
        monitoring_active = False
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/stop_monitoring', methods=['POST'])
def stop_monitoring():
    """Stop monitoring."""
    global monitoring_active
    try:
        monitoring_active = False
        return jsonify({'status': 'success', 'message': 'Monitoring stopped'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error stopping: {str(e)}'})

def _capture_loop():
    """
    Dedicated camera-read thread.
    ONLY this function ever calls camera.read() — prevents the race condition
    that was causing the camera to crash when two threads read simultaneously.
    """
    global monitoring_active, camera, latest_frame, latest_frame_b64

    print("📷 Capture loop started")
    consecutive_failures = 0

    while monitoring_active and camera and camera.isOpened():
        try:
            ret, frame = camera.read()
            if ret and frame is not None and frame.size > 0:
                consecutive_failures = 0
                _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                b64 = base64.b64encode(buf).decode('utf-8')
                with frame_lock:
                    latest_frame = frame.copy()
                    latest_frame_b64 = b64
            else:
                consecutive_failures += 1
                if consecutive_failures > 30:   # ~3 s of failures
                    print("⚠ Camera read failing repeatedly — stopping capture")
                    break
                time.sleep(0.1)
                continue

            time.sleep(0.05)   # ~20 fps capture rate

        except Exception as e:
            print(f"Capture loop error: {e}")
            time.sleep(0.2)

    print("📷 Capture loop exited")


@app.route('/get_camera_frame')
def get_camera_frame():
    """Return the latest captured frame from the shared buffer (no camera.read() here)."""
    try:
        with frame_lock:
            b64 = latest_frame_b64

        if b64:
            return jsonify({
                'status': 'success',
                'frame': b64,
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({'status': 'error', 'message': 'No frame available yet'})

    except Exception as e:
        print(f"get_camera_frame error: {e}")
        return jsonify({'status': 'error', 'message': f'Camera error: {str(e)}'})

@app.route('/monitoring_status')
def monitoring_status():
    """Get current monitoring status"""
    return jsonify({
        'active': monitoring_active,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/entry_logs')
def entry_logs():
    """View entry logs"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    logs = EntryLog.query.order_by(EntryLog.entry_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('entry_logs.html', logs=logs)

@app.route('/alerts')
def alerts():
    """View system alerts"""
    alerts = SystemAlert.query.order_by(SystemAlert.created_at.desc()).all()
    return render_template('alerts.html', alerts=alerts)

@app.route('/resolve_alert/<int:alert_id>', methods=['POST'])
def resolve_alert(alert_id):
    """Resolve a system alert"""
    try:
        alert = SystemAlert.query.get_or_404(alert_id)
        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
        db.session.commit()
        
        # Stop alarm when alert is resolved
        from alarm_system import stop_security_alarm
        stop_security_alarm()
        
        return jsonify({'status': 'success', 'message': 'Alert resolved and alarm stopped'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error resolving alert: {str(e)}'})

@app.route('/stop_alarm', methods=['POST'])
def stop_alarm():
    """Stop the security alarm"""
    try:
        from alarm_system import stop_security_alarm
        stop_security_alarm()
        return jsonify({'status': 'success', 'message': 'Alarm stopped'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error stopping alarm: {str(e)}'})

@app.route('/dashboard_stats')
def dashboard_stats():
    """Get real-time dashboard statistics"""
    try:
        # Get active alerts
        active_alerts = SystemAlert.query.filter_by(is_resolved=False).order_by(
            SystemAlert.created_at.desc()
        ).limit(5).all()
        
        # Get student count
        total_students = Student.query.filter_by(is_active=True).count()
        
        # Get today's entries
        today = datetime.utcnow().date()
        today_entries = EntryLog.query.filter(
            db.func.date(EntryLog.entry_time) == today
        ).count()
        
        # Get recent entries
        recent_entries = EntryLog.query.order_by(EntryLog.entry_time.desc()).limit(5).all()
        
        return jsonify({
            'status': 'success',
            'data': {
                'total_students': total_students,
                'today_entries': today_entries,
                'active_alerts_count': len(active_alerts),
                'monitoring_active': monitoring_active,
                'recent_entries': [entry.to_dict() for entry in recent_entries],
                'active_alerts': [alert.to_dict() for alert in active_alerts]
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error getting stats: {str(e)}'})

@app.route('/clear_all_data', methods=['POST'])
def clear_all_data():
    """Clear all system data (alerts, logs, etc.)"""
    try:
        # Stop monitoring and alarms first
        global monitoring_active, camera
        monitoring_active = False
        if camera:
            camera.release()
            camera = None
        
        from alarm_system import stop_security_alarm
        stop_security_alarm()
        
        # Clear all alerts
        SystemAlert.query.delete()
        
        # Clear all entry logs
        EntryLog.query.delete()
        
        # Commit changes
        db.session.commit()
        
        print("All system data cleared successfully")
        return jsonify({'status': 'success', 'message': 'All data cleared successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error clearing data: {e}")
        return jsonify({'status': 'error', 'message': f'Error clearing data: {str(e)}'})

@app.route('/clear_alerts', methods=['POST'])
def clear_alerts():
    """Clear all resolved alerts"""
    try:
        # Delete all resolved alerts
        resolved_count = SystemAlert.query.filter_by(is_resolved=True).count()
        SystemAlert.query.filter_by(is_resolved=True).delete()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Cleared {resolved_count} resolved alerts'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Error clearing alerts: {str(e)}'})

@app.route('/system_reset', methods=['POST'])
def system_reset():
    """Reset entire system to clean state"""
    try:
        # Stop everything
        global monitoring_active, camera
        monitoring_active = False
        if camera:
            camera.release()
            camera = None
        
        from alarm_system import stop_security_alarm
        stop_security_alarm()
        
        # Clear all data but keep students
        SystemAlert.query.delete()
        EntryLog.query.delete()
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'System reset successfully - Students preserved'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Error resetting system: {str(e)}'})

@app.route('/analyze_frame', methods=['POST'])
def analyze_frame():
    """
    Receive a camera frame (base64 JPEG) from the browser and run face recognition on it.
    The browser captures via getUserMedia, encodes to base64, and POSTs here every few seconds.
    """
    if not monitoring_active:
        return jsonify({'status': 'skipped', 'message': 'Monitoring not active'})

    try:
        data = request.get_json()
        if not data or 'frame' not in data:
            return jsonify({'status': 'error', 'message': 'No frame data received'})

        frame_b64 = data['frame']

        # Decode base64 → numpy array
        img_bytes = base64.b64decode(frame_b64)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if frame is None or frame.size == 0:
            return jsonify({'status': 'error', 'message': 'Could not decode frame'})

        current_time = datetime.utcnow()

        # Run AI face detection
        detected_faces = ai_service.process_frame_for_faces(frame)

        results = []

        for face_data in detected_faces:
            matched_student = None
            best_match_score = 0.0

            if face_data.get('features'):
                students = Student.query.filter_by(is_active=True).all()

                for student in students:
                    if student.face_encoding:
                        stored_features = json.loads(student.face_encoding)
                        similarity = ai_service.compare_faces(
                            face_data['features'],
                            stored_features
                        )
                        if similarity > best_match_score and similarity > 0.75:
                            best_match_score = similarity
                            matched_student = student

            # Log this detection
            entry_log = EntryLog(
                student_id=matched_student.id if matched_student else None,
                is_recognized=matched_student is not None,
                confidence_score=best_match_score if best_match_score > 0 else None,
                entry_time=current_time
            )
            db.session.add(entry_log)

            if matched_student:
                print(f"✅ Recognized: {matched_student.name} ({best_match_score:.2f})")
                results.append({'recognized': True, 'name': matched_student.name, 'confidence': best_match_score})
            else:
                print("❌ Unknown person detected!")
                # Create security alert
                alert = SystemAlert(
                    alert_type='unknown_person',
                    message=f'Unknown person detected at {current_time.strftime("%Y-%m-%d %H:%M:%S")}',
                    severity='high'
                )
                db.session.add(alert)
                trigger_security_alarm(
                    alert_type='unknown_person',
                    message=f'Unknown person detected at {current_time.strftime("%Y-%m-%d %H:%M:%S")}',
                    severity='high'
                )
                results.append({'recognized': False, 'name': 'Unknown'})

        db.session.commit()

        return jsonify({
            'status': 'success',
            'faces_detected': len(detected_faces),
            'results': results
        })

    except Exception as e:
        db.session.rollback()
        print(f"analyze_frame error: {e}")
        return jsonify({'status': 'error', 'message': str(e)})


def monitor_faces():
    """Kept for compatibility — browser-based mode uses /analyze_frame instead."""
    print("ℹ️ Monitoring thread started (browser-camera mode — waiting for /analyze_frame calls)")
    while monitoring_active:
        time.sleep(5)
    print("ℹ️ Monitoring thread stopped.")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)
