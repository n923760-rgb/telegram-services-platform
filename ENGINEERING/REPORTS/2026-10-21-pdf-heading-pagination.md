# Keep PDF section headings with their opening content

Date: 2026-10-21 (Asia/Riyadh). Baseline: official main
`070492b46d871f9465693ba50f971c8686429694`.

## Finding and bounded change

FACT: The shared ReportLab PDF builder emits each wrapped heading line as an
independent paragraph. A document with 20 short source paragraphs puts the next
section heading at the foot of page one and its opening content on page two.
The problem reproduces in Arabic and English, including bullet-only sections and
wrapped headings. Twelve new assertions fail before the fix; one whitespace/
heading-only compatibility case already passes.

CHANGE: Link the heading prefix (all its rendered lines and source-leading blank
spacers) to the first content flowable with ReportLab's existing keep-with-next
mechanism. The remaining section can paginate normally. A heading-only section
does not attach itself to a different section. Oversized prefixes retain the
renderer splitting fallback, preserving long blank source sequences without a
layout error; a prefix larger than a page cannot be promised to stay together.

No source text, numeric/contact/date tokens, heading font, body spacing, margins,
footer, source validation, service schema/version, price or activation changes.
Existing prepared files replay unchanged; newly built Text PDF output receives
the pagination fix. No provider calls or financial/runtime policy changes.

## Evidence and checks

- PASS: 13 new real-export page/glyph/source tests. Cover AR/EN paragraph/bullet
  openings, leading blank lines, multi-line headings, long sections across at
  least five pages, heading-only sections, oversized whitespace, content counts,
  page bounds and unchanged input models.
- PASS: Four synthetic before/after PDFs rendered with Poppler; all eight pages
  visually inspected. Before: heading at page-one foot, body alone on page two.
  After: heading and first content line at page-two top in both languages. Source
  records, numbers, margins, direction and page numbers remain visible.
- Local broader run: 116 PASS (includes the 13 new cases), plus 30 unrelated
  setup ERROR_ENV in existing PDF-to-Word fidelity tests because PostgreSQL at
  the configured local test port refuses connections. No local full-suite PASS.
- PASS: Eight existing PDF date/wrapping/source assertions in a DB-free harness;
  three executable architecture gates; global ruff lint/format/diff and embedded
  workflow Python syntax. Counts overlap and are not an aggregate test total.
- PASS LOCALLY: Four new native-worker assertions for AR/EN short/wrapped
  headings using reopened PDFs. Add them to the existing non-root, network-off
  worker qualification; the actual container and full DB suite require hosted CI
  success on the exact candidate before merge.

The PDF skill informed real-page rendering and visual inspection. Synthetic
fixtures verify this pagination defect, not every possible PDF layout, title-page
behavior or live-provider semantic quality. No live Telegram, mobile/Office
certification, production setting or deployment action.
