#!/bin/bash
set -euo pipefail

# Usage: ./restore.sh <backup_file>

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_file>"
    echo ""
    echo "Available backups:"
    echo "=================="
    echo ""
    echo "Daily backups:"
    find /backups/daily -name "backup_*.sql.gz" -exec ls -lh {} \; 2>/dev/null | tail -5 || echo "No daily backups found"
    echo ""
    echo "Weekly backups:"
    find /backups/weekly -name "backup_*.sql.gz" -exec ls -lh {} \; 2>/dev/null || echo "No weekly backups found"
    echo ""
    echo "Monthly backups:"
    find /backups/monthly -name "backup_*.sql.gz" -exec ls -lh {} \; 2>/dev/null || echo "No monthly backups found"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

DB_USER=$(cat /run/secrets/db_user)
DB_HOST=$(cat /run/secrets/db_host)
DB_NAME=$(cat /run/secrets/db_name)
DB_PASS=$(cat /run/secrets/db_password)

PGPASS="/root/.pgpass"
echo "${DB_HOST}:5432:${DB_NAME}:${DB_USER}:${DB_PASS}" > "$PGPASS"
chmod 600 "$PGPASS"
unset DB_PASS 
trap 'rm -f "$PGPASS"' EXIT

export PGUSER="$DB_USER"
export PGHOST="$DB_HOST"
export PGDATABASE="$DB_NAME"

echo "========================================="
echo "Database Restore"
echo "========================================="
echo "Backup file: $BACKUP_FILE"
echo "Target database: $PGDATABASE@$PGHOST"
echo ""

CHECKSUM_FILE="${BACKUP_FILE}.sha256"
if [ -f "$CHECKSUM_FILE" ]; then
    echo "Verifying backup integrity..."
    if sha256sum -c "$CHECKSUM_FILE"; then
        echo "✅ Checksum verified"
    else
        echo "❌ Checksum verification failed!"
        read -p "Continue anyway? (yes/no): " CONTINUE
        if [ "$CONTINUE" != "yes" ]; then
            exit 1
        fi
    fi
fi


echo "Testing backup file integrity..."
if ! gunzip -t "$BACKUP_FILE"; then
    echo "❌ Backup file is corrupted!"
    exit 1
fi
echo "✅ Backup file integrity verified"


echo ""
echo "⚠️  WARNING: This will DROP and RECREATE the database!"
echo "⚠️  All current data will be lost!"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

echo ""
echo "Starting restore process..."


echo "Checking PostgreSQL connection..."
until pg_isready -h "$PGHOST" -U "$PGUSER" -q; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 2
done


SAFETY_BACKUP="/backups/pre-restore-backup-$(date +%Y%m%d_%H%M%S).sql.gz"
echo "Creating safety backup of current database..."
pg_dump -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" --format=plain --no-owner --no-acl | gzip > "$SAFETY_BACKUP"
echo "✅ Safety backup created: $SAFETY_BACKUP"

echo "Terminating existing database connections..."
psql -h "$PGHOST" -U "$PGUSER" -d postgres -c "
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '${PGDATABASE}'
  AND pid <> pg_backend_pid();"


echo "Dropping database..."
psql -h "$PGHOST" -U "$PGUSER" -d postgres -c "DROP DATABASE IF EXISTS ${PGDATABASE};"

echo "Creating database..."
psql -h "$PGHOST" -U "$PGUSER" -d postgres -c "CREATE DATABASE ${PGDATABASE};"

echo "Restoring backup..."
if gunzip -c "$BACKUP_FILE" | psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" > /dev/null 2>&1; then
    echo "✅ Database restored successfully!"
    echo ""
    echo "Safety backup available at: $SAFETY_BACKUP"
    echo "You can delete it if the restore is working as expected."
else
    echo "❌ Restore failed!"
    echo "Attempting to restore safety backup..."
    psql -h "$PGHOST" -U "$PGUSER" -d postgres -c "DROP DATABASE IF EXISTS ${PGDATABASE};"
    psql -h "$PGHOST" -U "$PGUSER" -d postgres -c "CREATE DATABASE ${PGDATABASE};"
    gunzip -c "$SAFETY_BACKUP" | psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE"
    echo "⚠️  Restored to pre-restore state"
    exit 1
fi

echo "========================================="
echo "Restore completed at $(date)"
echo "========================================="
