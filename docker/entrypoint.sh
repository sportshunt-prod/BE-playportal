#!/bin/sh
set -e

# Ensure staticfiles directory exists
mkdir -p /app/staticfiles

if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
    echo "Running database migrations..."
    python manage.py migrate --noinput
fi

# Always collect static files in production (or if COLLECT_STATIC is true)
if [ "${COLLECT_STATIC:-true}" = "true" ]; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput || {
        echo "Warning: collectstatic failed, but continuing..."
    }
fi

echo "Starting server: $*"
exec "$@"

