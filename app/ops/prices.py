"""Owner-controlled Stars prices; provider expense remains independent."""

from uuid import UUID

from sqlalchemy import select

from app.core.db import sessions
from app.core.models import Service, StarPriceChange
from app.core.settings import config
from app.core.transactions import transaction_retry
from app.services.base import ServiceError


@transaction_retry
async def change_stars_price(slug, new_price, *, expected_price, actor_id, change_id):
    if type(actor_id) is not int or actor_id not in config().admin_ids:
        raise ServiceError("not_allowed")
    if type(new_price) is not int or not 1 <= new_price <= 1000000:
        raise ServiceError("input_invalid")
    if expected_price is not None and (
        type(expected_price) is not int or not 1 <= expected_price <= 1000000
    ):
        raise ServiceError("input_invalid")
    try:
        change_id = UUID(str(change_id))
    except (ValueError, TypeError, AttributeError):
        raise ServiceError("input_invalid") from None
    async with sessions.begin() as db:
        service = await db.scalar(select(Service).where(Service.slug == slug).with_for_update())
        if not service:
            raise ServiceError("unavailable")
        previous = await db.get(StarPriceChange, change_id)
        if previous:
            if (
                previous.actor_id,
                previous.service_slug,
                previous.old_price,
                previous.new_price,
            ) != (actor_id, slug, expected_price, new_price):
                raise ServiceError("invalid_request")
            return
        if service.price_stars != expected_price:
            raise ServiceError("price_changed")
        if service.price_stars == new_price:
            return
        db.add(
            StarPriceChange(
                id=change_id,
                actor_id=actor_id,
                service_slug=slug,
                old_price=service.price_stars,
                new_price=new_price,
            )
        )
        service.price_stars = new_price
