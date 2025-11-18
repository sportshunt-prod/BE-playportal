# SportsHunt Documentation

Welcome to the SportsHunt Tournament Management System documentation. This system provides a comprehensive platform for managing sports tournaments, from organization creation to match scheduling and scoring.

## 📚 Documentation Structure

| Document | Description |
|----------|-------------|
| [Getting Started](./docs/getting-started.md) | Quick start guide for developers |
| [Architecture Overview](./docs/architecture.md) | System architecture and design patterns |
| [API Reference](./docs/api-reference.md) | Complete API endpoint documentation |
| [Authentication](./docs/authentication.md) | Native Django authentication with JWT Bearer tokens |
| [Database Schema](./docs/database-schema.md) | Data models and relationships |
| [Deployment Guide](./docs/deployment.md) | Production deployment instructions |
| [Development Guide](./docs/development.md) | Local development setup |
| [Testing Guide](./docs/testing.md) | Testing strategies and examples |
| [Troubleshooting](./docs/troubleshooting.md) | Common issues and solutions |

## 🚀 Quick Links

- **API Endpoints & Postman**: [PlayPortal Endpoints / Postman collection (docs/playportal-endpoints.json)](./docs/playportal-endpoints.json)
- **Core API**: [Core API Documentation](./docs/core_api.md)
- **Organization API**: [Organization API Documentation](./docs/organization_api.md)

> Note: The repository previously included various Postman and OpenAPI files at the repo root. Those were consolidated/renamed — see `docs/playportal-endpoints.json` for the Postman collection/endpoints. If you have a separate `openapi.yaml`, place it in the repo root or `docs/` and update `docs/PLACEHOLDERS.md`.

## 🏆 About SportsHunt

SportsHunt is a modern tournament management system designed to handle various sports tournaments efficiently. The system supports:

- **Multi-organization Support**: Organizations can create and manage their own tournaments.
- **Flexible Tournament Formats**: Support for knockout, round-robin, and mixed formats.
- **Real-time Scoring**: Live match updates and scoring.
- **User Management**: Role-based access for organizers and participants.
- **Payment Integration**: Registration fee handling (coming soon).

## 🛠️ Technology Stack

- **Backend**: Django 5.1+ with Django REST Framework.
- **Authentication**: Native Django auth with email/password and Google OAuth, JWT Bearer tokens.
- **Database**: SQLite (development), PostgreSQL (production).
- **Testing**: Django Test Framework.
- **Deployment**: Docker, Gunicorn.

## 🐳 Docker Usage

1. **Create an environment file** (e.g., `.env`) that includes every setting required by `sportshunt/conf/prod.py`, such as:
   - `DJANGO_SECRET_KEY`
   - `DJANGO_SETTINGS_MODULE`
   - `DEBUG`
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `JWT_SECRET`
   - `FRONTEND_URL`
   - `ALLOWED_HOSTS`
   - `POSTGRES_HOST`
   - `POSTGRES_DB`
   - `POSTGRES_USER`
   - `POSTGRES_PASSWORD`
   - `POSTGRES_PORT`
   - any other prod-only flags (e.g., `USE_HTTPS`, `LOGS_DIR`)

2. **Build the image**:
   ```bash
   docker build -t playportal-be .
   ```

3. **Run the container** (pass the env file and opt-in to migrations/static collection when needed):
   ```bash
   docker run \
     --env-file .env \
     -e RUN_MIGRATIONS=true \
     -e COLLECT_STATIC=true \
     -p 8000:8000 \
     playportal-be
   ```

   - The container defaults to `sportshunt.conf.prod` and serves via Gunicorn on port 8000.
   - `RUN_MIGRATIONS` / `COLLECT_STATIC` are optional toggles consumed by `docker/entrypoint.sh`.

> **Note:** The application expects to reach a PostgreSQL instance (Azure Flexible Server in production). Ensure the connection details in your env file point to the correct database host.

Example `.env` snippet for local Docker runs:

```
DJANGO_SECRET_KEY=your-secret-key-here-change-this-in-production
DJANGO_SETTINGS_MODULE=sportshunt.conf.prod
DEBUG=false
ALLOWED_HOSTS=localhost,127.0.0.1
POSTGRES_DB=playportal
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-secure-password-here
POSTGRES_HOST=db
POSTGRES_PORT=5432
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
JWT_SECRET=your-jwt-secret-key-here-change-this
FRONTEND_URL=http://localhost:3000
USE_HTTPS=false
LOGS_DIR=/app/logs
```

## 📞 Support

For questions, issues, or contributions:

- **Issues**: Create an issue in the repository.
- **Documentation**: Contributions welcome via pull requests.
- **Contact**: [Your contact information].


*Last updated: August 2025*
