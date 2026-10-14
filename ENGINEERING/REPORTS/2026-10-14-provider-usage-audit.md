# Provider usage audit and independent cap guard

Baseline/operator-deployed source 624c853 (#80); core healthy, zero unfinished orders at deployment, provider paused. Private backup EvFsFgt1. Owner approves continuing billing/usage review and controlled probe preparation.

## FACT / INFERENCE

Owner's historical usage export reports two requests at 13:00–14:00 Asia/Riyadh on 2026-10-13, prompt tokens 3180 (1408 hits/1772 misses), completion tokens 29256, total USD 0.017823624. Exported miss/output rates in that hour are USD 0.15/0.60 per million, cached input USD 0.003 per million. This is historical invoice evidence, not current pricing guidance.

Operator database snapshot shows two holds for C64ECF1E in that hour: one unknown, one returned 1590 prompt/15532 output tokens, calculated SAR 0.071683 using configured USD 0.30/1.20 per million and conversion 3.75. If those are the export's only calls (no other usage of the key), subtraction implies first-attempt output 13724 and prompt 1590. Exact per-call billed cost remains UNKNOWN because hourly cache allocation and independent call identity are absent. No raw export, account/key identifiers, customer content or secrets committed.

## Bounded implementation

Compatible adapter records consistent OpenAI cached-token/DeepSeek hit/miss details, safe-format request ID, requested output cap/parameter and cap breach flag in existing rate_snapshot JSON. Malformed optional cache detail is tagged invalid without discarding complete total usage. No cached discount, current rate update or fabricated invoice cost; the same conservative cost/bound calculation is retained.

Gateway settles full usage first, then pauses the provider for returned output above the request cap even if monetary usage stays below a generous bound. Existing monetary overrun pause uses the same DB-only retry-safe pause operation. Unknown exposure is retained and later admission still obeys the pause. No direct vendor calls or retry loop added.

Order diagnostics displays a curated audit view. Old returned-token records are calculated, with cache/wire-limit/invoice evidence unknown; old records are not rewritten. Raw rate_snapshot/private request content is not dumped in diagnostics.

Owner-only synthetic cap preflight prepares the actual adapter body at <=128 output tokens, body hash and conservative reservation bound, then reads pause state in a bounded read-only snapshot. No HTTP/AI call, wallet/order/cost hold, delivery or unpause. This is preparation ONLY; the actual live administrative probe is BLOCKED by retained global pause and must use a separately controlled budgeted path. It must not be a direct unaccounted API call.

## Verification

PASS locally: 60 focused adapter/cache/legacy-diagnostic/auth/architecture checks; global lint/format/diff. Hosted PostgreSQL tests additionally cover under-cost-bound token overrun, full settlement, cache metadata persistence, independent pause, untouched unknown exposure, blocked next call, and read-only no-network administrative preparation. Full hosted financial/native workflow required before merge; actual logs recorded in PR.

No dependencies/migrations, service versions/prices/gates, configured rates, historical usage/ledger edits, unknown-cost settlement, provider credential changes or global resume. Live provider cap/current pricing/mobile quality/individual billed-cost reconciliation remain UNKNOWN.
