#!/bin/sh
set -e

if [ "$1" = "celery" ]; then
    echo "Celery worker detected - skipping migrations and collectstatic..."
    exec "$@"
fi

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec "$@"
