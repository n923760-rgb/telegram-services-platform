# Source-owned headings for PDF table workbooks

Baseline: official main 6d3a39f71c0434f92ce3beb268553d9b6c1356b6. Owner authorizes continued development, tested merging and deployment. Existing runtime update remains unverified; unrelated governance PR #21 is untouched.

## Customer contract

PDF tables v4 adds an explicit third mode: use the first extracted row of every table as column headings. It uses no AI. Native Data tables start their records at the original R2 reference; Source keeps every extracted row, including R1. Review still reports the total extracted row count and explicitly explains this movement, with all headings shown before approval. The language choice affects review/generic headings, not translation of source headings.

Source headings must be nonblank, unique ignoring case, single-line, at most 100 characters each and have no edge whitespace. The existing complete heading/review budgets apply. Unsupported headings fail as input_invalid, release customer credit and do not count as an infrastructure failure under existing policy. No silent renaming, truncation, fallback to another mode or inference that a first row really is a header. Generic columns remain available for unsupported source headers. Formula-shaped headings are literal native strings; numeric headers are source content, not AI claims.

Explicit visual Arabic recovery also applies to the selected Data headings. Normal/mixed cells retain the existing conservative behavior. Headers are checked after recovery so collisions fail; Source remains unchanged. Prepared continuations revalidate labels against the stored extraction and selected display policy before export. Delivery retries reuse prepared files.

## Verification and limits

PASS LOCALLY: 87 focused source-heading, existing service, Arabic recovery, real bounded-child table extraction and architecture checks. Readback covers Arabic/English headings, multiple tables, explicit Arabic recovery, row references/filters, exact source cells, zero/leading zeros, literal formula-shaped headers, editable output, reference-column collisions, invalid and oversized headings, changed continuation rejection, provider-free operation and one extraction only. Global lint/format/diff checks pass.

New DB lifecycle coverage requires hosted CI: native AR/EN source-heading completion and one capture, provider-paused direct admission, invalid-heading release, rejection release, prepared delivery retry and v2/v3 upgrades preserving administrator price/activation and cached outputs. The existing non-root, network-disabled worker qualification is extended with AR/EN ruled/unruled native extraction-to-source-header workbooks. Existing qualification checks remain intact.

No new dependencies, migrations, provider requests/caps/retries, ledger rules, price/activation changes or production pause changes. The v4 contract uses existing snapshot/version policy: unprepared old orders cancel/release, prepared results remain replayable. Customer deployment must wait for exact-head hosted CI and worker qualification.

UNKNOWN/NOT RUN: live Telegram, real customer PDF extraction quality, Microsoft Excel/mobile visual rendering and server deployment. Native readback does not prove that the PDF's first extracted row is a meaningful heading, semantic correctness or original-layout reconstruction. Every-table selection is deliberate; mixed per-table heading choices, merged/multiline header reconstruction and repeated page-header removal are outside this slice.
