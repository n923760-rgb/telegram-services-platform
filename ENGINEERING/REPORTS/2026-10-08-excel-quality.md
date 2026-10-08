# Professional Excel quality slice — 2026-10-08

## Authority and baseline

- OWNER REQUEST: All approved services should provide professional results with native Office
  editability, suitable for a future paid service. This does not authorize payments or paid launch.
- FACT: Live official main is `25529b5216a7d8f37869a6a14f3080b96cc194cc`, PR #15 Word
  date/layout repair. Hosted workflow `37813772656` passed 279 tests and all existing gates.
- FACT: No open PR was present at baseline inspection. Word improvements are retained,
  not recreated. Work is isolated in `feat/professional-excel-quality`.
- OPERATOR-REPORTED: `/health` returned `ok`; deployed SHA is not bound to that latest reply.
  This is runtime health evidence only. No SSH, production user test or deployment here.

## Findings and implementation

- FACT: Existing Excel was a styled range, not a native Excel Table; no displayed title,
  typed date/percentage contract or source-quality preview. Header/title formula safety
  and numeric precision needed coverage beyond body-cell escaping.
- IMPLEMENTED: Visible title separate from native `Records` table; banded rows, frozen
  headers, adaptive sizes, RTL/LTR cell direction, bounded print area, repeating print headers
  and page numbers. No merged cells inside the dataset and no additional worksheets.
- IMPLEMENTED: Optional bounded format metadata (`text`, `number`, `date`, `percent`, `boolean`)
  validated against actual cell types. Only explicit ISO Gregorian dates are converted.
  Legacy plans remain accepted, with text dates unconverted. Invalid dates/precision fail
  schema validation and enter the existing single repair path; builder failures fail safely.
- IMPLEMENTED: Prompt separates records/attributes, keeps missing data null and retains all
  duplicate/source notes. Delivery preview reports missing/repeated cells/rows and brief usage.
- FACT: No new dependency, migration, service, price, payment or financial-policy changes.
  Input contract/version 5 is unchanged; the optional output extension accepts old plans.
  Direct/literal Word and prepared-result recovery paths remain unchanged.

## Evidence

- PASS: `uv sync --locked --group dev`, Ruff lint/format and `git diff --check`.
- PASS: 69 local builder/Office service tests run with `--noconftest` so no production/disposable
  DB fixture is bypassed for an integration claim. Tests reopen the actual XLSX, edit/save/reopen
  a native cell, inspect table XML and reconcile source values; no ZIP-only quality claim.
- PASS: 308 tests collected for hosted execution; collection is not a full integration result.
- COVERAGE: Typed dates/percentages/booleans/numbers, text identifiers/zeros, blanks vs zero,
  duplicate records, title/header/body injection, invalid/ambiguous dates, unsafe precision,
  sanitized-header collision, large table/long note, old continuation without another AI call.
- ADDED FOR HOSTED CI: Five lifecycle cases: normal/one-repair delivery with single capture,
  schema/builder failure release with one notice, cached delivery retry with no new AI call.
- NOT RUN locally: Full PostgreSQL/Redis suite, Docker, actual renderer or Microsoft Excel,
  live Telegram/AI, visual/native table-expansion qualification and production deployment.
- NOT CLAIMED: All-service quality completion, arbitrary formulas/charts/multiple datasets,
  factual fidelity of a live provider, fully editable PDF or full-fidelity PDF reconstruction.

See [output quality gates](../../docs/OUTPUT_QUALITY.md) and the canonical roadmap for remaining
service slices. Hosted source-bound CI evidence must be inspected before merge.
