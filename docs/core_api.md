# Core API Documentation

This document details the endpoints available in the Core API.

---

## Authentication

### Register

-   **Description:** Register a new user with email and password.
-   **Endpoint:** `/auth/register/`
-   **Method:** `POST`
-   **Authentication:** None required
-   **Request Body:**
    ```json
    {
        "email": "user@example.com",
        "username": "johndoe",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!"
    }
    ```
-   **Success Response (201 Created):**
    ```json
    {
        "message": "Registration successful",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "user": {
            "id": 1,
            "username": "johndoe",
            "email": "user@example.com",
            "is_organizer": false
        }
    }
    ```
-   **Error Response (400 Bad Request):**
    ```json
    {
        "email": ["User with this email already exists"],
        "password": ["This password is too common."]
    }
    ```

### Login

-   **Description:** Login with email and password to receive a JWT token.
-   **Endpoint:** `/auth/login/`
-   **Method:** `POST`
-   **Authentication:** None required
-   **Request Body:**
    ```json
    {
        "email": "user@example.com",
        "password": "SecurePass123!"
    }
    ```
-   **Success Response (200 OK):**
    ```json
    {
        "message": "Login successful",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "user": {
            "id": 1,
            "username": "johndoe",
            "email": "user@example.com",
            "is_organizer": false
        }
    }
    ```
-   **Error Response (401 Unauthorized):**
    ```json
    {
        "error": "Invalid credentials"
    }
    ```

### Google OAuth

-   **Description:** Login or register using Google OAuth credentials.
-   **Endpoint:** `/auth/google/`
-   **Method:** `POST`
-   **Authentication:** None required
-   **Request Body:**
    ```json
    {
        "credential": "google-id-token-here"
    }
    ```
-   **Success Response (200 OK):**
    ```json
    {
        "message": "Google authentication successful",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "user": {
            "id": 2,
            "username": "googleuser",
            "email": "googleuser@example.com",
            "is_organizer": false
        }
    }
    ```
-   **Error Response (401 Unauthorized):**
    ```json
    {
        "error": "Invalid Google token"
    }
    ```

### Check Authentication Status

-   **Description:** Checks if the user is authenticated using their Bearer token.
-   **Endpoint:** `/auth/check/`
-   **Method:** `GET`
-   **Authentication:** Required (Bearer Token)
-   **Headers:**
    ```
    Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    ```
-   **Success Response (200 OK):**
    ```json
    {
        "isAuthenticated": true,
        "user": {
            "id": 1,
            "name": "johndoe",
            "email": "user@example.com",
            "is_org": false
        }
    }
    ```
-   **Error Response (Not Authenticated):**
    ```json
    {
        "isAuthenticated": false
    }
    ```

### Logout

-   **Description:** Logout endpoint (token should be removed client-side).
-   **Endpoint:** `/auth/logout/`
-   **Method:** `POST`
-   **Authentication:** None required
-   **Success Response (200 OK):**
    ```json
    {
        "message": "Logout successful"
    }
    ```

---

## Sports

### List All Sports

-   **Description:** Retrieves a list of all available sports in the system. No authentication required.
-   **Endpoint:** `/sports/`
-   **Method:** `GET`
-   **Authentication:** None required
-   **Success Response (200 OK):**
    ```json
    [
        {
            "id": 1,
            "name": "Tennis",
            "scoring_type": "sets"
        },
        {
            "id": 2,
            "name": "Badminton",
            "scoring_type": "sets"
        },
        {
            "id": 3,
            "name": "Basketball",
            "scoring_type": "simple"
        },
        {
            "id": 4,
            "name": "Football",
            "scoring_type": "simple"
        },
        {
            "id": 5,
            "name": "Volleyball",
            "scoring_type": "sets"
        }
    ]
    ```


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
-   **Headers:**
    ```
    Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    ```
-   **Success Response (200 OK):**
    ```json
    {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "is_organizer": false
    }
    ```
-   **Error Response (401 Unauthorized):**
    ```json
    {
        "error": "Authorization header required. Format: Bearer <token>"
    }
    ```
