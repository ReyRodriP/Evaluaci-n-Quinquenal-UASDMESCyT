#!/bin/bash
set -e
set -o pipefail

if [ -z "$BACKUP_PASSPHRASE" ]; then
    echo "ERROR: BACKUP_PASSPHRASE no definida (necesaria para cifrado AES-256)." >&2
    exit 1
fi

BACKUP_DIR="/backups/evaluacion-quinquenal"
TMP_DIR="${TMPDIR:-/tmp}/evaluacion-quinquenal-backup"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="${DB_NAME:-evaluacion_quinquenal}"
DB_USER="${DB_USER:-evaluacion_user}"
DB_HOST="${DB_HOST:-localhost}"
MEDIA_PATH="${MEDIA_PATH:-media}"

mkdir -p "$BACKUP_DIR" "$TMP_DIR"

echo "=== Backup iniciado: $DATE ==="

# Base de datos: pg_dump + gzip + cifrado AES-256-CBC
pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" 2>/dev/null | gzip > "$TMP_DIR/db_$DATE.sql.gz"
if [ ! -s "$TMP_DIR/db_$DATE.sql.gz" ]; then
    echo "ERROR: pg_dump produjo un backup vacío. No se genera el archivo cifrado." >&2
    rm -f "$TMP_DIR/db_$DATE.sql.gz"
    exit 1
fi
openssl enc -aes-256-cbc -pbkdf2 -salt -pass env:BACKUP_PASSPHRASE -in "$TMP_DIR/db_$DATE.sql.gz" -out "$BACKUP_DIR/db_$DATE.sql.gz.enc"
rm -f "$TMP_DIR/db_$DATE.sql.gz"

# Media: tar + gzip + cifrado AES-256-CBC
if [ -d "$MEDIA_PATH" ]; then
    tar -czf "$TMP_DIR/media_$DATE.tar.gz" -C "$(dirname "$MEDIA_PATH")" "$(basename "$MEDIA_PATH")"
    openssl enc -aes-256-cbc -pbkdf2 -salt -pass env:BACKUP_PASSPHRASE -in "$TMP_DIR/media_$DATE.tar.gz" -out "$BACKUP_DIR/media_$DATE.tar.gz.enc"
    rm -f "$TMP_DIR/media_$DATE.tar.gz"
else
    echo "AVISO: no existe $MEDIA_PATH, se omite el respaldo de media."
fi

# Rotacion: eliminar backups cifrados de mas de 30 dias
find "$BACKUP_DIR" -name "*.enc" -mtime +30 -delete

echo "=== Backup completado y cifrado en $BACKUP_DIR ==="