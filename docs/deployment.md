# Deployment Guide

This guide explains how to deploy the SportsHunt backend to a production environment with native authentication.

## 🚀 Deployment Checklist

- [ ] Set up a production database (PostgreSQL recommended)
- [ ] Configure environment variables (see `.env` example below)
- [ ] Set `DEBUG=False` in production
- [ ] Set up a secure `SECRET_KEY` and `JWT_SECRET`
- [ ] Configure allowed hosts
- [ ] Set up static and media file hosting
- [ ] Configure Google OAuth for production domain
- [ ] Set up email service for password reset (future)
- [ ] Set up a WSGI server (e.g., Gunicorn, Waitress)
- [ ] Use a reverse proxy (e.g., Nginx, Apache)
- [ ] Set up HTTPS (SSL/TLS) - required for secure cookies
- [ ] Set up logging and monitoring
- [ ] Configure CORS for production frontend URL

## 📝 Production Environment Variables

### Required Variables

```env
# Django Settings
DEBUG=False
DJANGO_SECRET_KEY=your-secure-random-production-secret-key
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-production-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-production-client-secret

# JWT Configuration
JWT_SECRET=your-secure-jwt-secret-key-different-from-django-secret

# Frontend Configuration
FRONTEND_URL=https://yourdomain.com

# Database Configuration
DATABASE_URL=postgres://user:password@host:port/dbname

# Optional: Email Configuration (for future password reset)
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_HOST_USER=your-email@gmail.com
# EMAIL_HOST_PASSWORD=your-app-password
```

### Security Notes

**SECRET_KEY Generation:**
```python
import secrets
import string

# Generate Django SECRET_KEY
''.join(secrets.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(50))

# Generate JWT_SECRET
''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(64))
```

**Important:**
- Use different values for `DJANGO_SECRET_KEY` and `JWT_SECRET`
- Never commit secrets to version control
- Rotate secrets periodically
- Use environment-specific secrets

## 🔐 Google OAuth Production Setup

### 1. Google Cloud Console Configuration

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your production project
3. Navigate to "Credentials"
4. Edit your OAuth 2.0 Client ID
5. Add production URLs:
   - **Authorized JavaScript origins:**
     - `https://yourdomain.com`
     - `https://www.yourdomain.com` (if applicable)
   - **DO NOT** include `http://` URLs in production
6. Save changes

### 2. Frontend Integration

Update your frontend Google Sign-In initialization:

```javascript
google.accounts.id.initialize({
    client_id: 'YOUR_PRODUCTION_CLIENT_ID',
    callback: handleCredentialResponse,
    // Production-specific options
    auto_select: false,
    cancel_on_tap_outside: true
});
```

## 🗄️ Database Setup

### PostgreSQL (Recommended)

**Install PostgreSQL:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE sportshunt;
CREATE USER sportshunt_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE sportshunt TO sportshunt_user;
\q
```

**Update settings:**
```python
# sportshunt/conf/prod.py

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'sportshunt',
        'USER': 'sportshunt_user',
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

**Install psycopg2:**
```bash
pip install psycopg2-binary
```

### Run Migrations

```bash
python manage.py migrate
python manage.py createsuperuser
```

## 📦 Static & Media Files

### Configure Static Files

```python
# sportshunt/conf/prod.py

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### Collect Static Files

```bash
python manage.py collectstatic --noinput
```

## 🚀 WSGI Server Setup

### Gunicorn (Recommended)

**Install:**
```bash
pip install gunicorn
```

**Run:**
```bash
gunicorn sportshunt.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class sync \
    --timeout 120 \
    --access-logfile logs/gunicorn-access.log \
    --error-logfile logs/gunicorn-error.log \
    --log-level info
```

**Systemd Service:**
```ini
# /etc/systemd/system/sportshunt.service

[Unit]
Description=SportsHunt Django Application
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/sportshunt
Environment="PATH=/var/www/sportshunt/venv/bin"
ExecStart=/var/www/sportshunt/venv/bin/gunicorn \
    --workers 4 \
    --bind unix:/var/www/sportshunt/sportshunt.sock \
    sportshunt.wsgi:application

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl enable sportshunt
sudo systemctl start sportshunt
sudo systemctl status sportshunt
```

### Waitress (Alternative, cross-platform)

**Install:**
```bash
pip install waitress
```

**Run:**
```bash
waitress-serve --port=8000 sportshunt.wsgi:application
```

## 🌐 Nginx Configuration

### Full Configuration Example

```nginx
# /etc/nginx/sites-available/sportshunt

upstream sportshunt_backend {
    server unix:/var/www/sportshunt/sportshunt.sock fail_timeout=0;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Client body size limit (for file uploads)
    client_max_body_size 10M;

    # Static files
    location /static/ {
        alias /var/www/sportshunt/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /var/www/sportshunt/media/;
        expires 7d;
    }

    # API endpoints
    location / {
        proxy_pass http://sportshunt_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 75s;
        proxy_send_timeout 75s;
        proxy_read_timeout 75s;
    }
}
```

### Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/sportshunt /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔒 HTTPS Setup with Let's Encrypt

**Install Certbot:**
```bash
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx
```

**Obtain Certificate:**
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

**Auto-renewal:**
```bash
sudo certbot renew --dry-run
```

## 🔐 Cookie Security Configuration

For production with HTTPS, cookies are configured securely:

```python
# sportshunt/conf/prod.py

# Session cookies
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# CSRF cookies
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False  # Must be accessible to JavaScript
CSRF_COOKIE_SAMESITE = 'Lax'

# Security settings
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

**JWT Cookie Settings in Views:**
```python
# Production JWT cookies are set with:
response.set_cookie(
    'jwt_token',
    token,
    httponly=True,      # Prevents JavaScript access
    secure=True,        # HTTPS only
    samesite='Lax',     # CSRF protection (change from 'None' in dev)
    max_age=30*24*60*60 # 30 days
)
```

## 📊 Logging and Monitoring

### Django Logging Configuration

```python
# sportshunt/conf/prod.py

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/sportshunt/django.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/sportshunt/django-error.log',
            'maxBytes': 10485760,
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'coreApi': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'organizationApi': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### Monitoring Tools

**Sentry (Error Tracking):**
```bash
pip install sentry-sdk
```

```python
# sportshunt/conf/prod.py
import sentry_sdk

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    traces_sample_rate=0.1,
    profiles_sample_rate=0.1,
)
```

## 🔧 Performance Optimization

### Database Connection Pooling

```python
# Install pgbouncer or use Django database connection pooling
DATABASES['default']['CONN_MAX_AGE'] = 600
```

### Caching with Redis

```bash
pip install redis django-redis
```

```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

## 🚨 Troubleshooting

### Common Production Issues

**1. 502 Bad Gateway**
- Check Gunicorn/WSGI server is running
- Verify socket file permissions
- Check Nginx error logs: `sudo tail -f /var/log/nginx/error.log`

**2. Static Files Not Loading**
- Run `python manage.py collectstatic`
- Check Nginx static file path
- Verify file permissions

**3. CORS Errors**
- Verify `FRONTEND_URL` matches exactly
- Check `CORS_ALLOWED_ORIGINS` includes production URL
- Ensure `CORS_ALLOW_CREDENTIALS = True`

**4. Cookie Not Set**
- Must use HTTPS in production
- Check `secure=True` in cookie settings
- Verify SameSite settings (should be 'Lax' for production)

**5. Google OAuth Fails**
- Check production URL is in Google Console authorized origins
- Verify `GOOGLE_CLIENT_ID` is correct
- Check that Google+ API is enabled

### Log Locations

```bash
# Django logs
tail -f /var/log/sportshunt/django.log
tail -f /var/log/sportshunt/django-error.log

# Gunicorn logs
tail -f logs/gunicorn-access.log
tail -f logs/gunicorn-error.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Systemd service logs
sudo journalctl -u sportshunt -f
```

## ✅ Post-Deployment Checklist

- [ ] Test user registration with email/password
- [ ] Test login with email/password
- [ ] Test Google OAuth login (if enabled)
- [ ] Verify JWT tokens are set as cookies
- [ ] Test protected endpoints with authentication
- [ ] Verify HTTPS is working
- [ ] Check static files load correctly
- [ ] Test CORS with frontend
- [ ] Monitor error logs for issues
- [ ] Set up automated backups
- [ ] Configure monitoring and alerts
- [ ] Document deployment process
- [ ] Set up staging environment

## 📚 Additional Resources

- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Google OAuth Production Best Practices](https://developers.google.com/identity/protocols/oauth2/production-readiness)

---

Need help? Check the [Troubleshooting Guide](./troubleshooting.md) or create an issue!
