# Read-only order diagnostics

Owner continuation after the provider incident. Baseline main d97c040; operator
reported its successful deployment, correct max_tokens/8192 wire configuration,
healthy services and PROVIDER_PAUSED=true. The historical unknown bill remains
unresolved and is not settled or released by this task.

## Change

Private CLI `python -m app.ops.order_diagnostics REFERENCE [--actor ADMIN_ID]`.
Configured owner authorization happens before database access. References are an
eight-character hexadecimal prefix or a full UUID. Prefix lookup uses an indexed
UUID range, stops at two matches and rejects ambiguity. Full UUID resolves exactly.

A repeatable-read, read-only PostgreSQL transaction provides one coherent snapshot;
each statement has a five-second timeout. Related ledger/charge/hold/attempt queries
are bounded at 64 rows; overflow returns an error, not a partial financial report.
Queries select operational columns only, not input/result/payload/customer identities.

The report exposes order/job/error states, UTC timestamps, order-only ledger totals,
exact test-credit reserve/release evidence, Stars state counts, recorded usage and
cost overruns, unresolved hold UUIDs, and current pause/output-limit configuration.
Unknown recorded costs remain null, never fabricated zero. Stars states are not
interpreted as a newly performed refund. Malformed pause state fails closed.

No provider request, file operation, financial settlement, service activation,
provider unpause or database row writes. No schema/dependency/contract/price changes.
CLI failures redact exception bodies; this CLI is not a public HTTP/bot endpoint.

## Verification

- PASS locally: 15 reference/authorization/ledger/privacy/error/architecture cases.
- PASS: lint, formatting and whitespace checks; CLI help is read-only.
- Added hosted PostgreSQL cases for an actual recorded overrun plus uncertain hold,
  exact release evidence, repeated snapshot stability, no private input disclosure,
  unknown/ambiguous references, full UUID selection, overflow, malformed pause and
  enforced read-only writes. Existing financial/native suite remains enabled.
- Full exact-source hosted qualification required before merge; deployment NOT RUN.

## Limits

This reports current retained database evidence, not provider invoice truth, past
raw responses, or the cause of an unknown bill. It cannot retroactively recover
missing provider receipts or grant authority to unpause/reconcile. External delivery
and provider records may change outside the database snapshot. Legacy unaudited
wallet changes and financial mutations remain separate operator workflows.
