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

## 📞 Support

For questions, issues, or contributions:

- **Issues**: Create an issue in the repository.
- **Documentation**: Contributions welcome via pull requests.
- **Contact**: [Your contact information].


*Last updated: August 2025*
