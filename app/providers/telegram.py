"""Select Telegram's official API consistently for every runtime process."""

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import PRODUCTION, TEST

from app.core.settings import config


def create_bot() -> Bot:
    cfg = config()
    api = TEST if cfg.telegram_api_environment == "test" else PRODUCTION
    return Bot(cfg.bot_token.get_secret_value(), session=AiohttpSession(api=api))
