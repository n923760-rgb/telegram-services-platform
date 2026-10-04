from decimal import Decimal

from app.core.models import Setting
from app.core.settings import config


async def setting(db, key, default=None):
    row = await db.get(Setting, key)
    return (
        row.value["value"]
        if row
        else (default if default is not None else getattr(config(), key.lower()))
    )


async def decimal_setting(db, key):
    from app.services.base import ServiceError

    try:
        value = Decimal(str(await setting(db, key)))
        if not value.is_finite() or value < 0 or (key.startswith("MAX_") and value == 0):
            raise ValueError
        return value
    except (ValueError, ArithmeticError):
        raise ServiceError("provider_config") from None
