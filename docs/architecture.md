# Project Architecture

This document provides a high-level overview of the project's architecture, including the authentication and authorization flow.

## Technology Stack

- **Backend:** Django, Django REST Framework
- **Authentication:** Auth0 (OAuth 2.0)
- **Database:** SQLite (for development)

## Project Structure

The project is divided into three main Django apps:

- `sportshunt`: The main project directory, containing settings and root URL configuration.
- `coreApi`: Handles core functionalities like user authentication, profile management, and public-facing tournament information.
- `organizationApi`: Manages functionalities for tournament organizers, such as creating and managing organizations, tournaments, and categories.

## Authentication Flow (Login)

The application uses Auth0 for a secure and robust authentication process.

1.  **Initiate Login:** The user is redirected from the frontend to the `/login/` endpoint in `coreApi`.
2.  **Redirect to Auth0:** The `login_view` redirects the user to the Auth0 login page.
3.  **User Authentication:** The user authenticates with Auth0 using their credentials (e.g., Google, email/password).
4.  **Callback to Application:** After successful authentication, Auth0 redirects the user back to the application's callback URL (`/login/handler/`).
5.  **User Creation/Update:** The `social_django` library handles the callback, creating a new `User` in the database if they don't exist, or updating their information if they do. A JWT token is generated for the user.
6.  **API Authentication:** For subsequent API requests, the JWT token must be included in the `Authorization` header as a Bearer token.

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
+-------+---------+      +-----------+------------+      +-------------------+
        ^                            ^
        | (Login Request)            | (Handles User/Token)
        |                            |
        v                            v
+-----------------+      +------------------------+
|                 |      |                        |
|      Auth0      |<---->|     social_django      |
| (Authentication)|      | (OAuth Callback/User)  |
|                 |      |                        |
+-----------------+      +------------------------+

```

---

## Organizer User Flow

This section details the step-by-step process an organizer follows to create and manage a tournament.

1.  **Authentication & Authorization**
    *   The user logs in via the standard Auth0 flow.
    *   The system verifies that the user has the `is_organizer` flag set to `True`.
    *   The user receives a JWT token that grants access to the `organizationApi` endpoints.

2.  **Create an Organization**
    *   **Action:** If the organizer is new, they create an organization. A user can only be an admin of one organization.
    *   **Endpoint:** `POST /org/create/`
    *   **Details:** The organizer provides the organization's name, email, and phone number.

3.  **Create a Tournament**
    *   **Action:** The organizer creates a new tournament and associates it with their organization.
    *   **Endpoint:** `POST /org/tournament/create/`
    *   **Details:** They provide tournament details like name, dates, venue, and the sport.

4.  **Define Categories**
    *   **Action:** The organizer adds one or more categories to the tournament (e.g., "U-19 Men's Singles", "Open Women's Doubles").
    *   **Endpoint:** `POST /org/tournament/<tournament_id>/category/create/`

5.  **Manage Registration**
    *   **Action:** The organizer opens registration for a specific category.
    *   **Endpoint:** `POST /org/tournament/<t_id>/category/<c_id>/toggle-registration/`

6.  **Register Teams**
    *   **Action:** The organizer manually adds teams to the category.
    *   **Endpoint:** `POST /org/tournament/<t_id>/category/<c_id>/team/create/`

7.  **Create a Fixture**
    *   **Action:** After closing registration (using the same `toggle-registration` endpoint), the organizer creates a fixture for the category.
    *   **Endpoint:** `POST /org/tournament/<t_id>/category/<c_id>/fixture/create/`
    *   **Details:** The organizer specifies the `fixtureType`, such as "KO" (Knockout) or "RR" (Round Robin).

8.  **Generate & Schedule Matches**
    *   **Action (for KO):** The organizer generates the initial bracket of matches.
    *   **Endpoint:** `POST /org/tournament/<t_id>/category/<c_id>/create_ko_matches/`
    *   **Action:** The organizer schedules the matches that are ready to be played.
    *   **Endpoint:** `POST /org/tournament/<t_id>/category/<c_id>/schedule_match/`

9.  **Manage Live Tournament**
    *   **Action:** As matches are played, the organizer updates the scores.
    *   **Endpoint:** `POST /org/tournament/<t_id>/category/<c_id>/update_score/`
    *   **System Behavior:** When a match finishes, the system automatically progresses the winner to the next round in a knockout fixture, making the next match available for scheduling.

10. **Monitor Progress**
    *   **Action:** Anyone can view the live state of the tournament bracket or standings.
    *   **Endpoint:** `GET /org/tournament/<t_id>/category/<c_id>/fixture/details/`

This flow continues until the final match is played and a tournament winner is determined.
