from pathlib import Path
import os
import tempfile
import logging

BASE_DIR = Path(__file__).resolve().parent.parent.parent

def ensure_logs_directory():
    """
    Ensure logs directory exists, with fallback to temporary directory.
    Returns the absolute path to the logs directory.
    """
    logs_dir = BASE_DIR / 'logs'
    try:
        logs_dir.mkdir(exist_ok=True)
        return logs_dir
    except (PermissionError, OSError):
        # Fallback to system temp directory for restrictive environments
        temp_logs_dir = Path(tempfile.gettempdir()) / 'sportshunt_logs'
        temp_logs_dir.mkdir(exist_ok=True)
        return temp_logs_dir

# Create logs directory
LOGS_DIR = ensure_logs_directory()

# Logging Configuration
LOGGING = {
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
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': str(LOGS_DIR / 'django.log'),  # Convert Path to string for compatibility
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'organizationApi': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'coreApi': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'sportshunt': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    'corsheaders',
    'rest_framework',
]

APPS = [
    "coreApi",
    "organizationApi",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "sportshunt.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "sportshunt.wsgi.application"


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]



LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "coreApi.User"

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
}

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

CORS_ALLOW_CREDENTIALS = True

# Sentry Configuration
SENTRY_DSN = os.environ.get('SENTRY_DSN')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    
    # Get sample rates from environment variables (default to 1.0 for 100%)
    traces_sample_rate = float(os.environ.get('SENTRY_TRACES_SAMPLE_RATE', '1.0'))
    profile_session_sample_rate = float(os.environ.get('SENTRY_PROFILE_SESSION_SAMPLE_RATE', '1.0'))
    
    # Configure logging integration
    logging_integration = LoggingIntegration(
        level=logging.INFO,        # Capture info and above as breadcrumbs
        event_level=logging.ERROR  # Send errors and above as events
    )
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        # Add data like request headers and IP for users
        send_default_pii=True,
        # Enable sending logs to Sentry
        enable_logs=True,
        # Set traces_sample_rate to capture transactions for tracing
        traces_sample_rate=traces_sample_rate,
        # Set profile_session_sample_rate to profile sessions
        profile_session_sample_rate=profile_session_sample_rate,
        # Set profile_lifecycle to "trace" to automatically run the profiler
        # when there is an active transaction
        profile_lifecycle="trace",
        # Integrations
        integrations=[
            DjangoIntegration(
                transaction_style='url',
                middleware_spans=True,
                signals_spans=True,
                cache_spans=True,
            ),
            logging_integration,
        ],
        # Set environment
        environment=os.environ.get('SENTRY_ENVIRONMENT', 'development'),
        # Release version (optional)
        release=os.environ.get('SENTRY_RELEASE'),
    )