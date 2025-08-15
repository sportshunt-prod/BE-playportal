# Troubleshooting Guide

This guide lists common issues and solutions for the SportsHunt backend.

## 🐞 Common Issues

### 1. Migrations Not Applying
- **Solution:**
  ```bash
  python manage.py makemigrations
  python manage.py migrate
  ```

### 2. Auth0 Login Fails
- **Solution:**
  - Check Auth0 domain, client ID, and secret in your `.env` file.
  - Ensure callback URLs are set correctly in Auth0 dashboard.

### 3. Static Files Not Loading
- **Solution:**
  - Run `python manage.py collectstatic`.
  - Check your web server configuration for static and media files.

### 4. Database Connection Errors
- **Solution:**
  - Verify database credentials and host in `.env`.
  - Ensure the database server is running.

### 5. JWT Token Errors
- **Solution:**
  - Ensure the Authorization header is set: `Authorization: Bearer <token>`
  - Check token expiration and validity.

## 🛠️ Logs
- Check `logs/django.log` for error details.

## 📚 More Help
- See [README](./README.md) and [API Reference](./api-reference.md) for more info.
