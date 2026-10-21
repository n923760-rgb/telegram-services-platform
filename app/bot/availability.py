"""Read-only UI admission hints; order submission remains authoritative."""

from app.core.db import sessions
from app.core.settings import config
from app.ops.settings import provider_paused
from app.services.base import InputSchema
from app.services.registry import registry


async def ai_admission_available(db):
    if not config().ai_enabled:
        return False
    return not await provider_paused(db)


async def mandatory_ai_unavailable(slug):
    plugin = registry.types.get(slug)
    if not plugin or not plugin.requires_ai:
        return False
    async with sessions() as db:
        return not await ai_admission_available(db)


def declared_ai_choices(data):
    """Do not apply current UI hints to a stale version or different draft schema."""
    plugin = registry.types.get(data.get("slug"))
    if (
        not plugin
        or data.get("version") != plugin.version
        or not plugin.ai_intake_choices
        or InputSchema.model_validate(data["schema"]) != plugin.input_schema
    ):
        return {}
    return plugin.ai_intake_choices


async def mixed_ai_unavailable(data):
    if not declared_ai_choices(data):
        return False
    if not config().ai_enabled:
        return True
    async with sessions() as db:
        return not await ai_admission_available(db)
