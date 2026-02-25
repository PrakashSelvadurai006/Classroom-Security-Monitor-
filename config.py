import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'dev-secret-key'
    
    # Use SQLite for development (reliable and no setup required)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///classroom_monitor.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # OpenRouter AI Configuration
    OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
    OPENROUTER_BASE_URL = os.environ.get('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
    
    # Upload Configuration
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'static/uploads/known_faces')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16777216))  # 16MB
    
    # Alarm Configuration
    ALARM_SOUND_PATH = os.environ.get('ALARM_SOUND_PATH', 'static/sounds/alarm.mp3')
    ALERT_EMAIL = os.environ.get('ALERT_EMAIL', 'admin@school.com')
    
    # Ensure upload directory exists
    @staticmethod
    def init_app(app):
        upload_path = os.path.join(app.instance_path, '..', Config.UPLOAD_FOLDER)
        os.makedirs(upload_path, exist_ok=True)
        
        # Create sounds directory
        sounds_path = os.path.join(app.instance_path, '..', 'static/sounds')
        os.makedirs(sounds_path, exist_ok=True)