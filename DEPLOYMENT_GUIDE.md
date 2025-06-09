# 🚀 SportsHunt Django Deployment Guide

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Local Production Setup](#local-production-setup)
4. [Azure Web App Deployment](#azure-web-app-deployment)
5. [Docker Deployment](#docker-deployment)
6. [Database Configuration](#database-configuration)
7. [Security Checklist](#security-checklist)
8. [Monitoring & Logging](#monitoring--logging)
9. [Troubleshooting](#troubleshooting)

---

## 📋 Prerequisites

### System Requirements
- **Python**: 3.8+ (Recommended: 3.11+)
- **Database**: SQLite3 (default) or PostgreSQL (recommended for production)
- **Web Server**: Waitress (Windows) or Gunicorn (Unix/Linux)
- **Memory**: Minimum 512MB RAM
- **Storage**: 1GB+ available space

### Required Accounts
- **Auth0**: OAuth authentication provider
- **Azure**: For cloud deployment (optional)
- **Domain**: For production deployment (optional)

---

## 🔧 Environment Configuration

### 1. Create Environment File

Create a `.env` file in the backend root directory:

```bash
# .env file for SportsHunt

# Django Configuration
DJANGO_SECRET_KEY=your-super-secret-key-here
DJANGO_SETTINGS_MODULE=sportshunt.conf.prod

# Auth0 Configuration
AUTH0_DOMAIN=your-auth0-domain.auth0.com
AUTH0_CLIENT_ID=your-auth0-client-id
AUTH0_CLIENT_SECRET=your-auth0-client-secret

# Application Configuration
FRONTEND_URL=https://your-frontend-domain.com,http://localhost:3000
JWT_SECRET=your-jwt-secret-key
ALLOWED_HOSTS=your-domain.com,localhost,127.0.0.1

# Logging Configuration (Optional)
LOGS_DIR=/path/to/logs

# Database Configuration (Optional)
DATABASE_URL=sqlite:///db.sqlite3

# Security Settings (Production)
SECURE_SSL_REDIRECT=True
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_SECURE=True
```

### 2. Environment Variables Explanation

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | ❌ | Django secret key (auto-generated if not provided) | `your-secret-key` |
| `AUTH0_DOMAIN` | ✅ | Auth0 tenant domain | `sportshunt.auth0.com` |
| `AUTH0_CLIENT_ID` | ✅ | Auth0 application client ID | `abc123xyz789` |
| `AUTH0_CLIENT_SECRET` | ✅ | Auth0 application client secret | `secret-key-here` |
| `FRONTEND_URL` | ✅ | Frontend application URLs (comma-separated) | `https://app.sportshunt.com` |
| `JWT_SECRET` | ✅ | JWT token signing secret | `your-jwt-secret` |
| `ALLOWED_HOSTS` | ❌ | Django allowed hosts (auto-derived if not provided) | `sportshunt.com,api.sportshunt.com` |
| `LOGS_DIR` | ❌ | Custom logs directory path | `/var/log/sportshunt` |

---

## 🖥️ Local Production Setup

### 1. Install Dependencies

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# OR create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Run migrations
python manage.py migrate --settings=sportshunt.conf.prod

# Create superuser (optional)
python manage.py createsuperuser --settings=sportshunt.conf.prod

# Collect static files (if serving static files)
python manage.py collectstatic --settings=sportshunt.conf.prod --noinput
```

### 3. Start Production Server

#### Option A: Cross-Platform Script (Recommended)
```bash
python start_server.py
```

#### Option B: Platform-Specific

**Windows:**
```bash
python run_prod.py
```

**Unix/Linux/Mac:**
```bash
gunicorn --config gunicorn.conf.py sportshunt.wsgi:application
```

### 4. Verify Deployment

- **Server Status**: Check console for "Starting SportsHunt..." message
- **Health Check**: Visit `http://localhost:8000/upcoming-past_tournaments/`
- **Admin Panel**: Visit `http://localhost:8000/admin/` (if superuser created)
- **Logs**: Check `logs/django.log` for application logs

---

## ☁️ Azure Web App Deployment

### 1. Azure Prerequisites

- Azure subscription
- Azure CLI installed and configured
- GitHub repository for CI/CD

### 2. Azure App Service Configuration

```bash
# Create resource group
az group create --name sportshunt-rg --location "East US"

# Create App Service plan
az appservice plan create \
    --name sportshunt-plan \
    --resource-group sportshunt-rg \
    --sku B1 \
    --is-linux

# Create web app
az webapp create \
    --resource-group sportshunt-rg \
    --plan sportshunt-plan \
    --name sportshunt-prod \
    --runtime "PYTHON|3.11"
```

### 3. Configure Application Settings

```bash
# Set environment variables
az webapp config appsettings set \
    --resource-group sportshunt-rg \
    --name sportshunt-prod \
    --settings \
    DJANGO_SETTINGS_MODULE=sportshunt.conf.prod \
    AUTH0_DOMAIN=your-auth0-domain.auth0.com \
    AUTH0_CLIENT_ID=your-client-id \
    AUTH0_CLIENT_SECRET=your-client-secret \
    FRONTEND_URL=https://your-frontend.com \
    JWT_SECRET=your-jwt-secret \
    ALLOWED_HOSTS=sportshunt-prod.azurewebsites.net
```

### 4. GitHub Actions Deployment

The repository includes GitHub Actions workflow (`.github/workflows/dev-v1.1.0_sportshunt-prod-dev.yml`):

1. **Setup Secrets** in GitHub repository:
   - `AZUREAPPSERVICE_CLIENTID_*`
   - `AZUREAPPSERVICE_TENANTID_*`
   - `AZUREAPPSERVICE_SUBSCRIPTIONID_*`

2. **Push to main branch** triggers automatic deployment

3. **Monitor deployment** in GitHub Actions tab

### 5. Custom Domain & SSL (Optional)

```bash
# Add custom domain
az webapp config hostname add \
    --webapp-name sportshunt-prod \
    --resource-group sportshunt-rg \
    --hostname api.sportshunt.com

# Enable SSL
az webapp config ssl bind \
    --certificate-thumbprint <thumbprint> \
    --ssl-type SNI \
    --name sportshunt-prod \
    --resource-group sportshunt-rg
```

---

## 🐳 Docker Deployment

### 1. Create Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=sportshunt.conf.prod

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create logs directory
RUN mkdir -p logs

# Run migrations and collect static files
RUN python manage.py migrate --noinput
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Start server
CMD ["python", "start_server.py"]
```

### 2. Create docker-compose.yml

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DJANGO_SETTINGS_MODULE=sportshunt.conf.prod
      - AUTH0_DOMAIN=${AUTH0_DOMAIN}
      - AUTH0_CLIENT_ID=${AUTH0_CLIENT_ID}
      - AUTH0_CLIENT_SECRET=${AUTH0_CLIENT_SECRET}
      - FRONTEND_URL=${FRONTEND_URL}
      - JWT_SECRET=${JWT_SECRET}
    volumes:
      - ./logs:/app/logs
      - ./db.sqlite3:/app/db.sqlite3
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - web
    restart: unless-stopped
```

### 3. Deploy with Docker

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## 🗄️ Database Configuration

### SQLite (Default)

```python
# Already configured in settings
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
```

### PostgreSQL (Recommended for Production)

1. **Install PostgreSQL**:
```bash
pip install psycopg2-binary
```

2. **Update settings**:
```python
# In prod.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'sportshunt'),
        'USER': os.environ.get('DB_USER', 'sportshunt_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

3. **Environment variables**:
```bash
DB_NAME=sportshunt
DB_USER=sportshunt_user
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=5432
```

---

## 🔒 Security Checklist

### Pre-Deployment Security

- [ ] **Environment Variables**: All sensitive data in environment variables
- [ ] **Secret Key**: Strong Django secret key set
- [ ] **Debug Mode**: `DEBUG=False` in production
- [ ] **Allowed Hosts**: Properly configured allowed hosts
- [ ] **HTTPS**: SSL/TLS certificates configured
- [ ] **Auth0**: Proper Auth0 configuration and callback URLs
- [ ] **CORS**: Frontend URLs properly configured in CORS settings

### Production Security Features

```python
# Already configured in prod.py
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

### Additional Security Measures

1. **Regular Updates**: Keep dependencies updated
2. **Database Backups**: Implement backup strategy
3. **Access Logs**: Monitor access patterns
4. **Rate Limiting**: Implement API rate limiting
5. **Firewall**: Configure server firewall rules

---

## 📊 Monitoring & Logging

### Logging Configuration

The application includes robust logging with fallback strategies:

1. **Primary Location**: `logs/django.log`
2. **Fallback Location**: System temp directory
3. **Log Levels**: INFO for application, WARNING for root
4. **Log Rotation**: Configure external log rotation

### Monitoring Endpoints

- **Health Check**: `GET /upcoming-past_tournaments/`
- **Admin Panel**: `/admin/` (if enabled)
- **API Documentation**: Available in `PROJECT_ANALYSIS.md`

### Log Analysis

```bash
# View recent logs
tail -f logs/django.log

# Search for errors
grep "ERROR" logs/django.log

# Monitor real-time logs
tail -f logs/django.log | grep "INFO\|ERROR\|WARNING"
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. FileNotFoundError: logs directory
**Solution**: The application now automatically creates logs directory with fallbacks

#### 2. Auth0 Authentication Fails
**Checklist**:
- [ ] Verify Auth0 domain, client ID, and secret
- [ ] Check Auth0 callback URLs include your deployment URL
- [ ] Ensure FRONTEND_URL is correctly configured

#### 3. CORS Errors
**Solution**:
```python
# Ensure frontend URL is in CORS_ALLOWED_ORIGINS
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend-domain.com",
    "http://localhost:3000"  # For development
]
```

#### 4. Static Files Not Loading
**Solution**:
```bash
# Collect static files
python manage.py collectstatic --settings=sportshunt.conf.prod

# Configure web server to serve static files
# See nginx configuration examples
```

#### 5. Database Migration Errors
**Solution**:
```bash
# Reset migrations (⚠️ Data Loss)
python manage.py migrate --fake-initial

# Or apply specific migration
python manage.py migrate app_name migration_name
```

### Performance Optimization

1. **Database Indexing**: Add indexes for frequently queried fields
2. **Caching**: Implement Redis caching for API responses
3. **Static Files**: Use CDN for static file delivery
4. **Database Connection Pooling**: Configure connection pooling

### Debug Mode

For troubleshooting, temporarily enable debug mode:

```python
# In settings
DEBUG = True
LOGGING['root']['level'] = 'DEBUG'
```

**⚠️ Remember to disable debug mode in production!**

---

## 📞 Support & Resources

### Documentation
- **API Documentation**: `PROJECT_ANALYSIS.md`
- **Task History**: `TASKS.md`
- **Django Documentation**: https://docs.djangoproject.com/

### Useful Commands

```bash
# Check Django configuration
python manage.py check --settings=sportshunt.conf.prod

# Run specific migration
python manage.py migrate app_name --settings=sportshunt.conf.prod

# Create admin user
python manage.py createsuperuser --settings=sportshunt.conf.prod

# Django shell
python manage.py shell --settings=sportshunt.conf.prod

# Show URLs
python manage.py show_urls --settings=sportshunt.conf.prod
```

### Environment Testing

```bash
# Test production configuration
python -c "
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'sportshunt.conf.prod'
import django
django.setup()
print('✅ Production configuration loaded successfully')
"
```

---

## 🎯 Quick Start Checklist

### For New Deployment:

1. [ ] Clone repository
2. [ ] Install dependencies (`pip install -r requirements.txt`)
3. [ ] Create `.env` file with required variables
4. [ ] Run migrations (`python manage.py migrate --settings=sportshunt.conf.prod`)
5. [ ] Start server (`python start_server.py`)
6. [ ] Test health endpoint (`curl http://localhost:8000/upcoming-past_tournaments/`)
7. [ ] Configure Auth0 callback URLs
8. [ ] Set up monitoring and backups

### For Updates:

1. [ ] Pull latest code
2. [ ] Update dependencies (`pip install -r requirements.txt`)
3. [ ] Run migrations (`python manage.py migrate --settings=sportshunt.conf.prod`)
4. [ ] Restart server
5. [ ] Verify functionality

---

**🏆 SportsHunt is now ready for production deployment!**

*For additional support or custom deployment scenarios, refer to the Django documentation or create an issue in the repository.*
