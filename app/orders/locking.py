from sqlalchemy import select

from app.core.models import Order, User


async def lock_order(db, order_id, *, skip_locked=False):
    """Acquire the customer row before the order; callers may subsequently lock its job."""
    reference = await db.get(Order, order_id)
    if not reference:
        return None
    user = await db.scalar(
        select(User).where(User.id == reference.user_id).with_for_update(skip_locked=skip_locked)
    )
    if user is None:
        return None
    return await db.scalar(
        select(Order)
        .where(Order.id == order_id)
        .with_for_update(skip_locked=skip_locked)
        .execution_options(populate_existing=True)
    )
