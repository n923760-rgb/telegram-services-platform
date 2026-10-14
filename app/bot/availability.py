"""Read-only UI admission hints; order submission remains authoritative."""

from app.core.db import sessions
from app.core.models import Setting
from app.core.settings import config
from app.services.registry import registry


async def ai_admission_available(db):
    if not config().ai_enabled:
        return False
    row = await db.get(Setting, "PROVIDER_PAUSED")
    return row is None or (isinstance(row.value, dict) and row.value.get("value") is False)


async def mandatory_ai_unavailable(slug):
    plugin = registry.types.get(slug)
    if not plugin or not plugin.requires_ai:
        return False
    async with sessions() as db:
        return not await ai_admission_available(db)
