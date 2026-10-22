# CSV organization and review — 2026-10-09

## Contract and value

- Baseline main f4dc678, merged meeting minutes #30, 598 hosted tests/native checks.
- Independent registry plugin csv_review, version 1, disabled by default, SAR 3.00
  administrator-issued test credit. No AI/dependency/migration/core policy changes.
- Input is pasted CSV text, NOT an uploaded CSV/XLSX file. Existing generic upload
  acceptance stays unchanged. Explicit comma/semicolon/tab delimiter, Arabic/English
  report headings and preserve/trim edge spaces/tabs. No automatic delimiter guessing.
- Limits: 12,000 characters, 1–500 records after a header, 1–20 source columns,
  80-character headers, 500-character cells and at most 10 cell newlines. Reject
  malformed quotes, ragged records, invalid controls and normalized header collisions
  before reserving credit. Existing printable validation normalizes CRLF/CR to LF;
  a leading BOM is omitted. Empty CSV lines after the header become all-empty records.
- Native editable Excel tables in Data/Source/Review with filters, frozen headers,
  wrapping, RTL where applicable, repeated print headers and source-owned styling.
- Source retains parsed original cell/header values; Data strips header whitespace
  and optionally only ASCII spaces/tabs at cell edges. No row is deleted or reordered.
  Blank fields display as blank cells; zeros, leading zeros, dates and formula-looking
  content remain exact strings. No inferred numeric/date types or financial totals.
- A generated reference column is appended to Data/Source with a unique heading.
  It is metadata, not a supplied business field, and travels with native table sorting.
- Review has static counts and a row for EVERY source record: reference, blank source
  column numbers, duplicate's first record reference, changed source column numbers.
  Duplicate equality compares entire post-rule records, including all-empty rows.
  Whitespace-only cells are not blank in preserve mode. Column numbers exclude the
  appended reference. Review does NOT update after customer edits; labeled in the file.
- Source-like expressions are explicitly serialized as strings, without modifying
  their content with apostrophe prefixes, Excel formulas, links or external parts.
- Reuses existing Excel builder/structural quality gate and owned storage. Bounded
  assembly runs in a thread; not a subprocess sandbox, aggregate quota or timeout.
  File-size/storage quotas and financial delivery/capture/release remain generic.

## Verification

- PASS locally: 31 independent tests including exact IDs/zeros/strings, original vs
  trimmed whitespace, full duplicate/empty-record counts, native table refs/styles,
  original/header collisions, strict bounds/controls, quoted comma/tab/semicolon,
  multiline/BOM/CRLF, formula-looking literals after save/reopen, owner denial,
  stable references and all 500 records. Lint/format/diff passed.
- Six new hosted lifecycle cases cover AR/EN actual output, zero provider calls/cost,
  one capture after delivery, file retention cleanup, render/save failure release,
  cached-delivery retry without generation, and bad input before reservation.
- Worker checks reopen the actual XLSX under non-root/network-none and assert IDs,
  zeros, source whitespace, formula-safe exact strings and duplicate references.
- Historical local test failures uncovered unsupported openpyxl shallow table copy
  and invalid cross-workbook style IDs; fixed by transferring tables and copying
  style components. No weakened assertions. CSV language choices reuse existing keys.
- Hosted checks required on exact PR head; run URLs and final results retained on PR.
- PASS locally: Actual AR/EN XLSX samples exported through native LibreOffice Calc,
  all three sheets per language rendered and visually inspected. IDs 00123/00017,
  zeros, amounts, dates, safe =1+1 literal and audit references were legible. Minimum
  column width adjusted to avoid splitting Customer mid-word. Native Calc is not
  representative Excel/mobile acceptance; full DB/Redis/Docker checks run in CI.
- Full suite collects 635 tests (37 new). No live Telegram/provider/server evidence.

## Activation

Default disabled. Operator must try representative pasted Arabic/English data in the
bot and inspect the actual Excel file before enabling. No production update, Stars
payment integration or commercial pricing qualification is part of this change.
