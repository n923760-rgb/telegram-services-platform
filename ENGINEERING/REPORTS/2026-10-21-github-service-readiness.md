# GitHub reuse for service readiness — 2026-10-21

## Scope and verified baseline

- Owner prioritizes service readiness and authorizes useful GitHub reuse and merging ready work.
- GitHub main verified as `b05d60b907745f48541be521df4bfba11f3ffed6`; its hosted workflow `39640086352` succeeded. Operator pasted deployment output showing that source, successful backup/migrations, healthy API/bot/worker and running monitor. This is operator-reported runtime evidence, not a server session executed here.
- Local task uses an isolated worktree. Existing OpenCV, Camelot, python-pptx, Pillow and RapidFuzz already cover important implementation needs. Installing more projects is not itself an acceptance result.

## Reviewed primary sources and decisions

License identifiers below are repository-level metadata, not a full transitive-dependency or model-weight license audit.

| Upstream | License | Current project fit and decision |
| --- | --- | --- |
| [python-pptx](https://github.com/scanny/python-pptx) | MIT | Already pinned at 1.0.2. Reuse native `Table.columns[index].width` and editable cells to improve uneven document tables now. Reviewed [1.0.2 source](https://github.com/scanny/python-pptx/tree/278b47b1dedd5b46ee84c286e77cdfb0bf4594be), [table API](https://github.com/scanny/python-pptx/blob/278b47b1dedd5b46ee84c286e77cdfb0bf4594be/src/pptx/table.py) and upstream LICENSE. |
| [OpenCV](https://github.com/opencv/opencv) | Apache-2.0 | Already used for bounded document illumination/contrast/sharpening. Next acceptance should exercise weak strokes and colored stamps; no additional installation in this round. |
| [pdfplumber](https://github.com/jsvine/pdfplumber) | MIT | Already a development dependency. Useful for independent PDF text/geometry inspection; not added as another production extractor without difficult-source comparison against current Camelot/pypdf paths. |
| [deskew](https://github.com/sbrunner/deskew) | MIT | Potential image/OCR follow-up; current pyproject requires scikit-image. Defer runtime integration until skewed AR/EN samples establish benefit and preserve corners, stamps and numeric marks. |
| [OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF) | MPL-2.0 | Searchable scanned PDFs are a potential separate output contract. Defer until customer value, resource budget, subprocess limits and component licenses are reviewed. Not required for the existing text-only PDF-to-Word contract. |
| [Docling](https://github.com/docling-project/docling) | MIT | Candidate benchmark for complex document structure. Current upstream has slim and optional conversion backends; assess the actual selected extras, model licenses, memory and fidelity before replacing existing paths. Not installed. |

No third-party implementation is vendored in this round. New project-owned layout logic uses existing public library APIs and Pillow metrics; upstream license files remain part of the installed distributions. Dependency locks remain unchanged.

## Implemented PowerPoint improvement

FACT: Equal-width columns reject a readable four-record table with a short ID, a longer note and a short amount. At the existing 20pt body size the Arabic fixture measures 393.2pt and the English fixture 489.2pt against a 349.2pt body limit.

CHANGE: Compare equal widths with two fixed content-weighted candidates. Measure actual DejaVu glyphs across headers and rows, preserve a 90pt minimum per column, and choose a candidate only when its total measured height is lower. Retain equal widths on ties. The two reproduced fixtures now measure 297.2pt. Serialize those same column widths into the native table, assigning the integer-EMU remainder to the last column so total table width stays exact.

Retain source order, blank cells, literal IDs/amounts/dates, 20pt body and 21pt headers, existing row/card limits, selected slide count, dense-content rejection, RTL and editable output. Prepared output replay and service/admin/payment/provider settings are unchanged.

## Verification and limits

- PASS locally: 101 focused PowerPoint checks, including 11 new cases; 17 existing native compatibility assertions executed in a DB-free harness; three architecture gates; global lint/format and whitespace checks.
- Native regression covers AR/EN uneven tables, 1–4 columns, first/last long columns, multiline headers, literal source cells, geometry and edit/save/reopen. Hosted worker qualification gains AR/EN fixtures with network disabled.
- PostgreSQL, Docker and LibreOffice are unavailable locally. Full migrated test suite and non-root worker qualification require hosted CI before merge. Native structure and font metrics do not certify actual Microsoft PowerPoint/mobile appearance or real-provider narrative quality.
- No production deployment in this round. The operator's installed baseline remains b05d60b until separately updated.

## Remaining readiness order

1. Run the updated isolated 29-case service acceptance suite on the operator's source; recheck PDF-to-Word and image enhancement, then all 16 services. Do not treat scripted models or healthy containers as live content acceptance.
2. Inspect real AR/EN/bilingual CV, Word/PDF and all PPTX slides, including Office/mobile edit/save/reopen and long-table pagination.
3. Benchmark difficult OCR/table/image fixtures against the current tools before choosing another backend. Preserve no-invention and no-meaningful-improvement rejection guards.
4. Qualify customer draft review/editing, delivery recovery and chosen payment flow before paid rollout. Owner prices/terms and actual payment/refund evidence remain separate decisions.
