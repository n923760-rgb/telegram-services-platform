# Generic completed-order handoff

This is an independent foundation before adding a hosted-page plugin (AGENTS.md,
service extension step 9). No registered service emits this capability yet. It
does not enable checkout, register a handler, run a provider or grant hosting.

## Problem and contract

Ordinary order files are deleted after terminal work, and retained result JSON is
later purged. A future completed-order projection must not depend on finding an
expiring file, generating AI again or publishing automatically after payment.

A trusted plugin can return an optional `Result.completion` with a versioned
internal `kind` and data-only JSON payload. A normal deliverable is still required;
the capability alone is not a customer result. The payload is detached, bounded
to 32 KiB, eight levels and 4096 value nodes; reject non-JSON types, non-finite
numbers, NUL, invalid Unicode and unknown top-level capability fields. Hash the
kind and literal payload together. Plugins cannot supply authoritative owner,
order, expiry, commercial entitlement or publication consent through this envelope.
Schema-specific handlers must interpret payload fields as untrusted customer data.

Migration 0015 adds one `order_completions` row per order. While customer/order
locks are held, completion stages the handoff in the same PostgreSQL transaction
as capture and transition to completed. Capture/commit failure rolls back the
handoff too. No handoff is staged for merely prepared, failed or cancelled work.
Delivery retry continues to reuse the existing persisted result. This does not
remove the existing Telegram send/commit crash window or its possible duplicate
message; DB handoff application is a separate atomic operation.

The fixed deadline is staging time plus the existing FILE_TTL_HOURS (default 24).
This is a processing retention deadline, **not** a hosting term. Replaying the
same staged identity/hash never extends it, restores scrubbed payload or replaces
content. A different hash/kind/owner for that order is rejected. A DB trigger
prevents changing identity, content or deadline and allows only one pending to
applied/discarded transition that scrubs the payload. Minimal order/owner/kind/hash,
timestamps and disposition remain; no ledger row is changed by consumption/purge.

## Internal consumption and recovery

`app.orders.completions.consume` takes a verified owner ID, expected kind and a
trusted **DB-only** handler. It is not a customer authentication API. It locks
customer, order and handoff in that order; verifies ownership, ban, completed
status, deadline, kind and content hash; and calls the handler in that same DB
transaction. Handlers must use only the supplied session: no provider, Telegram,
storage, HTTP call or nested transaction. Trusted code is not sandboxed. There
is deliberately no automatic transaction retry around an arbitrary callback.

Handler success scrubs payload and marks applied in the same commit as its DB
writes. Concurrent or later exact consumers return false without calling it again.
Handler failure rolls everything back and preserves the original pending payload.
A refunded, banned, expired or wrong-owner order cannot be consumed. Applied
replay still checks current owner/ban/completed state before acknowledging it.
Stars orders also require their accepted owner/order-bound charge to remain paid
at the confirmed Stars amount. Pending, in-flight, uncertain or confirmed refunds
block consumption even before the order's status catches up. These reads and refund
writers serialize on the existing customer lock; they do not request a new charge.

A bounded minute worker sweep scrubs at most 100 expired or no-longer-completed
pending rows, rechecking under the same lock order. Locked customers are skipped
for a later sweep. Ordinary terminal-file deletion/result retention remain unchanged;
they cannot erase the separate pending payload before its fixed deadline. Outages
past that deadline require explicit recovery, never silent AI regeneration/extension.
No dispatcher or production handler is installed in this round.

The later internal [profile transfer adapter](HOSTED_PROFILES.md#private-profile-transfer-2026-10-31)
can consume a prepared profile capability using a mandatory trusted entitlement
resolver. It is not registered with any dispatcher or customer purchase flow.

The later [six-month purchase contract](HOSTED_PROFILES.md#approved-six-month-purchase-contract-2026-10-31)
adds optional generic reviewed order evidence and a concrete DB-only resolver.
`transfer_purchased` uses those immutable dates and terms instead of an arbitrary
caller-created right. The later administrator-only `hosted_profile` pilot emits
the prepared handoff through the normal runner. No customer activation or automatic
dispatcher is installed; qualification invokes transfer explicitly.

## Hosted-page adapter still required

Before a future page plugin is enabled, add a reviewed handler and recoverable
dispatcher with schema/version and completed eligible order checks. Use the
explicit agreed hosting entitlement, price/terms snapshot and expiry contract;
an arbitrary completed order or completion row is insufficient. Prepare the
source/plan once using the job-scoped metered gateway, then project a private draft
through a DB-only publication adapter. Existing repository functions that open
their own sessions cannot be called inside this atomic handler unchanged.

Application must create a draft only. The customer's separate exact-content
publication consent remains mandatory. A refund after application needs an explicit
future hosting revocation policy; this generic receipt cannot undo a projection.
Pending-depth monitoring, dispatcher crash/restart tests, that revocation policy,
versioned immutable exports, real provider and Telegram/mobile qualification,
hosting/renewal/revision terms and backup/restore remain activation gates. No live
service price or enablement changes in this foundation.
