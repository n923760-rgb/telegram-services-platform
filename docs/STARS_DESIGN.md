# Direct Stars checkout

Owner's 2026-10-09 completion instruction expands the former test-credit-only
scope. This is a generic foundation change, not service-specific bot branching.
Official contracts: https://core.telegram.org/bots/payments-stars and
https://core.telegram.org/bots/api#refundstarpayment (reviewed 2026-10-09).

## Contract

- Keep existing SAR test ledger/history untouched. Do not convert SAR into Stars.
- Each service has an independent optional administrator-owned integer Stars price.
  No commercial price or exchange rate is inferred from the historical test price.
- Default payment mode remains test credit. Stars mode requires explicit operator
  configuration, owner-supplied Arabic/English terms and authenticated webhook mode.
- Snapshot service version, input contract, Stars price and accepted terms per order.
  Show the full terms before the customer's agree-and-pay confirmation.
- Unpaid order/invoice has a 15-minute expiry. No job/provider call before a valid
  successful-payment receipt. Pre-checkout approval alone never starts delivery.
- Bind checkout to owner, currency XTR, frozen amount, invoice and current service
  availability/version. Revalidate admission budgets; reject within Telegram's deadline.
- Persist charge IDs and append-only payment events; verify exact duplicate receipts.
  Late, mismatched or additional charges are recorded for refund rather than lost.
- Stars are paid upfront through Telegram. Successful delivery marks the order complete;
  it does not create a fictitious SAR capture. Failure/cancellation queues a full refund.
- Refund calls run outside DB transactions under a durable claim. A lost response or
  expired in-flight claim becomes uncertain, never blindly retried. Reconcile against
  Telegram transaction evidence; unresolved cases stay visible to the operator.
- Receipt handlers bypass customer conversation/rate/ban gates; acceptance still checks
  ownership and current user/service status. Authenticated updates persist in PostgreSQL.
- Provide terms, payment support, owner-scoped invoice recovery/cancellation and admin
  pricing/refund controls. Separate XTR receipts/refunds from SAR provider expenses.

## Release boundary

V1 covers the integrated Office/OCR/PDF/CV/meeting/CSV services and complete customer,
administration, recovery and payment paths. Future service candidates stay in the
portfolio; installing every possible tool is not a release requirement.
Source completion is separate from Telegram test-environment payments, real-provider
output acceptance, production backup/restore and owner-controlled server deployment.
Require full hosted financial concurrency/failure tests and exact-head CI before merge.
