# Core API Documentation

This document details the endpoints available in the Core API.

---

## Authentication

### Check Authentication Status

-   **Description:** Checks if the user is authenticated.
-   **Endpoint:** `/auth/check/`
-   **Method:** `GET`
-   **Authentication:** Required (Bearer Token)
-   **Success Response (200 OK):**
    ```json
    {
        "isAuthenticated": true,
        "user": {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "is_organizer": false
        }
    }
    ```
-   **Error Response (Not Authenticated):**
    ```json
    {
        "isAuthenticated": false
    }
    ```

### Login

-   **Description:** Redirects the user to the Auth0 login page to initiate the login flow.
-   **Endpoint:** `/login/`
-   **Method:** `GET`

### Logout

-   **Description:** Logs the user out and redirects to the Auth0 logout page.
-   **Endpoint:** `/logout/`
-   **Method:** `GET`

---

## Tournaments

### List Upcoming and Past Tournaments

-   **Description:** Retrieves a list of upcoming and past tournaments.
-   **Endpoint:** `/upcoming-past_tournaments/`
-   **Method:** `GET`
-   **Success Response (200 OK):**
    ```json
    {
        "upcoming_tournaments": [
            {
                "id": 1,
                "name": "Summer Championship",
                "organization": {
                    "name": "Sports Org"
                },
                "start_date": "2025-09-01",
                "end_date": "2025-09-05",
                "venue_address": "123 Main St, Anytown, USA",
                "completed": false,
                "start_month": "Sep",
                "start_day_date": "01",
                "card_details": "Starts on September 1, 2025",
                "end_date_": "September 5, 2025"
            }
        ],
        "past_tournaments": [
            {
                "id": 2,
                "name": "Winter Cup",
                "organization": {
                    "name": "Sports Org"
                },
                "start_date": "2025-01-10",
                "end_date": "2025-01-15",
                "venue_address": "456 Oak Ave, Anytown, USA",
                "completed": true,
                "start_month": "Jan",
                "start_day_date": "10",
                "card_details": "Ended on January 15, 2025",
                "end_date_": "January 15, 2025"
            }
        ]
    }
    ```

### Get Tournament Details

-   **Description:** Retrieves detailed information for a specific tournament.
-   **Endpoint:** `/tournament/<tournament_id>/`
-   **Method:** `GET`
-   **URL Parameters:**
    -   `tournament_id` (integer, required): The ID of the tournament.
-   **Success Response (200 OK):**
    ```json
    {
        "id": 1,
        "name": "Summer Championship",
        "details": "Annual summer tournament.",
        "organization": {
            "name": "Sports Org"
        },
        "start_date": "2025-09-01",
        "end_date": "2025-09-05",
        "venue_address": "123 Main St, Anytown, USA",
        "venue_link": "https://maps.google.com/?q=123+Main+St",
        "ph_number": "1234567890",
        "completed": false,
        "sport": "Football",
        "categories": [
            {
                "id": 1,
                "name": "U-19 Boys",
                "details": "Under 19 boys category",
                "price": "1000.00",
                "registration_status": true,
                "tournament": 1
            }
        ]
    }
    ```
-   **Error Response (404 Not Found):**
    ```json
    {
        "detail": "Not found."
    }
    ```

### Get Category Details

-   **Description:** Retrieves detailed information for a specific category within a tournament.
-   **Endpoint:** `/tournament/<tournament_id>/category/<category_id>/`
-   **Method:** `GET`
-   **URL Parameters:**
    -   `tournament_id` (integer, required): The ID of the tournament.
    -   `category_id` (integer, required): The ID of the category.
-   **Success Response (200 OK):**
    ```json
    {
        "id": 1,
        "name": "U-19 Boys",
        "details": "Under 19 boys category",
        "price": "1000.00",
        "registration_status": true,
        "tournament": 1,
        "teams": [],
        "fixtures": []
    }
    ```
-   **Error Response (404 Not Found):**
    ```json
    {
        "detail": "Not found."
    }
    ```

---

## User

### Get User Profile

-   **Description:** Retrieves the profile of the authenticated user.
-   **Endpoint:** `/profile/`
-   **Method:** `GET`
-   **Authentication:** Required (Bearer Token)
-   **Success Response (200 OK):**
    ```json
    {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "is_organizer": false,
        "auth0_data": {
            "uid": "auth0|62f1234567890abcdef",
            "extra_data": {
                "nickname": "testuser",
                "name": "Test User",
                "picture": "https://example.com/picture.jpg",
                "updated_at": "2025-08-14T12:00:00.000Z"
            }
        }
    }
    ```
