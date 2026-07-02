#!/bin/bash
set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT="/backups/backup_${TIMESTAMP}.sql.gz"

echo "[backup_db] Starting backup → ${OUTPUT}"
# Data-only: schema is exclusively owned by Alembic migrations (see src/database.py),
# never by the dump/restore cycle. --disable-triggers suspends FK checks during
# restore so table load order doesn't matter for plain-format dumps.
# alembic_version is excluded: it's Alembic's own migration-tracking row, already
# populated by the target's own migration run, not application data to restore.
PGPASSWORD="${DB_PASSWORD:-abtest_password}" pg_dump -h db -U abtest --data-only --disable-triggers --exclude-table=alembic_version abtest | gzip > "${OUTPUT}"
echo "[backup_db] Done: ${OUTPUT}"
