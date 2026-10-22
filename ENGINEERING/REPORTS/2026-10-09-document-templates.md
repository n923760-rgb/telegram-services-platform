# Professional template and structural output gate

Baseline: official main `7b72ac4` (PDF Arabic numeric extraction, PR #23).
Scope: first bounded implementation of the owner's approved document-engine direction.
Open governance-reference PR #21 is unrelated and remains untouched.

## Changes

- Source-owned reusable `docxtpl` professional Word template, escaped customer values,
  request-local renderers and native tables inserted at opaque slots in source order.
- Explicit internal template switch for professional Word; literal requests unchanged.
- Shared structural output gate called by DOCX/XLSX/PPTX/PDF builders before storage.
- Only docxtpl/Jinja2 added; existing dependency versions retained. Update both locks
  because production Docker installs `requirements.lock`, not `uv.lock`.
- Record candidates and qualification order in `docs/DOCUMENT_ENGINES.md`; do not
  install unused heavy tools. No copied upstream templates or Office skill code.

## Evidence

- PASS: locked development sync, lint, format, whitespace and 406 collected tests.
- PASS: 117 database-independent builder, schema, Office-plugin and architecture checks
  run from a temporary copy outside the DB-autouse fixture. The temporary governance
  copy explicitly points ROOT to the actual repository; repository tests are unchanged.
  This is not evidence of full local integration success.
- PASS: English/Arabic template values including XML/Jinja-looking text remain literal;
  dates, identifiers, native table order, adjacent-table separation and hidden titles.
  Concurrent requests use distinct documents; only immutable source template bytes cache.
- PASS: LibreOffice/Poppler render inspection of Arabic one-page fixture and every page
  of a 55-row three-page fixture; intact identifiers/dates, repeated headers and footer,
  no clipped records or blank terminal page. Synthetic plans, not real provider output.
- Full lifecycle regression added: corrupt final DOCX before gate; require failure,
  full credit release, zero delivery, one failure notice and storage cleanup.
- NOT RUN locally: PostgreSQL/Redis integration, migrations/drift, Docker build, Telegram,
  actual provider and native Microsoft Office/phone acceptance. Hosted CI must run the
  full suite including the new lifecycle test before merge.
- No server deployment or service enablement was performed here.
