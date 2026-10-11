"""Owner-bound result shortcuts; never create an order or reserve funds here."""

import re
from datetime import UTC, datetime, timedelta
from uuid import UUID

from pydantic import ValidationError

from app.core.db import sessions
from app.core.models import Order, Service
from app.core.settings import config
from app.services.base import Result, ServiceError
from app.services.registry import registry


def parse_callback(value):
    match = re.fullmatch(r"follow:([0-9a-f]{32}):([0-2])", value or "")
    if not match:
        raise ServiceError("stale_button")
    return UUID(match[1]), int(match[2])


async def available_followups(user_id, order_id, *, delivering=False):
    """Recheck authoritative source, expiry and target metadata on every use."""
    async with sessions() as db:
        order = await db.get(Order, order_id)
        cutoff = datetime.now(UTC) - timedelta(hours=config().file_ttl_hours)
        if (
            not order
            or order.user_id != user_id
            or order.status not in ({"completed", "delivering"} if delivering else {"completed"})
            or order.updated_at < cutoff
            or not order.result
        ):
            return {}
        source = registry.types.get(order.service_slug)
        if not source or source.version != order.service_version:
            return {}
        try:
            result = Result.model_validate(order.result)
        except ValidationError:
            return {}
        if result.needs_confirmation or not result.text:
            return {}
        actions = {}
        for index, action in enumerate(source.text_followups):
            target = registry.types.get(action.service)
            row = await db.get(Service, action.service)
            if (
                not target
                or not registry.customer_visible(action.service)
                or not row
                or not row.enabled
                or row.version != target.version
                or row.input_schema != target.input_schema.model_dump()
                or (target.requires_ai and not config().ai_enabled)
                or (config().stars_enabled and row.price_stars is None)
            ):
                continue
            try:
                target.validate_followup_text(action.field, result.text)
            except ServiceError:
                continue
            actions[index] = (action, row, result.text)
        return actions
