# Bot administration and owner-set prices

Only configured ADMIN_IDS can open `/admin` or the Admin panel button on their
home keyboard. The panel shows six services per page, enabled/disabled state and
Stars price. It also provides order-status totals, today's Stars report and the
last five recorded price edits (Riyadh time). Opening controls creates no order,
reservation or provider call, and preserves customer intake/support state.

### Manage services and service prices

`/admin` → Manage services (إدارة الخدمات) → choose a service. For price editing,
use Service prices (أسعار الخدمات), or the shortcut inside service details.
Both lists share the customer category/menu order and registered outcome labels.
Six entries per page; management shows page count and details show category.
Retired replacements are omitted. Refresh rereads the current database
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
The snapshot can change after rendering. Inspection does not activate a service,
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

The selling price is manual and independent of provider expense. Price editing does
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

### Confirmed activation changes

`/admin` → Service configuration checks → service → Enable/Disable. The button
only proposes a change. Review unfinished-order counts, test-credit order values,
unpaid Stars orders, recorded paid Stars and receipts already in refund workflow.
Confirm within five minutes or cancel. Prices are never changed. Browsing away
invalidates pending admin confirmations but preserves customer intake/support.
Every confirmation rechecks administrator authorization and current metadata,
activation, prices, payment mode, order states and known receipts against the
frozen fingerprint. A changed snapshot requires a fresh review.

Enable checks code/stored version, required local AI configuration and operational
pause, and a Stars price in Stars mode. It resets the existing circuit baseline,
not pricing, payment configuration or provider budgets. Pending cancellation from
an earlier panel disable must finish first. Mixed services retain actual
input-dependent admission; native tools/provider connection and output quality
are not certified by activation.

Disable commits the gate, immutable decision and cancellation task atomically.
The worker resumes fixed order IDs after a crash; it uses existing customer→order
locks and release/refund-request rules, outside the service lock. At most 100
unfinished orders and 500 relevant receipts can be reviewed through this panel;
larger impacts are refused without mutation and need operational handling. Each
recovery tick takes at most five tasks. A retry never re-applies an old flag change
or adds later/new orders to its cancellation intent. Terminal completed orders
are skipped, including concurrent completion after validation. In-flight provider
calls/delivery may already be underway and cannot be retracted by this gate.

Test credit release is not Stars refund success. Stars payments stay pending or
uncertain until existing Telegram evidence confirms refund. Late receipts follow
the existing cancelled-order payment reconciliation; no receipt is invented.
Activation history shows the last five panel changes, actor, Riyadh timestamp,
snapshot count and cancellation task state. Task completion means local order
settlement, not confirmed external refunds. Existing command/circuit/operator
changes are not retroactively audited here.

Migration 0013 adds immutable decision audit and resumable task tables only. It
changes no default service flags or selling prices. Deploy all bot/worker/API
components together after backup/migration. Actual Telegram mobile and runtime
acceptance is still separate from hosted database/financial tests.
