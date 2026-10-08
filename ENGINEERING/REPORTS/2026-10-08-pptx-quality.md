# Native PowerPoint quality round — 2026-10-08

## Authority and baseline

OWNER REQUEST: Continue professional, editable output improvements across approved services.
FACT: Main `ac14b1097a78c590602bb2f09501df750a6a325c` contains merged Excel PR #16.
Its post-merge workflow `37822366757` passed 308 tests. Main and open PRs were checked before
publication. This round authorizes a reviewable PowerPoint PR, not merge or deployment.

## Bounded implementation

- Native editable text and tables; 16:9, visible hierarchy and slide numbering.
- Cover only for a concise first slide in a multi-slide deck. Dense first and single slides
  keep normal content layout; the builder preserves the validated slide count.
- Source-bound provider instructions preserve names, IDs, amounts, dates, notes and duplicates.
  Tables use strings, 1–4 columns and 1–6 rows, with blank cells distinct from zero.
- Existing DejaVu font/Pillow dependency estimates density before export. Titles use 32/42 pt,
  body 20–26 pt, table cells 20/21 pt. The 12 pt footer is separate. No automatic truncation,
  added slides or shrinking body below 20 pt; invalid plans get the existing one repair.
- XML-safe bounded plans, per-paragraph language/direction and native table RTL flag.
  No charts, images, branding, formulas, new dependencies, financial policy or provider changes.
- Version 2 prevents silently running old pending orders under changed semantics. Registry
  synchronization preserves administrator price/enablement; old pending reservations release.

## Evidence and limits

PASS: `uv sync --locked --group dev`, Ruff lint/format and 35 focused tests (builder, plugin,
governance). Full suite collected 332 tests. Native file reopening preserves source text, IDs,
dates, blank cells and duplicate rows; native text/cell edits survive save/reopen. Structural
tests cover geometry, explicit fonts, dense rejection, long tokens, counts through 30 slides,
native bullet/RTL XML, and absence of images, macros and external relationships.

PASS: Artifact Tool read-only import/render generated all three slides from a synthetic Arabic/
English plan (cover, bullet body, native table). Every image was inspected; no clipping was
visible in this sample. The renderer was not used to rewrite the delivered PPTX.

FAIL: That imported rendering reverses multiword Arabic titles and Arabic/Latin reading order,
and displays table columns left-to-right despite the native RTL flag. Do not treat the sample
as Arabic visual qualification. UNKNOWN: whether this is renderer import behavior or a native
Office output issue. Logical text/RTL XML remains present, but only native PowerPoint testing
can resolve the application-specific result. Font substitution is another remaining gate.

NOT RUN locally: PostgreSQL/Redis full-suite and lifecycle tests (hosted workflow required).
Added cases cover success/one repair, exhausted repair, builder failure, cached delivery retry,
single capture, cleanup and version upgrade cancellation with retained admin settings.
NOT RUN: Live provider/source fidelity, Microsoft PowerPoint edit/save/render, Telegram staging,
container deployment or paid launch. No operator runtime was changed.

Use [output quality gates](../../docs/OUTPUT_QUALITY.md) and
[Telegram acceptance](../../docs/TELEGRAM_ACCEPTANCE.md); retain source SHA and actual engine
for acceptance. A fixed plan and font estimates cannot establish AI fidelity or universal fit.
