from .common import *
from dotenv import load_dotenv
import os
import secrets
import string
from pathlib import Path
import tempfile

load_dotenv()

# Production-specific logging configuration
LOGS_DIR = os.environ.get('LOGS_DIR', str(BASE_DIR / 'logs'))
LOGS_PATH = Path(LOGS_DIR)

# Ensure logs directory exists with proper fallback strategy
def ensure_log_directory():
    """
    Create logs directory with multiple fallback options for different environments.
    Returns the absolute path to the log file.
    """
    # Primary: Use configured logs directory
    try:
        LOGS_PATH.mkdir(parents=True, exist_ok=True)
        log_file = LOGS_PATH / 'django.log'
        # Test write permissions
        log_file.touch(exist_ok=True)
        return str(log_file)
    except (PermissionError, OSError):
        pass
    
    # Secondary: Try system temp directory with app-specific folder
    try:
        temp_logs = Path(tempfile.gettempdir()) / 'sportshunt_logs'
        temp_logs.mkdir(parents=True, exist_ok=True)
        log_file = temp_logs / 'django.log'
        log_file.touch(exist_ok=True)
        return str(log_file)
    except (PermissionError, OSError):
        pass
    
    # Tertiary: Use current working directory
    try:
        cwd_logs = Path.cwd() / 'logs'
        cwd_logs.mkdir(parents=True, exist_ok=True)
        log_file = cwd_logs / 'django.log'
        log_file.touch(exist_ok=True)
        return str(log_file)
    except (PermissionError, OSError):
        pass
    
    # Final fallback: Return None to disable file logging
    return None

LOG_FILE_PATH = ensure_log_directory()

# Override logging configuration for production
def get_logging_config():
    """
    Get logging configuration with conditional file handler.
    """
    handlers = {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'null': {
            'class': 'logging.NullHandler',
        },
    }
    
    # Only add file handler if we have a valid log file path
    if LOG_FILE_PATH:
        handlers['file'] = {
            'class': 'logging.FileHandler',
            'filename': LOG_FILE_PATH,
            'formatter': 'verbose',
        }
        default_handlers = ['console', 'file']
        app_handlers = ['file']
    else:
        # Fallback to console-only logging if file logging fails
        default_handlers = ['console']
        app_handlers = ['console']
    
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
                'style': '{',
            },
            'simple': {
                'format': '{levelname} {message}',
                'style': '{',
            },
        },
        'handlers': handlers,
        'root': {
            'handlers': default_handlers,
            'level': 'WARNING',
        },
        'loggers': {
            'django': {
                'handlers': default_handlers,
                'level': 'INFO',
                'propagate': False,
            },
            'organizationApi': {
                'handlers': app_handlers,
                'level': 'INFO',
                'propagate': False,
            },
            'coreApi': {
                'handlers': app_handlers,
                'level': 'INFO',
                'propagate': False,
            },
            'sportshunt': {
                'handlers': app_handlers,
                'level': 'INFO',
                'propagate': False,
            },
            # Silence noisy third-party loggers
            'social_django': {
                'handlers': ['null'],
                'level': 'WARNING',
                'propagate': False,
            },
        },
    }

LOGGING = get_logging_config()

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', ''.join(secrets.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(50)))
DEBUG = False

required_env_vars = {
    'AUTH0_DOMAIN': os.environ.get('AUTH0_DOMAIN'),
    'AUTH0_CLIENT_ID': os.environ.get('AUTH0_CLIENT_ID'),
    'AUTH0_CLIENT_SECRET': os.environ.get('AUTH0_CLIENT_SECRET'),
    'FRONTEND_URL': os.environ.get('FRONTEND_URL'),
    'JWT_SECRET': os.environ.get('JWT_SECRET')
}

for var_name, value in required_env_vars.items():
    if not value:
        raise ValueError(f"Missing required environment variable: {var_name}")

SOCIAL_AUTH_AUTH0_DOMAIN = required_env_vars['AUTH0_DOMAIN']
SOCIAL_AUTH_AUTH0_KEY = required_env_vars['AUTH0_CLIENT_ID']
SOCIAL_AUTH_AUTH0_SECRET = required_env_vars['AUTH0_CLIENT_SECRET']
FRONTEND_URL = required_env_vars['FRONTEND_URL'].strip().split(",")
JWT_SECRET = required_env_vars['JWT_SECRET'].strip()

ALLOWED_HOSTS = required_env_vars.get('ALLOWED_HOSTS', '').strip().split(",")

CSRF_TRUSTED_ORIGINS = [
    *[f"{url.strip()}" for url in FRONTEND_URL ],
    *[f"https://{url.strip()}" for url in ALLOWED_HOSTS ],
]

CSRF_COOKIE_SECURE = False  # Set to True in production with HTTPS
CSRF_COOKIE_HTTPONLY = False  # Ensure CSRF token is accessible to JavaScript

STATIC_URL = "static/"

WSGI_APPLICATION = "sportshunt.wsgi.application"

CORS_ALLOWED_ORIGINS = [
    *[f"{url.strip()}" for url in FRONTEND_URL],
    *[f"https://{url.strip()}" for url in ALLOWED_HOSTS ],
]
CSRF_COOKIE_SAMESITE = 'Lax'

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Security settings
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SECURE_SSL_REDIRECT = True

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
