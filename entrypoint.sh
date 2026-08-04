#!/bin/sh
set -e

PORT="${PORT:-8000}"

if [ -n "$POSTGRES_HOST" ] && [ -n "$POSTGRES_DATABASE" ] && [ -n "$POSTGRES_USER" ] && [ -n "$POSTGRES_PASSWORD" ]; then
  echo "{\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"level\":\"info\",\"message\":\"Attempting database migrations\"}"
  if python -c "from app import create_app; from config.database import db; from users import models; app = create_app(); app.app_context().push(); db.create_all(); print('ok')"; then
    echo "{\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"level\":\"info\",\"message\":\"Database migrations complete\"}"
  else
    echo "{\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"level\":\"warn\",\"message\":\"Database migrations failed. Continuing with available fallback\"}"
  fi
else
  echo "{\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"level\":\"warn\",\"message\":\"POSTGRES_* env vars not set. Skipping migrations and using in-memory fallback\"}"
fi

if [ "$#" -eq 0 ] || [ "$1" = "gunicorn" ]; then
  exec gunicorn wsgi:application \
    --bind "0.0.0.0:${PORT}" \
    --workers "${WEB_CONCURRENCY:-1}" \
    --graceful-timeout "${GUNICORN_GRACEFUL_TIMEOUT:-30}" \
    --timeout "${GUNICORN_TIMEOUT:-60}" \
    --access-logfile - \
    --error-logfile -
fi

exec "$@"
