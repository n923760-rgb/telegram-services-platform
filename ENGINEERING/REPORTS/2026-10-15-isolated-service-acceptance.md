# Isolated all-service live acceptance runner

## Authority and runtime evidence

Owner requested a full test of all services after the first real provider probe.
Baseline main c3a61f3 (#83), operator-confirmed healthy deployment with pause true,
zero unfinished orders; backup telegram-strict-pause-Yx8fNOzW.
Operator probe C6F5D1AD completed: one call, 458 input/93 output tokens within the
requested max_tokens=128, calculated SAR .000934, settled hold .004530. Cache
256 hit/202 miss recorded. This proves that one synthetic request succeeded,
not universal cap enforcement, pricing/invoices or CV/visual quality. Historic
uncertain cost remains unchanged; owner explicitly authorizes testing without
waiting for its reconciliation.

## Implementation

- Twenty-eight synthetic cases cover exactly sixteen public services, bilingual/
  Arabic/English CV, OCR images, both PDF tools, editing modes, direct/smart
  documents, native/AI table labels, minutes and translations.
- CLI defaults to a pure plan; --execute requires APP_ENV=test, a fresh uniquely
  named *_acceptance_test database, dedicated acceptance storage, one synthetic
  administrator, AI enabled, Stars off and bounded test-only cost settings.
- No production test subjects, wallet seeding, service activation, pause edits,
  HTTP/Telegram delivery or historical reconciliation. Synthetic credit and gate
  setup occur only after isolated-target and fresh-database guards.
- Existing submit/job/gateway/settlement/confirmation/capture/cleanup paths execute
  with normal semantic review/repair. An independent monotonic sum of conservative
  call bounds is at most SAR 5, with at most 96 provider calls; ordinary test DB
  global/user/job budgets remain active. These are reservation assumptions, not a
  guarantee against a provider violating usage/pricing contracts.
- No automatic network retry after transient worker failure. Incomplete synthetic
  orders fail/release once, retaining the last attempt error and unknown provider
  exposure. Cap breaches stop future AI admission; direct cases can still execute.
- Delivery opens PDF/Word/Excel/PPTX/images/text, checks fixture tokens/page minima,
  forbids spreadsheet formulas/hyperlinks, and copies synthetic results before
  ordinary artifact cleanup. Terminal replay must not regenerate or redeliver.
  Each case checkpoints a safe JSON report with calculated usage/cache/cap audit.

## Operator wrapper

scripts/service-acceptance.sh requires production pause true; it creates a separate
PostgreSQL database and mounts only the new ops modules into the existing qualified
worker image. In-process URL/database/storage/test settings overrides never print
credentials or alter .env. Existing production services remain running/paused;
no Redis dispatch, Telegram messages or production ledger mutations are used.
The wrapper retains the test database, custom-format dump and a ZIP of outputs/
report in a private operator directory even when service cases need review. It
never automatically drops billing exposure. A crash may leave a partial report or
unsettled test exposure; retained DB evidence must be reviewed before cleanup.

## Evidence and limitations

PASS LOCALLY: 15 focused pure fixture/isolation/readback/bound/architecture cases,
lint/format, plan generation and Bash syntax. Hosted PostgreSQL lifecycle, cap,
transport-failure and financial checks required before merge. No full live run
claimed here; operator execution and individual output review remain pending.

Coverage is a synthetic acceptance sweep of major modes, not every input boundary,
all CV profiles, real payment/Stars acceptance, Telegram/mobile UX, semantic
correctness, visual polish, unsupported provider vision or invoice certification.
Service failures are reported as failures rather than silently replacing AI or
claiming that successful native exports prove human-quality results.
