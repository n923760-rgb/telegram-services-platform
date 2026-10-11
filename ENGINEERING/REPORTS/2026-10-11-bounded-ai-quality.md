# Bounded automatic content quality — 2026-10-11

## FACT: baseline and authority

Owner authorized continuous verified development/merges, automatic AI assistance,
manual separate selling prices and optional independent translation. Baseline main
2ac05a78e22f357aa2ec3abd4963868c78c5741e. Preserve unrelated pending work.

## Implementation

Generic injected AI gateway reviews schema-valid candidates against original source,
images, task and contract. Strict finite issue codes; no raw feedback storage/logging.
One creation repair is shared by schema and semantic defects. First verdict has one
schema repair; final verdict has none. Two creation calls plus at most three review
calls per extraction. Subsequent schema-specific validators still enforce fidelity.
Production runtime applies this automatically; injected legacy gateway fixtures can
retain their explicit single-generation behavior. No operator/customer review flag.

Every review/repair reserves existing budgets, settles actual usage, or retains
unknown exposure. Terminal failure uses existing credit release/Stars refund queue.
Source and customer prices never change on a review. Cached retry reuses prepared
result. No version change because input/result contracts are unchanged; queued
unprepared work adopts the current internal gateway, cached work is preserved.

## Verification

- PASS local: 16 pure gateway cases including source/image forwarding, translation
  contract, strict verdict, repair allowance, maximum five calls and cost boundaries.
- PostgreSQL fixtures added: first-pass/corrected success, delivery outage/replay,
  second rejection, invalid verdict, denied review budget, uncertain provider call,
  paid Stars rejection queuing a single refund without credit conversion.
- Full hosted PostgreSQL/Redis/lint/migration/native worker workflow REQUIRED before
  merge. Local database/native container suite NOT RUN (not installed here).

## UNKNOWN / NOT RUN

Representative real provider quality, false decisions, VPS latency/budget headroom,
mobile output acceptance. Native success paths and rendered files are not reviewed
by this slice. Do not claim all services now use AI or all output is correct.
