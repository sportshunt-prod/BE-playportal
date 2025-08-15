# API Reference

This document describes the primary API endpoints for the SportsHunt backend. Use the `docs/playportal-endpoints.json` Postman collection to import endpoints and example requests.

## Importing the Postman Collection

- Open Postman and import `docs/playportal-endpoints.json`.
- If you used to have environment files, create or import an environment in Postman and configure the base URL and auth variables according to your local setup.

> Note: The repository no longer includes `openapi.yaml` or legacy Postman environment files. If you require an OpenAPI spec, export one and place it in `docs/openapi.yaml` or add it to the repository root.

## Authentication

Authentication uses Auth0; see `authentication.md` for details on obtaining tokens and using them against endpoints.

## Common Endpoints

- /api/organizations/ — Organization list and create
- /api/organizations/{id}/ — Organization detail
- /api/tournaments/ — Tournament list and create
- /api/tournaments/{id}/ — Tournament detail

(For the full list and example requests, import the Postman collection above.)

## Missing Examples / Fixtures

Some example fixtures and data sets referenced in older docs are not present. If you need sample data for testing, create them under `docs/fixtures/` and reference them from the relevant docs.
