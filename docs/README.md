# SportsHunt Documentation

This folder contains the documentation for the SportsHunt backend.

Primary files:

- `getting-started.md` — Quick start guide for developers.
- `architecture.md` — System architecture and design patterns.
- `api-reference.md` — API endpoints and examples.
- `authentication.md` — Auth0 integration and JWT handling.
- `database-schema.md` — Data models and relationships.
- `deployment.md` — Production deployment instructions.
- `development.md` — Local development setup.
- `testing.md` — Testing strategies and examples.
- `troubleshooting.md` — Common issues and solutions.

Quick links

- **API Collections**: [PlayPortal Endpoints / Postman collection](./playportal-endpoints.json)
- **Core API**: [Core API Documentation](./core_api.md)
- **Organization API**: [Organization API Documentation](./organization_api.md)
- **OpenAPI Spec**: (not present) See `PLACEHOLDERS.md` for instructions to add `openapi.yaml`

Missing / Consolidated artifacts

Some artifacts that used to live in the repository (Postman collections, environment files, and OpenAPI YAML) were consolidated or removed. Use the following guidelines:

- If you relied on old Postman or environment files, import `playportal-endpoints.json` into Postman.
- If you need an OpenAPI spec, create or export one into `docs/openapi.yaml` or place it at the repository root as `openapi.yaml`.
- If you have fixtures or sample data referenced in docs, add them to `docs/fixtures/` and update the markdown to point at that path.

See `PLACEHOLDERS.md` for a checklist of missing items and how to re-create them.

---

*Last updated: August 2025*
