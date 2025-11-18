from .common import *
from dotenv import load_dotenv
import os
from pathlib import Path
import tempfile
from urllib.parse import urlparse

load_dotenv()


def get_required_env(var_name):
    value = os.environ.get(var_name)
    if value is None:
        raise ValueError(f"Missing required environment variable: {var_name}")
    value = value.strip()
    if not value:
        raise ValueError(f"Environment variable '{var_name}' cannot be empty")
    return value


def parse_csv(value):
    return [item.strip() for item in value.split(",") if item.strip()]


def prepare_frontend_urls(urls):
    formatted_urls = []
    origins = []
    for url in urls:
        cleaned = url.strip()
        if not cleaned:
            continue

        parsed = urlparse(cleaned)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(
                "FRONTEND_URL entries must be fully qualified URLs "
                "(e.g., https://app.example.com)"
            )

        formatted_urls.append(cleaned)
        origins.append(f"{parsed.scheme}://{parsed.netloc}")

    if not formatted_urls:
        raise ValueError("FRONTEND_URL must include at least one valid URL")

    # Preserve ordering while removing duplicates
    return list(dict.fromkeys(formatted_urls)), list(dict.fromkeys(origins))


def normalize_allowed_hosts(hosts):
    normalized = []
    for host in hosts:
        cleaned = host.strip()
        if not cleaned:
            continue
        if "://" in cleaned:
            raise ValueError("ALLOWED_HOSTS entries must not include schemes")
        normalized.append(cleaned)

    if not normalized:
        raise ValueError("ALLOWED_HOSTS must define at least one hostname")

    return list(dict.fromkeys(normalized))


def build_host_origins(hosts, scheme, include_wildcards=True):
    origins = []
    for host in hosts:
        formatted = host
        if formatted.startswith('.'):
            formatted = f"*.{formatted.lstrip('.')}"
        if not include_wildcards and '*' in formatted:
            continue
        origins.append(f"{scheme}://{formatted}")
    return list(dict.fromkeys(origins))

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
        },
    }

LOGGING = get_logging_config()

SECRET_KEY = get_required_env('DJANGO_SECRET_KEY')
DEBUG = False

GOOGLE_CLIENT_ID = get_required_env('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = get_required_env('GOOGLE_CLIENT_SECRET')
JWT_SECRET = get_required_env('JWT_SECRET')

FRONTEND_URL, FRONTEND_ORIGINS = prepare_frontend_urls(parse_csv(get_required_env('FRONTEND_URL')))
ALLOWED_HOSTS = normalize_allowed_hosts(parse_csv(get_required_env('ALLOWED_HOSTS')))
POSTGRES_PASSWORD = get_required_env('POSTGRES_PASSWORD')

# Production email settings (configure for password reset)
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = os.environ.get('EMAIL_HOST')
# EMAIL_PORT = os.environ.get('EMAIL_PORT', 587)
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')

# Allow disabling HTTPS enforcement for specific deployments
USE_HTTPS = os.environ.get('USE_HTTPS', 'true').lower() == 'true'
HOST_SCHEME = 'https' if USE_HTTPS else 'http'

HOST_ORIGINS = build_host_origins(ALLOWED_HOSTS, HOST_SCHEME)
HOST_ORIGINS_NO_WILDCARD = build_host_origins(ALLOWED_HOSTS, HOST_SCHEME, include_wildcards=False)

CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(FRONTEND_ORIGINS + HOST_ORIGINS))
CSRF_COOKIE_HTTPONLY = False  # Ensure CSRF token is accessible to JavaScript
CSRF_COOKIE_SAMESITE = 'Lax'

CORS_ALLOWED_ORIGINS = list(dict.fromkeys(FRONTEND_ORIGINS + HOST_ORIGINS_NO_WILDCARD))

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

WSGI_APPLICATION = "sportshunt.wsgi.application"

# CORS Configuration
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db.sqlite3",
#     }
# }


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get('POSTGRES_DB', 'playportal'),
        "USER": os.environ.get('POSTGRES_USER', 'postgres'),
        "PASSWORD": POSTGRES_PASSWORD,
        "HOST": os.environ.get('POSTGRES_HOST', 'localhost'),
        "PORT": os.environ.get('POSTGRES_PORT', '5432'),
        "CONN_MAX_AGE": 600,  # Connection pooling - keeps connections alive for 10 minutes
        "OPTIONS": {
            "connect_timeout": 10,
        }
    }
}
# Security settings
if USE_HTTPS:
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
else:
    # Local testing without HTTPS
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SESSION_COOKIE_SAMESITE = 'Lax'
