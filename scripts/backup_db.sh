#!/bin/bash
set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT="/backups/backup_${TIMESTAMP}.sql.gz"

echo "[backup_db] Starting backup → ${OUTPUT}"
pg_dump -h db -U abtest abtest | gzip > "${OUTPUT}"
echo "[backup_db] Done: ${OUTPUT}"
