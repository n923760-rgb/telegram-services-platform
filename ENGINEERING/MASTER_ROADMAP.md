# Master engineering roadmap

Reconcile this single roadmap after live-source verification. Documentation round: 2026-10-04.
This roadmap is not a production release approval.

## Current verified state

- FACT: Local implementation covers the four authorized phases and revised specification.
- FACT: The application suite passed 83 tests before this documentation-only adaptation.
- FACT: Alembic head 0010, lint, format, dump/restore and HTTP readiness passed locally.
- FACT: Root AGENTS.md preserves project policy and adapts the reviewed engineering reference.
- FACT: Target is n923760-rgb/telegram-services-platform on main; the owner authorized initial publication.
- FACT: Integration access now succeeds; initial source import preserves the repository initialization commit.
- BLOCKED: Docker/VPS execution is unavailable in this environment.
- FACT: Initial hosted run passed 83 tests, lint/format, migration and schema-drift checks.
- FAIL: Final Compose check lacked its service .env file; a bounded CI-only correction is under review.
- NOT RUN: Authenticated Telegram/AI journeys.
- FACT: File-retention safety fix applied (gate purge on durable deletion; protect referenced
  files from age expiry). Regression tests authored but NOT RUN in this environment; see
  [report](REPORTS/2026-10-04-file-retention-safety.md).
- FACT: Approved bounded fixes applied (private-chat gate, HTTPS-only AI endpoints, truthful
  draft-cancel text, per-admin support delivery with reusable ticket ids, retryable intake
  I/O errors, user cost-cap label, stale-plugin enablement). Regression tests authored but
  NOT RUN in this environment; see [report](REPORTS/2026-10-04-bounded-fixes.md).
- FACT: Second bounded-fix round applied (scoped draft cancel, idempotent /resume prompt recovery,
  per-owner upload quota, OCR new-request wording, safe ops/parse errors). Notifier dedup verified
  intentional (dedup by type per README). Regression tests authored but NOT RUN here; see
  [report](REPORTS/2026-10-04-full-review.md).
- FACT: Third bounded-fix round applied (correct `fund` import, confirm-state prompt handler,
  strengthened confirmation-recovery regression tests). Regression tests authored but NOT RUN here.
- FACT: Finalization round applied (explicit update-not-applied recovery notice for multiple images,
  truthful storage-quota wording, dedicated stale-button guidance, confirm-state instruction, quota
  defaults in .env.example/README, lock-filename correction). Regression tests authored but NOT RUN
  here; see [report](REPORTS/2026-10-05-finalization.md).
- FACT: Office Expert Quality v1 was re-scoped from a mistaken new `office_expert` plugin into a shared-builder quality upgrade (Word/Excel/PPTX/PDF): content-based RTL/LTR, mixed Arabic/English handling, professional typography/layout, preserved formula-injection protection, adaptive Excel direction, PPTX title slide, and PDF font fallback with page footers; the plugin's i18n/docs/tests were reverted. Builder tests authored but NOT RUN in this environment; the plugin directory deletion is BLOCKED here (pending `rm -rf app/services/office_expert`); see [report](REPORTS/2026-10-06-office-expert-quality.md).
- FACT: Telegram Services UX v1 implemented (bilingual Arabic/English customer UX via the existing
  `User.language` column; localized menus, prompts, confirmations, support flow and delivery envelopes;
  runtime language switch via /lang and the main menu). Tests authored; execution NOT RUN in this
  environment. See REPORTS/2026-10-07-ux-v1.md.

## Architecture and state owners

Use registry-driven plugins and generic bot intake. Purchases belong to orders, execution
attempts to jobs and credit authority to the immutable PostgreSQL ledger.
PostgreSQL owns durable dispatch/results/deletion recovery; Redis supplies queues and
short-lived coordination. Inject provider/storage interfaces and use typed file builders.
Keep specific service names out of core policy.

## Closed historical work

| Milestone | Retained result |
| --- | --- |
| Foundation and registry | Revised phase 1: 51 tests |
| Operations and financial recovery | Revised phase 2: 58 tests |
| Shared AI/file layers | Revised phase 3: 72 tests |
| Real services and complete recovery paths | Revised phase 4: 83 tests |
| Governance adaptation | Inspection complete; focused checks recorded in evidence index |

Details: [validation](../docs/VALIDATION.md),
[baseline](REPORTS/2026-10-04-governance-baseline.md), [evidence](EVIDENCE/README.md).

## Findings and release blockers

1. Complete hosted verification of the Compose environment-file correction before CI qualification.
2. BLOCKED Docker build/start/recovery prevents container deployment qualification.
3. NOT RUN real Telegram/provider journeys leave delivery and Arabic OCR quality unqualified.
4. UNKNOWN current provider rates/billing need operator configuration and reconciliation.
5. FACT SAR wallet credits are test credits; Telegram digital sales need a separate Stars design.
6. FACT external delivery is at least once; send/commit crashes can duplicate output.

## Ordered qualification gates

| Gate | Required proof / authority |
| --- | --- |
| Remote source | Verified target and write access; preserve existing initialization and verify the uploaded tree |
| Hosted checks | Run the existing workflow against the published source and inspect actual logs |
| Container staging | Build Compose, migrate, check health and test restart/recovery on an available machine |
| Private setup | Configure Telegram/AI credentials and rates on the operating machine |
| Real journeys | Echo first, then clear/unclear Arabic/English OCR and Word/Excel; inspect ledger/deletion |
| Operations | Verify alerts, reports, backup/restore and off-server copying in staging |
| Candidate freeze | Bind source SHA, artifact hash and retained evidence |
| Production decision | Explicit deployment authority and resolved digital-sales payment contract |

## Owner decisions and deferred work

Identify staging and configure secrets privately; retain remote/hosted evidence separately from deployment.
Keep payment gateways, dashboards, extra services, agent loops and n8n out of current scope.
Do not purchase infrastructure, merge, tag, release or deploy implicitly.

## Exact immediate next round

Verify the file-retention safety change and its regression tests on a disposable migrated
PostgreSQL/Redis setup before merge; verify the bounded-fix regression tests (including the
second-round draft-recovery and upload-quota tests and the finalization-round recovery-notice,
stale-button and confirm-state tests) and review the tested Compose CI correction
and its hosted workflow; merge only with explicit owner authority.
Then identify an available Docker staging environment and inspect it before runtime work.
Do not reopen completed phases without a confirmed finding or invent hosted/runtime evidence.

Publication history: [initial permission rejection](REPORTS/2026-10-04-publication.md) and
[authorized import](REPORTS/2026-10-04-import.md).

Hosted evidence and CI correction: [report](REPORTS/2026-10-04-compose-ci.md).
