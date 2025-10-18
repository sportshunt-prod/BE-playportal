# API Reference

This document describes the primary API endpoints for the SportsHunt backend. Use the `docs/playportal-endpoints.json` Postman collection to import endpoints and example requests.

## Importing the Postman Collection

- Open Postman and import `docs/playportal-endpoints.json`.
- If you used to have environment files, create or import an environment in Postman and configure the base URL and auth variables according to your local setup.

> Note: The repository no longer includes `openapi.yaml` or legacy Postman environment files. If you require an OpenAPI spec, export one and place it in `docs/openapi.yaml` or add it to the repository root.

## Authentication

Authentication uses JWT Bearer tokens; see `authentication.md` for details on obtaining tokens and using them against endpoints. Include tokens in the `Authorization: Bearer <token>` header.

## Core API Endpoints

### User Management
- `/api/auth/` — User authentication endpoints
- `/api/user/` — User profile management

### Organization API Endpoints

#### Organization Management
- `/api/org/org_auth/` — Validate organization user authentication
- `/api/org/create/` — Create organization
- `/api/org/dashboard/` — Organization dashboard data

#### Tournament Management
- `/api/org/tournament/create/` — Create tournament
- `/api/org/tournament/{tournament_id}/` — Tournament details

#### Category Management
- `/api/org/tournament/{tournament_id}/category/create/` — Create category
- `/api/org/tournament/{tournament_id}/category/{category_id}/toggle-registration/` — Toggle registration
- `/api/org/tournament/{tournament_id}/category/{category_id}/team/create/` — Register team

#### Fixture & Match Management
- `/api/org/tournament/{tournament_id}/category/{category_id}/fixture/create/` — Create fixture
- `/api/org/tournament/{tournament_id}/category/{category_id}/create_ko_matches/` — Create knockout matches
- `/api/org/tournament/{tournament_id}/category/{category_id}/schedule_match/` — Schedule match (with optional court assignment)
- `/api/org/tournament/{tournament_id}/category/{category_id}/update_score/` — Update match score (with automatic court advancement)
- `/api/org/tournament/{tournament_id}/category/{category_id}/fixture/details/` — Get fixture details

#### Court Management
- `/api/org/tournament/{tournament_id}/courts/` — List tournament courts
- `/api/org/tournament/{tournament_id}/new_courts/` — Create court
- `/api/org/courts/{court_id}/` — Court details, update, delete

## Enhanced Features

### Court Assignment & Auto-Queue Management
- **Match Scheduling with Courts**: Assign matches to courts during scheduling
- **Automatic Queue Management**: Courts automatically manage FIFO match queues
- **Auto-Advancement**: Courts automatically advance to next match on completion
- **Real-time Status**: Get live court status and queue information

### Comprehensive Tournament Management
- **Multi-format Support**: Knockout (KO) and Round Robin (RR) fixtures
- **Set-based & Simple Scoring**: Support for different sport scoring systems
- **Live Score Updates**: Real-time score tracking with match progression
- **Tournament State Management**: Track completion status and winners

## Missing Examples / Fixtures

Some example fixtures and data sets referenced in older docs are not present. If you need sample data for testing, create them under `docs/fixtures/` and reference them from the relevant docs.
