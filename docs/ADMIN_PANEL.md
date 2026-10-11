# Bot administration and owner-set prices

Only configured ADMIN_IDS can open `/admin` or the Admin panel button on their
home keyboard. The panel shows six services per page, enabled/disabled state and
Stars price. It also provides order-status totals, today's Stars report and the
last five recorded price edits (Riyadh time). Opening controls creates no order,
reservation or provider call, and preserves customer intake/support state.

### Read-only service configuration checks

`/admin` → Service configuration checks → choose a service. Six entries per
page; retired replacements are omitted. Refresh rereads the current database
snapshot and local bot configuration. Details show activation, actual menu
activation/payment-price filters, stored/code versions, global AI enabled/paused
state and local provider cost-configuration validation, current payment mode
and the manually set Stars price. Missing Stars prices are highlighted only in
Stars mode. An Edit Stars price shortcut reuses the existing audited price flow.

This is not a service readiness certificate: no AI/network calls, native tool
probes, worker-container inspection, remaining-budget checks, or customer output
acceptance occur. A listing is not admission approval. Mixed-input services are
not tested using fabricated inputs: their actual admission still checks
`needs_ai(inputs)`. Provider error details, endpoint and credentials are not shown.
The snapshot can change after rendering. The panel does not activate any service,
change prices, cancel orders or reserve funds. Client drafts/support state remain.
Authentication and the existing private-chat gate precede every report callback.
Verify runtime tools and representative results separately before enabling.

Choose a service, reply to its price prompt with a whole number (1..1000000),
review the frozen old/new values, then confirm or cancel. The prompt/confirmation
expires after five minutes and belongs to the current administrator's private
FSM context. Every callback/reply rechecks current ADMIN_IDS. A concurrent change
invalidates the old confirmation; reopen the service to review its current price.
Price input accepts Western and Arabic-Indic digits. Later replies cannot alter
an existing confirmation silently. Only replies to the original prompt enter
this flow; ordinary messages continue their original conversation.

The selling price is manual and independent of provider expense. This panel does
not activate payment, convert SAR test balances or enable/disable services. Existing
activation commands remain available. Existing `/setstars` now records its
administrator and price change too; `/setprice` remains SAR test credit pricing.

Actual changes are atomic with an immutable PostgreSQL audit row containing
actor Telegram ID, service, previous/new Stars price, timestamp and operation ID.
Retrying the same operation is idempotent; different payloads cannot reuse its ID.
This records bot admin edits going forward, not historical edits or arbitrary
operator database changes. Registry synchronization preserves prices/activation.

Unpaid invoices at a previous price become invalid under the existing pre-checkout
policy. Paid order contracts keep their original Stars price. Updating a price
does not cancel paid orders or trigger a refund. Migration 0012 only adds audit
storage; it does not modify existing service/order/receipt prices.

Deployment requires normal verified backup and Alembic migration. Real Telegram
ForceReply/mobile acceptance is still required; fake sessions do not establish it.
