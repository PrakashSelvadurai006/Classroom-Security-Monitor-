# 🔐 AI Classroom Entry Monitor

A professional web application that uses AI-powered face recognition to monitor classroom entry, identify students, and trigger security alerts for unknown persons.

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-v3.0.0-green.svg)
![OpenCV](https://img.shields.io/badge/opencv-v4.8.1-red.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 🌟 Features

### 🎯 Core Functionality
- **Real-time Face Detection**: Live webcam monitoring with AI-powered face detection
- **Student Recognition**: Compare detected faces against a database of known students
- **Security Alerts**: Automatic alarm system for unknown persons
- **Entry Logging**: Comprehensive logging of all entry attempts with timestamps

### 🖥️ Professional Web Interface
- **Modern Dashboard**: Real-time monitoring with live camera feed
- **Student Management**: Add, edit, and manage student profiles with photos
- **Alert System**: View and manage security alerts with different severity levels
- **Entry History**: Detailed logs with filtering and search capabilities

### 🤖 AI-Powered Recognition
- **OpenRouter AI Integration**: Uses free AI models for face analysis
- **Multiple Model Support**: Gemini Flash 1.5 and Llama 3.2 Vision models
- **High Accuracy**: Advanced facial feature extraction and comparison
- **Confidence Scoring**: Detailed similarity scores for recognition accuracy

### 🔧 Advanced Features
- **Multi-user Support**: Manage multiple students with individual profiles
- **Database Integration**: PostgreSQL support for scalable data storage
- **Alarm System**: Audio and visual alerts with configurable severity levels
- **Professional UI**: Responsive design with Bootstrap and modern styling

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   AI Service    │
│   (HTML/JS)     │◄──►│   (Flask)       │◄──►│   (OpenRouter)  │
│                 │    │                 │    │                 │
│ • Dashboard     │    │ • Face Monitor  │    │ • Face Detection│
│ • Student Mgmt  │    │ • Entry Logging │    │ • Feature Extract│
│ • Alert System  │    │ • Alert System  │    │ • Face Compare  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────►│   Database      │◄─────────────┘
                        │   (PostgreSQL)  │
                        │                 │
                        │ • Students      │
                        │ • Entry Logs    │
                        │ • System Alerts │
                        └─────────────────┘
```

## 📋 Prerequisites

- **Python 3.8+** - Programming language
- **PostgreSQL** - Database (optional, SQLite fallback available)
- **Webcam** - For live face detection
- **OpenRouter API Key** - For AI face recognition (free tier available)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd ai-classroom-monitor
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings (see Configuration section)
```

### 4. Setup Database
```bash
# For PostgreSQL (recommended)
createdb classroom_monitor

# For SQLite (development)
# No additional setup needed
```

### 5. Initialize Database
```bash
python app.py
# Database tables will be created automatically
```

### 6. Run the Application
```bash
python app.py
```

Visit `http://localhost:5000` to access the application.

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# OpenRouter AI API Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Database Configuration (PostgreSQL)
DATABASE_URL=postgresql://username:password@localhost:5432/classroom_monitor
DB_HOST=localhost
DB_PORT=5432
DB_NAME=classroom_monitor
DB_USER=username
DB_PASSWORD=password

# Flask Configuration
FLASK_SECRET_KEY=your_secret_key_here
FLASK_ENV=development
DEBUG=True

# Upload Configuration
UPLOAD_FOLDER=static/uploads/known_faces
MAX_CONTENT_LENGTH=16777216  # 16MB

# Alarm Configuration
ALARM_SOUND_PATH=static/sounds/alarm.mp3
ALERT_EMAIL=admin@school.com
```

### OpenRouter AI Setup

1. **Sign up** at [OpenRouter.ai](https://openrouter.ai)
2. **Get API Key** from your dashboard (free tier available)
3. **Add to .env**: Set `OPENROUTER_API_KEY=your_key_here`

**Free Models Used:**
- `google/gemini-flash-1.5` - Primary vision model
- `meta-llama/llama-3.2-11b-vision-instruct:free` - Backup model

### Database Setup

#### PostgreSQL (Recommended)
```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib  # Ubuntu/Debian
brew install postgresql  # macOS

# Create database
sudo -u postgres createdb classroom_monitor
sudo -u postgres createuser your_username

# Set password
sudo -u postgres psql
ALTER USER your_username PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE classroom_monitor TO your_username;
```

#### SQLite (Development)
If you don't configure PostgreSQL, the system will automatically use SQLite:
```bash
# Automatically created as: classroom_monitor.db
```

## 📱 Usage Guide

### 1. Initial Setup
1. **Start the application**: `python app.py`
2. **Open browser**: Navigate to `http://localhost:5000`
3. **Add students**: Click "Add Student" to register known faces

### 2. Adding Students
1. **Navigate**: Dashboard → Add Student
2. **Fill form**: Name, Student ID, Email (optional), Phone (optional)
3. **Upload photo**: Clear, front-facing photo for best recognition
4. **Save**: AI will automatically extract facial features

### 3. Start Monitoring
1. **Dashboard**: Click "Start Monitoring"
2. **Camera access**: Allow webcam permissions
3. **Live feed**: View real-time camera feed with face detection
4. **Automatic alerts**: System triggers alarms for unknown faces

### 4. Managing Alerts
1. **View alerts**: Dashboard → Alerts
2. **Filter by severity**: High, Medium, Low priority
3. **Resolve alerts**: Mark alerts as resolved
4. **View details**: See captured images and timestamps

### 5. Entry Logs
1. **View history**: Dashboard → Entry Logs
2. **Filter by date**: Search specific time periods
3. **Export data**: Download entry history (feature in development)

## 🎯 Face Recognition Guidelines

### Photo Requirements
- **Lighting**: Well-lit, avoid shadows
- **Angle**: Front-facing, looking at camera
- **Quality**: High resolution, clear image
- **Background**: Simple, uncluttered
- **Face coverage**: No sunglasses, masks, or obstructions

### Recognition Accuracy
- **Confidence threshold**: 70% similarity required
- **Multiple photos**: Add 2-3 photos per student for better accuracy
- **Lighting variations**: Include photos in different lighting conditions

## 🔧 Troubleshooting

### Common Issues

#### Camera Not Working
```bash
# Check camera permissions
# Ensure no other applications are using the camera
# Try different camera index in app.py (change from 0 to 1)
```

#### AI API Errors
```bash
# Verify OpenRouter API key
# Check internet connection
# Ensure sufficient API credits
```

#### Database Connection Issues
```bash
# PostgreSQL: Check connection string
# Ensure database exists
# Verify user permissions
```

#### Face Recognition Accuracy
```bash
# Add multiple photos per student
# Ensure good photo quality
# Check lighting conditions
# Verify face is clearly visible
```

### Error Logs
- **Application logs**: Check console output
- **Alarm logs**: `logs/alarm_log.json`
- **Database errors**: Check Flask debug output

## 🏗️ Development

### Project Structure
```
ai-classroom-monitor/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── models.py             # Database models
├── ai_service.py         # AI/OpenRouter integration
├── alarm_system.py       # Security alarm system
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables
├── templates/            # HTML templates
│   ├── base.html        # Base template
│   ├── index.html       # Dashboard
│   ├── students.html    # Student management
│   ├── add_student.html # Add student form
│   ├── entry_logs.html  # Entry history
│   └── alerts.html      # Alert management
├── static/              # Static files
│   ├── uploads/         # Student photos
│   └── sounds/          # Alarm sounds
└── logs/                # Application logs
```

### Adding New Features
1. **Models**: Add to `models.py`
2. **Routes**: Add to `app.py`
3. **Templates**: Create in `templates/`
4. **AI Features**: Extend `ai_service.py`

### API Integration
The system uses OpenRouter AI API for face recognition:
- **Face Detection**: Identify faces in images
- **Feature Extraction**: Create facial feature vectors
- **Face Comparison**: Calculate similarity scores

## 📊 Performance

### System Requirements
- **RAM**: 4GB minimum, 8GB recommended
- **CPU**: Multi-core processor recommended
- **Storage**: 1GB for application, additional for photos/logs
- **Network**: Internet connection for AI API calls

### Optimization Tips
- **Camera resolution**: Lower resolution for better performance
- **Processing interval**: Adjust monitoring frequency
- **Database cleanup**: Regular cleanup of old logs
- **Photo compression**: Optimize student photos

## 🔒 Security

### Data Protection
- **Local storage**: Student photos stored locally
- **Encrypted connection**: HTTPS recommended for production
- **API security**: OpenRouter API key protection
- **Database security**: Use strong database credentials

### Privacy Considerations
- **Consent**: Ensure student consent for photo collection
- **Data retention**: Implement data retention policies
- **Access control**: Limit system access to authorized personnel

## 📈 Future Enhancements

### Planned Features
- [ ] **Multi-camera support**: Monitor multiple entrances
- [ ] **Mobile app**: iOS/Android companion app
- [ ] **Email notifications**: Automated alert emails
- [ ] **Advanced analytics**: Entry patterns and statistics
- [ ] **Integration APIs**: Connect with school management systems
- [ ] **Cloud deployment**: Docker containers and cloud hosting
- [ ] **Backup system**: Automated data backup
- [ ] **Role-based access**: Different user permission levels

### Contributing
1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenRouter AI** - For providing free AI models
- **OpenCV** - Computer vision library
- **Flask** - Web framework
- **Bootstrap** - UI framework
- **Font Awesome** - Icons

## 📞 Support

For support and questions:
- **Issues**: GitHub Issues
- **Documentation**: This README
- **Email**: [your-email@domain.com]

---

**Made with ❤️ for classroom security and student safety**