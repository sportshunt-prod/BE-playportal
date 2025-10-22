# Getting Started

This guide will help you get the SportsHunt backend up and running quickly.

## 📋 Prerequisites

- Python 3.12+
- Git
- SQLite (included with Python)
- Google Cloud Console account (for Google OAuth, optional)

## 🚀 Quick Setup

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd BE-playportal

# Install dependencies using uv (recommended)
uv sync

# Or use pip
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the project root (see `docs/PLACEHOLDERS.md` for a template and missing env examples):

```env
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Google OAuth Configuration (optional but recommended)
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# JWT Configuration
JWT_SECRET=your-jwt-secret-key-here

# Frontend URL
FRONTEND_URL=http://localhost:3000

# Database (SQLite for development)
DATABASE_URL=sqlite:///db.sqlite3

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 3. Google OAuth Setup (Optional)

If you want to enable Google Sign-In:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized JavaScript origins: `http://localhost:3000` (add production URLs later)
5. Copy Client ID and Client Secret to your `.env` file

**Note:** You can skip Google OAuth and use only email/password authentication for development.

### 4. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data (optional)
# If sample fixtures are present, they should be located in docs/fixtures/
python manage.py loaddata docs/fixtures/sample_data.json
```

### 5. Start Development Server

```bash
# Using the startup script
./startup.sh

# Or manually
python manage.py runserver
```

The API will be available at `http://localhost:8000`

## 🔧 Development Tools

### Django Admin

Access the Django admin interface at `http://localhost:8000/admin/` using your superuser credentials.

### API Testing

#### Manual Testing

You can test the authentication endpoints using curl:

```bash
# Register a new user
curl -X POST http://localhost:8000/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
  }'

# The response contains a JSON payload with a 'token' field. Use it in Authorization header for subsequent requests:

# Login
curl -X POST http://localhost:8000/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'

# Example: check auth status (replace <token> with returned token)
curl -X GET http://localhost:8000/auth/check/ \
  -H "Authorization: Bearer <token>"

# Get profile
curl -X GET http://localhost:8000/profile/ \
  -H "Authorization: Bearer <token>"
```

#### Postman Collection

1. Import the Postman collection: `docs/playportal-endpoints.json`
2. Update the collection with new authentication endpoints:
   - `POST /auth/register/`
   - `POST /auth/login/`
   - `POST /auth/google/`
   - `GET /auth/check/`
3. Configure base URL and auth variables (see `docs/PLACEHOLDERS.md`)

## 📁 Project Structure

```
BE-playportal/
  coreApi/              # Core API endpoints (auth, tournaments)
  organizationApi/      # Organization management API
  sportshunt/           # Django project settings
    conf/               # Environment-specific configs
    utils/              # Shared utilities (auth, decorators)
  docs/                 # Documentation
  logs/                 # Application logs
  manage.py             # Django management script
  requirements.txt      # Python dependencies
  pyproject.toml        # UV project configuration
```

## 🧪 Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test coreApi
python manage.py test organizationApi

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

## 🔍 Key Concepts

### User Roles

- **Regular Users**: Can view tournaments, register for events, and manage their profile
- **Organizers**: Can create organizations and manage tournaments (set `is_organizer=True`)

### Authentication Flow

#### Email/Password Registration

1. User submits registration form → `POST /auth/register/`
2. Backend validates data and creates user
3. JWT token generated and set as HTTP-only cookie
4. Frontend receives user data

#### Email/Password Login

1. User submits login form → `POST /auth/login/`
2. Backend verifies credentials
3. JWT token generated and set as HTTP-only cookie
4. Frontend receives user data

#### Google OAuth

1. Frontend initiates Google Sign-In
2. User authenticates with Google
3. Frontend receives Google ID token
4. Frontend sends token → `POST /auth/google/`
5. Backend verifies token with Google
6. User created/updated in database
7. JWT token generated and set as HTTP-only cookie

### JWT Token Usage

- JWT tokens are automatically sent with requests via cookies
- No need to manually add Authorization headers
- Tokens expire after 30 days
- Use `@login_required_api` decorator to protect endpoints

## 🆘 Common Issues

### CORS Errors

Ensure your frontend URL is in `CORS_ALLOWED_ORIGINS` in settings and matches exactly (including protocol and port).

```python
# sportshunt/conf/dev.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React default
    "http://127.0.0.1:3000",
]
```

### Google OAuth Errors

- **"Invalid token"**: Check that `GOOGLE_CLIENT_ID` matches your Google Cloud Console project
- **"Wrong issuer"**: Token might be expired or from wrong domain
- **Google+ API disabled**: Enable it in Google Cloud Console

### JWT Token Issues

- **"Unauthorized"**: Token might be expired or `JWT_SECRET` changed
- **Token not sent**: Ensure you include the Authorization header in requests: `Authorization: Bearer <token>`
- **Cookie not set**: Check CORS and SameSite settings

### Database Issues

```bash
# Reset database
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

### Import Errors After Migration

If you get import errors related to `social_django`:

```bash
# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -name "*.pyc" -delete

# Reinstall dependencies
pip install -r requirements.txt
```

## 🔐 Security Notes

### Development vs Production

**Development (.env):**

```env
DEBUG=True
FRONTEND_URL=http://localhost:3000
# Cookies work with SameSite=None in dev
```

**Production:**

```env
DEBUG=False
FRONTEND_URL=https://yourdomain.com
# Requires HTTPS for secure cookies
# Set SECURE_SSL_REDIRECT=True
```

### Password Requirements

- Minimum 8 characters
- Cannot be too similar to username/email
- Cannot be a commonly used password
- Cannot be entirely numeric

## 📚 Next Steps

- Read the [Authentication Guide](./authentication.md) for detailed auth flow
- Explore the [API Reference](./api-reference.md) for all endpoints
- Check out [Development Guide](./development.md) for advanced setup
- Review [Architecture Overview](./architecture.md) for system design

Need help? Check the [Troubleshooting Guide](./troubleshooting.md) or create an issue!
