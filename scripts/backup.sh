#!/bin/sh
set -eu
# Run from the project directory. Cron invokes this daily.
umask 077
BACKUP_DIR=${BACKUP_DIR:-./backups}
RETENTION_DAYS=${RETENTION_DAYS:-7}
mkdir -p "$BACKUP_DIR"
backup_stamp=$(date -u +%Y%m%dT%H%M%SZ)
backup_path="$BACKUP_DIR/services-$backup_stamp.dump"
docker compose exec -T postgres sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$backup_path.tmp"
test -s "$backup_path.tmp"
mv "$backup_path.tmp" "$backup_path"
find "$BACKUP_DIR" -type f -name 'services-*.dump' -mtime +"$RETENTION_DAYS" -delete
