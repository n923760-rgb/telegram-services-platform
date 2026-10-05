from uuid import UUID

from sqlalchemy import select

from app.core.db import sessions
from app.core.models import Order, Service, Setting, User
from app.core.transactions import transaction_retry
from app.orders.locking import lock_order
from app.orders.state import transition
from app.services.base import ServiceError
from app.wallet.ledger import apply


@transaction_retry
async def refund(order_id):
    async with sessions.begin() as db:
        order = await lock_order(db, UUID(str(order_id)))
        if not order or order.status not in {"completed", "refunded"}:
            raise ServiceError("refund_invalid")
        await apply(db, order.user_id, "refund", order.price_halala, f"refund:{order.id}", order.id)
        transition(order, "refunded")
        return order.id


async def set_service(slug, enabled=None, price=None):
    async with sessions.begin() as db:
        service = await db.scalar(select(Service).where(Service.slug == slug).with_for_update())
        if not service:
            raise ServiceError("unavailable")
        if enabled:
            from app.services.registry import registry

            plugin = registry.types.get(slug)
            if plugin is None:
                raise ServiceError("unavailable")
            if plugin.requires_ai:
                from app.providers.runtime import provider

                try:
                    if provider().upper_bound({}, "", "", []) <= 0:
                        raise ValueError
                except (ValueError, ServiceError):
                    raise ServiceError("provider_config") from None
        if enabled is not None:
            service.enabled = enabled
            if enabled:
                from datetime import UTC, datetime

                await db.merge(
                    Setting(
                        key=f"CIRCUIT_RESET:{slug}", value={"value": datetime.now(UTC).isoformat()}
                    )
                )
        if price is not None:
            service.price_halala = price
    if enabled is False:
        from app.orders.engine import fail_locked

        async with sessions() as db:
            ids = list(
                (
                    await db.scalars(
                        select(Order.id).where(
                            Order.service_slug == slug,
                            Order.status.in_(
                                ["queued", "processing", "waiting_confirmation", "delivering"]
                            ),
                        )
                    )
                ).all()
            )
        for order_id in ids:
            async with sessions.begin() as db:
                order = await lock_order(db, order_id)
                await fail_locked(db, order, "unavailable", cancelled=True)


@transaction_retry
async def ban(user_id):
    async with sessions.begin() as db:
        user = await db.get(User, user_id)
        if not user:
            raise ServiceError("invalid_request")
        user.banned = True
