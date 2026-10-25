#!/usr/bin/env bash
# Fresh synthetic DB, normal budget gateway, no production setting/ledger mutations.
set -Eeuo pipefail
umask 077
acceptance_native_only=false
if [ "${1:-}" = --native-only ]; then
  acceptance_native_only=true
  shift
fi
cd "$(dirname "$0")/.."
test "$(git branch --show-current)" = main
test -z "$(git status --porcelain)"
acceptance_mounts=(
  -v "$PWD/app/ops/service_acceptance.py:/opt/app/app/ops/service_acceptance.py:ro"
  -v "$PWD/app/ops/acceptance_cases.py:/opt/app/app/ops/acceptance_cases.py:ro"
)
# Git checkouts made under umask 077 may be unreadable by the worker UID.
# Probe the exact read-only mounts before creating an acceptance DB or backup.
if ! docker compose run --rm --no-deps -T "${acceptance_mounts[@]}" worker python -c '
from pathlib import Path
try:
    for name in ("service_acceptance.py", "acceptance_cases.py"):
        with (Path("/opt/app/app/ops") / name).open("rb") as source:
            source.read(1)
except OSError:
    raise SystemExit(1)
' </dev/null; then
  echo 'STOP: worker cannot read acceptance mounts, or its preflight could not start.' >&2
  echo 'Check Docker output and run: chmod 0644 app/ops/service_acceptance.py app/ops/acceptance_cases.py' >&2
  exit 1
fi
acceptance_cases=$(python3 - "$@" <<'PY'
import json
import sys
print(json.dumps(sys.argv[1:]))
PY
)
acceptance_sql() {
  docker compose exec -T postgres sh -c \
    'PGPASSWORD="$POSTGRES_PASSWORD" exec psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -v ON_ERROR_STOP=1 -c "$1"' sh "$1" </dev/null
}
if [ "$acceptance_native_only" = true ]; then
  docker compose run --rm --no-deps -T \
    -e ACCEPTANCE_CASES="$acceptance_cases" "${acceptance_mounts[@]}" worker python - <<'PY'
import json
import os
from app.ops.service_acceptance import ASSETS, cases, native_cases
native_cases(cases(ASSETS), json.loads(os.environ['ACCEPTANCE_CASES']))
print('NATIVE_SELECTION=validated_no_ai')
PY
fi
acceptance_pause_before=$(acceptance_sql "SELECT value->>'value' FROM settings WHERE key='PROVIDER_PAUSED';")
if [ "$acceptance_native_only" != true ] && [ "$acceptance_pause_before" != true ]; then
  echo 'STOP: live-provider acceptance requires PROVIDER_PAUSED=true. For explicitly selected non-AI cases use --native-only.' >&2
  exit 1
fi
acceptance_id=$(python3 -c 'import secrets; print(secrets.token_hex(6))')
acceptance_db="svc_${acceptance_id}_acceptance_test"
acceptance_backup=$(mktemp -d /home/aidev/service-acceptance-XXXXXXXX)
printf '%s\n' "$acceptance_db" > "$acceptance_backup/database-name.txt"
git rev-parse HEAD > "$acceptance_backup/source-commit.txt"
echo "BACKUP: $acceptance_backup"
echo "TEST_DATABASE: $acceptance_db"
trap 'acceptance_exit=$?; echo "ACCEPTANCE_EXIT=$acceptance_exit BACKUP=$acceptance_backup DATABASE=$acceptance_db"' EXIT

docker compose exec -T postgres sh -c \
  'PGPASSWORD="$POSTGRES_PASSWORD" exec createdb -U "$POSTGRES_USER" --maintenance-db="$POSTGRES_DB" "$1"' sh "$acceptance_db" </dev/null

acceptance_rc=0
docker compose run --rm --no-deps -T \
  -e ACCEPTANCE_DATABASE="$acceptance_db" -e ACCEPTANCE_RUN="$acceptance_id" \
  -e ACCEPTANCE_CASES="$acceptance_cases" \
  -e ACCEPTANCE_NATIVE_ONLY="$acceptance_native_only" \
  "${acceptance_mounts[@]}" \
  worker python - <<'PY' || acceptance_rc=$?
import os
import json
import re
import sys
from pathlib import Path
from sqlalchemy.engine import make_url
from app.core.settings import config

original = config()
name = os.environ['ACCEPTANCE_DATABASE']
run = os.environ['ACCEPTANCE_RUN']
assert re.fullmatch(r'svc_[a-f0-9]{12}_acceptance_test', name)
assert name == f'svc_{run}_acceptance_test'
assert original.storage_root.resolve() == Path('/data/files')
# Secrets stay in-process; never print the inherited URL/key or write another .env.
os.environ.update({
    'APP_ENV': 'test',
    'DATABASE_URL': make_url(original.database_url.get_secret_value()).set(database=name).render_as_string(hide_password=False),
    'STORAGE_ROOT': f'/data/files/acceptance-{run}',
    'ADMIN_IDS': '[424242424242]',
    'STARS_ENABLED': 'false',
    'MAX_DAILY_COST_SAR': '5',
    'MAX_COST_PER_USER_PER_DAY': '5',
    'MAX_JOB_COST_SAR': '.75',
})
config.cache_clear()
if os.environ['ACCEPTANCE_NATIVE_ONLY'] == 'true':
    os.environ['AI_ENABLED'] = 'false'
    config.cache_clear()
from app.ops.service_acceptance import ASSETS, cases, isolated, main, selected_cases, native_cases
isolated()  # Refuse wrong targets before migrations or seeding.
selection = json.loads(os.environ['ACCEPTANCE_CASES'])
native_only = os.environ['ACCEPTANCE_NATIVE_ONLY'] == 'true'
(native_cases if native_only else selected_cases)(cases(ASSETS), selection or None)
from alembic import command
from alembic.config import Config
command.upgrade(Config('alembic.ini'), 'head')
sys.argv = ['service_acceptance', '--execute']
if native_only:
    sys.argv.append('--native-only')
for name in selection:
    sys.argv.extend(['--case', name])
raise SystemExit(main())
PY

# Preserve the test accounting database even when some services fail. Never auto-drop it.
docker compose exec -T postgres sh -c \
  'PGPASSWORD="$POSTGRES_PASSWORD" exec pg_dump -U "$POSTGRES_USER" -d "$1" -Fc' sh "$acceptance_db" \
  </dev/null > "$acceptance_backup/database.dump"
test -s "$acceptance_backup/database.dump"
docker compose cp "worker:/data/files/acceptance-$acceptance_id/results" "$acceptance_backup/results"
python3 - "$acceptance_backup" <<'PY'
import sys
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
root = Path(sys.argv[1])
with ZipFile(root / 'service-acceptance-results.zip', 'w', ZIP_DEFLATED) as archive:
    # Checkout provenance, not proof of which source built the worker image.
    archive.write(root / 'source-commit.txt', 'source-commit.txt')
    for path in sorted((root / 'results').rglob('*')):
        if path.is_file():
            archive.write(path, path.relative_to(root))
print('RESULT_ZIP:', root / 'service-acceptance-results.zip')
PY
test "$(acceptance_sql "SELECT value->>'value' FROM settings WHERE key='PROVIDER_PAUSED';")" = "$acceptance_pause_before"
echo "PRODUCTION_PROVIDER_PAUSED=${acceptance_pause_before:-unset} (unchanged)"
exit "$acceptance_rc"
