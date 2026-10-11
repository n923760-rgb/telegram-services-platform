# Private admin panel and Stars prices — 2026-10-11

FACT: owner authorized admin controls, manual independent selling prices and verified
continuous merges. Initial main baseline 2ac05a7. Preserve unrelated pending work.

## Bounded implementation

Generic plugin-derived six-item service pages, price/state text and full-width name
buttons. Private `/admin` plus a button for configured administrators. Read-only
order totals, Stars reporting and last-five price audit. No customer engine choice,
new service, bulk activation, payment conversion or invented selling price.

Price prompt uses ForceReply without replacing customer draft/support state. A
five-minute owner-context token binds service, old price and a single proposed new
value. Confirmation rechecks authorization and current database price. An immutable
migration-backed audit and Stars price update commit together; operation IDs are
payload-bound/idempotent. Existing `/setstars` gets the same audit boundary.

Existing pre-checkout policy invalidates old unpaid invoices when current Stars
price changes. Paid order prices remain frozen; this feature changes no receipts,
financial ledger or refund policy. Audit records contain no customer content.

## Verification requirements

Added PostgreSQL cases for atomic/idempotent changes, concurrent stale edits,
invalid/unauthorized edits, audit immutability, registry preservation and actual
paid/unpaid invoice behavior. Actual dispatcher tests cover price reply/confirmation,
Arabic digits, later-reply freezing, cancellation/expiry/revocation/other-admin,
non-admin access, unchanged draft and command audit.

PASS/FAIL hosted evidence is recorded through the exact PR workflow; full migration,
lint/format, financial suite and native-worker gates REQUIRED before merge.
Local database/container unavailable: integration tests NOT RUN locally.
UNKNOWN: real Telegram ForceReply, owner mobile UX, production update/load.
