from aiogram.exceptions import TelegramAPIError

from app.core.i18n import tr
from app.services.base import ServiceError


async def update_profile(bot):
    # Explicit admin command only. Arabic default covers unsupported UI languages.
    # Retrying is idempotent; Telegram cannot make all six writes atomic.
    try:
        for language in ("", "ar", "en"):
            catalog = language or "ar"
            if not await bot.set_my_description(
                description=tr("bot_description", catalog), language_code=language
            ):
                raise ServiceError("profile_update_failed")
            if not await bot.set_my_short_description(
                short_description=tr("bot_short_description", catalog), language_code=language
            ):
                raise ServiceError("profile_update_failed")
    except TelegramAPIError:
        raise ServiceError("profile_update_failed") from None
