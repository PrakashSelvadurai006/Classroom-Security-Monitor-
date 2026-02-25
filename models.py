from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    student_id = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    photo_path = db.Column(db.String(255), nullable=False)
    face_encoding = db.Column(db.Text, nullable=True)  # Store face encoding as JSON string
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with entry logs
    entry_logs = db.relationship('EntryLog', backref='student', lazy=True, cascade='all, delete-orphan')
    
    def set_face_encoding(self, encoding):
        """Convert numpy array to JSON string for storage"""
        if encoding is not None:
            self.face_encoding = json.dumps(encoding.tolist())
    
    def get_face_encoding(self): 
        """Convert JSON string back to numpy array"""
        if self.face_encoding:
            import numpy as np
            return np.array(json.loads(self.face_encoding))
        return None
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'student_id': self.student_id,
            'email': self.email,
            'phone': self.phone,
            'photo_path': self.photo_path,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class EntryLog(db.Model):
    __tablename__ = 'entry_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)
    entry_time = db.Column(db.DateTime, default=datetime.utcnow)
    is_recognized = db.Column(db.Boolean, default=False)
    confidence_score = db.Column(db.Float, nullable=True)
    image_path = db.Column(db.String(255), nullable=True)  # Store captured image
    notes = db.Column(db.Text, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else 'Unknown',
            'entry_time': self.entry_time.isoformat() if self.entry_time else None,
            'is_recognized': self.is_recognized,
            'confidence_score': self.confidence_score,
            'image_path': self.image_path,
            'notes': self.notes
        }

class SystemAlert(db.Model):
    __tablename__ = 'system_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(50), nullable=False)  # 'unknown_person', 'system_error', etc.
    message = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), default='medium')  # 'low', 'medium', 'high', 'critical'
    is_resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    image_path = db.Column(db.String(255), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'alert_type': self.alert_type,
            'message': self.message,
            'severity': self.severity,
            'is_resolved': self.is_resolved,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'image_path': self.image_path
        }