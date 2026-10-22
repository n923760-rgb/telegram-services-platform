# Source-preserving CV formatting

Baseline main 081de25a0793f5c0ad8f13a15137d37469cccabe, PR #27 merged.
Reviewed workflow 37925068485 and merged-main 37925579559 passed 516 tests,
DB/migration/drift/Compose and actual non-root network-disabled native worker.
Owner requested gradual integration of useful services with outputs worth paying for;
continued implementation/publication/merge authorized after checks.

## Contract and value

Independent cv_formatting plugin, disabled by default, SAR 5.00 administrator-issued
test credit. Structured final name/contact/skills, experience or education required,
optional summary/additional facts. Arabic or English section headings; user writes
the final content. Classic single-column editable Word plus native PDF, using the
existing source-owned template and abstract DocumentRenderer. No AI, career facts,
translation, employment/ATS outcome claim, photo or uploaded template.

Input per-field bounds and 9,000 characters overall; at most 100 lines per section.
All supplied sections retained; no one-page truncation promise. Field rejection
occurs through needs_ai admission before reservation. Existing printable text/date
handling reused; invisible LTR date marks are formatting, not character equality.
Source title trimmed by existing strict model; body whitespace/blank lines retained.
Classic headings supplied by our AR/EN catalogs, never inferred from credentials.

Shared word_pdf_result helper prepares required file pairs with the existing
renderer/storage error semantics and partial-save cleanup. Existing text_to_word_pdf
uses it without contract/version/price changes. Credit capture still requires both
deliveries; retries reuse prepared files. Partial Telegram delivery can duplicate
Word under existing at-least-once policy. TTL cleanup remains the crash fallback.

## Verification

- REPRODUCED visually: Arabic title/body right-aligned but Latin contacts and standalone
  year were left-aligned under content-based direction, giving inconsistent CV edges.
- FIX: Optional generic Word-only alignment auto/left/right, default auto preserves
  existing documents. Apply leading/trailing logical edge after per-paragraph script
  direction; CV selects right for Arabic, left for English. Dates remain LTR.
- PASS: 35 local independent cases: 20 new CV cases, existing Word/PDF pair tests and
  architecture gates. Actual native Arabic/English PDF export, leading-zero phone,
  email, ID, dates, amount and certificate retained. No tables/images/text boxes.
- PASS: Native 90-record multi-page CV retains every unique ID within page bounds.
  Single-page Arabic and English PDF fixtures rendered and visually inspected.
- Added hosted lifecycle: native two-file success/single capture/zero AI cost/cleanup;
  unavailable/timeout/partial-save failure release, cached retry before/after Word
  delivery and invalid content before reserve.
- CI adds Arabic/English CV to the real non-root network-disabled worker image.
- Full DB/Redis/image checks NOT RUN locally; exact-head hosted result retained on
  task PR and required before merge. No new dependencies/migrations or bot/core,
  ledger/order/worker policy changes.
- NOT RUN: Representative customer/native Word/mobile acceptance, live Telegram,
  external recruiting/ATS systems, production deployment or service activation.

Local native runtime remains LibreOfficeDev 26.8 alpha; distribution Writer and
Debian worker qualification are hosted checks. Reuse attribution/process bounds
documented in docs/DOCUMENT_ENGINES.md. No customer data in fixtures.
