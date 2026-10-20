# Explicit PowerPoint slide counts

Baseline: official main 4eeecd891e35579192349bc5fbfcc2d527849745. Owner authorizes continuing development and tested merging, with one production deployment after improvements. No server action; unrelated governance PR #21 remains untouched.

## Output contract

PPTX v5 adds an optional slide-count field before content. The customer can enter 1–30 in Western or Arabic decimal digits, or skip for the existing automatic behavior. The count includes any cover. No source-prose count parser or generated default is introduced. A separately selected count takes precedence over conflicting count instructions in the source; the source text passed to AI is unchanged.

The validated count is captured in a request-local Deck subclass. Its slide array publishes exact minItems/maxItems in JSON Schema and validates the same bound on provider output, injected-model revalidation and approval continuation before file creation. A short trusted prompt explains that the number is an output constraint rather than a new source fact. Source numeric/contact counters, readable geometry/font checks and all other deck rules remain in force. Missing-information responses still need no placeholder deck.

Wrong count uses the existing schema/content creation repair budget. Persistent invalid output fails through the existing safe failure/release path rather than saving the wrong number of slides. No additional AI request stage, retry allowance or raised provider limit. Existing automatic requests and legacy internal inputs without a count retain 1–30 bounds and the original prompt.

## Compatibility and checks

The stricter optional contract bumps text_to_pptx v4 to v5. Same output artifact, renderer, administrator-owned price/activation, financial policy, source limits and dependencies. Existing version guards cancel/release unprepared older requests, including v4; prepared historical PPTX files replay without regeneration or inferred count. Tests preserve administrator SAR/Stars prices and activation.

PASS LOCALLY: 86 focused count/schema/native/service/palette regressions and three architecture gates; global Ruff lint/format/diff and YAML/embedded worker syntax. New cases cover optional mode; 1/3/30 actual native files and footer counts; Arabic/Persian/Western digits; invalid ranges/types; exact JSON Schema bounds and privacy; isolated simultaneous request schemas; unchanged source-token safeguards; trusted prompt/source separation; continuation acceptance/rejection without another provider call; and an injected adapter that ignores schema returning the wrong count.

Hosted lifecycle cases cover direct success and one repair, one capture across duplicate execution, calculated usage and persistent mismatch release, invalid input with no order/hold/reservation, approval continuation reusing its plan, counted cached-file retry, and v1/v3/v4 cancellation or prepared historical replay. The non-root/network-disabled worker gate adds editable native PPTX checks at 1, 3 and 30 slides while retaining every earlier check. Full exact-head hosted PostgreSQL/Redis/worker qualification is required before merge. Docker is unavailable locally; no local container claim.

## Limits

Only the separate selected count is enforced exactly. Skipping retains best-effort interpretation of any count written in the content. Exact length does not prove semantic completeness, truthful grouping or live provider/native-mobile quality. Dense content at a low selected count may fail existing readability/content/budget safeguards; those are not relaxed to force delivery. No new live provider/Telegram/mobile test or production deployment is claimed.
