# Ordered image PDF pages

Baseline main 00848f79cfe3460ffc0adcd02a07272c71a65295, CV PR #28 merged.
Reviewed workflow 37927874220, job 113811093334 passed 545 tests, DB/migrations/
drift/Compose and non-root network-disabled native worker including AR/EN CV.
Owner authorized useful services, publication and continued merges after checks.

## Scope and contract

Independent images_to_pdf plugin, disabled by default, SAR 2.00 administrator-issued
test credit. Up to five source images in sent order, one per page. A4 portrait,
landscape or automatic per-image orientation, centered within 10 mm margins, original
aspect ratio and no crop. Apply EXIF orientation before placement; composite alpha
on white. Decode/re-embed pixels, with no new lossy JPEG encoding and no source EXIF
metadata. No AI, OCR, resolution restoration, scan correction or compression promise.

Existing generic Telegram image intake remains unchanged: images are normalized
to at most 1024 pixels and re-encoded JPEG at quality 88. Original upload resolution
and alpha/animation may already have been lost by intake; this builder preserves
the received decoded pixels, not original camera files. Direct animated inputs are
rejected instead of silently dropping frames. Real Telegram clarity needs acceptance.

Limits: five files, 10 MiB per file/20 MiB total, 20 million total decoded pixels,
minimum 32-pixel sides/maximum side 10,000, output 10 MiB. Header/pixel checks occur
before image load. Builder runs in a thread and validates PDF structure before saving.
These bounded inputs are not a sandbox, aggregate worker memory quota or execution
timeout. Output assembly may use more working memory than the final byte limit.

Owned storage protects inputs/output. Invalid/missing/foreign content fails and
releases reservation; another owner's source must remain intact. Credit capture
after required delivery; retry uses prepared PDF with no regeneration. Existing
at-least-once external delivery and retention/crash limitations apply. Duplicate
keys/invalid choices/counts reject before reservation; image-content failures occur
during execution. No bot/core/financial/order/worker policy changes or dependencies.

## Verification record

- Local editor/commands stopped returning during preparation. Earlier CV local
  results remain valid; image unit/lifecycle/render inspection locally NOT RUN.
- Work continues through Git Data APIs and hosted CI; source is reviewed independently
  of the incomplete unpublished image worktree. Do not claim local/remote tree equality.
- Added 19 meaningful independent cases: actual PDF embedded pixel equality, page
  order, A4 geometry/margins/aspect/centering, EXIF and metadata, alpha, source limits,
  animated input rejection, output size, ownership and input admission.
- Added seven hosted lifecycle cases: two-page actual success, single capture/zero
  AI cost/input-output cleanup; invalid/missing/foreign/save failure release; prepared
  result retry; duplicate-key rejection before reserve.
- Worker image adds actual ordered pixel checks as non-root with network disabled.
- Require exact-head hosted lint/format/tests/migration/drift/Compose/image success
  before merge. Final IDs/results retained on PR separately from local checks.
- NOT RUN: Local visual acceptance, representative customer/photo/scan quality,
  client/mobile/native PDF opening, real Telegram/staging/server load/deployment or
  service activation. Geometry and exact synthetic pixels do not prove those gates.

Reuse existing ReportLab/Pillow/pypdf libraries and locked dependencies. Update the
single canonical roadmap and portfolio, not an additional competing project plan.

First published head f93b913 workflow 37929605989 stopped at formatting: one new
builder condition required canonical Ruff wrapping. Lint passed; tests/image were
not reached. Exact diagnostic diff applied without changing behavior or checks.
