# Bot administration and owner-set prices

Only configured ADMIN_IDS can open `/admin` or the Admin panel button on their
home keyboard. The panel shows six services per page, enabled/disabled state and
Stars price. It also provides order-status totals, today's Stars report and the
last five recorded price edits (Riyadh time). Opening controls creates no order,
reservation or provider call, and preserves customer intake/support state.

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
