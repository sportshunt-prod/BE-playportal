from .common import *
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = "django-insecure-a5$u$o^s8o)y%bsaxnl%lbzn$mc&w#7po^gy#b_oe%g&(py_yj"
DEBUG = True

# Validate and get required environment variables
required_env_vars = {
    'GOOGLE_CLIENT_ID': os.environ.get('GOOGLE_CLIENT_ID'),
    'GOOGLE_CLIENT_SECRET': os.environ.get('GOOGLE_CLIENT_SECRET'),
    'FRONTEND_URL': os.environ.get('FRONTEND_URL'),
    'JWT_SECRET': os.environ.get('JWT_SECRET'),
    'RAZORPAY_KEY_ID': os.environ.get('RAZORPAY_KEY_ID'),
    'RAZORPAY_KEY_SECRET': os.environ.get('RAZORPAY_KEY_SECRET'),
}

for var_name, value in required_env_vars.items():
    if not value:
        raise ValueError(f"Missing required environment variable: {var_name}")

GOOGLE_CLIENT_ID = required_env_vars['GOOGLE_CLIENT_ID']
GOOGLE_CLIENT_SECRET = required_env_vars['GOOGLE_CLIENT_SECRET']
FRONTEND_URL = required_env_vars['FRONTEND_URL'].strip().split(",")
JWT_SECRET = required_env_vars['JWT_SECRET'].strip()

# Razorpay Configuration
RAZORPAY_KEY_ID = required_env_vars['RAZORPAY_KEY_ID']
RAZORPAY_KEY_SECRET = required_env_vars['RAZORPAY_KEY_SECRET']
RAZORPAY_WEBHOOK_SECRET = os.environ.get('RAZORPAY_WEBHOOK_SECRET', 'whsec_default_test')

# Email backend for development (console output)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

ALLOWED_HOSTS = ['*']

# CORS Configuration
# CORS_ALLOW_ALL_ORIGINS = True  # WARNING: Only enable for local testing with file:// protocol
CSRF_TRUSTED_ORIGINS = [
    *[f"{url.strip()}" for url in FRONTEND_URL],
]
CORS_ALLOW_CREDENTIALS = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

STATIC_URL = "static/"

WSGI_APPLICATION = "sportshunt.wsgi.application"

CORS_ALLOWED_ORIGINS = [
    *[f"{url.strip()}" for url in FRONTEND_URL],
]
# print(CORS_ALLOWED_ORIGINS)

# CSRF_COOKIE_SAMESITE = 'Lax'