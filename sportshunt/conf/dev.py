from .common import *
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = "django-insecure-a5$u$o^s8o)y%bsaxnl%lbzn$mc&w#7po^gy#b_oe%g&(py_yj"
DEBUG = True

# Validate and get required environment variables
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

ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = [
    *[f"{url.strip()}" for url in FRONTEND_URL ],
    *[f"https://{url.strip()}" for url in ALLOWED_HOSTS ],
]

CSRF_COOKIE_SECURE = False  # Set to True in production with HTTPS
CSRF_COOKIE_HTTPONLY = False  # Ensure CSRF token is accessible to JavaScript
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
    *[f"https://{url.strip()}" for url in ALLOWED_HOSTS ],
]
CSRF_COOKIE_SAMESITE = 'Lax'