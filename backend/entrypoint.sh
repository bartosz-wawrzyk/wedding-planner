#!/bin/bash
set -e

if [ "$RENDER" != "true" ]; then
  echo "=== [LOCAL] Local environment detected. Waiting for the db container... ==="
  while ! nc -z db 5432; do
    sleep 0.1
  done
  echo "=== [LOCAL] PostgreSQL is running ==="
else
  echo "=== [PRODUCTION] Render environment detected. Skipping nc check (Database managed) ==="
fi

echo "=== Running database migrations (Alembic) ==="
alembic upgrade head

echo "=== Starting production application ==="

exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"