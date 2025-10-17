# Authentication Endpoints - Quick Reference

Quick reference guide for native authentication with JWT Bearer tokens.

## 🔐 Authentication Endpoints

### 1. Register New User

**Endpoint:** `POST /auth/register/`  
**Authentication:** None required

**Request Body:**
```json
{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
}
```

**Success Response (201 Created):**
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

**Error Response (400 Bad Request):**
```json
{
    "email": ["User with this email already exists"],
    "username": ["Username already taken"],
    "password": ["This password is too common."],
    "password_confirm": ["Passwords do not match"]
}
```

**Password Requirements:**
- Minimum 8 characters
- Cannot be too similar to username/email
- Cannot be a commonly used password
- Cannot be entirely numeric

**Token:** Store the returned `token` in localStorage or sessionStorage

---

### 2. Login with Email/Password

**Endpoint:** `POST /auth/login/`  
**Authentication:** None required

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "SecurePass123!"
}
```

**Success Response (200 OK):**
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

**Error Response (401 Unauthorized):**
```json
{
    "error": "Invalid credentials"
}
```

**Token:** Store the returned `token` in localStorage or sessionStorage

---

### 3. Google OAuth Authentication

**Endpoint:** `POST /auth/google/`  
**Authentication:** None required

**Request Body:**
```json
{
    "credential": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjZmODk..."
}
```

**Success Response (200 OK):**
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

**Error Response (401 Unauthorized):**
```json
{
    "error": "Invalid Google token"
}
```

**Notes:**
- The `credential` is the Google ID token obtained from Google Sign-In
- User is created if email doesn't exist
- Username is derived from email (before @ symbol)
- Store the returned `token` in localStorage or sessionStorage

**Frontend Integration Example:**
```javascript
google.accounts.id.initialize({
    client_id: 'YOUR_GOOGLE_CLIENT_ID',
    callback: handleCredentialResponse
});

function handleCredentialResponse(response) {
    fetch('/auth/google/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({credential: response.credential})
    })
    .then(res => res.json())
    .then(data => {
        // Store token
        localStorage.setItem('token', data.token);
        console.log('Authenticated:', data.user);
    });
}
```

---

### 4. Check Authentication Status

**Endpoint:** `GET /auth/check/`  
**Authentication:** Bearer Token required

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK) - Authenticated:**
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

**Success Response (200 OK) - Not Authenticated:**
```json
{
    "isAuthenticated": false
}
```

**Usage:**
- Called on app initialization to check if user is logged in
- Must include Bearer token in Authorization header
- No request body needed

---

### 5. Logout

**Endpoint:** `POST /auth/logout/`  
**Authentication:** None required

**Response (200 OK):**
```json
{
    "message": "Logout successful"
}
```

**Usage:**
```javascript
// Remove token from storage
localStorage.removeItem('token');

// Optional: call logout endpoint for logging
fetch('/auth/logout/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'}
});
```

---

## 🔑 JWT Bearer Token Details

### Token Storage
- Store in `localStorage` or `sessionStorage`
- Include in `Authorization` header for all authenticated requests
- Format: `Authorization: Bearer <token>`

### Token Expiration
- **Duration:** 30 days
- **Auto-refresh:** Not implemented (token is valid for full 30 days)
- **On expiration:** User must login again

### Using Tokens in Requests
```javascript
const token = localStorage.getItem('token');

fetch('/api/endpoint/', {
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    }
});
```

---

## 🌐 Frontend Integration Examples

### Fetch API (Vanilla JavaScript)

```javascript
// Registration
async function register(email, username, password, passwordConfirm) {
    const response = await fetch('/auth/register/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            email, 
            username, 
            password, 
            password_confirm: passwordConfirm
        })
    });
    
    if (response.ok) {
        const data = await response.json();
        // Store token
        localStorage.setItem('token', data.token);
        return {success: true, user: data.user};
    } else {
        const errors = await response.json();
        return {success: false, errors};
    }
}

// Login
async function login(email, password) {
    const response = await fetch('/auth/login/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email, password})
    });
    
    if (response.ok) {
        const data = await response.json();
        // Store token
        localStorage.setItem('token', data.token);
        return {success: true, user: data.user};
    } else {
        const errors = await response.json();
        return {success: false, error: errors.error};
    }
}

// Check auth
async function checkAuth() {
    const token = localStorage.getItem('token');
    if (!token) return null;
    
    const response = await fetch('/auth/check/', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    const data = await response.json();
    return data.isAuthenticated ? data.user : null;
}

// Logout
function logout() {
    localStorage.removeItem('token');
    fetch('/auth/logout/', {method: 'POST'});
}

// Make authenticated request
async function getProfile() {
    const token = localStorage.getItem('token');
    const response = await fetch('/profile/', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    return response.json();
}
```

### Axios

```javascript
import axios from 'axios';

// Configure axios instance
const api = axios.create({
    baseURL: 'http://localhost:8000',
    headers: {'Content-Type': 'application/json'}
});

// Add auth token to all requests
api.interceptors.request.use(config => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Registration
async function register(email, username, password, passwordConfirm) {
    try {
        const response = await api.post('/auth/register/', {
            email, username, password, password_confirm: passwordConfirm
        });
        // Store token
        localStorage.setItem('token', response.data.token);
        return {success: true, user: response.data.user};
    } catch (error) {
        return {success: false, errors: error.response.data};
    }
}

// Login
async function login(email, password) {
    try {
        const response = await api.post('/auth/login/', {email, password});
        // Store token
        localStorage.setItem('token', response.data.token);
        return {success: true, user: response.data.user};
    } catch (error) {
        return {success: false, error: error.response.data.error};
    }
}

// Check auth
async function checkAuth() {
    try {
        const response = await api.get('/auth/check/');
        return response.data.isAuthenticated ? response.data.user : null;
    } catch (error) {
        return null;
    }
}

// Logout
function logout() {
    localStorage.removeItem('token');
    api.post('/auth/logout/');
}
```

### React Hook Example

```javascript
import { useState, useEffect } from 'react';

export function useAuth() {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        checkAuth();
    }, []);

    async function checkAuth() {
        const token = localStorage.getItem('token');
        if (!token) {
            setLoading(false);
            return;
        }

        const response = await fetch('/auth/check/', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        const data = await response.json();
        setUser(data.isAuthenticated ? data.user : null);
        setLoading(false);
    }

    async function login(email, password) {
        const response = await fetch('/auth/login/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email, password})
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('token', data.token);
            setUser(data.user);
            return {success: true};
        } else {
            return {success: false, error: 'Invalid credentials'};
        }
    }

    async function register(email, username, password, passwordConfirm) {
        const response = await fetch('/auth/register/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                email, username, password, 
                password_confirm: passwordConfirm
            })
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('token', data.token);
            setUser(data.user);
            return {success: true};
        } else {
            const errors = await response.json();
            return {success: false, errors};
        }
    }

    function logout() {
        localStorage.removeItem('token');
        setUser(null);
        fetch('/auth/logout/', {method: 'POST'});
    }

    return {user, loading, login, register, logout, checkAuth};
}
```

---

## 🧪 Testing with cURL

```bash
# Register
curl -X POST http://localhost:8000/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"SecurePass123!","password_confirm":"SecurePass123!"}'

# Save token from response, then:

# Login
TOKEN=$(curl -X POST http://localhost:8000/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"SecurePass123!"}' \
  | jq -r '.token')

# Check auth
curl -X GET http://localhost:8000/auth/check/ \
  -H "Authorization: Bearer $TOKEN"

# Access protected endpoint
curl -X GET http://localhost:8000/profile/ \
  -H "Authorization: Bearer $TOKEN"

# Logout
curl -X POST http://localhost:8000/auth/logout/
```

---

## 🔒 Security Considerations

### Token Storage Options

**localStorage (Recommended for SPAs):**
- Persists across browser sessions
- Survives page refreshes
- More convenient for users

**sessionStorage:**
- Clears when tab is closed
- More secure but less convenient
- Good for sensitive applications

### Security Best Practices

1. **Always use HTTPS in production**
2. **Set appropriate token expiration** (currently 30 days)
3. **Validate token on every request** (done automatically by decorators)
4. **Clear token on logout**
5. **Handle token expiration gracefully** (redirect to login)

### CORS Configuration

Backend must allow your frontend domain:
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Development
    "https://yourdomain.com",  # Production
]
```

---

## 📚 Related Documentation

- [Full Authentication Guide](./authentication.md)
- [Getting Started](./getting-started.md)
- [Deployment Guide](./deployment.md)
- [Core API Reference](./core_api.md)
