"""Bounded, provider-free recovery of administrative prepared profile handoffs."""

import logging
from datetime import UTC, datetime

from sqlalchemy import select, tuple_

from app.core.db import sessions
from app.core.models import Order, OrderCompletion, User
from app.core.settings import config
from app.publications.fulfillment import KIND, transfer_purchased

logger = logging.getLogger(__name__)
BATCH = 10


async def candidates(cursor=None):
    now = datetime.now(UTC)
    statement = (
        select(OrderCompletion.order_id, OrderCompletion.owner_id, OrderCompletion.created_at)
        .join(Order, Order.id == OrderCompletion.order_id)
        .join(User, User.id == OrderCompletion.owner_id)
        .where(
            OrderCompletion.kind == KIND,
            OrderCompletion.state == "pending",
            OrderCompletion.expires_at > now,
            Order.status == "completed",
            Order.user_id == OrderCompletion.owner_id,
            Order.purchase_terms_hash.is_not(None),
            User.banned.is_(False),
            # Pilot only. Role loss blocks unattended projection too.
            User.id.in_(config().admin_ids),
        )
        .order_by(OrderCompletion.created_at, OrderCompletion.order_id)
        .limit(BATCH)
    )
    if cursor is not None:
        statement = statement.where(
            tuple_(OrderCompletion.created_at, OrderCompletion.order_id) > cursor
        )
    async with sessions() as db:
        return list((await db.execute(statement)).all())


async def dispatch_profiles(ctx):
    """DB pending rows are the queue; no AI, publish, charge or payload recreation.

    A lost process simply leaves pending evidence for the next scan. Atomic
    consumption makes a repeated/concurrent projection harmless. The cursor is
    only a fairness hint, not a receipt; restart never acknowledges unfinished work.
    """
    if not config().publications_enabled or not config().admin_ids:
        return {"selected": 0, "applied": 0, "deferred": 0}
    cursor = ctx.get("profile_dispatch_cursor")
    rows = await candidates(cursor)
    if not rows and cursor is not None:
        rows = await candidates()
    counts = {"selected": len(rows), "applied": 0, "deferred": 0}
    for identity, owner, created in rows:
        # Advance even for malformed evidence so it cannot starve later rows.
        ctx["profile_dispatch_cursor"] = (created, identity)
        try:
            applied = await transfer_purchased(owner, identity, origin=config().publication_origin)
            counts["applied"] += int(applied)
        except Exception:
            # Never print exception bodies, source, URLs or provider details.
            # Cancellation/BaseException propagates; pending DB evidence survives.
            counts["deferred"] += 1
            logger.warning("profile_dispatch_deferred order=%s", identity)
    ctx["profile_dispatch_last"] = counts
    return counts
