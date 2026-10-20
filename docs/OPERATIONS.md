# Operations

## Isolated synthetic all-service acceptance

After owner authorization for live testing, run `bash scripts/service-acceptance.sh`
from clean main while production provider pause is true. The wrapper uses a fresh
uniquely named PostgreSQL acceptance database and dedicated shared-volume storage;
it does not stop production containers or modify their pause, users, credit, gates
or prices. Synthetic credit funds 29 cases across 16 services only inside that DB.
The plan now exercises an explicit three-slide presentation, optional minutes titles,
image page ordering, CSV Columns output and a native PDF rotation case. Exact PDF page
counts/rotation flags, selected slide counts and required workbook sheets are checked
where declared. The added rotation case is provider-free; AI case count and caps are unchanged.
These structural checks do not certify semantic completeness, image order or mobile appearance;
inspect outputs and retain separate representative Telegram/provider acceptance.
The configured provider/key is inherited in-process without printing credentials;
normal job-scoped cost reservation, schema/content review, native builders and
confirmation/replay paths remain active. No real Telegram/Stars transactions.

Default `python -m app.ops.service_acceptance` prints the pure plan without live
calls. Execution requires the wrapper's explicit isolated environment. The run
reserves at most SAR 5 in cumulative conservative call bounds and permits at most
96 calls, with further DB budget guards. A provider contract breach can still
exceed a calculated reservation; actual reported usage is preserved and blocks
further AI. Transient failures are not autonomously retried by the worker; unknown
exposure remains held. Production's old unknown holds are not touched.

The wrapper prints a private backup directory, separate DB name and results ZIP;
review report.json and the files individually. Exit 1 can mean REVIEW_REQUIRED,
not that all cases failed. Partial artifacts/reports and the test DB are retained
for investigation; no automatic DB deletion. The dump contains test accounting
and safe request audit metadata. Keep it private with the outputs. Opening files
and preserving fixture tokens do not certify visual polish, factual semantics,
mobile UX, every mode/boundary, provider vision support, paid invoices or Stars.

For a targeted rerun, pass exact case names, for example
`bash scripts/service-acceptance.sh cv_ar cv_en cv_bilingual`. The CLI equivalent
for a pure plan is `python -m app.ops.service_acceptance --case cv_en` (no call).
Omitting case names retains the full sweep; duplicates and unknown names fail.
Each execution still requires a fresh isolated database and output prefix.
Diagnostics identify generation versus review, JSON/schema/constraint rejection,
and valid semantic review verdicts using bounded codes only. They retain no raw
model output, customer text, validation locations/messages or prompts. A rejection
category is not an explanation of which source fact failed. Existing budget,
settlement and bounded repair behavior is reused without extra calls. The report
also totals `calculated_usage_sar`; cumulative conservative reservation bounds
are a separate allowance, and neither amount proves the provider invoice.

Trusted response schemas can declare a `diagnostic_categories` class-level mapping
of fixed custom validation codes to fixed labels. Only identifier-shaped labels
of at most 48 characters are accepted; built-in categories cannot be overridden.
Never derive this metadata from customer input. CV v6 uses this for distinctions
such as `cv_source_tokens`, `cv_section_order` and `cv_summary_sources`. Unregistered
types still collapse to `schema_type`; no raw messages, input, context or locations
are reported. This observer remains isolated-test-only, not production logging.

Word/PDF plan diagnostics distinguish `document_missing_body`,
`document_missing_question`, `document_invalid_text` and `document_source_tokens`.
PPTX distinguishes `pptx_missing_deck`, `pptx_missing_question`,
`pptx_source_tokens` and `pptx_slide_count`. Other constraints can still use the
generic category; these labels do not recover the cause of an older report.
Valid plan events also expose only the boolean `missing_information` and
`ambiguous` dispositions when present, never the clarification or output text.
After updating the worker image, a bounded targeted investigation is
`bash scripts/service-acceptance.sh word_smart text_pdf_smart pptx`.
Passing source tests or prompt clarification does not establish live acceptance.

PDF-to-Word v6 distinguishes conversion from authoring: the supplied extracted
text is the complete input, including sparse cell values and partial notes.
Missing/null document or `missing_information=true` now produces the fixed
`pdf_word_missing_body` category and enters the existing single repair before
semantic review. Persistent refusal fails as `provider_invalid` without a file.
Exact prior numeric/contact occurrence rules remain, with a fixed
`pdf_word_source_tokens` category. Image/form/page guards and normal cost budgets
are unchanged. Build the updated worker image before isolated PDF-to-Word testing.
Administrator settings and prepared historical replay are retained across v6 sync.

The latest full d63d896 operator run is 27/29: PDF-to-Word requests context and
image enhancement reports `enhancement_not_improved`. The latter is the existing
quality-decline path, not evidence of successful enhancement or necessarily a
runtime defect. It must remain visible for review; a model accepting its refusal
does not certify a useful processed image. Positive output quality requires
inspection, while the controlled refusal must deliver no image and release credit.
Enhancement v4 now explicitly judges meaningful paper-illumination/background
improvement as well as text legibility/edges. Original readability alone does not
exclude useful illumination correction; brightness changes alone are insufficient.
Preserve characters, numbers, marks and color-coded distinctions, and retain none
for uncertain fidelity or no useful improvement. Native processing and the three
evidence images/output files are unchanged. Build the new worker image, then run
`bash scripts/service-acceptance.sh pdf_word enhance` for targeted live qualification.
Prepared image v3 files replay; admin settings and existing old-job release remain.

Schema repair now supplies the original source, the bounded rejected candidate
(up to 16384 characters; omitted in full above that limit) and fixed validation
categories to the existing correction attempt. This context remains in memory
and goes only to the configured provider; it is not stored in diagnostic reports,
cost audits or exception messages. Raw validation messages, locations and context
are excluded. Every repair still reserves its full actual request exposure before
calling the provider, and every completed call settles its reported usage.
Larger repair inputs may hit an existing job budget; caps are not increased.
After correction, the original schema/source guards and content review still apply.
There is no added creation attempt or automatic fallback that bypasses fidelity.

Smart Word and PowerPoint use temporary references for numeric/contact literals
inside provider input, with a dictionary of the exact original values. Known
references are restored before schema/source/layout validation and content review;
rendered files and continuations contain resolved values. Unknown or incomplete
current references report the fixed `protected_value_reference` category. Existing
source-count checks still reject invented/changed/over-repeated values; references
do not establish correct meaning or associations. PDF and Excel inputs are unchanged.
The dictionary is transient provider input, not encryption, and is absent from
diagnostic reports and JSON schemas. Larger inputs use existing reservations and
caps. The reference protocol adds no provider call or production unpause.
Operator's abe7bb8 run passed Word smart and Text PDF smart. The targeted c69bf5f
PPTX run identified exactly two excess numeric occurrences in third-slide bullets
on both attempts, with zero added values. PPTX v7 deliberately changes repetition
policy: each exact numeric source literal may appear once more across the deck,
on another slide; the original per-slide count budget and original whole-deck
contact budget remain. New/altered values and further repetition reject. This
allows contextual reuse, not duplicated records, padding or changed meaning;
normal semantic review remains required. Word/PDF source-count policies are unchanged.
Isolated PPTX failures
also report `token_diagnostics`: counts of added/repeated numeric/contact values,
and at most 32 locations containing only slide ordinal, fixed field/category and
occurrence count. Altered values count as added. Locations are the occurrences
beyond the current per-slide/whole-deck budgets in traversal order, not a decision about which copy to
remove. Numeric parts inside contacts mirror the existing validator and may also
contribute to numeric counts. No source values, hashes or model text are retained.
Failed-case diagnostics print directly in console output as well as report.json.
Diagnostics share the v7 production budget function, so allowed contextual reuse
is not reported as a violation. Build the new worker image before running
`bash scripts/service-acceptance.sh pptx`. The PPTX fixture requires the original
ID and amount in native text/table cells as well as exactly three slides. Version
sync retains administrator prices/activation; prepared older files replay and
unprepared older jobs cancel/release. Provider pause is unchanged. A live pass and
visual/semantic output review are still required before production qualification.

The wrapper mounts operational modules, not changed service implementations.
After a service-code update, build the worker image before its acceptance run:
`docker compose build worker`, then `bash scripts/service-acceptance.sh cv_en`.
Building a new image does not replace running production containers; full production
deployment and updated live output acceptance remain separate steps.

## Customer behavior during provider pause

Catalog browsing shows a localized notice for categories containing required-AI
services while AI is disabled or provider pause is set. Buttons/names/categories,
admin ownership and Stars price visibility remain intact. Selecting or explicitly
resuming a required-AI service shows an availability notice before a new prompt;
any prior draft remains unchanged. Source-bound result followups requiring AI are
hidden and stale callbacks are rejected while unavailable.

Direct/mixed services remain browsable: do not infer a customer's mode from
fabricated inputs or disable direct work due to provider pause. Final submission
still checks actual needs_ai(inputs) before reservation/invoice, including a pause
race after intake. Existing mid-collection drafts are not deleted or automatically
rerouted; these UI hints do not certify credentials, budgets, provider or output
quality and never toggle pause/admin service gates.

All admission paths use the same strict pause reader: a missing setting retains
the existing default, and only JSON `{"value": false}` explicitly permits calls.
Malformed values (including zero/null/strings/arrays or a missing `value`) block AI
submission, Stars pre-checkout and provider reservations, and readiness reports
paused. Direct modes remain available. Nothing repairs the setting automatically
or changes historical holds; correcting it remains an operator action.

## Provider cache/cap audit and synthetic preflight

New compatible-provider calls preserve safe request IDs, requested wire limits,
cap breach flags and consistent cache hit/miss counts in cost_usage.rate_snapshot.
Missing/invalid optional cache data stays explicitly unknown/invalid; complete
reported prompt/output totals are still costed using the configured full rates.
No automatic cached-input discount or claim that calculated SAR is a paid invoice.
Output above the request cap is recorded fully and pauses future admission even
when its cost fits the monetary reservation. No token clamping or hidden usage.

`docker compose exec -T worker python -m app.ops.provider_cap_preflight` prepares
an owner-authorized synthetic request with <=128 output tokens, its body hash and
conservative reservation bound. Pass `--actor ID` for multiple configured admins.
It reads pause state in a bounded read-only transaction; performs no network call,
reservation, order, delivery, reconciliation, configuration change or resume.
`prepared` means the wire request was prepared; it does not verify the provider's
actual cap behavior. The global pause still blocks live calls; do not bypass the
job-scoped budget gateway to turn this preparation into an unaccounted API call.

Hourly billing exports cannot allocate per-call cache charges or identify calls
without independent request/key evidence. Keep individual unknown exposure held;
never reconcile it with an assumed zero, an estimated range or by subtracting a
conservative calculated cost from an aggregate paid amount. Invoice adjustments
and live recovery remain separately reviewed operational actions.

## Private read-only order diagnostics

Run `docker compose exec -T worker python -m app.ops.order_diagnostics C64ECF1E`
with the customer's eight-character order reference or full UUID. This uses the
sole configured administrator; when there are multiple admins, pass `--actor ID`.
Ambiguous short references require the full UUID. Output is a bounded metadata-only
database snapshot, not provider invoice evidence or a performed recovery action.
Unknown costs stay null. Pause/cost/ledger states are not changed; no provider call.
Do not use report success as authorization to unpause or clear unknown exposure.
Overflow or unavailable state returns a safe error instead of a partial report.

Run `scripts/backup.sh` daily from the project directory, for example a root cron entry:
`15 2 * * * cd /srv/telegram-services && ./scripts/backup.sh >> /var/log/services-backup.log 2>&1`.
The script uses pg_dump custom format, restrictive permissions, atomic rename and 7-day retention.
Use an SSH key to copy each completed dump to a separate server, for example
`rsync -a --chmod=F600 backups/ backup-user@backup-host:/srv/backups/telegram-services/`.
Check copy exit status, alert externally on failure, and keep a separate remote retention policy.
Keep a separate encrypted copy of .env and any files that must survive a server loss.

Restore into an empty replacement database, never blindly over production:
1. Stop bot, worker, API, monitor; retain the original database/volume.
2. Point .env and Compose at a NEW empty PostgreSQL database/volume.
3. Verify target and backup, then `CONFIRM_RESTORE=YES ./scripts/restore.sh backups/FILE.dump`.
4. Run migrations, compare ledger/order counts and totals, and test a single isolated order.
5. Restart services. Reconcile uncertain provider costs and interrupted deliveries.
Test the restore periodically on a disposable instance. Customer-file volume is separate from pg_dump.

The independent monitor can report worker/Redis/database failures while the worker is down.
It cannot alert when the VPS or its internet connection is down: use an external uptime monitor.
Alerts deduplicate for 15 minutes through Redis, with shared-volume lock fallback.
A send outage may postpone alerts. No secrets or customer content is included in alerts.

Cost settings use Settings rows with JSON {"value": VALUE}, overriding corresponding environment defaults.
Daily boundaries and report cron use Asia/Riyadh. Cost reservations cover in-flight exposure;
uncertain provider calls retain exposure until billing reconciliation (no invented zero-cost success).
Assign provider costs to the cost hold's opening day, matching admission budgets rather than
the later settlement day. Reports show unsettled exposure separately; margin remains provisional.
A report sent before midnight is a snapshot of that day, not a closed accounting statement.
PROVIDER_BALANCE_SAR is optional operator-reported balance; providers without a balance API remain unknown.
MAX_JOB_COST_SAR, MAX_DAILY_COST_SAR and MAX_COST_PER_USER_PER_DAY must be positive decimals.
Disabling a service cancels all unsettled orders and releases reservations, including pending deliveries.
A concurrent Telegram send may already have reached the customer; cancellation never captures their credit.
Re-enabling resets the breaker observation window.
Re-enable with /enable SLUG. Support admins reply with /reply TICKET_UUID MESSAGE.
Delivery is at least once: a crash after Telegram accepts a send but before DB commit can duplicate a
message/file, while ledger settlement and refunds remain idempotent. Never claim exactly-once sends.


Provider cost is computed from returned usage and the configured model rates and exchange rate.
`AI_TOKEN_LIMIT_PARAMETER=auto` uses `max_tokens` on exact `api.deepseek.com` and
`max_completion_tokens` elsewhere. Custom gateways may explicitly choose either
validated name. Requests and reservations use the same `AI_MAX_OUTPUT_TOKENS`.
Thinking/model settings are unchanged; reported completion usage is never clamped.
After a cap-contract failure, keep the provider paused until the corrected deployed
request is verified and billing exposure is reviewed. Do not release uncertain holds
or automatically resume calls merely because code or readiness checks passed.
It is not an invoice receipt: discounts, cached-token rates and subsequent billing adjustments are not
inferred. Configure conservative current prices and reconcile discrepancies against provider billing.
A timed-out call might have been billed: inspect cost_holds and provider records, then run
`uv run python -m app.ops.reconcile HOLD_UUID CONFIRMED_COST_SAR`. This is an operator action, not
an automatic release of unknown exposure. The reconciliation command is idempotent for equal amounts.

The circuit breaker evaluates the most recent configured window of completed/failed jobs, after the
minimum sample count, and also alerts on consecutive failures. User credit releases are not a refund
of provider expenditure: OCR rejected as unreadable still may incur provider cost.
Explicit unsupported PDF content/forms, PDF input limits and invalid page selections are excluded
before filling that window, so they do not pause a healthy service or emit failure alerts.
Generic `file_invalid`, unknown processing errors and provider failures still count. This policy
does not re-enable a service that an administrator or an earlier circuit evaluation disabled.


Revised-spec controls:
- Jobs record terminal finished_at; reports and circuit windows use outcome time, not later content edits.
- Cancellation is distinct from execution failure; missing/unreadable input and budget/config gates do not trip the service breaker.
- Usage rows preserve provider/model and non-secret rate assumptions. Historic unknown pricing remains unknown.
- Daily reports retain pending Redis work and retry every minute after failed sends. Crash windows can still duplicate an external send.
- Financial operations lock customer rows before order/job rows. Provider-budget operations lock global budget, user budget, then job.
- Retry helpers apply only to PostgreSQL deadlock/serialization aborts in database-only functions, at most three attempts. Never decorate AI or delivery calls.
- Ledger keys are globally bound to the original customer and payload. Migration 0009 aborts if historic keys conflict; inspect conflicts and propose a reviewed resolution, never rewrite immutable history automatically.
- Banning blocks new orders and structure approvals. Existing queued/running orders continue; waiting approvals expire and release credit.


Terminal file deletion has a durable files_deleted marker and a 20-second/startup recovery sweep.
Cleanup failures keep the marker pending. Storage implementations own TTL expiry; Telegram delivery
reads through the storage interface rather than assuming a local filesystem path.

CI pulls the existing Docker Official Image tags from ECR Public, falling back once
per image to Docker Hub after a failed/90-second timed-out pull. The fixed allowlist
is PostgreSQL 16-bookworm, Redis 7-alpine and Python 3.12-slim. No registry credentials,
new image publisher or production image/configuration changes are needed. Both
sources may be unavailable: that fails CI, never marks checks skipped/passed.
The selected references are logged through ordinary public Docker pull output and
GitHub step outputs; tags can change or mirrors can lag, so this is not digest identity
or registry uptime certification.

Checkout and Python setup precede image selection. The selected local images start
only the disposable services in `.github/compose.ci.yml`, under a unique CI run/attempt
project name with loopback-only ports and the existing health probes. Compose uses
`--pull never --wait --wait-timeout 120`; no tests run before readiness succeeds.
An always-run cleanup removes only that CI project's containers/network/anonymous
volumes. It never uses the production Compose file. Do not run this CI stack on the
production VPS. The helper refuses missing GitHub Actions/output context; this is an
operational guard, not a sandbox for repository code.

All lint, formatting, migration, complete pytest, Alembic drift, production Compose
syntax validation and the non-root/network-disabled native worker qualification
remain mandatory. Worker builds use the selected Python image with pull disabled;
Dockerfile defaults remain unchanged. Public-registry failures must be resolved and
the full workflow rerun; do not skip financial/native checks to obtain a green result.

References: [Docker's official ECR mirror announcement](https://www.docker.com/blog/news-from-aws-reinvent-docker-official-images-on-amazon-ecr-public/),
[Compose readiness and pull policy](https://docs.docker.com/reference/cli/docker/compose/up/),
[scoped Compose cleanup](https://docs.docker.com/reference/cli/docker/compose/down/).

## Explicit DeepSeek completion mode

For the exact official `api.deepseek.com` host and documented `deepseek-flash` /
`deepseek-v4-pro` models, the adapter now sends an explicit `thinking.type`.
`AI_DEEPSEEK_THINKING=disabled` is the default for bounded JSON service work;
`enabled` is an operator opt-in requiring separate budget/output-quality acceptance.
No vendor thinking field is sent to other hosts, proxies or unknown models. The
existing token-limit parameter selection remains. Real .env files are not rewritten.

DeepSeek documentation checked 2026-10-17 says thinking is enabled with high effort
by default. Earlier requests omitted the field. That mismatch is observed in source;
it is a plausible contributor to long generations, not proof of the uninspected
bilingual provider_usage incident. Official references:
https://api-docs.deepseek.com/guides/thinking_mode/ and
https://api-docs.deepseek.com/api/create-chat-completion/ .

Usage snapshots add fixed finish-reason enums, optional validated reasoning-token
counts and the requested thinking mode; never reasoning text. Historical missing
fields stay unknown. All returned completion tokens remain in the calculated cost;
reasoning counts are not subtracted or billed twice. A `length` finish reason is
settled before rejecting the incomplete candidate and using only the existing bounded
repair allowance. A valid JSON fragment with `length` is not accepted as complete.
Actual overrun/cap breach still records full usage and pauses admission. No pause is
automatically cleared and no unknown hold is fabricated as zero.

Build a new worker image before isolated acceptance; copying only ops files cannot
update installed adapter code. Keep production paused and test synthetic CV AR/EN/
bilingual in a fresh test DB using `scripts/service-acceptance.sh`. Inspect completion
metadata and actual artifacts. A successful run qualifies that sample, not future
provider uptime, invoice accuracy or all-service quality. Historical invoice
reconciliation is not a prerequisite for these isolated development tests.
