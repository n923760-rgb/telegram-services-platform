# Master engineering roadmap

Reconciled with live GitHub on 2026-10-08. This roadmap is not a production release approval.

## Current verified state

- FACT: Source of truth is n923760-rgb/telegram-services-platform, official branch main.
- FACT: PRs #1–#4 and #6 are merged: Compose CI setup, recovery/retention safeguards,
  text-to-PowerPoint, text-to-PDF and shared Office builder quality.
- FACT: PR #7 is merged at a8f70f7eb58d457dfefb4e378c5085e6fc9d3092:
  persistent Arabic/English menus, intake, support and delivery notices.
- PASS: Reviewed UX head f498413 passed 152 tests, lint, format, migrations, schema drift
  and Compose configuration in workflow 37575252712. Post-merge main workflow
  37575645208 also completed successfully.
- FACT: PR #5 is merged at a3aaf573238a497659bfa3137073185bf10b7340. PDF-to-Word
  is discovered, disabled by default, and rejects encrypted, unreadable, mixed and oversized
  input before an AI call. Original page-layout/image/table reconstruction is outside scope.
- PASS: Reviewed PDF-to-Word head a0cce87 passed 171 tests, lint/format, migrations,
  schema drift and Compose configuration in workflow 37576254914. Nineteen focused cases
  cover extraction, ownership/limits, credit release and cached delivery recovery.
- PASS: Local smoke used actual PDF parsing and DOCX reopening. Hosted integration evidence
  is retained in EVIDENCE/README.md separately from real-provider qualification.
- NOT RUN here: Container runtime and authenticated Telegram/provider journeys; no access to
  the operator's server or private configuration is available in this workspace.
- FACT: No production deployment or service enablement was performed in this review.
- Historical environment limitations in dated reports remain historical evidence, not the
  current hosted test result. See REPORTS/2026-10-07-pdf-to-word-review.md.

## Customer experience continuation — 2026-10-07

- FACT: Task branch adds persistent two-column navigation, owner-scoped paginated order
  history, localized state/time details, prompt steps and scoped cancellation.
- FACT: Menu/support/home navigation preserves drafts; language changes redraw the current
  question. Existing service-selection, payment and settlement contracts remain in place.
- PASS: Locked local install, lint/format/diff and collection of 203 tests (32 new cases).
- PASS: Task source d3d10b04 passed [hosted workflow 37659108407](https://github.com/n923760-rgb/telegram-services-platform/actions/runs/37659108407):
  203 tests, lint/format, migrations/drift and Compose configuration. The later evidence
  update changes documentation only; inspect its final-head workflow separately.
- NOT RUN: Authenticated Telegram/provider and deployment qualification.
- Evidence: [customer-navigation report](REPORTS/2026-10-07-customer-navigation.md).

## Direct document continuation — 2026-10-08

- FACT: Baseline main faab75a includes merged PR #9; post-merge workflow 37727678417 passed
  203 tests, lint/format, migrations/drift and Compose configuration.
- OPERATOR-REPORTED: Compose build succeeded, services healthy and migrations exited 0;
  the operator's `/health` response was HTTP 200 on 2026-10-08. No SSH access is available here.
- OPERATOR-REPORTED: Telegram screenshots show echo delivery, completed order history,
  persistent navigation and zero reserved credit. Real Office/PDF output quality and full
  before/after financial audit remain unqualified.
- FACT: Current task adds explicit direct Word/PDF modes without AI, a shared bounded input
  contract and pure per-request AI gating. Existing smart behavior, prices, ledger, general
  cost admission limits and cached-delivery rules are preserved. Plugin contracts become version 2.
- FACT: No dependency, database schema, new service, agent loop or workflow was added;
  no unused-code deletion was justified in this bounded inspection. Shared input validation
  replaces repeated parsing, and a duplicate import was removed.
- PASS: Local service tests and Word/PDF render inspection; final counts and limits in
  [the direct-document report](REPORTS/2026-10-08-direct-documents.md).
- PASS: Application/test source 798f023 passed [workflow 37771104090](https://github.com/n923760-rgb/telegram-services-platform/actions/runs/37771104090):
  240 tests, lint/format, migrations/drift and Compose configuration. Final evidence-only
  update CI must be inspected separately before merging PR #10.
- NOT RUN: New direct-mode server deployment/Telegram acceptance. This section is task
  evidence, not post-merge proof.

## Optional document title continuation — 2026-10-08

- OPERATOR-REPORTED: Main 67b46d1 deployed; clean source, healthy API/bot/worker,
  migrations exited 0 and `/health` returned `{"status":"ok"}`.
- FACT: Uploaded PDF sample is readable with correct title and leading-zero numbers.
  Uploaded Word repeats the whole body as its title; the file cannot prove how that title
  was entered. Uploaded Excel is one text column, not typed structured data.
- FACT: This bounded task makes direct Word/PDF titles optional with localized No title
  buttons and single-line validation; preserves strict smart-mode document schemas.
- FACT: No provider call, dependency, migration, price or financial policy change.
  Contracts increment to version 3; stale drafts restart and unprepared old jobs release.
- PASS: Local lint/format and 39 service tests; full integration evidence requires CI.
- NOT RUN: Updated server deployment, Telegram optional-title acceptance and financial audit.
- Excel specialization remains a separate next slice.

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

1. NOT RUN: Real source-bound Telegram/provider acceptance on a dedicated staging account.
2. NOT RUN here: Docker build/start/recovery and server-specific deployment qualification.
3. NOT RUN: Representative Arabic/English PDF extraction and live provider output quality.
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
Keep payment gateways, dashboards, unapproved extra services, agent loops and n8n out of current scope.
Do not purchase infrastructure, merge, tag, release or deploy implicitly.

## Exact immediate next round

Verify the latest main workflow before using that source for runtime qualification.
Complete the bounded direct-document task and its hosted checks; qualify direct Word/PDF
using the updated acceptance guide before extending direct modes to Excel or PowerPoint.
Run the [Telegram acceptance guide](../docs/TELEGRAM_ACCEPTANCE.md) on an available staging
server with a dedicated test account and operator-configured secrets. Use echo first, then
Office/PDF and clear/unclear OCR; inspect reservations, capture/release and file cleanup.
The operator must identify the installation and deployment method before runtime changes.
Keep real-provider quality and billing evidence separate from mocked integration checks.
Do not reopen completed phases without a confirmed finding or invent runtime evidence.

Publication history: [initial permission rejection](REPORTS/2026-10-04-publication.md) and
[authorized import](REPORTS/2026-10-04-import.md).

Hosted evidence and CI correction: [report](REPORTS/2026-10-04-compose-ci.md).
