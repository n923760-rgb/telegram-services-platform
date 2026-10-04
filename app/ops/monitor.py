import asyncio

from aiogram import Bot
from redis.asyncio import Redis
from sqlalchemy import text

from app.core.db import sessions
from app.core.settings import config
from app.ops.notifier import Notifier
from app.providers.notifier import TelegramAdminChannel


async def monitor_once(redis, notifier):
    low_balance = False
    try:
        async with asyncio.timeout(4):
            async with sessions() as db:
                await db.execute(text("SELECT 1"))
                from decimal import Decimal

                from app.ops.settings import decimal_setting, setting

                reported = await setting(db, "PROVIDER_BALANCE_SAR", default="unknown")
                if reported != "unknown" and Decimal(str(reported)) < await decimal_setting(
                    db, "PROVIDER_LOW_BALANCE_SAR"
                ):
                    low_balance = True
    except Exception:
        await notifier.alert("database_unreachable")
    if low_balance:
        await notifier.alert("low_provider_balance")
    try:
        await redis.ping()
        if not await redis.exists("arq:queue:health-check"):
            await notifier.alert("worker_unreachable")
        if config().telegram_mode == "polling" and not await redis.exists("health:bot"):
            await notifier.alert("bot_unreachable")
    except Exception:
        await notifier.alert("redis_unreachable")


async def main():
    bot = Bot(config().bot_token.get_secret_value())
    redis = Redis.from_url(config().redis_url.get_secret_value(), socket_timeout=3)
    notifier = Notifier(redis, TelegramAdminChannel(bot))
    try:
        await asyncio.sleep(45)
        while True:
            try:
                await monitor_once(redis, notifier)
            except Exception:
                pass  # The monitor must survive a Telegram transport outage.
            await asyncio.sleep(30)
    finally:
        await redis.aclose()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
