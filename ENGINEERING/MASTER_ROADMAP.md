# Master engineering roadmap

Reconciled with live GitHub on 2026-10-07. This roadmap is not a production release approval.

## Current verified state

- FACT: Source of truth is n923760-rgb/telegram-services-platform, official branch main.
- FACT: PRs #1–#4 and #6 are merged: Compose CI setup, recovery/retention safeguards,
  text-to-PowerPoint, text-to-PDF and shared Office builder quality.
- FACT: PR #7 is merged at a8f70f7eb58d457dfefb4e378c5085e6fc9d3092:
  persistent Arabic/English menus, intake, support and delivery notices.
- PASS: Reviewed UX head f498413 passed 152 tests, lint, format, migrations, schema drift
  and Compose configuration in workflow 37575252712. Post-merge main workflow
  37575645208 also completed successfully.
- FACT: PR #5 remains open for PDF-to-Word. Its original workflow failed at formatting;
  no application test result is claimed for that original run. This review fixes discovery,
  incremental extraction limits, rejection of non-extractable pages and literal newline errors.
- PASS: Local PDF-to-Word smoke exercised registry discovery, real PDF parsing, editable DOCX
  content and encrypted/mixed/blank rejection without AI calls. Lint/format/diff checks passed.
- PENDING: Hosted qualification of the updated PR #5; unit and order/wallet/delivery regression
  tests are authored, including reservation release and cached delivery retry.
- NOT RUN here: Container runtime and authenticated Telegram/provider journeys; no access to
  the operator's server or private configuration is available in this workspace.
- FACT: No production deployment or service enablement was performed in this review.
- Historical environment limitations in dated reports remain historical evidence, not the
  current hosted test result. See REPORTS/2026-10-07-pdf-to-word-review.md.

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

1. PENDING qualification of updated PDF-to-Word PR #5 against the latest main.
2. NOT RUN here: Docker build/start/recovery and server-specific deployment qualification.
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

Inspect hosted checks for updated PR #5 and fix confirmed failures before merge. The owner
has authorized continued implementation and merge of the reviewed work in this continuation.
After merge, verify the post-merge main workflow and record attributable results.
Then run the [Telegram acceptance guide](../docs/TELEGRAM_ACCEPTANCE.md) on an available staging
server with a dedicated test account and operator-configured secrets. Use echo first, then
Office/PDF and clear/unclear OCR; inspect reservations, capture/release and file cleanup.
Keep real-provider quality and billing evidence separate from mocked integration checks.
Do not reopen completed phases without a confirmed finding or invent runtime evidence.

Publication history: [initial permission rejection](REPORTS/2026-10-04-publication.md) and
[authorized import](REPORTS/2026-10-04-import.md).

Hosted evidence and CI correction: [report](REPORTS/2026-10-04-compose-ci.md).
