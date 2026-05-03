#!/bin/bash
set -euo pipefail


BACKUP_DIR="/backups"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-7}
KEEP_WEEKLY=${BACKUP_KEEP_WEEKLY:-4}
KEEP_MONTHLY=${BACKUP_KEEP_MONTHLY:-3}

echo "========================================="
echo "Starting backup cleanup at $(date)"
echo "========================================="


if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Backup directory not found: $BACKUP_DIR"
    exit 1
fi

echo "Cleaning daily backups older than ${RETENTION_DAYS} days..."
if [ -d "${BACKUP_DIR}/daily" ]; then
    find "${BACKUP_DIR}/daily" -name "backup_*.sql.gz"   -type f -mtime +"${RETENTION_DAYS}" -delete
    find "${BACKUP_DIR}/daily" -name "backup_*.sha256"   -type f -mtime +"${RETENTION_DAYS}" -delete
    find "${BACKUP_DIR}/daily" -name "backup_*.meta"     -type f -mtime +"${RETENTION_DAYS}" -delete
fi

echo "Cleaning weekly backups, keeping ${KEEP_WEEKLY} most recent..."
if [ -d "${BACKUP_DIR}/weekly" ]; then
    cd "${BACKUP_DIR}/weekly"
    
    if compgen -G "backup_*.sql.gz" > /dev/null 2>&1; then
        ls -t backup_*.sql.gz  | tail -n +"$((KEEP_WEEKLY + 1))"  | xargs -r rm --
        ls -t backup_*.sha256  | tail -n +"$((KEEP_WEEKLY + 1))"  | xargs -r rm --
        ls -t backup_*.meta    | tail -n +"$((KEEP_WEEKLY + 1))"  | xargs -r rm --
    fi
fi

echo "Cleaning monthly backups, keeping ${KEEP_MONTHLY} most recent..."
if [ -d "${BACKUP_DIR}/monthly" ]; then
    cd "${BACKUP_DIR}/monthly"
    if compgen -G "backup_*.sql.gz" > /dev/null 2>&1; then
        ls -t backup_*.sql.gz  | tail -n +"$((KEEP_MONTHLY + 1))" | xargs -r rm --
        ls -t backup_*.sha256  | tail -n +"$((KEEP_MONTHLY + 1))" | xargs -r rm --
        ls -t backup_*.meta    | tail -n +"$((KEEP_MONTHLY + 1))" | xargs -r rm --
    fi
fi

echo ""
echo "Backup Statistics:"
echo "===================="
DAILY_COUNT=$(find "${BACKUP_DIR}/daily"   -name "backup_*.sql.gz" 2>/dev/null | wc -l)
WEEKLY_COUNT=$(find "${BACKUP_DIR}/weekly"  -name "backup_*.sql.gz" 2>/dev/null | wc -l)
MONTHLY_COUNT=$(find "${BACKUP_DIR}/monthly" -name "backup_*.sql.gz" 2>/dev/null | wc -l)

echo "Daily backups:   ${DAILY_COUNT} files"
echo "Weekly backups:  ${WEEKLY_COUNT} files"
echo "Monthly backups: ${MONTHLY_COUNT} files"
echo ""
echo "Total backup size:"
du -sh "${BACKUP_DIR}" 2>/dev/null || echo "Could not calculate size"

echo "========================================="
echo "Cleanup completed at $(date)"
echo "========================================="