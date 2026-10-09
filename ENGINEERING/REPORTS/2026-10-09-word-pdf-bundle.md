# Native source-owned Word/PDF bundle

Baseline main b1f86fe05da7c01f9cd5bac5de8b134c369ae5e4, PR #26 merged.
Reviewed workflow 37920858118 and merged-main 37921298499 passed 481 tests,
all architecture/DB/Compose checks and actual non-root OCR worker image.
Owner authorized continued implementation/publication/merge after checks.

## Scope

Independent text_to_word_pdf plugin, default disabled, SAR 3.00 test credit.
Final text + optional title, professional source-owned template, editable Word
and native PDF from the same DOCX. No AI provider/cost/fallback, translation or
rewriting. Existing service contracts/prices remain unchanged. No uploaded Office
files: injected DocumentRenderer accepts typed WordDocument; builder owns bytes.
No bot/core/ledger/order/job changes, Python dependencies or migrations.

LibreOffice Writer is installed in the existing document-worker target only.
Fresh request-local profile with macro security level 3; fixed headless writer
export, no listener or customer options. Shared per-loop capacity with Tesseract;
queue timeout transient, existing bounded job retries. Native child: 1 GiB address
space, 60 CPU seconds, 90 wall seconds, 10 MiB output file, zero core dump, clean
environment. Generic execution helper kills/reaps process groups before temporary
cleanup on success/failure/cancellation; OCR contract/limits preserved. Trusted
native execution, not a security sandbox or aggregate worker resource quota.

12,000 input characters, optional single-line 200-character title, 50 output pages,
10 MiB artifacts. Structural output gates, both results before first save, partial
save rollback. Unreferenced crash/deletion leftovers rely on existing TTL cleanup.
Both required files before capture; cached delivery avoids another export. A send
failure after Word was accepted can resend Word under existing at-least-once policy.

## Findings and verification

- REPRODUCED: First native Arabic sample displayed 09-10-2026 while the source and
  pypdf logical extraction showed 2026-10-09. PNG inspection detected the defect.
- FIX: Reuse existing Word date-direction formatting for the new renderer. Invisible
  LTR marks are added around date runs; visible text/numbers are not rewritten.
  Formatted DOCX is therefore not character-for-character identical to source text.
- PASS: Native glyph-position regression failed before and passed after the fix.
- PASS: 25 new independent renderer/plugin/execution cases; 61 checks including
  existing OCR and architecture gates. Lint/format/diff checks. Suite collects 516.
- PASS: Actual local LibreOfficeDev 26.8.0.0.alpha0, build
  2c87e51eeaa2b413ff4ae097b2705eea1995d8e5. Word text, leading-zero ID, amount/date,
  hidden optional title, literal template-like text and blank lines checked.
- PASS: A4 page dimensions, embedded fonts, 55 unique IDs/dates/amounts across a
  three-page Arabic table, repeated headers and glyph bounds. Single-page bilingual
  sample and all three table pages visually inspected after the correction.
- Added hosted lifecycle: real native success/single capture/zero AI usage/cleanup;
  unavailable/timeout/bad/oversized export and partial save release; cached retry
  before/after Word delivery; busy retry and pre-reservation validation.
- Full DB/Redis and image build NOT RUN locally. CI additionally runs actual native
  tests on distribution Writer and builds/non-root tests the worker with --network
  none, including Word/PDF + 55-row table. Require exact-head success before merge;
  final hosted run IDs retained on the task PR.
- NOT RUN: Representative customer content, all native Office engines, arbitrary
  uploaded Office parsing, Excel/PowerPoint export, production/VPS/staging deployment,
  real Telegram journeys, server load/throughput or service enablement.

License/source attribution and process limitations: docs/DOCUMENT_ENGINES.md.
