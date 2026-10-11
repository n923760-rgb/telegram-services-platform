# Confirmed administrator activation controls

## Authority / baseline

Owner explicitly continued the proposed activation/deactivation confirmation
slice after PR #59. Baseline main b810384; no deployment or production flag write
was made here. Prices and provider expense remain independent.

## Implementation

- Private service inspection offers an enable/disable proposal, not an immediate
  mutation. Actor-scoped FSM token expires in five minutes; cancel/navigation
  invalidates pending admin action without replacing customer/support state.
- Review shows unfinished count, test-credit values, unpaid Stars count, recorded
  paid receipt total and existing refund states. Only metadata/financial references
  enter a canonical fingerprint; no customer text/files are retained in the audit.
- Server-side authorization, globally serialized operation identity, service-row
  lock, current fingerprint and target eligibility are checked before mutation.
  Retrying the same operation is idempotent; a different payload is rejected.
- Enable checks stored/code version, mandatory local provider configuration and
  pause, Stars selling price when required, and pending prior panel cancellations.
  Existing circuit reset is retained; no remote connection/quality certification.
- Disable atomically records gate, immutable decision and outbox task containing
  the reviewed fixed IDs. No order/customer locks are acquired under service lock.
- Bounded worker recovery processes five intents/tick, at most 100 orders/500
  receipts per reviewed intent. Separate DB-only, customer-first settlement
  transactions are terminal-safe; replay/partial crash cannot duplicate release
  or cancel new requests after later reactivation. Existing disabled-service
  sweep can also settle targets; outbox then safely records completion.
- Completed orders are skipped. Paid Stars are requested for refund through the
  existing workflow, never labelled externally refunded by this task. Late
  receipts remain governed by existing cancellation/payment recovery.
- Additive migration 0013: immutable audit (update/delete protection, guarded
  downgrade) and mutable task completion marker. No default flag/price changes.
- Last five panel decisions display actor/date (Riyadh), count and local task
  status; commands/circuit/manual DB changes are not retroactively audited.

## Evidence / limits

PASS LOCAL: 35 pure activation/readiness tests, three pure architecture gates,
lint and formatting. Added hosted cases for atomic flag/audit, replay binding,
stale state/prices/orders/receipts, privilege revocation, immutable audit,
concurrent admission/recovery, partial recovery crash, terminal completion,
new-order exclusion, credit release, paid/late Stars, enable gates and actual
dispatcher confirmation/cancellation/expiry/foreign token/customer state.

BLOCKED LOCAL: PostgreSQL/Redis/full financial and migration execution are not
available here; require the unchanged exact-head hosted workflow before merge.
NOT RUN: VPS/mobile/provider and real Telegram Stars charge/refund acceptance.
In-flight external work can finish around disable; the gate cannot undo delivery
or provider spend. Order/payment state may change after validation; terminal-safe
settlement and existing late-receipt rules remain authoritative, not a claim of
global atomicity between UI, worker and Telegram. All components require the
normal operator backup/migration/update before runtime availability.
