# Deployment Guide

This guide explains how to deploy the SportsHunt backend to a production environment.

## 🚀 Deployment Checklist

- [ ] Set up a production database (PostgreSQL recommended)
- [ ] Configure environment variables (see `.env` example below)
- [ ] Set `DEBUG=False` in production
- [ ] Set up a secure `SECRET_KEY`
- [ ] Configure allowed hosts
- [ ] Set up static and media file hosting
- [ ] Configure Auth0 for production domain
- [ ] Set up a WSGI server (e.g., Gunicorn, uWSGI)
- [ ] Use a reverse proxy (e.g., Nginx)
- [ ] Set up HTTPS (SSL/TLS)
- [ ] Set up logging and monitoring

## Example Production `.env`

```env
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=yourdomain.com
DATABASE_URL=postgres://user:password@host:port/dbname
SOCIAL_AUTH_AUTH0_DOMAIN=your-auth0-domain
SOCIAL_AUTH_AUTH0_KEY=your-auth0-client-id
SOCIAL_AUTH_AUTH0_SECRET=your-auth0-client-secret
```

## Static & Media Files

- Run `python manage.py collectstatic` to gather static files.
- Configure your web server to serve static and media files.

## Database Migrations

- Run `python manage.py migrate` after deployment.

## Gunicorn Example

```bash
gunicorn sportshunt.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

## Nginx Example (snippet)

```
server {
    listen 80;
    server_name yourdomain.com;

    location /static/ {
        alias /path/to/static/;
    }
    location /media/ {
        alias /path/to/media/;
    }
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Monitoring & Logging

- Use tools like Sentry, Prometheus, or ELK stack for monitoring.
- Configure Django logging in `settings.py`.

## Troubleshooting

- Check logs for errors: `logs/django.log`
- Ensure all environment variables are set correctly.
- Verify database connectivity.
