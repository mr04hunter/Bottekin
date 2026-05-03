#!/bin/bash
set -euo pipefail

DB_USER=$(cat /run/secrets/db_user)
DB_HOST=$(cat /run/secrets/db_host)
DB_NAME=$(cat /run/secrets/db_name)
DB_PASS=$(cat /run/secrets/db_password)
DB_PORT=${PGPORT:-5432}

PGPASS="/root/.pgpass"

echo "${DB_HOST}:*:${DB_NAME}:${DB_USER}:${DB_PASS}" > "$PGPASS"
chmod 600 "$PGPASS"
unset DB_PASS

export PGUSER="$DB_USER"
export PGHOST="$DB_HOST"
export PGDATABASE="$DB_NAME"

BACKUP_TYPE=${1:-daily}
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/${BACKUP_TYPE}/backup_${TIMESTAMP}.sql.gz"

echo "========================================="
echo "Starting ${BACKUP_TYPE} backup at $(date)"
echo "========================================="

echo "Checking PostgreSQL connection..."
until pg_isready -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" -q; do
    echo "Waiting for PostgreSQL to be ready..."
    sleep 2
done
echo "✅ PostgreSQL is ready"

mkdir -p "${BACKUP_DIR}/${BACKUP_TYPE}"

echo "Creating backup: $BACKUP_FILE"

LOG_FILE="/tmp/pg_dump_${TIMESTAMP}.log"

if pg_dump \
    --format=plain \
    --no-owner \
    --no-acl \
    --verbose \
    2>"$LOG_FILE" | gzip > "$BACKUP_FILE"; then

    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✅ Backup completed successfully"
    echo "   File: $BACKUP_FILE"
    echo "   Size: $BACKUP_SIZE"

    echo ""
    echo "Backup details:"
    cat "$LOG_FILE"

    echo ""
    echo "Creating checksum..."
    sha256sum "$BACKUP_FILE" > "${BACKUP_FILE}.sha256"

    cat > "${BACKUP_FILE}.meta" <<METADATA
{
  "timestamp": "$(date -Iseconds)",
  "type": "${BACKUP_TYPE}",
  "database": "${PGDATABASE}",
  "host": "${PGHOST}",
  "size": "${BACKUP_SIZE}",
  "file": "$(basename "$BACKUP_FILE")",
  "checksum_file": "$(basename "${BACKUP_FILE}.sha256")"
}
METADATA

    echo "Testing backup integrity..."
    if gunzip -t "$BACKUP_FILE" 2>/dev/null; then
        echo "✅ Backup integrity verified"
    else
        echo "❌ WARNING: Backup integrity check failed!"
        exit 1
    fi


    rm -f "$LOG_FILE"

    echo "========================================="
    echo "Backup completed at $(date)"
    echo "========================================="
else
    echo "❌ Backup failed!"
    if [ -f "$LOG_FILE" ]; then
        echo "Error log:"
        cat "$LOG_FILE"
        rm -f "$LOG_FILE"
    fi
    exit 1
fi