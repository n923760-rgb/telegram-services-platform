"""Durable direct checkout; no network calls inside monetary DB transactions."""

import hashlib
import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert

from app.core.db import sessions
from app.core.models import Job, Order, Service, StarCharge, StarCheckout, StarEvent, User
from app.core.settings import config
from app.core.transactions import transaction_retry
from app.orders.locking import lock_order
from app.orders.state import transition
from app.services.base import ServiceError
from app.services.registry import registry


def terms_hash():
    cfg = config()
    return hashlib.sha256(
        json.dumps(
            [cfg.stars_terms_version, cfg.stars_terms_ar, cfg.stars_terms_en], ensure_ascii=False
        ).encode()
    ).hexdigest()


def payload(order_id):
    return f"stars:{order_id}"


def reference(value):
    try:
        if not value.startswith("stars:"):
            return None
        return UUID(value[6:])
    except (ValueError, AttributeError):
        return None


async def event(db, charge, kind):
    await db.execute(
        insert(StarEvent)
        .values(id=uuid4(), charge_id=charge.charge_id, kind=kind)
        .on_conflict_do_nothing()
    )


async def request_refund(db, charge):
    if charge.state == "paid":
        charge.state = "refund_pending"
    if charge.state == "refund_pending":
        await event(db, charge, "refund_requested")


@transaction_retry
async def pre_checkout(user_id, invoice_payload, currency, amount, query_id):
    order_id = reference(invoice_payload)
    if (
        not config().stars_enabled
        or currency != "XTR"
        or not order_id
        or not query_id
        or len(query_id) > 200
    ):
        raise ServiceError("payment_invalid")
    async with sessions.begin() as db:
        order = await lock_order(db, order_id)
        if (
            not order
            or order.user_id != user_id
            or order.payment_mode != "stars"
            or order.status != "awaiting_payment"
            or type(amount) is not int
            or order.price_stars != amount
        ):
            raise ServiceError("payment_invalid")
        checkout = await db.get(StarCheckout, order_id)
        user = await db.get(User, user_id)
        service = await db.get(Service, order.service_slug)
        plugin = registry.types.get(order.service_slug)
        if (
            not checkout
            or checkout.expires_at <= datetime.now(UTC)
            or user.banned
            or not service
            or not service.enabled
            or not plugin
            or service.version != order.service_version
            or plugin.version != order.service_version
            or service.price_stars != amount
            or order.terms_hash != terms_hash()
        ):
            raise ServiceError("payment_invalid")
        if checkout.query_id is not None and checkout.query_id != query_id:
            raise ServiceError("payment_invalid")
        from app.ops.costs import check_admission
        from app.ops.settings import setting

        await check_admission(db, user_id)
        if plugin.needs_ai(order.inputs) and (
            not config().ai_enabled or await setting(db, "PROVIDER_PAUSED", default=False)
        ):
            raise ServiceError("provider_config")
        checkout.query_id = query_id
        return order.id


@transaction_retry
async def receive(user_id, invoice_payload, currency, amount, charge_id):
    """Accept only authenticated Telegram receipts/transaction evidence at the adapter.

    Known money is persisted even after the feature gate is disabled or a buyer banned.
    Unexpected second/late/mismatched charges become refundable audit records.
    """
    if (
        type(user_id) is not int
        or user_id <= 0
        or currency != "XTR"
        or type(amount) is not int
        or not 1 <= amount <= 1000000
        or not isinstance(charge_id, str)
        or not 1 <= len(charge_id) <= 255
        or not isinstance(invoice_payload, str)
        or len(invoice_payload) > 128
    ):
        raise ServiceError("payment_invalid")
    async with sessions.begin() as db:
        # Register within this same DB-only retry boundary; nesting register's
        # decorator would multiply the three-attempt cap during repeated aborts.
        await db.execute(
            insert(User).values(id=user_id, language="ar", banned=False).on_conflict_do_nothing()
        )
        user = await db.scalar(select(User).where(User.id == user_id).with_for_update())
        await db.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:charge, 0))"),
            {"charge": "star:" + charge_id},
        )
        previous = await db.get(StarCharge, charge_id)
        if previous:
            if (previous.user_id, previous.amount, previous.payload) != (
                user_id,
                amount,
                invoice_payload,
            ):
                raise ServiceError("payment_invalid")
            return previous.order_id, previous.state
        order_id = reference(invoice_payload)
        order = await db.get(Order, order_id) if order_id else None
        if order and order.user_id == user_id:
            order = await lock_order(db, order_id)
        checkout = await db.get(StarCheckout, order_id) if order else None
        existing = (
            await db.scalar(
                select(StarCharge.charge_id).where(
                    StarCharge.order_id == order_id, StarCharge.accepted.is_(True)
                )
            )
            if order
            else None
        )
        accepted = bool(
            order
            and order.user_id == user_id
            and order.payment_mode == "stars"
            and order.price_stars == amount
            and order.status == "awaiting_payment"
            and checkout
            and checkout.query_id
            and not user.banned
            and not existing
        )
        charge = StarCharge(
            charge_id=charge_id,
            order_id=order.id if order else None,
            user_id=user_id,
            amount=amount,
            accepted=accepted,
            payload=invoice_payload,
            state="paid" if accepted else "refund_pending",
        )
        db.add(charge)
        await db.flush()
        await event(db, charge, "received")
        if accepted:
            transition(order, "queued")
            db.add(Job(order_id=order.id, status="pending"))
        else:
            await request_refund(db, charge)
        return charge.order_id, charge.state


async def cancel_invoice(order_id, user_id):
    from app.orders.engine import fail_locked

    async with sessions.begin() as db:
        order = await lock_order(db, order_id)
        if not order or order.user_id != user_id or order.status != "awaiting_payment":
            raise ServiceError("payment_invalid")
        await fail_locked(db, order, "payment_expired", cancelled=True)


async def expire_invoices(ctx=None):
    async with sessions() as db:
        rows = list(
            (
                await db.execute(
                    select(Order.id, Order.user_id)
                    .join(StarCheckout)
                    .where(
                        Order.status == "awaiting_payment",
                        StarCheckout.expires_at <= datetime.now(UTC),
                    )
                    .limit(100)
                )
            ).all()
        )
    for order_id, user_id in rows:
        try:
            await cancel_invoice(order_id, user_id)
        except ServiceError:
            pass  # Receipt/cancellation may have won the same customer/order lock.
