#!/bin/bash
set -euo pipefail


DB_USER=$(cat /run/secrets/db_user)
DB_HOST=$(cat /run/secrets/db_host)
DB_NAME=$(cat /run/secrets/db_name)
DB_PASS=$(cat /run/secrets/db_password)

PGPASS="/root/.pgpass"
echo "${DB_HOST}:*:${DB_NAME}:${DB_USER}:${DB_PASS}" > "$PGPASS"
chmod 600 "$PGPASS"
unset DB_PASS

export PGUSER="$DB_USER"
export PGHOST="$DB_HOST"
export PGDATABASE="$DB_NAME"

BACKUP_DIR="/backups"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-7}
KEEP_WEEKLY=${BACKUP_KEEP_WEEKLY:-4}
KEEP_MONTHLY=${BACKUP_KEEP_MONTHLY:-3}

mkdir -p "$BACKUP_DIR"/{daily,weekly,monthly}
mkdir -p /etc/cron.d

echo "Starting backup service with cron..."
echo "Backup retention: ${RETENTION_DAYS} days, ${KEEP_WEEKLY} weekly, ${KEEP_MONTHLY} monthly"


cat > /etc/cron.d/postgres-backup << CRONEOF
# Cron environment — these are passed to each job
BACKUP_RETENTION_DAYS=${RETENTION_DAYS}
BACKUP_KEEP_WEEKLY=${KEEP_WEEKLY}
BACKUP_KEEP_MONTHLY=${KEEP_MONTHLY}

# Daily backup at 2 AM
0 2 * * * root /scripts/backup.sh daily 2>&1 | tee -a /backups/backup.log

# Weekly backup on Sunday at 3 AM
0 3 * * 0 root /scripts/backup.sh weekly 2>&1 | tee -a /backups/backup.log

# Monthly backup on 1st of month at 4 AM
0 4 1 * * root /scripts/backup.sh monthly 2>&1 | tee -a /backups/backup.log

# Cleanup old backups at 5 AM daily
0 5 * * * root /scripts/cleanup-backups.sh 2>&1 | tee -a /backups/backup.log
CRONEOF

chmod 0644 /etc/cron.d/postgres-backup

echo "Running initial backup..."
/scripts/backup.sh daily

echo "Starting cron daemon..."
exec cron -f