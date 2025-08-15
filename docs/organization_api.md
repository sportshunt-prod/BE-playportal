# Organization API Documentation

This document details the endpoints available in the Organization API. All endpoints in this API require the user to be an authenticated organizer.

---

## Authentication

### Validate Organization User

-   **Description:** Checks if the user is an authenticated organizer and returns their organization details.
-   **Endpoint:** `/org/org_auth/`
-   **Method:** `GET`
-   **Authentication:** Required (Bearer Token, Organizer)
-   **Success Response (200 OK):**
    ```json
    {
        "isAuthenticated": true,
        "user": {
            "id": 2,
            "username": "orguser",
            "email": "org@example.com",
            "is_organizer": true
        },
        "organization": {
            "id": 1,
            "name": "My Sports Org",
            "admin": 2,
            "mail": "org@example.com",
            "ph_number": "0987654321"
        }
    }
    ```
-   **Error Response (Not Authenticated or Not Organizer):**
    ```json
    {
        "isAuthenticated": false
    }
    ```

---

## Organization

### Create Organization

-   **Description:** Creates a new organization for the authenticated organizer.
-   **Endpoint:** `/org/create/`
-   **Method:** `POST`
-   **Authentication:** Required (Bearer Token, Organizer)
-   **Request Body:**
    ```json
    {
        "name": "New Sports League",
        "mail": "contact@newleague.com",
        "ph_number": "1122334455"
    }
    ```
-   **Success Response (201 Created):**
    ```json
    {
        "id": 2,
        "name": "New Sports League",
        "admin": 2,
        "mail": "contact@newleague.com",
        "ph_number": "1122334455"
    }
    ```
-   **Error Response (400 Bad Request):**
    ```json
    {
        "name": [
            "Organization with this name already exists"
        ]
    }
    ```

---

## Tournaments

### Get Organizer's Dashboard

-   **Description:** Retrieves a list of tournaments created by the organizer's organization.
-   **Endpoint:** `/org/dashboard/`
-   **Method:** `GET`
-   **Authentication:** Required (Bearer Token, Organizer)
-   **Success Response (200 OK):**
    ```json
    {
        "tournaments": [
            {
                "id": 1,
                "name": "Summer Championship",
                "start_date": "2025-09-01",
                "end_date": "2025-09-05",
                "completed": false
            }
        ]
    }
    ```

### Create Tournament

-   **Description:** Creates a new tournament for the organizer's organization.
-   **Endpoint:** `/org/tournament/create/`
-   **Method:** `POST`
-   **Authentication:** Required (Bearer Token, Organizer)
-   **Request Body:**
    ```json
    {
        "name": "Annual Gala",
        "details": "The biggest tournament of the year.",
        "organization": 1,
        "start_date": "2025-10-01",
        "end_date": "2025-10-05",
        "venue_address": "789 Pine St, Anytown, USA",
        "ph_number": "5544332211",
        "sport": 1
    }
    ```
-   **Success Response (201 Created):**
    ```json
    {
        "id": 3,
        "name": "Annual Gala",
        "details": "The biggest tournament of the year.",
        "organization": 1,
        "start_date": "2025-10-01",
        "end_date": "2025-10-05",
        "venue_address": "789 Pine St, Anytown, USA",
        "venue_link": null,
        "ph_number": "5544332211",
        "sport": 1
    }
    ```

### Get Tournament Details

-   **Description:** Retrieves detailed information for a specific tournament owned by the organizer.
-   **Endpoint:** `/org/tournament/<tournament_id>/`
-   **Method:** `GET`
-   **Authentication:** Required (Bearer Token, Organizer)
-   **URL Parameters:**
    -   `tournament_id` (integer, required): The ID of the tournament.
-   **Success Response (200 OK):** (Similar to Core API's Get Tournament Details)

---

## Categories

### Create Category

-   **Description:** Creates a new category for a specific tournament.
-   **Endpoint:** `/org/tournament/<tournament_id>/category/create/`
-   **Method:** `POST`
-   **Authentication:** Required (Bearer Token, Organizer)
-   **URL Parameters:**
    -   `tournament_id` (integer, required): The ID of the tournament.
-   **Request Body:**
    ```json
    {
        "name": "U-15 Girls",
        "details": "Under 15 girls category",
        "price": "500.00",
        "tournament": 1
    }
    ```
-   **Success Response (201 Created):**
    ```json
    {
        "id": 2,
        "name": "U-15 Girls",
        "details": "Under 15 girls category",
        "price": "500.00",
        "tournament": 1
    }
    ```

### Toggle Registration

-   **Description:** Opens or closes registration for a category.
-   **Endpoint:** `/org/tournament/<tournament_id>/category/<category_id>/toggle-registration/`
-   **Method:** `POST`
-   **Authentication:** Required (Bearer Token, Organizer)
-   **URL Parameters:**
    -   `tournament_id` (integer, required): The ID of the tournament.
    -   `category_id` (integer, required): The ID of the category.
-   **Success Response (200 OK):**
    ```json
    {
        "success": true,
        "new_status": true,
        "status_text": "Registration Open"
    }
    ```

---


## Teams & Fixtures

### Register Team

-   **Description:** Registers a new team for a specific category in a tournament.
-   **Endpoint:** `/org/tournament/<tournament_id>/category/<category_id>/team/create/`
-   **Method:** `POST`
-   **Authentication:** Required (Bearer Token, Organizer)
-   **URL Parameters:**
    -   `tournament_id` (integer, required): The ID of the tournament.
    -   `category_id` (integer, required): The ID of the category.
-   **Request Body:**
    ```json
    {
        "name": "The Champions"
    }
    ```
-   **Success Response (201 Created):**
    ```json
    {
        "success": true,
        "team": {
            "id": 1,
            "name": "The Champions",
            "category": 1
        }
    }
    ```
-   **Error Response (400 Bad Request):**
    ```json
    {
        "success": false,
        "errors": {
            "name": [
                "This field may not be blank."
            ]
        }
    }
    ```

### Create Fixture

-   **Description:** Creates a fixture (e.g., Knockout or Round Robin) for a category.
-   **Endpoint:** `/org/tournament/<tournament_id>/category/<category_id>/fixture/create/`
-   **Method:** `POST`
-   **Authentication:** Required (Bearer Token, Organizer)
-   **URL Parameters:**
    -   `tournament_id` (integer, required): The ID of the tournament.
    -   `category_id` (integer, required): The ID of the category.
-   **Request Body:**
    ```json
    {
        "fixtureType": "KO"
    }
    ```
-   **Success Response (201 Created):**
    ```json
    {
        "success": true,
        "fixture": {
            "id": 1,
            "fixtureType": "KO",
            "category": 1
        }
    }
    ```
-   **Error Response (400 Bad Request):**
    ```json
    {
        "error": "This category already has a fixture"
    }
    ```

### Create Knockout Matches

-   **Description:** Creates the initial set of matches for a knockout fixture.
-   **Endpoint:** `/org/tournament/<tournament_id>/category/<category_id>/create_ko_matches/`
-   **Method:** `POST`
-   **Authentication:** Required (Bearer Token, Organizer)
-   **URL Parameters:**
    -   `tournament_id` (integer, required): The ID of the tournament.
    -   `category_id` (integer, required): The ID of the category.
-   **Request Body:**
    ```json
    {
        "matches": [
            {"team_1": 1, "team_2": 2},
            {"team_1": 3, "team_2": "BYE"}
        ],
        "no_sets": 3,
        "points_win": 21,
        "use_complete_bracket": true
    }
    ```
-   **Success Response (200 OK):**
    ```json
    {
        "success": true,
        "message": "Matches created successfully.",
        "bracket_mode": "complete_bracket",
        "matches_created": 1,
        "immediately_schedulable": 1
    }
    ```

### Schedule Match

-   **Description:** Schedules a match from the available pool of matches in a fixture. Can also be used to retrieve available matches.
-   **Endpoint:** `/org/tournament/<tournament_id>/category/<category_id>/schedule_match/`
-   **Method:** `GET`, `POST`
-   **Authentication:** Required (Bearer Token, Organizer)
-   **URL Parameters:**
    -   `tournament_id` (integer, required): The ID of the tournament.
    -   `category_id` (integer, required): The ID of the category.
-   **GET Success Response (200 OK):**
    ```json
    {
        "success": true,
        "fixture_type": "KO",
        "available_matches": [
            {
                "id": 1,
                "team1": "Team A",
                "team2": "Team B"
            }
        ],
        "total_matches": 1
    }
    ```
-   **POST Request Body:**
    ```json
    {
        "match_id": 1
    }
    ```
-   **POST Success Response (200 OK):**
    ```json
    {
        "success": true,
        "message": "Match scheduled successfully",
        "match": {
            "id": 1,
            "team1": "Team A",
            "team2": "Team B",
            "status": "scheduled"
        },
        "next_available_matches": 0
    }
    ```

### Update Score

-   **Description:** Updates the score for a scheduled match.
-   **Endpoint:** `/org/tournament/<tournament_id>/category/<category_id>/update_score/`
-   **Method:** `POST`
-   **Authentication:** Required (Bearer Token, Organizer)
-   **URL Parameters:**
    -   `tournament_id` (integer, required): The ID of the tournament.
    -   `category_id` (integer, required): The ID of the category.
-   **Request Body:**
    ```json
    {
        "match_id": 1,
        "action": "increment",
        "team_id": 1
    }
    ```
-   **Success Response (200 OK):**
    ```json
    {
        "success": true,
        "message": "Score updated",
        "match_completed": false,
        "winner": null,
        "next_matches_available": 0,
        "tournament_completed": false
    }
    ```

### Get Fixture Details

-   **Description:** Retrieves the full fixture details, structured for frontend visualization (e.g., a tournament bracket).
-   **Endpoint:** `/org/tournament/<tournament_id>/category/<category_id>/fixture/details/`
-   **Method:** `GET`
-   **Authentication:** Required (Bearer Token, Organizer)
-   **URL Parameters:**
    -   `tournament_id` (integer, required): The ID of the tournament.
    -   `category_id` (integer, required): The ID of the category.
-   **Success Response (200 OK for KO):**
    ```json
    {
        "fixture_type": "KO",
        "sport_type": "sets",
        "stages": [
            {
                "stageIndex": 1,
                "name": "Finals",
                "matches": [
                    {
                        "id": "s1m1",
                        "team1": "Team A",
                        "team2": "Team B",
                        "winner": "Team A",
                        "team1Score": 2,
                        "team2Score": 1,
                        "currentSetScore": {
                            "team1Points": 0,
                            "team2Points": 0
                        }
                    }
                ]
            }
        ]
    }
    ```
-   **Success Response (200 OK for RR):**
    ```json
    {
        "fixture_type": "RR",
        "sport_type": "simple",
        "teams": ["Team A", "Team B", "Team C"],
        "results": [
            {
                "team1": "Team A",
                "team2": "Team B",
                "score1": 21,
                "score2": 15
            }
        ]
    }
    ```

