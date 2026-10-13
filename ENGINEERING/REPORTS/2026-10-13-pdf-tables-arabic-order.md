# Explicit visual-order Arabic recovery for PDF tables

## Authority and baseline

Owner accepted continuing the confirmed PDF-to-Excel Arabic defect review.
Baseline main 4a852dc. Operator supplied an actual XLSX from the generated
Arabic table PDF: numeric cells and leading zeros survived; Arabic presentation
forms remained in visual order and displayed incorrectly in LibreOffice.
This is one source encoding example, not proof all Arabic PDFs fail.

## Bounded change

- Service v3 adds an optional explicit `arabic_order=visual` choice after language.
  Skip/legacy inputs preserve extracted cells. Direction cannot be inferred
  safely from presentation forms alone; no automatic reversal is introduced.
- Only cells composed entirely of Arabic presentation-form letters, spaces and
  newlines are recovered, line by line. Reverse glyph order before compatibility
  expansion so lam-alef ligatures retain their internal order. Reject unfamiliar
  non-letter expansions. Normal Arabic, Latin, digits, punctuation, combining
  marks and mixed cells remain byte-for-byte unchanged.
- Data contains the selected recovered display text. Source retains exact
  extraction, all rows/header rows/columns/references remain stable. Data notes
  show changed and untouched presentation-form cell counts. Confirmation explains
  the choice and the remaining limitations.
- No extraction retry, provider request, dependency, database migration, price,
  service activation or pause change. Existing cached artifacts replay; stale
  unprepared v2 jobs cancel via the existing credit-release path.

## Evidence

- PASS locally: 57 focused normalization/plugin/architecture cases; global ruff lint/format
  and diff checks. Non-DB tests run with an alternate bytecode cache.
- PASS locally: rebuilding the operator-supplied extracted rows recovers the
  three product names and preserves identifiers/source exactly. Native Camelot
  subprocess unavailable in this workspace; hosted native CI is required.
- Added hosted native extraction/confirmation/export test with zero AI calls,
  exact Source and recovered Data; administrator override and old-job/cache
  compatibility tests. Full PostgreSQL/Redis/native CI required before merge.
- Actual server v3 deployment and repeat Telegram acceptance NOT RUN.

## Limits

Explicit selection asserts the source direction; it does not certify it.
Mixed cells remain unresolved intentionally. This does not provide OCR, Arabic
translation, automatic header detection, semantic repair or cell correctness.
Provider remains paused; historical uncertain provider cost remains unresolved.
