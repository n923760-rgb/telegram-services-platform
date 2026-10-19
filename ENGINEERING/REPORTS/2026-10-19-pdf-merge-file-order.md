# Explicit PDF merge file order — 2026-10-19

## Baseline and bounded scope

FACT: Official main 55010c8f346afba858c0b430cfcde69ad2d5ee3f includes #106.
Owner authorizes continuing tested development/merges and defers production deployment
to one later batch. This round adds merge input ordering, not another PDF operation.

## Contract

CHANGE: PdfTools v3 adds an optional single-line file_order (32 characters) for merge only.
File 1 is the first upload. Use each uploaded file exactly once; accept the same decimal
digits and comma/Arabic comma/space/tab syntax as image ordering. Omitted/null/Skip keeps
upload sequence. Nonmerge orders reject supplied ordering rather than silently ignoring it.
Actual source file order is shown in the AR/EN result preview.

Only read order changes: the existing native builder receives whole files in the chosen
sequence and preserves page order within each file. No page omission, repetition, rasterizing
or rewriting is added. Limits, source ownership and existing encrypted/form/signed PDF
rejection remain. Same result.pdf, price/activation overrides, AI-free runtime and ledger.

REUSE: Extract the existing image ordering parser to app/files/upload_order.py and reuse
it from both input contracts. ImagesToPdf retains v3, identical fields/validation and result
behavior; unchanged regression tests include every bounded permutation and invalid input.

## Verification

PASS LOCALLY: 154 focused PDF merge, shared order/image regression, rotation, ownership,
native image/source-pixel and injected-service tests. Tests include all 2–5-file permutations,
source page contents/geometry/rotation/order, defaults, AR/Western/Persian digits, invalid
admission and the merge-only conditional field. Three architecture gates, global Ruff
lint/format, diff whitespace and workflow YAML/embedded worker syntax PASS.

Hosted tests extend capture/zero provider usage, malformed order before reservation,
prepared merge replay without rebuilding, and v1/v2 release/cached output with administrator
prices retained. Native non-root network-disabled worker additionally merges two different
image-bearing PDFs in reverse order through the actual service and reads source images back.
Full exact-head hosted workflow required before merge; local checks are not live acceptance.

SAFETY: No dependency, migration, provider/budget/retry change, new service, live provider
execution or server action. Existing version guards handle unprepared legacy work and
prepared historical results. No customer data used.

LIMITS: Upload sequence is authoritative; filenames are not ordering evidence. Existing PDF
metadata/outline limitations are unchanged. Native readback is not universal viewer/mobile
appearance acceptance. Production deployment remains deferred.
