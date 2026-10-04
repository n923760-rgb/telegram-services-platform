# Master engineering baseline report

Date: 2026-10-04. Inspector/executor: Codex in the shared local coding environment.
Inspection mode: READ-ONLY, completed before the subsequent governance mutation branch.
Inspected clean local source: a54876dc7580f0a13ec82bd53d21872db0c720b5 on master.
Target remote repository and official branch: UNKNOWN; no Git remote configured.
Reviewed reference: n923760-rgb/engineering-governance at
641e4f9e45da109257ba1f38752b94604c2e4531 through the GitHub connection.
This record was retained in the later authorized adaptation, not written during inspection.

## A. Project identity
FACT: Arabic-first Saudi Telegram platform. Python package telegram-services.
Real services: image_to_text and text_to_office; echo verifies the flow.

## B. Live repository state
FACT: Inspected local master HEAD recorded above was clean with no remote.
FACT: GitHub inventory includes engineering-governance; the suggested project repository
telegram-services-platform was absent from the returned inventory.
UNKNOWN: Remote official branch, PRs and protections until a target repository is identified.

## C. Current canonical source
FACT: The bootstrap source is the local Git implementation. Remote canonical status is
UNKNOWN. Reverify current HEAD before subsequent work; do not substitute an unrelated repo.

## D. Existing governance
FACT: Root AGENTS.md holds the financial, architectural, privacy and extension rules below
120 lines. The new reference was not yet adapted; no ENGINEERING roadmap existed.

## E. Build and release
FACT: Python 3.12, uv.lock, requirements.lock, non-root Dockerfile and Compose exist.
Migrations precede service startup and healthchecks exist. Private setup avoids overwriting .env.
BLOCKED: Docker unavailable. UNKNOWN: VPS, hostname, credentials and deployment authority.

## F. Architecture
FACT: Bot/API are adapters; core owns settings/DB/i18n; wallet owns financial policy;
orders/jobs own execution state; plugins use providers and typed builders.
Files owns intake/retention; ops owns alerts/reports/costs/circuits.

## G. State ownership
FACT: Immutable ledger determines credit; customer locks and idempotency guard changes.
Orders freeze purchases/contracts; jobs and attempts own execution. PostgreSQL owns durable
dispatch, prepared results and deletion recovery. Redis supplies short-lived coordination.

## H. Features
FACT: Dynamic menus/intake, credit confirmation, delivery, admin/support, budgets/circuits,
reports/alerts, retention and backup/restore exist. OCR optional translation and Word/Excel
use the shared pattern. No payment gateway, dashboard or additional real services exists.

## I. Runtime contract
FACT: Arabic-default Telegram surface, polling by default, authenticated future webhook,
PostgreSQL/Redis and local shared storage. NOT RUN: Representative real Telegram clients.

## J. Tests
FACT: Retained validation records 83 tests with real PostgreSQL/Redis and mocked AI/Telegram,
including concurrency, refunds, costs, circuits, builders, intake, recovery and webhook.
The read-only inspection did not rerun that suite; the docs round needs focused checks.

## K. CI and automation
FACT: A pinned-actions GitHub workflow defines migration/test/lint/Compose checks.
ARQ schedules recovery, cleanup and reports. NOT RUN: Hosted GitHub CI.

## L. Security and privacy
FACT: No tracked .env; authorization, bounded uploads, webhook secret, redacted logging
and retention exist in source. Plugins are trusted executable Python, not sandboxed.
INFERENCE: These reduce exposure; they do not establish full production security.

## M. Evidence coverage
FACT: docs/VALIDATION.md retains local outcomes and explicit limits.
NOT RUN: Docker/VPS, real OCR/Telegram, native Office visual rendering or invoice accuracy.
UNKNOWN: Production capacity and incident response effectiveness.

## N. Risk and gap ledger
BLOCKED: Container staging. UNKNOWN: Remote identity and official branch.
NOT RUN: Authenticated E2E/hosted CI. FACT: Send/commit crashes can duplicate output.
FACT: Usage-rate costs need reconciliation; SAR is test credit pending a separate Stars design.

## O. Proposed authority model
Preserve owner instructions and hard rules; extend concise AGENTS.md with live verification,
bounded rounds, Git safety, protected actions and truthful evidence.
Adapt generic guidance rather than import another project's facts.

## P. Proposed resource map
Use PROJECT-SOURCES.md for navigation, explicitly marking remote identity UNKNOWN.
Link canonical ENGINEERING locations without a second roadmap.

## Q. Proposed roadmap
Record completed phases, ownership, remaining runtime/remote gaps and ordered staging gates
in ENGINEERING/MASTER_ROADMAP.md. Scaffolding does not qualify production.

## R. Lab plan
FACT: Local shell/Git/Python and isolated PostgreSQL/Redis checks are available.
BLOCKED: Docker. Use separately available staging for container/live journeys.
Do not purchase resources or select a cloud provider implicitly.

## S. Exact toolchain
Python 3.12, uv, PostgreSQL 16, Redis 7, Alembic, ruff and pytest locally.
Require Docker Compose and privately configured Telegram/AI credentials for staging.
Disposable local database test tooling is not the production deployment method.

## T. Controller and executor
FACT: The same Codex session executes authorized local work; no delegated execution.
The existing build/governance request authorizes the bounded documentation adaptation.
Remote publication and deployment are not inferred.

## U. Evidence and reports
Use ENGINEERING/REPORTS and ENGINEERING/EVIDENCE with source attribution and sanitized
results. Keep customer content and credentials out of records.

## V. Protected owner decisions
Identify target repository and staging machine; configure secrets privately.
Require authority for publishing, merge/tag/release, production/destructive work and
changes to the payment/product contract.

## W. Exact next round
Implement only the requested governance adaptation on a bounded local branch, run focused
checks, review diff and package. Then identify remote source and Docker staging before
performing their corresponding operations.
