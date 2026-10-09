# Direct Stars checkout: launch qualification

The code and synthetic tests are not evidence of a deployed bot, real purchase, provider
quality, support coverage or commercial viability. Keep `STARS_ENABLED=false` until this
source-bound checklist passes in Telegram's dedicated test environment first.

## Operator prerequisites

- Back up the database and record the exact deployed Git SHA before migration `0011`.
- Configure the authenticated HTTPS Telegram webhook through the existing deployment
  instructions. Do not expose PostgreSQL, Redis or the loopback API publicly.
  Run API/worker/monitor and omit the polling bot process in webhook mode.
- Privately supply owner-approved Arabic/English purchase/refund/support terms, each
  20–2500 characters and at most 2500 UTF-16 units. No legal/business terms are invented
  by the application. Increment `STARS_TERMS_VERSION` whenever either language changes.
- Set an independent integer price for each saleable service: `/setstars SLUG INTEGER`.
  There is no default Stars price, SAR conversion, Stars top-up or internal Stars wallet.
- Use `/enable SLUG` only after that service's file/provider quality gate passes. Echo
  is a test service, not a meaningful commercial product. Configure provider costs privately.
- Set `STARS_ENABLED=true` only with webhook mode, secret and both approved terms.
  Config validation fails closed otherwise. Never store real secrets in Git or chat.

## Required test journeys

| Journey | Required evidence |
| --- | --- |
| Terms and invoice | Arabic/English price and full terms precede explicit agreement; `/terms` works; one private XTR invoice with empty provider token. |
| No payment | Invoice alone creates no job or ledger reservation; expiry/cancellation blocks execution. |
| Pre-checkout | Owner, currency, frozen price, live service/version, terms and expiry checked; answer within Telegram's 10-second window. Approval alone starts no job. |
| Successful purchase | Persist actual Telegram charge ID before execution; one job despite repeated receipt; SAR test ledger unchanged. |
| Recovery | Restart API/Redis/worker between approval, receipt and delivery; restore invoice through `/orders`; reuse cached output rather than repeat AI generation. |
| Native output | Test representative Arabic/English inputs for each enabled service, inspect files and identifiers in native Office/PDF, and verify cleanup. |
| Refund | Inject safe staging failure/cancel approved review; actual Telegram refund confirms full XTR amount once; `/refund ORDER_UUID` is pending until confirmation. |
| Uncertainty | Simulate lost refund response; no automatic repeat; `/starstatus` surfaces unresolved state; reconcile actual transaction evidence. |
| Support | `/paysupport` reaches the responsible administrator; verify replies, including a banned customer. Support must be staffed before sales. |
| Operations | Test alert delivery, daily separate XTR/SAR reporting, off-server backup and restore against the same source. |

Use a dedicated Telegram test account, never production customers as synthetic subjects.
Record outcomes as PASS/FAIL/NOT RUN with source SHA and redacted evidence. Do not paste
tokens, customer content or full receipts into public issue/PR logs.

## Refund reconciliation

`/starstatus` reports receipt/refund amounts in XTR and pending/uncertain counts. A successful
HTTP request, an empty page, or absence of a transaction is never proof of a refund.
`/starreconcile OFFSET` scans up to 1000 history entries and shows its actual next offset.
Continue pages when coverage is bounded; API ordering is not assumed. It can recover incoming
receipts only for this platform's known Stars orders and confirm refunds only by exact charge
ID, customer and amount. It never refunds unrelated historic products.

An uncertain refund is not retried automatically, even when transaction history does not
show it. Investigate through the responsible merchant and Telegram support; do not mutate the
audit tables to force an outcome. Disabling new purchases does not disable pending refunds.
If an approved checkout did not finish payment, cancel its pending invoice and create a new
order rather than reuse a different checkout query; completed receipts remain idempotent.
Migration downgrade refuses to erase recorded Stars purchases or receipts; use forward fixes.

## Commercial acceptance

Before a paid launch, the owner must approve service prices against actual provider billing,
support workload, refund risk and Telegram settlement terms. Recorded XTR receipts are neither
profit nor a cash balance; never subtract SAR provider cost from XTR receipts as one margin.
Telegram/API/provider transactions and production deployment were not performed by this document.
