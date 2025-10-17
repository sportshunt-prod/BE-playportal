# Project Architecture

This document provides a high-level overview of the project's architecture, including the authentication and authorization flow.

## Technology Stack

- **Backend:** Django, Django REST Framework
- **Authentication:** Native Django auth with email/password and Google OAuth, JWT Bearer tokens
- **Database:** SQLite (for development), PostgreSQL (for production)

## Project Structure

The project is divided into three main Django apps:

- `sportshunt`: The main project directory, containing settings and root URL configuration.
- `coreApi`: Handles core functionalities like user authentication, profile management, and public-facing tournament information.
- `organizationApi`: Manages functionalities for tournament organizers, such as creating and managing organizations, tournaments, and categories.

## Authentication Flow (Login)

The application uses native Django authentication with support for email/password and Google OAuth.

### Email/Password Login
1.  **User Submission:** The user submits their email and password to the `POST /auth/login/` endpoint.
2.  **Credential Validation:** The backend validates the credentials against the database.
3.  **JWT Generation:** Upon successful validation, a JWT token is generated with a 30-day expiration.
4.  **Token Response:** The JWT token is returned in the response body along with user details.
5.  **Client Storage:** The frontend stores the token in localStorage or sessionStorage.
6.  **API Authentication:** For subsequent API requests, the JWT token must be included in the `Authorization` header as `Bearer <token>`.

### Google OAuth Login
1.  **Google Sign-In:** The user authenticates with Google on the frontend using Google Sign-In.
2.  **ID Token:** Google returns an ID token to the frontend.
3.  **Token Verification:** The frontend sends the Google ID token to `POST /auth/google/`.
4.  **User Creation/Update:** The backend verifies the token with Google and creates or updates the user in the database.
5.  **JWT Generation:** A JWT token is generated for the authenticated user.
6.  **Token Response:** The JWT token is returned in the response body along with user details.

## Authorization

- **General Users:** Authenticated users can access public tournament data and their own profile information.
- **Organizers:** Users marked as `is_organizer` have access to the `organizationApi` endpoints. This is controlled by the `@organizer_required_api` decorator.

## API Structure

The API is split into two main parts:

- **Core API (`/`):** Endpoints for general users.
- **Organization API (`/org/`):** Endpoints for organizers.

---

## Architecture Diagram

```
+-----------------+      +------------------------+      +-------------------+
|                 |      |                        |      |                   |
|   Frontend      |----->|    Django Backend      |<---->|     Database      |
| (React/Vue/etc) |      |      (sportshunt)      |      | (SQLite/Postgres) |
|                 |      |                        |      |                   |
|  - Stores JWT   |      |  - Native Auth         |      |  - User Data      |
|  - Sends Bearer |      |  - Google OAuth        |      |  - Organizations  |
|    Token        |      |  - JWT Generation      |      |  - Tournaments    |
+-----------------+      +------------------------+      +-------------------+
        |                            ^
        | (JWT Bearer Token)         | (OAuth Verification)
        v                            |
+-----------------+      +------------------------+
|                 |      |                        |
| localStorage/   |      |   Google OAuth API     |
| sessionStorage  |      | (Token Verification)   |
|                 |      |                        |
+-----------------+      +------------------------+

```

---

## Organizer User Flow

This section details the step-by-step process an organizer follows to create and manage a tournament.

1.  **Authentication & Authorization**
    *   The user logs in via email/password or Google OAuth.
    *   The system verifies that the user has the `is_organizer` flag set to `True`.
    *   The user receives a JWT Bearer token that grants access to the `organizationApi` endpoints.
    *   The token must be included in all requests: `Authorization: Bearer <token>`

2.  **Create an Organization**
    *   **Action:** If the organizer is new, they create an organization. A user can only be an admin of one organization.
    *   **Endpoint:** `POST /org/create/`
    *   **Details:** The organizer provides the organization's name, email, and phone number.

3.  **Create a Tournament**
    *   **Action:** The organizer creates a new tournament and associates it with their organization.
    *   **Endpoint:** `POST /org/tournament/create/`
    *   **Details:** They provide tournament details like name, dates, venue, and the sport.

4.  **✅ Set Up Courts (NEW)**
    *   **Action:** The organizer creates courts for the tournament to manage match scheduling and progression.
    *   **Endpoint:** `POST /org/tournament/<tournament_id>/new_courts/`
    *   **Details:** They provide court names (e.g., "Court 1", "Center Court").
    *   **Features:** Courts support automatic match queuing and progression.

5.  **Define Categories**
    *   **Action:** The organizer adds one or more categories to the tournament (e.g., "U-19 Men's Singles", "Open Women's Doubles").
    *   **Endpoint:** `POST /org/tournament/<tournament_id>/category/create/`

6.  **Manage Registration**
    *   **Action:** The organizer opens registration for a specific category.
    *   **Endpoint:** `POST /org/tournament/<t_id>/category/<c_id>/toggle-registration/`

7.  **Register Teams**
    *   **Action:** The organizer manually adds teams to the category.
    *   **Endpoint:** `POST /org/tournament/<t_id>/category/<c_id>/team/create/`

8.  **Create a Fixture**
    *   **Action:** After closing registration (using the same `toggle-registration` endpoint), the organizer creates a fixture for the category.
    *   **Endpoint:** `POST /org/tournament/<t_id>/category/<c_id>/fixture/create/`
    *   **Details:** The organizer specifies the `fixtureType`, such as "KO" (Knockout) or "RR" (Round Robin).

9.  **Generate & Schedule Matches with Courts ✅ ENHANCED**
    *   **Action (for KO):** The organizer generates the initial bracket of matches.
    *   **Endpoint:** `POST /org/tournament/<t_id>/category/<c_id>/create_ko_matches/`
    *   **Action:** The organizer schedules matches with optional court assignment.
    *   **Endpoint:** `POST /org/tournament/<t_id>/category/<c_id>/schedule_match/`
    *   **NEW:** `{"match_id": 1, "court_id": 2}` - Courts automatically manage queues
    *   **Behavior:** If court is available → assign as current match, if occupied → add to queue

10. **Manage Live Tournament with Automatic Court Progression ✅ ENHANCED**
    *   **Action:** As matches are played, the organizer updates the scores.
    *   **Endpoint:** `POST /org/tournament/<t_id>/category/<c_id>/update_score/`
    *   **NEW System Behavior:** When a match finishes:
        - System automatically progresses the winner to the next round
        - ✅ **Courts automatically advance** to the next queued match
        - Next match becomes available for scheduling
        - Court status updates in real-time

11. **Monitor Courts & Tournament Progress ✅ ENHANCED**
    *   **Action:** View live tournament state and court utilization.
    *   **Endpoints:** 
        - `GET /org/tournament/<t_id>/category/<c_id>/fixture/details/` - Tournament bracket
        - ✅ `GET /org/tournament/<t_id>/courts/` - **NEW** Court status overview
        - ✅ `GET /org/courts/<court_id>/` - **NEW** Detailed court queue information

## ✅ Court Management Workflow (NEW)

**Automatic Court Management System:**

1. **Court Setup** → Organizer creates courts for tournament
2. **Match Assignment** → Matches assigned to courts during scheduling
3. **Auto-Queue Management** → System handles current vs upcoming match logic
4. **Match Completion** → Score updates trigger automatic court advancement
5. **Real-time Status** → Live court availability and queue monitoring

**Key Benefits:**
- **Automated Workflow**: No manual intervention needed for court progression
- **Queue Management**: FIFO processing with transparent position tracking  
- **Real-time Updates**: Immediate status changes on match completion
- **Scalable Design**: Supports multiple courts and complex tournament structures

This flow continues until the final match is played and a tournament winner is determined, with courts automatically managing match progression throughout the tournament.
