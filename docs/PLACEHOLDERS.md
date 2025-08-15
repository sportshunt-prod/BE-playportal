# PLACEHOLDERS & Missing Artifacts

This file documents artifacts that are referenced in the documentation but are not currently present in the repository. It also provides guidance on how to re-create or add them.

## Current canonical endpoint collection

- `docs/playportal-endpoints.json` — Current Postman collection and canonical endpoints list. Import this into Postman.

## Missing / Recommended artifacts

- `openapi.yaml` or `openapi.json` — OpenAPI 3.0 specification for the API.
  - Recommendation: Generate an OpenAPI spec from the running server using drf-spectacular or drf-yasg and commit it to `docs/openapi.yaml`.

- Postman environment files (e.g., `postman_environment.playportal.json`) — environment variables for Postman.
  - Recommendation: Export your Postman environment and commit to `docs/postman-environments/`.

- Postman collection variants — if you kept multiple collections (core, organization), consolidate or place them under `docs/postman-collections/`.

- Fixtures / sample data — referenced in older guides but not present.
  - Recommendation: Add JSON fixtures under `docs/fixtures/` and document how to load them using `manage.py loaddata`.

## How to add artifacts

1. Create the file locally (e.g., export from Postman or generate OpenAPI).
2. Place it under `docs/` or an appropriate subfolder under `docs/`.
3. Update the relevant markdown file to point to the new path.
4. Commit and open a PR explaining the new artifact.

## Short checklist for maintainers

- [ ] Generate and add `docs/openapi.yaml` if you need API schema.
- [ ] Export and add Postman environment files to `docs/postman-environments/`.
- [ ] Add any example fixtures to `docs/fixtures/` and update docs accordingly.
- [ ] Remove or edit any other references in markdown that point to deleted files.
