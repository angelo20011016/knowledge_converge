#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

echo "==> Running database migrations..."
# This command creates the database tables if they don't exist
# and applies any subsequent migrations.
flask db upgrade

echo "==> Starting Gunicorn server..."
# Now, execute the main command (start the web server)
exec gunicorn --workers 4 --worker-class gthread --timeout 360 --bind 0.0.0.0:5000 "app:app"