"""DB-only completion handoffs. Handlers are trusted internal code, never plugins.

Stage with capture in the order transaction. Consume under customer/order locks;
handlers must use only the supplied DB session, with no AI, I/O or nested transaction.
No handler, entitlement, dispatcher or public consent is registered by this module.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.db import sessions
from app.core.models import Order, OrderCompletion, StarCharge, User
from app.core.settings import config
from app.orders.locking import lock_order
from app.services.base import Result, ServiceError
from app.services.completion import Completion


async def stage_locked(db, order):
    """Caller holds customer/order locks; commit/rollback together with capture."""
    raw = (order.result or {}).get("completion")
    if raw is None:
        return
    result = Result.model_validate(order.result)
    if order.status != "delivering" or result.needs_confirmation:
        raise ServiceError("invalid_request")
    value = Completion.model_validate(result.completion.model_dump())
    digest = value.digest()
    previous = await db.get(OrderCompletion, order.id)
    if previous:
        if (
            previous.owner_id != order.user_id
            or previous.kind != value.kind
            or previous.content_hash != digest
        ):
            raise ServiceError("invalid_request")
        return  # Never replenish purged content or move the original deadline.
    now = datetime.now(UTC)
    db.add(
        OrderCompletion(
            order_id=order.id,
            owner_id=order.user_id,
            kind=value.kind,
            payload=value.payload,
            content_hash=digest,
            state="pending",
            created_at=now,
            expires_at=now + timedelta(hours=config().file_ttl_hours),
        )
    )
    await db.flush()


async def consume(order_id, owner_id, kind, handler):
    """Apply once in one DB transaction; exact replay returns False.

    Internal adapter supplies verified owner, expected kind and a DB-only handler.
    That handler must validate its schema AND commercial entitlement before writes.
    A completed arbitrary order or this row alone is never a hosting entitlement.
    Handler failures roll back its writes and retain the original pending payload.
    There is no automatic transaction retry around the injected handler.
    """
    async with sessions.begin() as db:
        order = await lock_order(db, order_id)
        if not order or order.user_id != owner_id:
            raise ServiceError("not_allowed")
        user = await db.get(User, owner_id)
        if user.banned or order.status != "completed":
            raise ServiceError("not_allowed")
        if order.payment_mode == "stars":
            paid = await db.scalar(
                select(StarCharge.charge_id).where(
                    StarCharge.order_id == order.id,
                    StarCharge.user_id == owner_id,
                    StarCharge.accepted.is_(True),
                    StarCharge.state == "paid",
                    StarCharge.amount == order.price_stars,
                )
            )
            if not paid:
                raise ServiceError("payment_invalid")
        row = await db.scalar(
            select(OrderCompletion).where(OrderCompletion.order_id == order_id).with_for_update()
        )
        if not row or row.owner_id != owner_id or row.kind != kind:
            raise ServiceError("invalid_request")
        if row.state == "applied":
            return False
        if row.state != "pending" or row.expires_at <= datetime.now(UTC):
            raise ServiceError("unavailable")
        checked = Completion(kind=row.kind, payload=row.payload)
        if checked.digest() != row.content_hash:
            raise ServiceError("invalid_request")
        await handler(db, order, checked.payload)
        row.payload, row.state = None, "applied"
        return True


async def purge(ctx=None):
    """Bounded scrub of expired or refunded payloads; never change financial rows."""
    async with sessions() as db:
        ids = list(
            (
                await db.scalars(
                    select(OrderCompletion.order_id)
                    .join(Order, Order.id == OrderCompletion.order_id)
                    .where(
                        OrderCompletion.state == "pending",
                        (OrderCompletion.expires_at <= datetime.now(UTC))
                        | (Order.status != "completed"),
                    )
                    .order_by(OrderCompletion.expires_at, OrderCompletion.order_id)
                    .limit(100)
                )
            ).all()
        )
    for order_id in ids:
        async with sessions.begin() as db:
            order = await lock_order(db, order_id, skip_locked=True)
            if not order:
                continue
            row = await db.scalar(
                select(OrderCompletion)
                .where(OrderCompletion.order_id == order_id)
                .with_for_update()
            )
            if (
                row
                and row.state == "pending"
                and (row.expires_at <= datetime.now(UTC) or order.status != "completed")
            ):
                row.payload, row.state = None, "discarded"
