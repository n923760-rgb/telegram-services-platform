"""Generic order settlement; test credit and real Stars never share units/history."""

from sqlalchemy import select

from app.core.models import StarCharge
from app.wallet.ledger import apply, capture, release, reserve


async def reserve_order(db, order):
    if order.payment_mode == "test_credit":
        await reserve(db, order.user_id, order.price_halala, f"reserve:{order.id}", order.id)


async def capture_order(db, order):
    if order.payment_mode == "test_credit":
        await capture(db, order.user_id, order.price_halala, f"capture:{order.id}", order.id)


async def refund_order(db, order, *, captured=False):
    if order.payment_mode == "test_credit":
        if captured:
            await apply(
                db, order.user_id, "refund", order.price_halala, f"refund:{order.id}", order.id
            )
        else:
            await release(db, order.user_id, order.price_halala, f"release:{order.id}", order.id)
        return True
    from app.payments.stars import request_refund

    charges = list(
        (
            await db.scalars(
                select(StarCharge).where(
                    StarCharge.order_id == order.id, StarCharge.user_id == order.user_id
                )
            )
        ).all()
    )
    for charge in charges:
        await request_refund(db, charge)
    return bool(charges) and all(charge.state == "refunded" for charge in charges)
