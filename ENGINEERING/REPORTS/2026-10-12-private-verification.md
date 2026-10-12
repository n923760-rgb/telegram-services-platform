# Administrator-only verification — 2026-10-12

The owner approved hiding the verification service from customer menus and keeping
it for admins. Hiding a button alone leaves old callbacks and direct new-order paths.

## Generic implementation

- BaseService.admin_only defaults False and registry discovery requires a real bool.
- Echo alone declares True; renamed Internal admin test / تجربة داخلية للأدمن.
- Registry.can_request uses canonical visibility and an explicit trusted admin boolean.
- Customer menu role comes from authenticated message/callback sender, never bot-message
  sender or a client flag. Existing Other category disappears if no available public items;
  admin sees the internal tool, subject to normal enabled/Stars-price filters.
- Direct selection, followups and new-order submission enforce the same metadata.
- Stars pre-checkout rechecks current role before authorizing an unpaid checkout.
- Admin management remains authorized separately and can inspect/configure the tool.
- No new dependencies, migrations, prices, enabled defaults, versions, input contract or
  AI calls. Admin verification is not made free and uses current ordinary billing policy.

## Historical boundaries

Do not cancel accepted orders or rewrite ledger/payment history on role changes.
Prior accepted jobs continue; cached delivery and matching idempotent replays retain
their existing semantics without creating a new order. Unpaid checkouts revalidate
role; recorded successful receipts and refund recovery remain unchanged.

## Test evidence and limits

Eight local pure audience/menu/inspection tests PASS; lint/format/architecture checks PASS.
Admin inspection explicitly discloses private audience and does not claim customer listing.
New PostgreSQL/router cases test non-admin old category and direct callbacks, preserved
drafts/no orders or reservations, admin execution, revoked confirmation/pre-checkout,
generic private metadata on a different plugin, and an already-paid job after revocation.

The shared PostgreSQL fixture explicitly makes echo a synthetic public plugin for
existing generic financial/security tests. Dedicated audience tests depend on that
fixture then restore production admin_only=True; pure tests independently assert the
actual code default is True. No historic financial assertions/cases are removed/skipped.
Full exact-head hosted qualification required before merge. Fixtures are not real Stars
purchases/refunds, actual VPS deployment or non-admin mobile acceptance.

After deployment open /services from an admin and a non-admin account. With no other
public service in Other, only admin should see that category. Old customer buttons
must reject new verification requests; existing history remains accessible to its owner.
