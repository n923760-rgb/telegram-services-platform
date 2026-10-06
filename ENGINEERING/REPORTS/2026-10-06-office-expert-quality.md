# Office Expert Quality v1 — correction to shared builders

Date: 2026-10-06
Scope: correct a mis-scoped uncommitted change and implement the quality upgrade in the shared builders.

## Finding

- FACT: Prior uncommitted work added a new customer-facing `office_expert` plugin (new service
  slug, SAR 8 price, three input fields, 7 i18n keys, README rows and two integration tests).
  This misunderstood the task, which required improving the existing shared builders without
  adding a service slug.
- FACT: The plugin's i18n keys, README rows and integration tests were reverted. Existing slugs
  `text_to_office`, `text_to_pptx` and `text_to_pdf` are preserved unchanged.
- BLOCKED: The `app/services/office_expert/` directory could not be physically deleted in this
  environment (the sandbox denies `rm`, `find`, `python3 -c` and `git clean`). A human must run
  `rm -rf app/services/office_expert` before any test run or merge; until then
  `app/services/registry.py` auto-discovers the stale slug and rejects it for missing i18n keys.

## Changes

- Reverted the 7 `expert_*`/`pptx`/`pdf` i18n keys from `app/i18n/ar.json` and `app/i18n/en.json`.
- Reverted the `README.md` and `README_AR.md` service references.
- Removed the two `office_expert` integration tests from `tests/test_real_services.py`.
- Added `app/builders/direction.py`: content-based Arabic/Latin detection (`has_arabic`, `is_rtl`)
  so builders follow the dominant script instead of forcing RTL everywhere.
- `app/builders/word.py`: professional title/headings, 2.2/2.5 cm margins, 1.15 line spacing,
  paragraph/run-level bidi and complex-script fonts, bullets, and a centered PAGE field footer.
- `app/builders/excel.py`: adaptive sheet direction, per-cell alignment, bordered header styling,
  wide-glyph-aware column widths, row heights, freeze panes, auto filter, and preserved
  formula-injection protection.
- `app/builders/pptx.py`: centered title slide, content slides with adaptive font sizing,
  bounded shapes and per-paragraph RTL/LTR.
- `app/builders/pdf.py`: registered DejaVu regular/bold with fallback path lookup, RTL/LTR styles,
  mixed-content bidi rendering and a centered page-number footer.
- Added `tests/test_builders.py` covering direction detection and re-opening DOCX/XLSX/PPTX/PDF
  outputs for Arabic and English content.

## Verification

- NOT RUN: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .` were not executed
  in this environment (no disposable `_test` database/Redis and no authorized venv execution).
  No passing run is claimed.
- Existing `tests/test_file_layers.py` builder assertions were reviewed against the new builders and
  are expected to remain satisfied (content, `w:bidi`, `rightToLeft`, injection guard, bounded
  shapes, multi-page PDF).

## Boundaries preserved

No wallet/order/provider/storage change. No bot/core service-specific branching. No payment change.
No external assets or fabricated content. No secrets touched. Nothing deployed, committed or pushed.
