import asyncio
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisEventIsolation, RedisStorage

from app.bot.handlers import create_router as services_router
from app.bot.middleware import Guard, PrivateChatGate, UserContext
from app.bot.navigation import create_router as navigation_router
from app.bot.ops_handlers import create_router as operations_router
from app.bot.payments import create_router as payments_router
from app.core.db import sessions
from app.core.logging import configure_logging
from app.core.settings import config
from app.ops.heartbeat import heartbeat
from app.services.registry import registry


def create_dispatcher(storage=None, guard=True):
    storage = storage or RedisStorage.from_url(
        config().redis_url.get_secret_value(), state_ttl=3600, data_ttl=3600
    )
    isolation = (
        RedisEventIsolation(redis=storage.redis) if isinstance(storage, RedisStorage) else None
    )
    dp = Dispatcher(storage=storage, events_isolation=isolation)
    dp.message.outer_middleware(PrivateChatGate())
    dp.callback_query.outer_middleware(PrivateChatGate())
    dp.message.outer_middleware(UserContext())
    dp.callback_query.outer_middleware(UserContext())
    if guard:
        dp.message.outer_middleware(Guard(storage.redis))
        dp.callback_query.outer_middleware(Guard(storage.redis))
    dp.include_router(payments_router())
    dp.include_router(navigation_router())
    dp.include_router(operations_router())
    dp.include_router(services_router())
    return dp


async def main():
    configure_logging()
    async with sessions.begin() as db:
        await registry.sync(db)
    cfg = config()
    bot = Bot(cfg.bot_token.get_secret_value())
    dp = create_dispatcher()
    pulse = asyncio.create_task(heartbeat())
    try:
        if cfg.telegram_mode != "polling":
            raise RuntimeError("run webhook mode through API, not polling")
        await bot.delete_webhook(drop_pending_updates=False)
        await dp.start_polling(bot)
    finally:
        pulse.cancel()
        with suppress(asyncio.CancelledError):
            await pulse
        await dp.storage.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
