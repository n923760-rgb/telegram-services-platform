# Master engineering roadmap

## Telegram mobile UI review — 2026-10-10

- OWNER AUTHORITY: Fix screenshot issues and check related interface paths; continuous verified merge authority persists.
- VERIFIED BASELINE: Main 1421359 / PR #40; post-merge workflow 38075628816 SUCCESS.
- CURRENT SLICE: Adaptive full-width choice labels, separate cancellation/approval rows, display-only short references, complete UTF-16 preview splitting and localized PDF-table reviews independent of file heading language.
- Source UUIDs/ownership/financial policy remain authoritative; legacy previews retain fallback. Full IDs remain in order details for support.
- PASS LOCAL: 63 independent UI/provider/PDF-table/architecture checks; 900 tests collected. Exact published head requires full hosted lifecycle and seven native gates before merge.
- Evidence: [mobile UI report](REPORTS/2026-10-10-mobile-ui.md).
- NOT RUN: Updated device/font screenshots, live AI heading qualification, server update.

## PDF tables to Excel — 2026-10-10

- OWNER AUTHORITY: Complete independent development slice; prior verified continuous merge authority persists.
- VERIFIED BASELINE: Main 822efbd / PR #39; 829 tests and six native worker gates passed on its published head.
- CURRENT SLICE: Default-disabled `pdf_tables_excel`, Camelot 2.0.0, bounded text-only PDF extraction with lattice/stream; source-preserving Excel and mandatory structure confirmation.
- Optional AI proposes headings only; original cells remain literal text in Data/Source sheets with stable references and Review metrics. Metrics do not prove extraction correctness.
- PASS LOCAL: 44 independent plugin/native/architecture checks; full hosted lifecycle/native qualification required before merge.
- Evidence and constraints: [PDF tables report](REPORTS/2026-10-10-pdf-tables-excel.md).
- NOT RUN: Representative customer PDF/mobile Excel/live AI/Telegram, server installation, activation and commercial prices.

## Extractive source-bound key points — 2026-10-10

- OWNER AUTHORITY: Continue independent useful services under prior verified merge
  instruction. Current bounded slice implements extractive points, not free-text claims.
- VERIFIED BASELINE: Main e624000 / PR #38. Post-merge workflow 38070202160,
  job 114265871891: 785 tests, migration/drift, Compose and all six native worker gates PASS.
- CURRENT SLICE: Default-disabled `text_summary`: 12000 characters, 2–80 nonempty
  source lines (one paragraph per line); short/standard selects at most 3/7 points,
  always fewer paragraphs than the source. Original source strings only in source order.
- AI returns strict unique known integer IDs only; no AI-produced prose is delivered.
  Heading language AR/EN does not translate source. Chat points plus owned UTF-8
  summary-source.txt containing selected points and all numbered source paragraphs.
- Semantic importance, coherence and omitted context remain unqualified; exact quotes
  do not establish summary completeness or customer value. Live provider/user acceptance
  required before activation; rewriting/study questions remain separate proposals.
- PASS LOCAL: 90 independent source/service/architecture checks, lint/format/diff;
  829 tests collected, including 30 new unit cases and 14 new DB lifecycle cases.
- LOCAL/HOSTED evidence: [key-points report](REPORTS/2026-10-10-text-summary.md).
  Exact published head must pass full lifecycle/native CI before authorized merge.
- NOT RUN: Live provider/Telegram, server update, pricing and activation.

## Independent proofreading and rewriting — 2026-10-10

- OWNER AUTHORITY: Continue the proposed independent writing/proofreading service;
  prior continuous verified merge instruction persists. No deployment/activation implied.
- VERIFIED BASELINE: Main 68ae143 / PR #37. Post-merge workflow 38069092755,
  job 114262659938: 740 tests, migration/drift, Compose, all six actual native worker gates PASS.
- CURRENT SLICE: Default-disabled `text_editing`: original-language Arabic/English
  pasted text, proofread-only or rewrite; tone intake shown only for rewrite.
  12000 characters/80 nonempty source lines; output bounded to 24000 characters.
- Exact source ID coverage/order, per-line numeric/contact-token occurrence counts,
  original blank lines and owned UTF-8 revision.txt. Existing AI budget/one repair,
  cached delivery and financial policy reused; no new vendor SDK/dependency/migration.
- Structural validation cannot prove language, meaning, names, negations, qualifiers
  or promises. Draft needs customer review and real-provider semantic qualification.
- PASS LOCAL: 82 service/source/architecture checks and lint/format; 785 tests collected.
- LOCAL/HOSTED evidence: [editing report](REPORTS/2026-10-10-text-editing.md).
  Exact published head must pass hosted lifecycle/native gates before authorized merge.
- NOT RUN: Live AI/Telegram, server update, operator pricing and activation.
  Next bounded proposals: source-bound summaries/revision and actual-fact CV writing.

## Independent source-bound text translation — 2026-10-10

- OWNER REQUEST: Add separately discoverable text translation and useful paid services;
  preserve modular architecture and existing source/payment/quality boundaries.
- VERIFIED BASELINE: Main 99f4b6f / PR #36; post-merge workflow 38066931365 passed
  708 tests and every existing financial/native document qualification gate.
- CURRENT SLICE: Default-disabled `text_translation`: pasted text, AR/EN target, four
  existing styles; 12000 input characters/80 nonempty lines, 24000 output characters.
- Strict source IDs exactly once, numeric-token multiset per line, original ordering
  and blank lines retained; text and UTF-8 TXT delivery. Shared existing numeric validator
  moved without changing the OCR contract; old imports retained for compatibility.
- PASS LOCAL: 49 independent service/schema/OCR-number/architecture checks; lint/format.
  Full lifecycle/financial/DB/native hosted gates required before authorized merge.
- NOT RUN: Live semantic/style/names/links qualification, Telegram/server deployment,
  operator prices and paid launch. Structural/source-ID checks are not semantic proof.
- Next proposals and existing deliverables: [service portfolio](../docs/SERVICE_PORTFOLIO.md).
  Evidence: [translation report](REPORTS/2026-10-10-text-translation.md).

## Dedicated Telegram test-server qualification — 2026-10-10

- VERIFIED BASELINE: main a0ab15c includes Stars PR #32 and corrections #33–#35.
  Workflow 37992934577/job 114031500940 passed 696 tests, lint/format, migration/drift,
  Compose and all six actual non-root/network-disabled native worker qualifications.
- CONFIRMED GAP: All four runtime processes constructed production-only Telegram bots;
  the documented dedicated-test-environment Stars journeys could not select the test API.
- CURRENT SLICE: Explicit validated `TELEGRAM_API_ENVIRONMENT=production|test` and one
  provider bot factory, used by API/polling/worker/monitor for methods and file URLs.
  Production remains the default; no automatic endpoint fallback or Stars activation.
- Verification and boundaries: [test-server report](REPORTS/2026-10-10-telegram-test-environment.md).
- NEXT: On an identified isolated installation, execute the source-bound
  [Stars acceptance guide](../docs/STARS_ACCEPTANCE.md), then representative provider/native
  Office output, restart/recovery, support, alerts and off-server backup/restore journeys.
  These require private operator configuration; no live payment/deployment evidence claimed.

## CSV organization and review — 2026-10-09

- MERGED BASELINE: Main f4dc678 includes PR #30; workflow 37933829212 passed
  598 tests, migration/drift, Compose and all native network-disabled worker checks.
- CURRENT SLICE: Independent default-disabled csv_review turns pasted bounded CSV
  into Data/Source/Review Excel tables. Explicit delimiter and optional ASCII edge
  trimming; source IDs/numbers/dates remain text. No AI, deleted rows or inferred totals.
- Stable generated record references remain attached during sorting; review reports
  empty fields, full-record duplicates and changed source-column numbers.
- PASS: 31 local unit cases, lint/format/diff. Full lifecycle/worker qualification
  required on the exact published head before authorized merge; evidence on the PR.
- NOT RUN: Production deployment, Telegram/staging, representative Excel/mobile
  qualification and actual customer willingness to pay. Test-credit price only.
- Evidence: [CSV review](REPORTS/2026-10-09-csv-review.md).

## Current service expansion verification — 2026-10-09

- MERGED: CV formatting PR #28 at 00848f7; reviewed workflow 37927874220 and
  merged-main 37928968731 passed 545 tests/native Arabic-English CV worker checks.
- MERGED: Images PDF PR #29 at 30ec14c; reviewed workflow 37930551954 and
  merged-main 37931140860 passed 571 tests/native ordered pixel checks.
- MERGED PR #30 at f4dc678: Source-bound meeting-note categories, every source ID visible
  in review, mandatory approval before native Word/PDF; no invented fields/content.
- PASS: Local execution recovered; exact implementation head 27423a9 passes 73
  independent cases (CV 20/images 19/minutes 19/Word-PDF 12/governance 3), lint/format.
- PASS: Native AR/EN minute PDFs and both pages of synthetic receipt/review image PDF
  rendered and visually inspected. Earlier local unavailability is historical below.
- PASS: PR #30 final-head workflow 37933171985 and merged-main 37933829212
  passed 598 tests and all native worker checks. Live AI
  category accuracy, representative/native Office/mobile/Telegram/staging/server
  deployment and service activation remain separate NOT RUN gates. All new plugins
  default disabled; SAR values remain administrator-issued test credit.
- Service contracts and next priorities: docs/SERVICE_PORTFOLIO.md; see linked reports.

## Source-bound meeting note organization — 2026-10-09

- MERGED BASELINE: Images PDF PR #29, main `30ec14c`, reviewed
  workflow `37930551954` passed 571 tests and network-disabled ordered image checks.
- CURRENT SLICE: Independent disabled `meeting_minutes` classifies existing note
  IDs only; every note exactly once, no generated assignees/deadlines/free text.
- Customer reviews counts/sample categories before Word/PDF creation. Confirmation
  resumes without another AI call; source notes retained with traceable IDs.
- Prompt treats ambiguous/mixed notes as review. Category correctness still needs
  live-provider/customer acceptance; structural coverage is not semantic proof.
- Uses existing job AI budget/one repair, confirmation, abstract renderer and
  financial policy. 80 notes/12,000 characters, no audio/transcription or translation.
- Local execution unavailable: local/visual checks NOT RUN. Exact-head hosted
  lifecycle/native worker checks required before merge; enablement remains separate.
- Evidence: [meeting minutes](REPORTS/2026-10-09-meeting-minutes.md).

## Ordered images to PDF — 2026-10-09

- MERGED BASELINE: CV formatting PR #28, main `00848f7`, reviewed workflow
  `37927874220` passed 545 tests and native Arabic/English CV worker checks.
- CURRENT SLICE: Separate disabled-by-default `images_to_pdf`, one image per page
  in supplied order, A4 portrait/landscape/automatic orientation and 10 mm margins.
  EXIF orientation, alpha on white, no cropping/aspect distortion or new AI call.
- Limits: five files, 10 MiB each/20 MiB total, 20 million total decoded pixels,
  10 MiB output. Decode to pixels before embedding; original metadata omitted.
- Existing Telegram intake normalizes images to 1024 pixels and JPEG quality 88;
  this service does not restore source resolution or promise scan enhancement.
- New tests target exact embedded pixels/order/geometry, rotation/transparency,
  bounds/rejection, native lifecycle capture/release/ownership/cleanup/cached retry.
- Local execution became unavailable during this round. Local image tests/visual
  inspection NOT RUN; hosted exact-head checks required before merge and retained
  on the task PR. Representative/mobile/client/staging acceptance remains NOT RUN.
- Evidence: [images PDF report](REPORTS/2026-10-09-images-pdf.md).

## Valuable service expansion — 2026-10-09

- OWNER DECISION: Integrate useful services gradually; paid value means a clear usable
  deliverable, explicit source-preservation rules and source-bound quality checks.
  No blanket deployment/enablement or untested tool-installation claim.
- MERGED BASELINE: PR #27, main `081de25`; reviewed workflow `37925068485` and
  merged-main `37925579559` passed 516 tests and actual native worker image checks.
- CURRENT SLICE: Independent `cv_formatting` turns final structured career details into
  a classic single-column Word/PDF pair, with Arabic/English headings and no AI or
  invented qualifications. Generic optional Word alignment, default auto unchanged.
- PASS locally: 35 independent checks; native bilingual fixtures visually inspected,
  90-record multi-page CV retained. Hosted lifecycle/image checks required before merge.
- NEXT: Bounded ordered images-to-PDF with A4 fit/original aspect ratio and EXIF handling.
- Remaining premium candidates and qualification criteria: [service portfolio](../docs/SERVICE_PORTFOLIO.md).
- Evidence: [CV formatting](REPORTS/2026-10-09-cv-formatting.md).

## Native Word/PDF bundle — 2026-10-09

- MERGED BASELINE: PR #26 at `b1f86fe`; reviewed workflow `37920858118` and
  merged-main workflow `37921298499` passed 481 tests, migrations/drift, Compose
  and non-root worker image build with actual Arabic/English/mixed OCR.
- NEXT SLICE: Separate default-disabled `text_to_word_pdf` formats final text with
  the source-owned Word template and exports that same DOCX through LibreOffice.
  No AI calls, rewriting, translation, uploaded Office parsing or core service branches.
- Shared native capacity serializes OCR/export; per-request profile and temporary
  files, fixed headless export, CPU/address-space/output/wall limits and group cleanup.
- REPRODUCED/FIXED: Native PDF visually reversed an Arabic-adjacent ISO date despite
  correct text extraction. Existing date-direction formatting fixes the new renderer;
  an actual glyph-position regression test failed before and passed after the fix.
- PASS: 25 new independent cases plus existing OCR/architecture regressions: 61 cases;
  single-page Arabic/bilingual sample and all three pages of a 55-row table inspected.
- Full suite collects 516 tests. Exact-head hosted lifecycle/image checks required
  before merge; real Telegram, native Office and server deployment remain NOT RUN.
- Evidence: [Word/PDF bundle](REPORTS/2026-10-09-word-pdf-bundle.md).

## Local printed-text OCR — 2026-10-09

- MERGED BASELINE: PR #25 at `02d11c8`; exact-head workflow `37918022653`
  and merged-main workflow `37918332000` passed 439 tests and all existing gates.
- NEXT SLICE: Independent default-disabled local OCR plugin, injected document provider
  and worker-only Tesseract packages. No AI calls, translation or automatic fallback.
- Limits: five images/20 MiB total, existing 1024-pixel normalization; serialized
  subprocesses with CPU/memory/output/wall limits and cancellation cleanup.
- PASS: 33 local independent tests, including actual Arabic/English/mixed native OCR
  and exact English identifier/amount/date matching; full suite collects 481 tests.
- Hosted lifecycle, migration/drift, Compose and actual worker image checks required
  before merge. Representative images, Telegram staging and deployment NOT RUN.
- Evidence: [local OCR report](REPORTS/2026-10-09-local-ocr.md).

## Deterministic PDF utilities — 2026-10-09

- MERGED: PR #24 at `27d67a6`; exact-head workflow `37917138383` passed 406 tests,
  lint/format, migrations/drift and Compose. Template and structural gate in main.
- NEXT SLICE: Registry-discovered `pdf_tools` merges PDFs and extracts selected pages
  without AI, using the existing pypdf library. Native page text/images/geometry retained.
- Limits: five files, 10 MiB each/20 MiB total, 200 source pages; explicit source order.
  Forms/signatures unsupported. New service remains disabled until operator acceptance.
- No bot/core branches, dependency, migration, existing price or financial-policy change.
- PASS: 24 local independent cases and lint/format; 439 full tests collected. Hosted
  capture/release/ownership/retry checks required before merge; no deployment performed.
- Evidence: [PDF utilities](REPORTS/2026-10-09-pdf-tools.md).

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
5. FACT SAR wallet credits remain test credits; separate direct Stars checkout is default-disabled and requires source-bound Telegram acceptance.
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

Owner's 2026-10-09 completion request authorizes the independent direct Stars V1 round.
Scope: existing registered services and generic customer/admin/payment/recovery flows.
See [design](../docs/STARS_DESIGN.md) and [acceptance](../docs/STARS_ACCEPTANCE.md).
Local lint/source checks and hosted PostgreSQL tests must pass before authorized merge.
Do not mark real Telegram purchase/refund, provider quality, or server deployment complete
without their actual evidence; future portfolio candidates remain separate work.

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
