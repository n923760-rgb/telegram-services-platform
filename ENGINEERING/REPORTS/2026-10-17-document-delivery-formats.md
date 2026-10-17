# One document intake, selected delivery files

Baseline: official main 4098b7d7659cb40bff67989d6b09e66188c92cc6, verified against origin and open PR inventory. Owner authorizes continued development and continuous reviewed merging. Unrelated governance PR #21 is preserved.

## Customer behavior

The existing document bundle becomes v3 and asks for Word, PDF or both before its current direct/smart preparation choice, one text intake and optional title. All three formats use the existing service's administrator-defined price; the prompt explains this. The service name/description describe the available outputs.

The renderer still prepares the same native Word/PDF pair in memory, including PDF for page limits and optional preview. Only selected customer artifacts are saved and delivered. No performance claim about avoiding PDF conversion is made. Both standard and visual review name the selected files; continuation/delivery retry reuse the saved artifacts.

The shared preparation helper's omitted format keeps its previous pair behavior, so CV and minutes retain their file contracts. Explicit format is allowlisted before rendering. Partial-save cleanup includes selected files and preview. Internal legacy document inputs default to both; public v3 intake requires a choice. Existing snapshot/version guards, prepared-result replay and financial settlement rules remain authoritative.

## Scope and verification

PASS LOCALLY: 117 focused output-selection, input/AI/source fidelity, policy/acceptance and existing bundle tests. Native editable-file rendering remains unchanged. Architecture, global lint/format/diff and links are recorded in the PR. Local PostgreSQL is unavailable; the full hosted workflow must qualify DB/native/dispatcher flows before merge.

Added/expanded hosted flows cover all three native delivered-format sets, no direct AI cost, capture once, visual approve/reject, delivery retry without another render, AR/EN dispatcher purchase and old v2 unprepared-job cancellation/release while preserving administrator price/activation. Unit coverage includes direct/smart with and without visual review, legacy internal default, invalid format before render and cleanup after preview-save failure.

No service-specific bot/core branch, new provider calls, cap/retry increase, dependency, migration, ledger rewrite, activation/price mutation, production deployment or unpause. Source numeric/contact guards remain; new live-provider/Telegram/mobile acceptance NOT RUN. This is delivery/intake improvement, not a new visual design or proof of AI semantic quality.

## Remaining consolidation

Other Word/PDF entries remain independently priced/enabled. Their removal or redirect is not implied by this change. A later reviewed migration must reconcile those administrator settings, historical orders and old buttons before presenting one canonical entry. Production adoption requires rebuilt images and the normal zero-unfinished-order/backup checks.
