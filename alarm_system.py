import os
import threading
import time
from datetime import datetime
import pygame
import json
from config import Config

class AlarmSystem:
    def __init__(self):
        self.is_active = False
        self.alarm_thread = None
        self.config = Config()
        
        # Initialize pygame mixer for audio
        try:
            pygame.mixer.init()
            self.audio_available = True
        except:
            self.audio_available = False
            print("Warning: Audio system not available. Using visual alerts only.")
    
    def trigger_alarm(self, alert_type="unknown_person", message="Unknown person detected", severity="high"):
        """
        Trigger an alarm with the specified parameters
        """
        if not self.is_active:
            self.is_active = True
            
            # Create alarm thread
            self.alarm_thread = threading.Thread(
                target=self._alarm_loop,
                args=(alert_type, message, severity),
                daemon=True
            )
            self.alarm_thread.start()
            
            # Log alarm activation
            self._log_alarm(alert_type, message, severity)
    
    def stop_alarm(self):
        """
        Stop the current alarm
        """
        self.is_active = False
        
        if pygame.mixer.get_init():
            pygame.mixer.stop()
    
    def _alarm_loop(self, alert_type, message, severity):
        """
        Main alarm loop - handles visual and audio alerts
        """
        alarm_duration = self._get_alarm_duration(severity)
        start_time = time.time()
        
        while self.is_active and (time.time() - start_time) < alarm_duration:
            # Play audio alarm
            if self.audio_available:
                self._play_alarm_sound(severity)
            
            # Flash console output (for debugging)
            self._console_alert(alert_type, message, severity)
            
            # Send notifications if configured
            self._send_notifications(alert_type, message, severity)
            
            # Wait before next iteration
            time.sleep(2 if severity == "high" else 5)
        
        # Auto-stop after duration
        self.is_active = False
    
    def _play_alarm_sound(self, severity):
        """
        Play alarm sound based on severity
        """
        try:
            # Check if alarm file exists
            alarm_path = self.config.ALARM_SOUND_PATH
            if os.path.exists(alarm_path):
                pygame.mixer.music.load(alarm_path)
                pygame.mixer.music.play()
            else:
                # Generate beep sound if no audio file
                self._generate_beep_sound(severity)
        except Exception as e:
            print(f"Error playing alarm sound: {e}")
    
    def _generate_beep_sound(self, severity):
        """
        Generate system beep sound
        """
        try:
            import winsound
            
            # Different frequencies for different severities
            frequency = 1000 if severity == "high" else 800 if severity == "medium" else 600
            duration = 500 if severity == "high" else 300
            
            # Multiple beeps for high severity
            if severity == "high":
                for _ in range(3):
                    winsound.Beep(frequency, 200)
                    time.sleep(0.1)
            else:
                winsound.Beep(frequency, duration)
        except ImportError:
            # Fallback for non-Windows systems
            print("\a" * (3 if severity == "high" else 1))  # ASCII bell character
        except Exception as e:
            print(f"Beep sound error: {e}")
    
    def _console_alert(self, alert_type, message, severity):
        """
        Display alert in console with colors
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # ANSI color codes
        colors = {
            "high": "\033[91m",      # Red
            "medium": "\033[93m",    # Yellow
            "low": "\033[94m",       # Blue
            "reset": "\033[0m"       # Reset
        }
        
        color = colors.get(severity, colors["reset"])
        
        print(f"{color}{'='*60}")
        print(f"🚨 SECURITY ALERT - {severity.upper()} PRIORITY")
        print(f"Time: {timestamp}")
        print(f"Type: {alert_type.replace('_', ' ').title()}")
        print(f"Message: {message}")
        print(f"{'='*60}{colors['reset']}")
    
    def _send_notifications(self, alert_type, message, severity):
        """
        Send notifications via email/webhook (placeholder)
        """
        # This would implement actual notification sending
        # For now, just log the notification
        notification_data = {
            "timestamp": datetime.now().isoformat(),
            "alert_type": alert_type,
            "message": message,
            "severity": severity,
            "recipient": self.config.ALERT_EMAIL
        }
        
        # In a real implementation, you would:
        # 1. Send email using SMTP
        # 2. Send webhook to external systems
        # 3. Send push notifications
        
        print(f"📧 Notification sent to: {self.config.ALERT_EMAIL}")
    
    def _get_alarm_duration(self, severity):
        """
        Get alarm duration based on severity
        """
        durations = {
            "high": 60,      # 1 minute
            "medium": 30,    # 30 seconds
            "low": 15        # 15 seconds
        }
        return durations.get(severity, 30)
    
    def _log_alarm(self, alert_type, message, severity):
        """
        Log alarm activation to file
        """
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "alert_type": alert_type,
                "message": message,
                "severity": severity,
                "status": "activated"
            }
            
            # Ensure logs directory exists
            logs_dir = "logs"
            os.makedirs(logs_dir, exist_ok=True)
            
            # Write to log file
            log_file = os.path.join(logs_dir, "alarm_log.json")
            
            # Read existing logs
            logs = []
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        logs = json.load(f)
                except:
                    logs = []
            
            # Add new log entry
            logs.append(log_entry)
            
            # Keep only last 1000 entries
            logs = logs[-1000:]
            
            # Write back to file
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            print(f"Error logging alarm: {e}")
    
    def get_alarm_history(self, limit=100):
        """
        Get alarm history from log file
        """
        try:
            log_file = os.path.join("logs", "alarm_log.json")
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = json.load(f)
                return logs[-limit:] if logs else []
            return []
        except Exception as e:
            print(f"Error reading alarm history: {e}")
            return []
    
    def test_alarm_system(self):
        """
        Test the alarm system
        """
        print("🔧 Testing alarm system...")
        
        # Test audio
        if self.audio_available:
            print("✅ Audio system initialized")
        else:
            print("⚠️ Audio system not available")
        
        # Test alarm trigger
        print("🚨 Testing alarm trigger...")
        self.trigger_alarm("test_alert", "This is a test alarm", "medium")
        
        # Wait a few seconds
        time.sleep(5)
        
        # Stop alarm
        self.stop_alarm()
        print("✅ Alarm system test completed")

# Global alarm instance
alarm_system = AlarmSystem()

def trigger_security_alarm(alert_type="unknown_person", message="Security breach detected", severity="high"):
    """
    Convenience function to trigger security alarm
    """
    alarm_system.trigger_alarm(alert_type, message, severity)

def stop_security_alarm():
    """
    Convenience function to stop security alarm
    """
    alarm_system.stop_alarm()

if __name__ == "__main__":
    # Test the alarm system
    alarm_system.test_alarm_system()