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
- PENDING: Inspect hosted CI for the exact imported source; the Actions run is the authoritative result.
- NOT RUN: Authenticated Telegram/AI journeys.

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

1. PENDING hosted CI verification for the imported source; check the actual run before claiming success.
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

Inspect the hosted workflow for the imported commit and record its actual result.
Then identify an available Docker staging environment and inspect it before runtime work.
Do not reopen completed phases without a confirmed finding or invent hosted/runtime evidence.

Publication history: [initial permission rejection](REPORTS/2026-10-04-publication.md) and
[authorized import](REPORTS/2026-10-04-import.md).
