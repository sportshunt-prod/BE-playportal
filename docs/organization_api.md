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
-   **Success Response (200 OK):**
    ```json
    {
        "tournament": {
            "id": 1,
            "name": "awfaf",
            "details": "awfawfa",
            "organization": 1,
            "start_date": "2025-08-17",
            "end_date": "2025-08-18",
            "venue_address": "earth",
            "venue_link": null,
            "ph_number": "1234567890",
            "sport": {
                "id": 1,
                "name": "tennis",
                "scoring_type": "sets"
            },
            "categories": [
                {
                    "id": 1,
                    "name": "u18",
                    "details": "Age Group: 18, Gender: mixed, Max Teams: Not specified, Team Size: Not specified",
                    "price": "500.00",
                    "registration_status": true
                }
            ]
        },
        "categories": [
            {
                "id": 1,
                "name": "u18",
                "details": "Age Group: 18, Gender: mixed, Max Teams: Not specified, Team Size: Not specified",
                "price": "500.00",
                "registration_status": true,
                "reg_status": "Open",
                "teams_count": 0,
                "teams": [],
                "winner": null,
                "has_fixture": false,
                "fixture_type": null,
                "scheduled_matches": [],
                "scheduled_matches_count": 0,
                "completed_matches_count": 0,
                "pending_matches_count": 0,
                "max_sets": 3,
                "required_points": 21
            }
        ],
        "teams": [],
        "total_teams": 0,
        "total_categories": 1,
        "scheduled_matches": [],
        "total_scheduled_matches": 0,
        "total_completed_matches": 0,
        "total_pending_matches": 0
    }
    ```

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

---

## Court Management

### List Courts

-   **Description:** Retrieves all courts for a specific tournament.
-   **Endpoint:** `/org/tournament/<tournament_id>/courts/`
-   **Method:** `GET`
-   **Authentication:** Required (Bearer Token, Organizer)
-   **URL Parameters:**
    -   `tournament_id` (integer, required): The ID of the tournament.
-   **Success Response (200 OK):**
    ```json
    {
        "courts": [
            {
                "id": 1,
                "name": "Court 1",
                "tournament": 1,
                "current_match": {
                    "id": 15,
                    "team1_name": "Team A",
                    "team2_name": "Team B",
                    "category_name": "Men's Singles",
                    "stage": 2,
                    "match_number": 1
                },
                "upcoming_matches_count": 3,
                "upcoming_matches": [],
                "is_available": false
            },
            {
                "id": 2,
                "name": "Court 2",
                "tournament": 1,
                "current_match": null,
                "upcoming_matches_count": 0,
                "upcoming_matches": [],
                "is_available": true
            }
        ]
    }
    ```

### Create Court

-   **Description:** Creates a new court for a specific tournament.
-   **Endpoint:** `/org/tournament/<tournament_id>/new_courts/`
-   **Method:** `POST`
-   **Authentication:** Required (Bearer Token, Organizer)
-   **URL Parameters:**
    -   `tournament_id` (integer, required): The ID of the tournament.
-   **Request Body:**
    ```json
    {
        "name": "Court 3"
    }
    ```
-   **Success Response (201 Created):**
    ```json
    {
        "id": 3,
        "name": "Court 3",
        "tournament": 1,
        "current_match": null,
        "upcoming_matches_count": 0,
        "upcoming_matches": [],
        "is_available": true
    }
    ```
-   **Error Response (400 Bad Request):**
    ```json
    {
        "name": ["Court with this name already exists in this tournament"]
    }
    ```

### Get Court Details

-   **Description:** Retrieves detailed information about a specific court, including current match and upcoming match queue.
-   **Endpoint:** `/org/courts/<court_id>/`
-   **Method:** `GET`
-   **Authentication:** Required (Bearer Token, Organizer)
-   **URL Parameters:**
    -   `court_id` (integer, required): The ID of the court.
-   **Success Response (200 OK):**
    ```json
    {
        "id": 1,
        "name": "Court 1",
        "tournament": 1,
        "current_match": {
            "id": 15,
            "team1_name": "Team A",
            "team2_name": "Team B",
            "category_name": "Men's Singles",
            "stage": 2,
            "match_number": 1
        },
        "upcoming_matches_count": 2,
        "upcoming_matches": [
            {
                "id": 16,
                "queue_position": 1,
                "team1_name": "Team C",
                "team2_name": "Team D",
                "category_name": "Men's Singles",
                "stage": 2,
                "match_number": 2
            },
            {
                "id": 17,
                "queue_position": 2,
                "team1_name": "Team E",
                "team2_name": "Team F",
                "category_name": "Women's Singles",
                "stage": 1,
                "match_number": 1
            }
        ],
        "is_available": false
    }
    ```

### Update Court

-   **Description:** Updates the name of a specific court.
-   **Endpoint:** `/org/courts/<court_id>/`
-   **Method:** `PUT`
-   **Authentication:** Required (Bearer Token, Organizer)
-   **URL Parameters:**
    -   `court_id` (integer, required): The ID of the court.
-   **Request Body:**
    ```json
    {
        "name": "Center Court"
    }
    ```
-   **Success Response (200 OK):**
    ```json
    {
        "id": 1,
        "name": "Center Court",
        "tournament": 1,
        "current_match": null,
        "upcoming_matches_count": 0,
        "upcoming_matches": [],
        "is_available": true
    }
    ```

### Delete Court

-   **Description:** Deletes a court. Only allowed if no matches are currently assigned or queued.
-   **Endpoint:** `/org/courts/<court_id>/`
-   **Method:** `DELETE`
-   **Authentication:** Required (Bearer Token, Organizer)
-   **URL Parameters:**
    -   `court_id` (integer, required): The ID of the court.
-   **Success Response (200 OK):**
    ```json
    {
        "success": true,
        "message": "Court deleted"
    }
    ```
-   **Error Response (400 Bad Request):**
    ```json
    {
        "error": "Court cannot be deleted while matches are assigned"
    }
    ```

---

## Enhanced Match Scheduling with Court Assignment

### Schedule Match with Court Assignment

-   **Description:** Schedules a match from the available pool and optionally assigns it to a court with automatic queue management.
-   **Endpoint:** `/org/tournament/<tournament_id>/category/<category_id>/schedule_match/`
-   **Method:** `POST`
-   **Authentication:** Required (Bearer Token, Organizer)
-   **URL Parameters:**
    -   `tournament_id` (integer, required): The ID of the tournament.
    -   `category_id` (integer, required): The ID of the category.
-   **Request Body (With Court Assignment):**
    ```json
    {
        "match_id": 15,
        "court_id": 1
    }
    ```
-   **Request Body (Without Court Assignment - Backward Compatible):**
    ```json
    {
        "match_id": 15
    }
    ```
-   **Success Response with Court Assignment (200 OK):**
    ```json
    {
        "success": true,
        "message": "Match scheduled successfully and assigned to Court 1",
        "match": {
            "id": 15,
            "team1": "Team A",
            "team2": "Team B",
            "stage": 2,
            "match_number": 1
        },
        "court": {
            "id": 1,
            "name": "Court 1"
        },
        "position": "current",
        "queue_position": null,
        "next_available_matches": 2
    }
    ```
-   **Success Response with Queue Assignment (200 OK):**
    ```json
    {
        "success": true,
        "message": "Match scheduled and queued for Court 1 (position 3)",
        "match": {
            "id": 16,
            "team1": "Team C",
            "team2": "Team D",
            "stage": 2,
            "match_number": 2
        },
        "court": {
            "id": 1,
            "name": "Court 1"
        },
        "position": "queued",
        "queue_position": 3,
        "next_available_matches": 1
    }
    ```

### Auto-Queue Logic

When a match is scheduled with a `court_id`:

1. **Court Available**: If `court.current_match` is `NULL`, the match is assigned as the current match
2. **Court Occupied**: If `court.current_match` exists, the match is added to `court.upcoming_matches` queue
3. **Queue Management**: The court automatically manages FIFO (First In, First Out) queue ordering
4. **Position Tracking**: API response indicates whether match is "current" or "queued" with position

---

## Enhanced Score Updates with Court Advancement

### Update Score with Automatic Court Advancement

-   **Description:** Updates match scores and automatically advances courts when matches are completed.
-   **Endpoint:** `/org/tournament/<tournament_id>/category/<category_id>/update_score/`
-   **Method:** `POST`
-   **Authentication:** Required (Bearer Token, Organizer)
-   **URL Parameters:**
    -   `tournament_id` (integer, required): The ID of the tournament.
    -   `category_id` (integer, required): The ID of the category.
-   **Request Body:**
    ```json
    {
        "match_id": 15,
        "action": "finish"
    }
    ```
-   **Success Response with Court Advancement (200 OK):**
    ```json
    {
        "success": true,
        "message": "Match completed successfully. Court Court 1 advanced to next match: Team C vs Team D",
        "match_completed": true,
        "winner": "Team A",
        "next_matches_available": 1,
        "tournament_completed": false,
        "court_advancement": {
            "court_id": 1,
            "court_name": "Court 1",
            "advanced": true,
            "previous_match_id": 15,
            "new_current_match": {
                "id": 16,
                "team1": "Team C",
                "team2": "Team D",
                "category": "Men's Singles"
            },
            "court_available": false,
            "remaining_queue_count": 1
        }
    }
    ```
-   **Success Response with Court Becoming Available (200 OK):**
    ```json
    {
        "success": true,
        "message": "Match completed successfully. Court Court 1 is now available",
        "match_completed": true,
        "winner": "Team B",
        "court_advancement": {
            "court_id": 1,
            "court_name": "Court 1",
            "advanced": true,
            "previous_match_id": 20,
            "new_current_match": null,
            "court_available": true,
            "remaining_queue_count": 0
        }
    }
    ```

### Court Advancement Workflow

When a match is completed:

1. **Match Completion**: System detects match completion (winner determined)
2. **Court Detection**: System checks if completed match was assigned to a court
3. **Auto-Advancement**: Court automatically advances to next queued match using `court.advance_to_next_match()`
4. **Status Update**: Court status updates (occupied → next match, or occupied → available)
5. **Response Enhancement**: API response includes detailed court advancement information

---

## Complete Court Management Workflow

### Tournament Setup with Courts

1. **Create Tournament** → `POST /org/tournament/create/`
2. **Create Categories** → `POST /org/tournament/{id}/category/create/`
3. **Create Courts** → `POST /org/tournament/{id}/new_courts/`
4. **Register Teams** → `POST /org/tournament/{id}/category/{id}/team/create/`
5. **Create Fixtures** → `POST /org/tournament/{id}/category/{id}/fixture/create/`
6. **Generate Matches** → `POST /org/tournament/{id}/category/{id}/create_ko_matches/`

### Match Management with Courts

1. **Schedule with Court** → `POST /org/tournament/{id}/category/{id}/schedule_match/` (with `court_id`)
2. **Update Scores** → `POST /org/tournament/{id}/category/{id}/update_score/`
3. **Auto-Advancement** → System automatically advances courts on match completion
4. **Monitor Courts** → `GET /org/tournament/{id}/courts/` or `GET /org/courts/{id}/`

### Court Status Management

- **Available**: `current_match` is `null`, no upcoming matches
- **Occupied**: `current_match` exists, may have upcoming matches in queue
- **Queued**: Matches waiting in `upcoming_matches` for their turn
- **Auto-Progression**: System handles all queue management automatically

