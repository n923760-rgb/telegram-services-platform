# Master engineering roadmap

## Document engines adoption — 2026-10-09

- OWNER DECISION: Adopt specialized deterministic tools and professional templates
  gradually, preserve clean registry-driven architecture and default professional output.
- FIRST SLICE: Reusable source-owned docxtpl Word template with escaped request values,
  native tables and existing Arabic/date handling; no additional provider calls.
- FIRST SLICE: Structural DOCX/XLSX/PPTX/PDF gate before storage/delivery, with generic
  failure/release lifecycle regression. No financial/intake/DB contract changes.
- PASS: 117 local database-independent checks, lint/format; 406 tests collected.
  Synthetic single-page and all three pages of 55-row Arabic output visually inspected.
- NOT RUN locally: Full DB/Redis CI, deployment, live provider and native Office acceptance.
- Remaining candidates and isolated-worker sequence: [document engines](../docs/DOCUMENT_ENGINES.md).
  See [template report](REPORTS/2026-10-09-document-templates.md). Only used dependencies
  are installed; approval of the direction does not imply all candidates are implemented.

## PDF Arabic numeric extraction — 2026-10-09

- FACT: A supplied one-page text PDF visually contains order 00123 and SAR 125.50;
  default extraction omits both with the project's locked pypdf 6.19.0.
- PASS: A generated synthetic Arabic/English regression fails on baseline and passes
  with bounded visitor-fragment collection and Arabic-presentation-form normalization.
- PASS: The supplied PDF retains its order, amount and date with the new extractor.
- FACT: PDF-to-Word version 3 invalidates older pending contracts while preserving
  administrator-owned enabled/price overrides. No new dependencies or schema migration.
- UNKNOWN: The exact real-provider reason for the earlier missing-information response.
  Provider success, native Word acceptance and production deployment remain NOT RUN.
- Hosted CI is recorded on the task PR separately from local unit verification.
- See REPORTS/2026-10-09-pdf-arabic-extraction.md.

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

## Legacy snapshot startup repair — 2026-10-08

- OPERATOR-REPORTED FAIL: Main f325f75 runs API and migrations, but bot/worker repeatedly
  fail `registry.sync` with the unchanged-version input-contract guard. Worker teardown
  additionally raises `KeyError: bot` because startup failed before constructing the bot.
- FACT: Adding default `skip_key` and `single_line` to InputField changes every serialized
  plugin schema; fresh-database CI did not exercise pre-upgrade stored snapshots.
- FIX: Compare contracts after removing only these two explicit no-op defaults recursively.
  Preserve every other/unknown difference and the version-bump guard; sync retains admin
  settings and stores the current schema. Worker teardown closes only a constructed bot.
- CHECKS: Add legacy-snapshot upgrade, repeated sync, unchanged queued-order settlement,
  actual/unknown contract-change rejection and failed-startup teardown regression tests.
- NOT RUN: Repaired server deployment and Telegram acceptance. No DB/ledger rewrite,
  dependency, migration, service version or price change is required.

## Professional Word continuation — 2026-10-08

- OPERATOR-REPORTED: PR #12 deployment at 949e040 is healthy; migrations exited 0 and
  `/health` returned `{"status":"ok"}`. Untitled literal Word preserves the sample but
  the owner rejects mere text transfer as the professional service experience.
- FACT: This task adds a clearly labeled first-choice professional Word route: concise
  AI-proposed title, task-appropriate sections/lists and bounded editable native tables.
  Literal transfer remains explicit, title optional and without provider calls.
- FACT: Word/Excel contract becomes version 4; PDF stays 3. No dependency, migration,
  price, financial policy or new service changes. Existing generic lifecycle stays intact.
- PASS: 47 local service tests; Arabic/English single-page and 55-row five-page builder
  samples visually inspected with repeated headers, legible cells and page numbers.
  Samples use explicit plans, not a real AI provider; they do not prove factual fidelity.
- PASS: Application head 0e003c5 passed [hosted workflow 37805173177](https://github.com/n923760-rgb/telegram-services-platform/actions/runs/37805173177):
  268 tests, lint/format, migrations/drift and Compose configuration. Includes rich-table
  delivery/capture, bounded repair/failure release, literal/Excel regressions and version-3
  snapshot upgrade retaining admin settings. Inspect the final documentation-head check too.
- NOT RUN: New server deployment and live professional Word/source-fidelity acceptance.
  Excel quality improvements remain a later independent task.

## Automatic Word intake — 2026-10-08

- OWNER DECISION: Professional Word should be automatic; remove the additional mode/title
  questions. Preserve literal text on explicit request without searching phrases inside prose.
- FACT: Office version 5 asks only content and format. Exact Arabic/English first-line
  directive selects literal rendering without provider calls; only the directive is removed.
  The remaining body retains whitespace/lines/identifiers. Empty body fails before reservation.
- FACT: No bot/core branch, dependency, migration, rendering, price or financial-policy change.
  PDF retains version 3 and its existing explicit modes/optional title. Removed unused mode labels.
- PASS: 57 local service tests, lint/format/diff; 276 tests collected. Full hosted CI must pass
  before merge, including generic intake, default-provider gating, literal settlement/recovery,
  rich Word delivery and old version-3/4 snapshots retaining admin settings.
- NOT RUN: New server deployment and source-bound professional Word acceptance. The latest
  screenshot shows the PR #13 prompt, not a newly reviewed output document.

## Word date layout qualification — 2026-10-08

- FACT: Reviewed the owner's actual three-order report against the supplied test source.
  Names, IDs 00123–00125, amounts, dates, customer notes and required actions are retained;
  no total or third-order delivery deadline was invented. The report is one editable page.
- FAIL: ISO dates display in reversed order within Arabic prose; the narrow receipt-date
  column wraps each date onto two lines. Logical source date strings themselves are intact.
- FIX: Isolate date text runs and use invisible LTR boundary marks only in professional
  Word mode; literal/default builders add no characters. Date-bearing table columns gain
  a 2.7 cm minimum width within existing page margins. No date conversion/calculation.
- PASS: Local structural/date-fidelity tests and 57 service tests; visually confirmed the
  same report content with correct displayed dates and single-line date cells. All four
  pages of a 55-row date fixture were inspected: repeated headers, intact dates and IDs,
  no clipped rows, and no blank terminal page.
- FACT: No dependency, migration, contract version, price or financial-policy change.
  PR #14 main workflow 37809651597 was cancelled during setup, not a passed main check;
  its reviewed identical application head passed 276 tests in workflow 37809263650.
- NOT RUN: New server deployment, Microsoft Word/iPhone rendering and broad provider
  quality qualification. This one real output is evidence for this sample only.

## All-service output quality request — 2026-10-08

- OWNER REQUEST: Professional, native-editable Office outputs across the approved services.
  This supersedes the earlier deferral of Excel/PowerPoint inspection, not payment/deployment gates.
- FACT: Baseline main `25529b5` retains the recent Word/date improvements; main workflow
  `37813772656` passed. Operator reports `/health` ok, without a current source-bound output sample.
- IMPLEMENTED ON TASK BRANCH: First bounded slice upgrades Excel to a native table with visible
  title, typed formats, source missing/duplicate observations, safer precision/header handling
  and read/edit/save/reopen plus lifecycle regression tests. Legacy plans remain supported.
- NOT RUN: Live-provider, visual renderer and Microsoft Excel acceptance for this new slice.
- NEXT SLICES: PowerPoint readability/overflow and richer native layouts; PDF-to-Word reconstruction
  within approved scope; service-specific OCR/PDF fidelity qualification. Do not advertise
  unimplemented charts, original-layout reconstruction or guaranteed AI fidelity.
- Use [output quality gates](../docs/OUTPUT_QUALITY.md) for every service; preserve the existing
  [Telegram acceptance guide](../docs/TELEGRAM_ACCEPTANCE.md). Evidence and local limits:
  [Excel quality report](REPORTS/2026-10-08-excel-quality.md).

## PowerPoint quality round — 2026-10-08

- FACT: PR #16 is merged as `ac14b10`; main workflow `37822366757` passed 308 tests.
- MERGED PR #17: Native editable text/tables, readable bounded layouts, normal
  content on dense first/single slides and schema-level density checks using existing one-repair
  handling. Service contract version 2 retains administrator-owned price and enablement.
- PASS: Local lint/format and 35 focused builder/plugin/governance tests; 332 tests collected.
- FAIL / UNKNOWN: Artifact Tool import/render produced all three synthetic slides without
  clipping, but reversed Arabic word order and ignored the table RTL column flag. This renderer
  does not qualify Arabic output. Native PowerPoint behavior remains UNKNOWN, not a passing gate.
- PASS: Head `d94cbe5` workflow `37826017821` and merged main `76613b9` workflow
  `37827248529` passed 332 tests, lint/format, migrations/drift and Compose validation.
- NOT RUN: Live-provider fidelity and Microsoft PowerPoint edit/render acceptance.
  See [PowerPoint quality report](REPORTS/2026-10-08-pptx-quality.md) and PR #17's final CI evidence.

## PDF date rendering round — 2026-10-08

- FAIL: Poppler rendering confirms the existing PDF builder displays source `2026-10-08`
  as `08-10-2026` inside Arabic text, including headings. This is a rendering error.
- MERGED PR #18: Protect matched numeric date order only during bidi shaping, and use
  the same shaped text for width measurement. Dates remain literal, with no parsing,
  conversion, calendar inference or added formatting controls in delivered text.
- PASS: 29 focused local builder/PDF-plugin/governance tests, lint/format. Inspect every page
  of the corrected one-page mixed fixture and four-page 80-record fixture with Poppler.
- PASS: Head `77aba3a` workflow `37827978286` and merged main `b3deb01` workflow
  `37829349423` passed 340 tests, lint/format, migrations/drift and Compose validation.
- NOT RUN: Live-provider source fidelity, new server/iPhone viewer acceptance.
  See [PDF date report](REPORTS/2026-10-08-pdf-dates.md). No contract, version, dependency,
  payment, database or runtime changes are included in this rendering fix.

## PDF-to-Word mixed-content fidelity round — 2026-10-08

- FAIL REPRODUCED: Four real hybrid PDFs pass the old service because selectable text masks
  raster content: ordinary image, inline image, nested Form image and later mixed page.
- MERGED PR #19: Reject raster drawing instructions before AI/output without
  decoding image pixels. Follow invoked Forms with cycle/depth/instruction traversal limits;
  retain text-only Forms and allow unused image resources. Localized intake/error explain scope.
- FACT: Contract version 2; preserve admin price/enablement and generic cancellation/release
  for old pending version-1 orders. No new OCR, provider, database or dependency changes.
- PASS: 24 local helper/plugin/governance tests; hosted lifecycle tests must prove release,
  one notification, no AI/delivery, cleanup and old-order settlement. Full suite collects 355 tests.
- PASS: Head `de90211` workflow `37830310598` and merged main `6415e57` workflow
  `37831298533` passed 355 tests, lint/format, migrations/drift and Compose validation.
- NOT RUN: Real provider/Word fidelity or deployment. This is a
  rejection safeguard, not image reconstruction or full-fidelity conversion qualification.
- Evidence: [mixed-content report](REPORTS/2026-10-08-pdf-word-image-fidelity.md).

## OCR translation numeric fidelity round — 2026-10-08

- FACT: The old translation model validates JSON/text length, but accepts changed amounts,
  dropped identifier zeros, missing/extra numbers and reformatted dates.
- MERGED PR #20: Request-local translation validation compares literal numeric
  tokens and their occurrence counts with the extracted text. Schema instructions preserve
  signs/separators/date notation/percentages and digit script; existing one-repair flow applies.
- FACT: Version 2; unchanged input fields, price/default gates, renderer, provider and financial
  policy. Old pending version-1 work releases; admin settings remain intact.
- PASS: 26 focused local schema/plugin/governance tests; 383 tests collected. Hosted cases
  cover repair, failure release, single capture, cost recording and cached TXT/DOCX delivery.
- PASS: Reviewed head `ea3b7d0` workflow `37832745093` and merged main `6ce0c5e`
  workflow `37862487540` passed 383 tests, lint/format, migrations/drift and Compose validation.
- NOT RUN: Live image/source fidelity, semantic translation and native Word acceptance.
  Matching numbers alone does not verify their associations, names, units or prose.
- Evidence: [OCR translation report](REPORTS/2026-10-08-ocr-translation-numbers.md).

## Excel filter interoperability round — 2026-10-09

- OPERATOR-REPORTED: Main `6ce0c5e` deployed with backup/migrations PASS, healthy application
  containers and `/health` ok. Actual uploaded XLSX retains the four synthetic source rows,
  IDs, dates, blank amount, zero and duplicate row, but Excel on iPhone requests repair and
  the owner reports recovery cannot open it. Native Excel acceptance is FAIL, not qualified.
- FACT: Both worksheet and native-table filters cover exactly the same range in the upload
  and current builder. Three new tests reproduce this filter-ownership defect before the fix.
- FIX ON TASK BRANCH: Remove only the overlapping worksheet filter; keep the native Records
  table and its filter. Existing values, formatting, RTL, print settings and freeze panes stay.
- INFERENCE: This known interop defect may explain the reported failure. Native iPhone
  opening/edit/save/reopen still must confirm the fix; no repaired-output claim is made.
- NOT RUN: Final hosted checks and post-fix native Excel/provider qualification.
- Evidence: [filter interoperability report](REPORTS/2026-10-09-excel-filter-ownership.md).

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
Complete the Excel filter-ownership fix and inspect its source-bound hosted checks.
Retest the same synthetic source in native Excel before considering Excel qualified.
Qualify professional Word, Excel and PowerPoint against supplied source and native Office;
keep literal Word/PDF checks distinct. The all-service quality request supersedes the earlier
Excel/PowerPoint deferral. Continue PDF/OCR fidelity rounds within their approved contracts.
Run the [Telegram acceptance guide](../docs/TELEGRAM_ACCEPTANCE.md) on an available staging
server with a dedicated test account and operator-configured secrets. Use echo first, then
Office/PDF and clear/unclear OCR; inspect reservations, capture/release and file cleanup.
The operator must identify the installation and deployment method before runtime changes.
Keep real-provider quality and billing evidence separate from mocked integration checks.
Do not reopen completed phases without a confirmed finding or invent runtime evidence.

Publication history: [initial permission rejection](REPORTS/2026-10-04-publication.md) and
[authorized import](REPORTS/2026-10-04-import.md).

Hosted evidence and CI correction: [report](REPORTS/2026-10-04-compose-ci.md).
