#!/bin/bash
# Azure Web Apps startup script for SportsHunt Django application
# Production-optimized Gunicorn configuration

python -m gunicorn \
    --bind=0.0.0.0:8000 \
    --workers=2 \
    --timeout=30 \
    --max-requests=1000 \
    --max-requests-jitter=100 \
    --access-logfile=- \
    --error-logfile=- \
    --log-level=info \
    --worker-class=sync \
    --preload \
    sportshunt.wsgi:application
