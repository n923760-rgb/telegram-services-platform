# Arabic Telegram Services Bot

[دليل التشغيل بالعربية](README_AR.md)

Python 3.12 bot for Saudi customers, with Arabic menus, immutable SAR credit accounting,
durable PostgreSQL orders, ARQ workers, operational controls, and independently discovered services.
All four requested phases are implemented. No payment gateway or dashboard is included.

**Payment constraint:** SAR credit is administrator-issued test credit here. Telegram requires Stars
for digital-service sales inside Telegram ([official policy](https://core.telegram.org/bots/payments-stars)).
This project is not cleared for a paid SAR checkout launch. Resolve that business requirement before
selling services; the implementation does not silently add a different payment system.

## Services and architecture

| Service | Default | Test price | Behavior |
| --- | --- | --- | --- |
| `echo` | Enabled | SAR 1 | Proves collection → confirmation → reservation → worker → delivery → capture. |
| `image_to_text` | Disabled | SAR 3 | Up to five images, Arabic/English OCR, optional Arabic/English translation and style; long output includes TXT and DOCX. |
| `text_to_office` | Disabled | SAR 5 | Text to editable Word or Excel; asks for structure approval only when the validated plan is ambiguous. |
| `text_to_pptx` | Disabled | SAR 5 | Text to an editable PowerPoint deck; asks for structure approval only when the validated plan is ambiguous. |
| `text_to_pdf` | Disabled | SAR 5 | Text to a professional, printable PDF document; asks for structure approval only when the validated plan is ambiguous. |

Word, Excel, PowerPoint and PDF builders are shared infrastructure. Blank, unreadable or empty OCR
is rejected and credit released.
OCR accuracy still depends on the selected model and the image; model confidence is not a guarantee.

`app/bot` handles Telegram; `app/api` handles HTTP; `app/core` holds configuration, DB and i18n.
`app/wallet` records signed integer-halalas entries; `app/orders` holds purchase state.
`app/services/<slug>` contains plugins; `app/workers` executes jobs and cron tasks.
`app/providers` owns all external integrations; `app/builders` renders validated data.
`app/files` validates and deletes temporary files; `app/ops` controls costs and reliability.

A service receives a job-scoped runtime, never a Telegram object. AI returns validated Pydantic JSON;
one bounded repair is allowed, then failure releases the customer reservation. Builders create files
in code. Orders, jobs and numbered execution attempts are separate. Service metadata is synced on
startup without overwriting database prices or enabled flags. Schema and plugin-version snapshots protect in-flight work. Incompatible pending versions release credit; cached delivery reuses the prepared output.

## Setup with Docker Compose

Install Docker Engine with Compose v2 on a Linux host. Copy the project and:

```bash
python scripts/configure.py
# Enter the token privately and administrator IDs; existing .env is never overwritten.
docker compose up -d --build
docker compose ps
curl --fail http://127.0.0.1:8000/health
```

Keep `.env` private (`chmod 600 .env`) and never commit it. Admins must start the bot so it can send
alerts. The migration container must succeed before API, bot and worker start. Polling is the default;
no public HTTP port is needed for it. PostgreSQL and Redis are internal only; the API binds host
loopback. Persistent volumes store the database, Redis AOF and temporary files.

For a VPS, configure the host firewall, SSH access, backups and an external uptime check. Keep one
polling bot replica. After backing up, deploy changes with `docker compose up -d --build`; inspect
migration exit status and health. Do not remove production volumes (`down -v` destroys them).
Healthchecks mark failure but do not themselves restart an unhealthy, still-running container.
The independent monitor reports worker/database outages; host or network outages require external monitoring.

## Run locally in polling mode

Install Python 3.12, uv, PostgreSQL 16 and Redis 7 (or run the disposable dependencies below).

```bash
uv sync --locked --group dev
cp .env.example .env
```

Use `localhost` database/Redis addresses and a writable `STORAGE_ROOT=./data/files` in local `.env`.
Set the Telegram token and administrator IDs. Then:

```bash
uv run alembic upgrade head
uv run python -m app.bot.main
# In separate terminals:
uv run uvicorn app.api.main:app --host 127.0.0.1 --port 8000
uv run arq app.workers.main.WorkerSettings
uv run python -m app.ops.monitor
```

In Telegram: `/start`, administrator `/addbalance USER_ID 20`, select a service, provide input,
confirm the displayed price, then receive the result. Never insert a mutable balance column.
Amounts accept at most two decimal places; ledger balance is the sum of entries.

## AI configuration

The concrete adapter implements an OpenAI-compatible chat-completions endpoint with structured JSON
and image inputs. Set `AI_ENABLED=true`, `AI_API_KEY`, `AI_BASE_URL`, `AI_MODEL`, and positive current
`AI_INPUT_USD_PER_MILLION` / `AI_OUTPUT_USD_PER_MILLION` rates. Verify the model supports the request
format. Restart processes, then `/enable image_to_text`, `/enable text_to_office`, `/enable text_to_pptx` and `/enable text_to_pdf`.
Changing a provider requires a provider implementation/factory change, not service or bot changes.
Transcription is an interface placeholder; no audio service is implemented.

Costs use provider-returned tokens multiplied by configured rates and `USD_TO_SAR`; this is not a
provider invoice. In-flight conservative holds protect daily budgets. Size/price bounds must cover
your chosen provider, including image token accounting. Unknown costs remain held for operator billing
reconciliation. See [operations](docs/OPERATIONS.md). No credentials are required for the mocked AI tests.

## Environment and settings

| Variables | Purpose / default |
| --- | --- |
| `BOT_TOKEN`, `ADMIN_IDS` | Telegram secret and JSON array of administrator IDs, e.g. `[123456789]`. |
| `DATABASE_URL`, `REDIS_URL` | Async PostgreSQL DSN and Redis DSN; container hostnames in Compose. |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | PostgreSQL container initialization; keep DSN consistent. |
| `APP_ENV`, `STORAGE_ROOT` | Environment; temporary file path (`/data/files` in Compose). |
| `TELEGRAM_MODE`, `TELEGRAM_WEBHOOK_SECRET` | `polling` by default; secret required for `webhook`. |
| `AI_PROVIDER`, `AI_BASE_URL`, `AI_MODEL`, `AI_API_KEY`, `AI_ENABLED` | Provider selection/configuration; AI disabled by default. |
| `AI_INPUT_USD_PER_MILLION`, `AI_OUTPUT_USD_PER_MILLION`, `USD_TO_SAR` | Operator-maintained current rates; rate defaults are zero to prevent accidental AI activation. |
| `AI_IMAGE_TOKEN_BOUND`, `AI_MAX_OUTPUT_TOKENS` | Conservative image bound 20000; output maximum 8192 tokens (configurable up to 32768). |
| `MAX_DAILY_COST_SAR`, `MAX_COST_PER_USER_PER_DAY`, `MAX_JOB_COST_SAR` | Exposure limits: 50, 10, 2 SAR. |
| `MAX_CONCURRENT_JOBS_PER_USER`, `MAX_ATTEMPTS` | Two unsettled orders and three failures by default. |
| `PROVIDER_LOW_BALANCE_SAR`, `FAILURE_ALERT_COUNT` | Low-balance threshold 10; consecutive-failure alert at 3. |
| `CIRCUIT_WINDOW`, `CIRCUIT_MIN_SAMPLES`, `CIRCUIT_FAILURE_THRESHOLD` | Last 10 terminal jobs, minimum 5, failure ratio at least 0.6. |
| `REPORT_HOUR`, `REPORT_MINUTE` | Daily report at 23:00 Asia/Riyadh. |
| `FILE_TTL_HOURS`, `MAX_FILE_BYTES` | 24-hour TTL and 10 MiB input/result limit. |
| `STORAGE_QUOTA_BYTES`, `STORAGE_QUOTA_FILES` | Per-owner upload quota: 52,428,800 bytes and 100 files by default. |

Operational settings rows store `{"value": ...}` and override environment defaults where used by the
settings helper. `PROVIDER_BALANCE_SAR` can record an operator-observed provider balance when no balance
API is available; `PROVIDER_PAUSED=true` blocks AI admission/calls. Report schedule changes require a
worker restart. Never put credentials in database settings. Configuration defaults and limits are in
`.env.example` and `app/core/settings.py`.

## Administrator commands

| Command | Action |
| --- | --- |
| `/addbalance USER_ID AMOUNT` | Add test credit through an immutable ledger entry; retrying the same Telegram update is idempotent. |
| `/balance USER_ID`, `/stats` | Show balance and totals. |
| `/enable SLUG`, `/disable SLUG` | Change service gate; disabling releases unsettled reservations. |
| `/setprice SLUG AMOUNT` | Change price for future orders; existing order prices remain frozen. |
| `/refund ORDER_UUID` | Idempotently refund a completed order once. |
| `/ban USER_ID` | Block new submissions. |
| `/report` | Show daily orders, revenue, provider cost, margin, failed jobs, refunds, top services and users. |
| `/reply TICKET_UUID MESSAGE` | Reply to a customer support ticket. |

The support button forwards the customer message and latest order context to administrators.
Redis limits per-user traffic and serializes conversation updates. Cost-cap errors use polite Arabic
messages. Alerts deduplicate by type for 15 minutes; no customer content appears in operational alerts.

## Webhook readiness

Use an HTTPS reverse proxy in front of the loopback API. Set `TELEGRAM_MODE=webhook` and a strong
`TELEGRAM_WEBHOOK_SECRET`, run API/worker/monitor (omit the polling bot), and register the public
`/webhooks/telegram` URL with Telegram `setWebhook`, passing the same `secret_token`. Registration is
an operator action; no token-bearing URL is logged by this project. Remove the webhook before returning
to polling. `/health/live` is liveness, `/health` checks DB and Redis. `/webhooks/payment` returns 501.

## Add a service without changing bot/core

1. Create `app/services/<slug>/` with `__init__.py`, `schema.py`, `prompt.py`, `service.py`, `test_service.py`.
2. Subclass `BaseService`; declare slug, version, Arabic/English names, Arabic description, Decimal `price_sar`,
   `requires_ai` if appropriate, default gate, and `InputSchema` fields.
3. Expose `SERVICE = YourService`. Folder discovery registers it automatically.
4. Use text/image/file/audio/form fields, choices, conditional `when`, and multiple file inputs as needed.
   Use validated input/output models, `runtime.ai.extract(...)` and typed builders.
5. Add prompt/choice/error keys to both i18n JSON files. Keep all customer text translated.
6. Test success plus failure releasing the reservation. Increment version for input-contract changes; syncing rejects an unchanged-version contract mutation. Restart worker/bot to discover and sync.
7. Enable and price through admin commands. If another bot/core change is needed, stop and propose
   a generic refactor; never add service-specific handlers or branches.

Copy the included service pattern. Plugins cannot import Telegram or directly call external APIs.
Do not treat executable third-party plugins as untrusted sandboxed code.

## Verification

Tests truncate tables. **Always use a disposable database whose name ends in `_test`, never production.**
Start dedicated dependencies (separate Compose file and project):

```bash
docker compose -p services-test -f compose.test.yml up -d --wait
export APP_ENV=test
export DATABASE_URL=postgresql+asyncpg://services:test-only-password@localhost:55432/services_test
export REDIS_URL=redis://localhost:56379/0
export STORAGE_ROOT=./data/test-files
uv run alembic upgrade head
uv run pytest
uv run alembic check
uv run ruff check .
uv run ruff format --check .
docker compose -p services-test -f compose.test.yml down -v
```

The suite exercises real PostgreSQL transactions and Redis, with fake Telegram delivery and mocked
AI responses: wallet concurrency/immutability, reservations/refunds, costs, alert deduplication,
circuit breakers, retry recovery, generic bot input, ambiguity approval, OCR/translation and builders.
Office files are reopened and inspected; Arabic PDF layout was rendered and visually inspected.
Live Telegram, live AI quality/billing and Docker/VPS deployment need credentials and deployment validation.

Read [AGENTS.md](AGENTS.md) for engineering rules and [operations](docs/OPERATIONS.md) for daily pg_dump,
retention, restore and off-server copying. Files are deleted after terminal delivery/failure, with a durable cleanup sweep for early cancellations and TTL
cleanup for interrupted work; expired database content is purged while financial audit rows remain.
Telegram delivery is at least once across process crashes; financial settlement remains idempotent.


Governance is in AGENTS.md with architecture tests and a pinned GitHub Actions workflow.
See docs/GOVERNANCE.md for the reviewed, pinned engineering-governance reference and project
adaptations. PROJECT-SOURCES.md links the single ENGINEERING/MASTER_ROADMAP.md and its reports/evidence.
The project repository is https://github.com/n923760-rgb/telegram-services-platform. Check its Actions page for attributable hosted results; publishing source does not deploy the bot.
PDF intake rejects encrypted/malformed/over-200-page files; audio intake checks PCM WAV, common
Opus/Vorbis Ogg headers or MP3 frame headers. Input validation is not a malware scanner.
