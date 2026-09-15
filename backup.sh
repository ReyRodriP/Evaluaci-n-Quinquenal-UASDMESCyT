#!/bin/bash
set -e

if [ -z "$BACKUP_PASSPHRASE" ]; then
    echo "ERROR: BACKUP_PASSPHRASE no definida (necesaria para cifrado AES-256)." >&2
    exit 1
fi

BACKUP_DIR="/backups/evaluacion-quinquenal"
TMP_DIR="${TMPDIR:-/tmp}/evaluacion-quinquenal-backup"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="${DB_NAME:-evaluacion_quinquenal}"
DB_USER="${DB_USER:-evaluacion_user}"

mkdir -p "$BACKUP_DIR" "$TMP_DIR"

echo "=== Backup iniciado: $DATE ==="

# Base de datos: pg_dump + gzip + cifrado AES-256-CBC
pg_dump -U "$DB_USER" -d "$DB_NAME" 2>/dev/null | gzip > "$TMP_DIR/db_$DATE.sql.gz"
openssl enc -aes-256-cbc -pbkdf2 -salt -pass env:BACKUP_PASSPHRASE -in "$TMP_DIR/db_$DATE.sql.gz" -out "$BACKUP_DIR/db_$DATE.sql.gz.enc"
rm -f "$TMP_DIR/db_$DATE.sql.gz"

# Media: tar + gzip + cifrado AES-256-CBC
tar -czf "$TMP_DIR/media_$DATE.tar.gz" media/
openssl enc -aes-256-cbc -pbkdf2 -salt -pass env:BACKUP_PASSPHRASE -in "$TMP_DIR/media_$DATE.tar.gz" -out "$BACKUP_DIR/media_$DATE.tar.gz.enc"
rm -f "$TMP_DIR/media_$DATE.tar.gz"

# Rotacion: eliminar backups cifrados de mas de 30 dias
find "$BACKUP_DIR" -name "*.enc" -mtime +30 -delete

echo "=== Backup completado y cifrado en $BACKUP_DIR ==="