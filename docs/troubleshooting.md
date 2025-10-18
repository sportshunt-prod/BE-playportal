# Troubleshooting Guide

This guide lists common issues and solutions for the SportsHunt backend.

## 🐞 Common Issues

### 1. Migrations Not Applying
- **Solution:**
  ```bash
  python manage.py makemigrations
  python manage.py migrate
  ```

### 2. Google OAuth Login Fails
- **Solution:**
  - Check `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in your `.env` file.
  - Ensure authorized JavaScript origins are set correctly in Google Cloud Console.
  - Verify Google+ API is enabled in your Google Cloud project.
  - Check that the Google ID token is not expired.

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
