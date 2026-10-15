"""Read-only configuration evidence, not runtime or customer-quality certification."""

from app.core.settings import config
from app.ops.settings import provider_paused
from app.providers.runtime import provider
from app.services.base import ServiceError
from app.services.registry import registry


async def ai_configuration(db):
    if not config().ai_enabled:
        return "off"
    if await provider_paused(db):
        return "paused"
    try:
        if provider().upper_bound({}, "", "", []) <= 0:
            return "invalid"
    except (ValueError, ServiceError):
        return "invalid"
    return "configured"


def checks(row, *, ai_state, stars_enabled):
    """Use plugin metadata only; never call needs_ai with fabricated customer inputs."""
    plugin = registry.types.get(row.slug)
    if plugin is None or not registry.customer_visible(row.slug):
        raise ServiceError("unavailable")
    return {
        "enabled": row.enabled,
        "version_matches": row.version == plugin.version,
        "source_version": plugin.version,
        "listed": row.enabled
        and not plugin.admin_only
        and (not stars_enabled or row.price_stars is not None),
        "admin_only": plugin.admin_only,
        "ai_required": plugin.requires_ai,
        "ai_state": ai_state,
        "stars_enabled": stars_enabled,
        "stars_price_missing": stars_enabled and row.price_stars is None,
    }
