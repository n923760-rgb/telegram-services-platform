from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update

from app.core.db import sessions
from app.core.models import Order
from app.core.settings import config
from app.providers.runtime import storage


async def cleanup(ctx=None):
    await cleanup_terminal_files()
    cfg = config()
    store = storage()
    cutoff = datetime.now(UTC) - timedelta(hours=cfg.file_ttl_hours)
    from app.orders.engine import fail_locked
    from app.orders.locking import lock_order

    expiry = datetime.now(UTC) - timedelta(minutes=30)
    async with sessions() as db:
        waiting = list(
            (
                await db.scalars(
                    select(Order.id).where(
                        Order.status == "waiting_confirmation", Order.updated_at < expiry
                    )
                )
            ).all()
        )
    for order_id in waiting:
        async with sessions.begin() as db:
            order = await lock_order(db, order_id, skip_locked=True)
            if order and order.status == "waiting_confirmation" and order.updated_at < expiry:
                await fail_locked(db, order, "confirmation_expired", cancelled=True)
    async with sessions.begin() as db:
        orders = list(
            (
                await db.scalars(
                    select(Order).where(
                        Order.updated_at < cutoff,
                        Order.status.in_(["completed", "failed", "refunded", "cancelled"]),
                    )
                )
            ).all()
        )
        for order in orders:
            order.inputs = {}
            order.result = None
    store.expire_before(cutoff)


async def delete_inputs(inputs, schema, owned_storage):
    from app.services.base import InputSchema

    success = True
    for field in InputSchema.model_validate(schema).conversation():
        if field.kind not in {"image", "file", "audio"}:
            continue
        value = inputs
        for part in field.name.split("."):
            value = value.get(part) if isinstance(value, dict) else None
        for key in value if isinstance(value, list) else [value]:
            if isinstance(key, str):
                try:
                    owned_storage.delete(key)
                except Exception:
                    success = False

    return success


async def cleanup_order_files(order_id, owned_storage=None):
    from app.providers.storage import OwnedStorage

    async with sessions() as db:
        order = await db.get(Order, order_id)
    if not order or order.status not in {"completed", "failed", "cancelled", "refunded"}:
        return False
    if order.files_deleted:
        return True
    owned = owned_storage or OwnedStorage(storage(), order.user_id)
    success = await delete_inputs(order.inputs, order.input_schema_snapshot, owned)
    for artifact in (order.result or {}).get("artifacts", []):
        try:
            owned.delete(artifact["key"])
        except Exception:
            success = False
    if success:
        async with sessions.begin() as db:
            await db.execute(update(Order).where(Order.id == order_id).values(files_deleted=True))
    return success


async def cleanup_terminal_files(ctx=None):
    async with sessions() as db:
        ids = list(
            (
                await db.scalars(
                    select(Order.id)
                    .where(
                        Order.files_deleted.is_(False),
                        Order.status.in_(["completed", "failed", "cancelled", "refunded"]),
                    )
                    .order_by(Order.created_at, Order.id)
                    .limit(100)
                )
            ).all()
        )
    for order_id in ids:
        try:
            await cleanup_order_files(order_id)
        except Exception:
            continue  # Retain the durable marker for the next sweep; never log content.
