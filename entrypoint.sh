#!/bin/sh
set -e

if [ -n "$POSTGRES_HOST" ] && [ -n "$POSTGRES_DATABASE" ] && [ -n "$POSTGRES_USER" ] && [ -n "$POSTGRES_PASSWORD" ]; then
  echo "[INFO] Attempting database migrations..."
  if python -c "from app import create_app; from config.database import db; from users import models; app = create_app(); app.app_context().push(); db.create_all(); print('ok')"; then
    echo "[INFO] Database migrations complete."
  else
    echo "[WARNING] Database migrations failed. Continuing with available fallback."
  fi
else
  echo "[WARNING] POSTGRES_* env vars not set. Skipping migrations and using in-memory fallback."
fi

exec "$@"
