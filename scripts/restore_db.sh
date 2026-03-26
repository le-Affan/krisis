#!/bin/bash
set -e

if [ -z "$1" ]; then
  echo "Usage: restore_db.sh <path-to-backup.sql.gz>"
  exit 1
fi

echo "[restore_db] Restoring from $1 ..."
gunzip -c "$1" | psql -h db -U abtest abtest
echo "[restore_db] Restore complete."
