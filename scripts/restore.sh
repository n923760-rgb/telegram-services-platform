#!/bin/sh
set -eu
# Restore only into an explicitly selected empty/disposable database.
test "$#" -eq 1 || { echo 'Usage: restore.sh backup.dump'; exit 2; }
test "${CONFIRM_RESTORE:-}" = YES || { echo 'Set CONFIRM_RESTORE=YES after stopping bot/worker/api and verifying the database target.'; exit 2; }
docker compose exec -T postgres sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --single-transaction --exit-on-error' < "$1"
