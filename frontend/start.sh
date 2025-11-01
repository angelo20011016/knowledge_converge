#!/bin/sh

# Default to development mode
if [ "$ENV_MODE" = "production" ]; then
  echo "Running in PRODUCTION mode"
  # Use the production config (no proxy)
  cp /etc/nginx/nginx.prod.conf /etc/nginx/conf.d/default.conf
else
  echo "Running in DEVELOPMENT mode"
  # Use the development config (with proxy to backend)
  cp /etc/nginx/nginx.dev.conf /etc/nginx/conf.d/default.conf
fi

# Wait for the backend to be available
echo "Waiting for backend..."
while ! nc -z backend 5000; do
  sleep 1
done
echo "Backend is up - starting Nginx"

# Start Nginx in the foreground
nginx -g 'daemon off;'
