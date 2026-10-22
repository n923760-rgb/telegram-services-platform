# Dedicated Telegram test-server routing — 2026-10-10

## Source and finding

FACT: Inspected canonical main a0ab15c95e0d86a140e1903fbf07fbb9021cf92c,
AGENTS.md, roadmap, runtime entry points and Stars qualification guide. Main workflow
37992934577/job 114031500940 actual logs pass 696 tests, lint/format, migration/no drift,
Compose and six real non-root/network-disabled worker qualifications.

FACT: API, polling bot, worker and monitor each constructed aiogram Bot without a
test API session. The guide requested Telegram's dedicated test environment but no
setting supported it. A separate ordinary-server bot does not implement test Stars.

References reviewed: Telegram's [test-server instructions](https://core.telegram.org/bots/features#dedicated-test-environment),
[Stars testing](https://core.telegram.org/bots/payments-stars) and
[aiogram 3.31 endpoint definitions](https://docs.aiogram.dev/en/latest/_modules/aiogram/client/telegram.html).

## Bounded implementation

Explicit Literal production/test configuration, independent of APP_ENV; production
remains the default. A provider-owned factory uses locked aiogram's PRODUCTION/TEST
definitions for both API and file endpoints. All four runtime processes share it;
each retains ownership of its own session and existing shutdown behavior.

No new dependencies, migrations, financial policy, service branches, prices, secret
changes, automatic webhook registration, endpoint fallback or payment enablement.
Document isolated credentials/storage/financial records and simultaneous process restart.

## Validation

- PASS: Local 15 database-independent routing/configuration/architecture/setup cases
  through `pytest --noconftest`: native aiogram invoice, refund/history, webhook and
  download routing for both APIs; timeout invokes only the selected test URL;
  invalid selection rejects and APP_ENV alone does not change API environment.
- Full suite retains the existing PostgreSQL autouse fixture and all financial checks;
  no workflow/test gate weakened. Added real-DB registry startup and webhook lifespan
  tests to confirm the selected runtime bot and worker delivery/refund identity.
- Hosted exact-head full suite, migrations/drift/Compose and native worker results
  must be inspected before authorized merge; retain final source/results on the PR.
- NOT RUN: Telegram test-server account, real purchase/refund, provider billing/output
  acceptance, deployed restart/health, support and backup/restore. No server credentials
  or identified staging installation are available here.

## Immediate next qualification

Use docs/STARS_ACCEPTANCE.md with a fresh test-server installation. Do not change an
existing financial database's Telegram environment or equate transport tests with a
real transaction. Keep future service expansion separate from these V1 launch gates.
