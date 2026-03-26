#!/bin/bash
set -e

echo "[init_db] Waiting for PostgreSQL to be ready..."
until pg_isready -h db -U abtest; do
  echo "[init_db] Postgres not ready yet, retrying in 1s..."
  sleep 1
done

echo "[init_db] Running Alembic migrations..."
alembic upgrade head

echo "[init_db] DB initialization complete."
