"""Explicit operator command: configure the authenticated Telegram Mini App menu."""

import asyncio

from aiogram.exceptions import TelegramAPIError
from aiogram.types import MenuButtonWebApp, WebAppInfo

from app.core.i18n import tr
from app.core.settings import Config, config
from app.providers.telegram import create_bot


async def configure_menu(bot, url: str):
    if not url:
        raise RuntimeError("miniapp_url_required")
    # Validate even when invoked independently of the configured CLI.
    Config(miniapp_url=url)
    try:
        success = await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(text=tr("miniapp_open"), web_app=WebAppInfo(url=url))
        )
    except TelegramAPIError:
        raise RuntimeError("miniapp_menu_setup_failed") from None
    if not success:
        raise RuntimeError("miniapp_menu_setup_failed")


async def main():
    url = config().miniapp_url
    if not url:
        raise RuntimeError("miniapp_url_required")
    bot = create_bot()
    try:
        await configure_menu(bot, url)
    finally:
        await bot.session.close()
    print("Mini App bot menu configured; actual Telegram acceptance still required.")


if __name__ == "__main__":
    asyncio.run(main())
