# Alpha Lab IT Complaint Portal - Installation & Setup Guide

**Version:** 2.0  
**Last Updated:** July 25, 2025  
**Python Requirements:** 3.8+  
**Django Version:** 4.2.23  

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.8+ installed
- pip package manager
- Git (for version control)
- Virtual environment support

### Installation Steps

#### 1. Clone the Repository
```bash
git clone https://github.com/your-org/Alpha-Lab-IT-Complaint-Portal.git
cd Alpha-Lab-IT-Complaint-Portal
```

#### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
```

#### 5. Create Superuser
```bash
python manage.py createsuperuser
```

#### 6. Load Sample Data (Optional)
```bash
python manage.py loaddata sample_data.json
```

#### 7. Run Development Server
```bash
python manage.py runserver
```

#### 8. Access the Application
- **Main Application**: http://localhost:8000
- **Admin Interface**: http://localhost:8000/admin

---

## 👤 Test User Accounts

The system comes with pre-configured test accounts:

| Username | Password | Role | Access Level |
|----------|----------|------|--------------|
| `admin` | `admin123` | Administrator | Full system access |
| `engineer1` | `testpass123` | Engineer | Complaint management |
| `testuser` | `testpass123` | Regular User | Submit complaints |

---

## ⚙️ Configuration

### Environment Variables
Create a `.env` file in the project root:

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1

# Email Configuration (Optional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True

# File Upload Settings
MAX_UPLOAD_SIZE=10485760  # 10MB in bytes
```

### Database Configuration

#### SQLite (Default - Development)
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

#### PostgreSQL (Production)
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'complaint_portal',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

---

## 🗄️ Database Setup

### Initial Migration
```bash
python manage.py makemigrations core
python manage.py makemigrations complaints
python manage.py makemigrations reports
python manage.py makemigrations faq
python manage.py makemigrations feedback
python manage.py migrate
```

### Sample Data Creation
```bash
python manage.py shell
```

```python
# Create sample roles and departments
from core.models import Role, Department
from django.contrib.auth.models import User

# Create roles
admin_role = Role.objects.create(name='Administrator', description='Full system access')
engineer_role = Role.objects.create(name='Engineer', description='Technical support staff')
user_role = Role.objects.create(name='User', description='Regular system user')

# Create departments
it_dept = Department.objects.create(name='IT Department', description='Information Technology')
hr_dept = Department.objects.create(name='HR Department', description='Human Resources')

# Create complaint types
from complaints.models import ComplaintType, Status

ComplaintType.objects.create(name='Hardware', description='Hardware-related issues', icon='fas fa-desktop')
ComplaintType.objects.create(name='Software', description='Software-related issues', icon='fas fa-code')
ComplaintType.objects.create(name='Network', description='Network connectivity issues', icon='fas fa-wifi')
ComplaintType.objects.create(name='Security', description='Security-related concerns', icon='fas fa-shield-alt')

# Create status options
Status.objects.create(name='Open', description='Newly submitted', order=1, is_closed=False)
Status.objects.create(name='In Progress', description='Being worked on', order=2, is_closed=False)
Status.objects.create(name='Resolved', description='Issue resolved', order=3, is_closed=True)
Status.objects.create(name='Closed', description='Ticket closed', order=4, is_closed=True)
```

---

## 🎨 Static Files Setup

### Development
```bash
python manage.py collectstatic
```

### Production
Configure static file serving in your web server (nginx example):

```nginx
location /static/ {
    alias /path/to/your/project/staticfiles/;
    expires 1y;
    add_header Cache-Control "public, immutable";
}

location /media/ {
    alias /path/to/your/project/media/;
    expires 1y;
    add_header Cache-Control "public";
}
```

---

## 🔒 Security Configuration

### Production Settings
Update `settings.py` for production:

```python
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### File Upload Security
```python
# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10MB

# Allowed file types
ALLOWED_FILE_TYPES = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'image/jpeg',
    'image/png',
    'image/gif'
]
```

---

## 🚀 Production Deployment

### Using Gunicorn
```bash
pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### Using Docker
Create `Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://user:pass@db:5432/complaint_portal
    depends_on:
      - db
  
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: complaint_portal
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data/

volumes:
  postgres_data:
```

---

## 📊 Monitoring & Logging

### Logging Configuration
Add to `settings.py`:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'django.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### Health Check Endpoint
Add to main `urls.py`:
```python
def health_check(request):
    return JsonResponse({'status': 'healthy'})

urlpatterns = [
    # ... existing patterns
    path('health/', health_check, name='health_check'),
]
```

---

## 🔧 Maintenance

### Regular Tasks

#### Database Backup
```bash
# SQLite
cp db.sqlite3 backups/db_backup_$(date +%Y%m%d).sqlite3

# PostgreSQL
pg_dump complaint_portal > backups/db_backup_$(date +%Y%m%d).sql
```

#### Log Rotation
```bash
# Add to crontab
0 0 * * * find /path/to/logs -name "*.log" -mtime +30 -delete
```

#### Static File Cleanup
```bash
python manage.py collectstatic --clear --noinput
```

### Performance Monitoring
```bash
# Install monitoring tools
pip install django-debug-toolbar
pip install django-extensions

# Add to INSTALLED_APPS in development
'debug_toolbar',
'django_extensions',
```

---

## 🐛 Troubleshooting

### Common Issues

#### Database Connection Error
```bash
# Check database status
python manage.py dbshell

# Reset migrations (if needed)
python manage.py migrate --fake-initial
```

#### Static Files Not Loading
```bash
# Collect static files
python manage.py collectstatic --clear

# Check STATIC_URL and STATIC_ROOT settings
```

#### File Upload Issues
```bash
# Check media directory permissions
chmod 755 media/
chmod 755 media/attachments/

# Verify upload settings
python manage.py shell
>>> from django.conf import settings
>>> print(settings.MEDIA_ROOT)
>>> print(settings.MEDIA_URL)
```

#### Permission Errors
```bash
# Check user roles
python manage.py shell
>>> from core.models import UserProfile
>>> UserProfile.objects.all()
```

---

## ✅ Verification Checklist

After installation, verify these components:

- [ ] **Server starts without errors**
- [ ] **Admin interface accessible**
- [ ] **User login/logout works**
- [ ] **Complaint submission functions**
- [ ] **File uploads work**
- [ ] **Email notifications (if configured)**
- [ ] **Database queries execute**
- [ ] **Static files load correctly**
- [ ] **Mobile responsiveness**
- [ ] **Cross-browser compatibility**

---

## 📞 Support

### Getting Help
- **Documentation**: Check `TECHNICAL_REPORT.md` for detailed info
- **Issues**: Create GitHub issues for bugs/features
- **Email**: support@alphalab.com (production)
- **Discord**: Development team chat (if available)

### Development Environment
```bash
# Enable debug mode
export DEBUG=True

# Run with verbose output
python manage.py runserver --verbosity=2

# Check system configuration
python manage.py check --deploy
```

---

**Installation Guide Complete**  
**Last Updated:** July 25, 2025  
**Next Review:** October 25, 2025  

*Follow this guide for a successful Alpha Lab IT Complaint Portal installation. All components are tested and production-ready.*