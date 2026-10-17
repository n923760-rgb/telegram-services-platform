# Provider-free selected PDF page rotation

Baseline: official main a4a307d885c5404d1fdd660b0368778c14763ba0. Owner explicitly requests continuing improvements and merging, followed by one production deployment after development. No server action; unrelated governance PR #21 remains untouched.

## Contract and behavior

PDF tools v2 retains merge and ordered extraction, adding rotation within the same service and existing administrator-owned price. Intake asks operation, one PDF, selected page numbers, then an explicit additional clockwise 90/180/270-degree angle. Angle is required only for rotation and rejected for other operations. Selection uses the existing Arabic/Western digits, comma and range parser, rejecting duplicates and out-of-range pages.

Unlike extraction, rotation retains all source pages in their original order regardless of selection order. Each page is copied to the writer; selected pages receive an additional rotation, normalized modulo 360 so an existing 270 plus 90 becomes 0. Unselected rotation is unchanged. No content transformation, text rewriting, rasterization or AI. Native text/content streams, image payloads, MediaBox and CropBox remain intact in fixtures. Results retain result.pdf with an operation-specific AR/EN preview; outlines/document metadata remain excluded as before.

No limit changes: 1–5 inputs overall, 2–5 for merge and one for extract/rotate; 10 MB per file, 20 MB total and 200 total source pages. Existing encrypted/corrupt/form/signature guards apply to rotation too. No AI construction/cost or provider budget changes. The version bump uses existing registry/version handling: administrator activation/prices survive; unprepared v1 requests cancel/release, while prepared historical files replay without rebuilding.

## Qualification

PASS LOCALLY: 55 pure/native PDF contract and injected-service checks including existing merge/extract regressions, plus three architecture gates; global Ruff lint/format and diff checks. New cases cover three angles; selected/unselected pages; reverse/Arabic selections; existing 270-degree rotation wrapping at 360; exact source text/streams/images/boxes; invalid/missing/foreign angles and multiple files; corrupt/encrypted/form inputs and missing page; localized preview and no AI call. Initial local additive-rotation tests exposed pypdf retaining 360/450/540 values; explicit normalization corrected that and all local checks pass.

Added hosted flows cover capture once and zero CostHold/CostUsage, no AI provider construction, release and ownership on corrupt/encrypted/form/out-of-range/foreign input, invalid rotation admission without reserved credit, delivery retry reusing prepared rotated output, and prepared/unprepared v1 upgrade with admin prices retained. The existing native worker gate gains one selected-page rotation/image/order/box check; all original gates remain. Full exact-head hosted PostgreSQL/Redis/native-worker qualification is required before merge. Local Docker is unavailable; no local non-root-container claim.

Reference checked 2026-10-17: [pypdf page rotation](https://pypdf.readthedocs.io/en/stable/user/cropping-and-transforming.html#page-rotation), alongside the locked installed library and native fixtures.

## Limits

This rotates PDF page display in 90-degree increments; it does not deskew a photographed/scanned page, OCR, compress, crop or rebuild layout. Forms/signatures remain unsupported; existing page-copy outline/metadata limits are disclosed. Native PDF structure/image readback is not a claim about every viewer or mobile appearance. Real provider/Telegram/mobile acceptance and production deployment are NOT RUN. No dependency, migration, financial-policy or service-activation change.
