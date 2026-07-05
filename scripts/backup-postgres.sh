#!/bin/sh
# Backup PostgreSQL — HPU SaaS
# File: ~/hpu-dev/_shared/scripts/backup-postgres.sh
# Usage: chạy trong container backup (xem docker-compose.saas.yml)

set -e

BACKUP_DIR=${BACKUP_DIR:-/backups}
DB_HOST=${DB_HOST:-db}
DB_USER=${DB_USER:-talentchart}
DB_NAME=${DB_NAME:-talentchart}
DATE=$(date +%Y%m%d-%H%M%S)
RETENTION_DAYS=${RETENTION_DAYS:-14}

mkdir -p "$BACKUP_DIR"

# pg_dump custom format (compressed, allows partial restore)
pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -F c \
    -f "$BACKUP_DIR/$DB_NAME-$DATE.dump"

gzip "$BACKUP_DIR/$DB_NAME-$DATE.dump"

# Remove old backups
find "$BACKUP_DIR" -name "$DB_NAME-*.dump.gz" -mtime +$RETENTION_DAYS -delete

# Optional: rsync to remote
if [ -n "$REMOTE_BACKUP" ]; then
    rsync -az "$BACKUP_DIR/" "$REMOTE_BACKUP/"
fi

echo "[$(date)] Backup completed: $DB_NAME-$DATE.dump.gz"

# Verify backup integrity
GZIP_FILE="$BACKUP_DIR/$DB_NAME-$DATE.dump.gz"
if ! gzip -t "$GZIP_FILE"; then
    echo "[ERROR] Backup file corrupted: $GZIP_FILE"
    exit 1
fi
