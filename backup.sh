#!/bin/bash
set -e

BACKUP_DIR="/backups/evaluacion-quinquenal"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="${DB_NAME:-evaluacion_quinquenal}"
DB_USER="${DB_USER:-evaluacion_user}"

mkdir -p $BACKUP_DIR

echo "=== Backup iniciado: $DATE ==="

pg_dump -U $DB_USER -d $DB_NAME | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

tar -czf "$BACKUP_DIR/media_$DATE.tar.gz" media/

find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "=== Backup completado ==="
