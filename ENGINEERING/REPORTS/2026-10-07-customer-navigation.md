# Customer navigation and order history — 2026-10-07

## Baseline and scope

- FACT: Inspected official repository n923760-rgb/telegram-services-platform and main
  at 5225b4d4cecb299d0548f06526b17445a5c7402f; clean fresh checkout, no open PRs.
- PASS: [main workflow 37576790402](https://github.com/n923760-rgb/telegram-services-platform/actions/runs/37576790402)
  completed successfully for that source; this is baseline evidence, not this task's result.
- FACT: Read AGENTS.md, the reviewed governance adaptations, canonical roadmap,
  bot/FSM, order state owners and existing regression/architecture checks before changes.
- FACT: Services/support navigation cleared the intake draft; customers had no order history.
- Authorized scope: improve the existing Telegram customer experience and fix related defects.
  No payment contract, plugin, schema, wallet policy or provider change is included.

## Resulting behavior

Persistent bilingual two-column navigation adds Services, My orders, Credit, Support,
Language and Help. A separate navigation router runs before intake/support text collection;
labels in either language are reserved controls. Existing menu callbacks remain supported.
Home and read-only sections preserve the draft; selection of a service explicitly starts
another draft, retaining the existing selection contract. Support stores its return state
and restores the draft after sending or leaving. Changing language redraws the current prompt.
Every intake prompt has a scoped cancel button, service identity and step number; upload
acknowledgements show received counts. Confirmation includes the service and reserved cost.

Order history is bounded to six rows per page with deterministic newest-first ordering.
Both list and details filter by authenticated Telegram customer ID; missing and foreign
orders use the same safe error. Details show original price, current state and Saudi time.
Waiting orders reuse the existing authorized structure-confirmation engine. No source text,
continuation JSON, storage paths or expired artifact-download capability is exposed.

## Verification

- PASS: uv sync --locked --group dev (Python 3.12.14).
- PASS: uv run ruff check .; uv run ruff format --check .; git diff --check.
- PASS: uv run pytest --collect-only -q: 203 tests collected, including 32 new cases.
- NOT RUN locally: PostgreSQL/Redis integration and Alembic. Local runtime lacks these
  servers and PostgreSQL package installation was unavailable in this restricted environment.
- PASS: [hosted workflow 37659108407](https://github.com/n923760-rgb/telegram-services-platform/actions/runs/37659108407) for source
  d3d10b04d2bdac1a5ce17a87f17cf1d4e50930e4: 203 tests passed (one dependency warning),
  lint/format, Alembic migrations, schema drift and Compose configuration.
- FACT: The final evidence update changes documentation only; the application/test tree
  remains identical to this tested source. Inspect its final-head workflow separately.
- NOT RUN: Real Telegram/provider journeys and production deployment; no server access or
  credentials were used. Follow docs/TELEGRAM_ACCEPTANCE.md after hosted checks.

Regression scope includes input/confirmation recovery, bilingual keyboard routing,
owner isolation, pagination, stale/malformed controls, support return and idempotent release.
Telegram reply keyboards are outgoing controls, not Message.reply_markup in Telegram's
response; test transports now model that API distinction and retain outgoing methods.

## Limits and next gate

Drafts remain ephemeral Redis data with the existing one-hour TTL. Service selection replaces
the previous draft; help documents this explicitly. History is metadata, not a file archive.
Hosted CI verifies internal behavior; live Telegram and actual provider quality remain
separate staging gates. This change grants no merge, deployment or paid-launch approval.
