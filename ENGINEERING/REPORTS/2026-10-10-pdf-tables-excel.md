# PDF tables to Excel — 2026-10-10

FACT: Owner authorized a complete development slice and continued verified merges.
Baseline main 822efbd / PR #39; no production deployment or activation authorization
is inferred. This slice adds independent default-disabled `pdf_tables_excel`, SAR 5
administrator-issued test credit. Commercial Stars prices remain unset.

Camelot 2.0.0 is locked in uv and container requirements. An injected abstract
TableExtractor runs native extraction in a separate child, with existing serialized
native slot, five-second admission, 45-second wall timeout, 35 CPU seconds, 1 GiB
address space, 512 KiB output and no core dump. Credentials/environment are cleared;
process-group cancellation/timeout cleanup is reused. These bounds are not a sandbox.
Workers share capacity only within each process; replicas have independent slots.

Only text PDFs without rendered raster images, 10 MiB / five pages, are accepted.
Every page must produce a table; at most five tables, 2–200 rows and 2–12 columns
per table, 5000 cells / 50000 characters overall. Reject encrypted/malformed PDFs,
missing pages/tables, ragged shapes and low Camelot placement metrics. Accuracy >=95
and whitespace <=30 are heuristics, not proof of correct values or complete tables.
Ruled tables use lattice; explicitly selected unruled spaced tables use stream.
No OCR, downloads, layout reconstruction or automatic fallback is added.

Optional AI receives only the first two rows, each cell clipped to 80 characters.
It may propose table/column headings through an exact-shape strict schema, with
one existing repair. It cannot return replacement rows/cells; numeric claims in
labels are rejected. Label meaning/language still needs customer/provider acceptance.
Both modes require customer structure confirmation before XLSX generation. Stored
continuation preserves extracted cells and avoids a second native/AI call on approval.

Excel has Data/Source sheets per table and Review metrics/page references. The first
extracted row remains data, including original headings. All cells remain literal
text, including leading zeros, dates, =/+ prefixes; no automatic numeric coercion,
row deletion or aggregation. Source is extracted text, not proof of fidelity to PDF.
Customer must compare with the PDF. Blank strings display as empty Excel cells.
Generic order/payment/budget/retention policy is reused without service branches.

PASS LOCAL: 44 independent plugin/native/architecture tests including complete heading-review bounds;
real synthetic AR/EN, lattice/stream two-page extraction matches all fixture cells.
Lint/format/diff and complete collection are recorded during final qualification.
NOT RUN LOCAL: full PostgreSQL/Redis lifecycle suite or Docker (unavailable here).
Hosted CI must execute all lifecycle tests and the seventh non-root/network-disabled
worker gate on the exact published head before merge. No hosted result is assumed.

NOT RUN: representative customer PDFs, native mobile Excel, live AI/Telegram,
load tests, server update, service activation and commercial payment qualification.
These remain separate operator gates. Synthetic unshaped Unicode fixtures establish
cell extraction only; they do not establish Arabic visual layout acceptance.
