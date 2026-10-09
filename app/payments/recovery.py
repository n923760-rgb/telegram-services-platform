"""Claim refunds once; reconcile uncertain outcomes with independent API evidence."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select

from app.core.db import sessions
from app.core.models import Order, StarCharge, User
from app.orders.locking import lock_order
from app.orders.state import transition
from app.payments.stars import event, receive, reference


async def locked_charge(db, charge_id):
    reference = await db.get(StarCharge, charge_id)
    if not reference:
        return None
    await db.scalar(select(User).where(User.id == reference.user_id).with_for_update())
    return await db.scalar(
        select(StarCharge)
        .where(StarCharge.charge_id == charge_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )


async def confirm_refund(db, charge):
    charge.state = "refunded"
    charge.lease_token = charge.lease_until = None
    await event(db, charge, "refunded")
    if charge.order_id and charge.accepted:
        reference = await db.get(Order, charge.order_id)
        if reference and reference.user_id == charge.user_id and reference.payment_mode == "stars":
            order = await lock_order(db, charge.order_id)
            if order.status == "completed":
                transition(order, "refunded")
            elif order.status in {"queued", "processing", "delivering", "waiting_confirmation"}:
                from app.orders.engine import fail_locked

                await fail_locked(db, order, "payment_refunded", cancelled=True)


async def refunds(ctx):
    now = datetime.now(UTC)
    async with sessions() as db:
        ids = list(
            (
                await db.scalars(
                    select(StarCharge.charge_id)
                    .where(StarCharge.state.in_(["refund_pending", "refunding"]))
                    .limit(100)
                )
            ).all()
        )
    for charge_id in ids:
        token = uuid4()
        async with sessions.begin() as db:
            charge = await locked_charge(db, charge_id)
            if charge.state == "refunding":
                if charge.lease_until and charge.lease_until > now:
                    continue
                charge.state = "refund_uncertain"
                charge.lease_token = charge.lease_until = None
                await event(db, charge, "refund_uncertain")
                continue
            if charge.state != "refund_pending":
                continue
            charge.state = "refunding"
            charge.lease_token, charge.lease_until = token, now + timedelta(minutes=5)
            await event(db, charge, "refund_started")
            user_id = charge.user_id
        # A crash here leaves a durable in-flight claim, not a fresh retryable refund.
        success = False
        try:
            success = await ctx["stars"].refund(user_id, charge_id) is True
        except Exception:
            pass  # No raw provider bodies or payment/customer data enter logs.
        async with sessions.begin() as db:
            charge = await locked_charge(db, charge_id)
            if charge.lease_token != token or charge.state != "refunding":
                continue
            if success:
                await confirm_refund(db, charge)
            else:
                charge.state = "refund_uncertain"
                charge.lease_token = charge.lease_until = None
                await event(db, charge, "refund_uncertain")
    async with sessions() as db:
        uncertain = await db.scalar(
            select(StarCharge.charge_id).where(StarCharge.state == "refund_uncertain").limit(1)
        )
    if uncertain and ctx.get("notifier"):
        await ctx["notifier"].alert("payment_reconciliation")


async def reconcile(ctx, offset=0, pages=10):
    """Bounded history inspection, never absence-as-proof or blind refund repetition.

    API pagination ordering is not assumed. Operators can scan subsequent offsets;
    a full page bound is reported as incomplete coverage, not account reconciliation.
    """
    if type(offset) is not int or offset < 0 or type(pages) is not int or not 1 <= pages <= 10:
        raise ValueError("invalid history bounds")
    scanned = 0
    for page in range(pages):
        transactions = await ctx["stars"].transactions(offset + page * 100, 100)
        for transaction in transactions:
            scanned += 1
            if getattr(transaction, "nanostar_amount", 0):
                continue
            source = transaction.source
            receiver = transaction.receiver
            if (
                source
                and source.type == "user"
                and source.transaction_type == "invoice_payment"
                and source.invoice_payload
                and transaction.amount > 0
            ):
                order_id = reference(source.invoice_payload)
                async with sessions() as db:
                    order = await db.get(Order, order_id) if order_id else None
                if not order or order.payment_mode != "stars":
                    continue  # Never refund unrelated historic purchases.
                await receive(
                    source.user.id,
                    source.invoice_payload,
                    "XTR",
                    transaction.amount,
                    transaction.id,
                )
            elif receiver and receiver.type == "user" and not source:
                async with sessions.begin() as db:
                    charge = await locked_charge(db, transaction.id)
                    if (
                        charge
                        and charge.user_id == receiver.user.id
                        and charge.amount == abs(transaction.amount)
                    ):
                        await confirm_refund(db, charge)
        if len(transactions) < 100:
            return scanned, True
    return scanned, False
