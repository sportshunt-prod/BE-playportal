# Getting Started

This guide will help you get the SportsHunt backend up and running quickly.

## 📋 Prerequisites

- Python 3.12+
- Git
- SQLite (included with Python)
- Auth0 account (for authentication)

## 🚀 Quick Setup

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd BE

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

# Auth0 Configuration
SOCIAL_AUTH_AUTH0_DOMAIN=your-auth0-domain
SOCIAL_AUTH_AUTH0_KEY=your-auth0-client-id
SOCIAL_AUTH_AUTH0_SECRET=your-auth0-client-secret

# Database (SQLite for development)
DATABASE_URL=sqlite:///db.sqlite3

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 3. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data (optional)
# If sample fixtures are present, they should be located in docs/fixtures/
python manage.py loaddata docs/fixtures/sample_data.json
```

### 4. Start Development Server

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
1. Import the Postman collection: `docs/playportal-endpoints.json`
2. Create or import a Postman environment and configure base URL and auth variables (see `docs/PLACEHOLDERS.md`)
3. Test endpoints using the collection

### OpenAPI Documentation
If an OpenAPI spec is present (e.g., `docs/openapi.yaml`), you can view interactive docs at `http://localhost:8000/docs/` when the project serves it.

## 📁 Project Structure

```
BE/
  coreApi/              # Core API endpoints
  organizationApi/      # Organization management API
  sportshunt/           # Django project settings
  conf/                 # Environment-specific configs
  utils/                # Shared utilities
  docs/                 # Documentation
  logs/                 # Application logs
  manage.py             # Django management script
  requirements.txt      # Python dependencies
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
- Regular Users: Can view tournaments and manage their profile
- Organizers: Can create organizations and manage tournaments

### Authentication Flow
1. User clicks login → Redirected to Auth0
2. Auth0 authentication → Callback to `/login/handler/`
3. JWT token generated → Use in API requests

## 🆘 Common Issues

CORS Errors: Ensure your frontend URL is in `CORS_ALLOWED_ORIGINS` in settings.

Auth0 Configuration: Set up Auth0 application and configure callback URLs: `http://localhost:8000/login/handler/` and update `.env` with Auth0 credentials.

Database Issues

```bash
# Reset database
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

## 📚 Next Steps

- Read the [Architecture Overview](./architecture.md)
- Explore the [API Reference](./api-reference.md)
- Check out [Development Guide](./development.md) for advanced setup

Need help? Check the [Troubleshooting Guide](./troubleshooting.md) or create an issue!
