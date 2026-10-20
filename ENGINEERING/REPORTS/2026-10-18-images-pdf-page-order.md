# Explicit image-to-PDF page order — 2026-10-18

## Baseline

FACT: Official main d0366a02c99038483317119d8fcf37ca1ed5df56 includes #103.
Owner authorizes development/qualification/merge; production deployment remains deferred
to one later batch. This bounded round adds native image-page reordering only.

## Contract

CHANGE: ImagesToPdf v3 adds optional single-line page_order (max 32 characters) between
image upload and orientation. Number 1 identifies the first uploaded image. Accept a complete
permutation of 1 through image count, using decimal digits (Western/Arabic/Persian included),
commas, Arabic commas, spaces or tabs. Omitted/null/Skip uses unchanged upload sequence.
Reject duplicates, missing/unknown IDs, ranges, decimals, malformed separators, multiline,
oversize and non-string values before reservation. Never infer filenames/document order.

The plugin reads the same owner-bound source images in validated selected order and passes
them to the unchanged native renderer. Every image appears once. Bilingual result previews
state actual source-image sequence. Orientation remains automatic per image or selected A4.
No extra AI call, file, dependency, price/activation, limit, ledger or provider-policy change.

## Verification

PASS LOCALLY: 74 focused order/native/source-preservation/service tests, including every
possible permutation for 1–5 images, AR/EN/Persian digits and separators, default/null,
invalid inputs and actual native PDFs. Native tests compare EXIF-transposed decoded pixel
bytes and dimensions, page orientation, metadata removal and bilingual order previews.
Three architecture gates, global Ruff lint/format, diff whitespace, workflow YAML and
embedded native-worker Python syntax PASS. Full exact-head hosted workflow required.

Hosted flow changes cover reversed native pages, zero provider construction/usage/holds/cost,
single capture and file cleanup, invalid-order admission without reservation, v1/v2 cancellation
with administrator prices retained, and prepared historical replay without regeneration.
Non-root network-disabled worker additionally exercises the real service with Arabic-digit
order 3,1,2, reads all three images back and compares source pixels and preview order.

SAFETY: Ownership and resource limits remain unchanged. Source-image omission/repetition
is intentionally unsupported. Unprepared legacy jobs cancel/release through existing version
guards; prepared output is reused. Existing high-resolution intake remains enabled.

LIMITS: Upload sequence is authoritative; Telegram photo compression may already reduce
quality before intake. Live Telegram/mobile visual acceptance and server deployment NOT RUN.
