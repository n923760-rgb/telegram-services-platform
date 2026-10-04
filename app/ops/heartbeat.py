import asyncio

from redis.asyncio import Redis

from app.core.settings import config


async def heartbeat():
    redis = Redis.from_url(config().redis_url.get_secret_value())
    try:
        while True:
            await redis.set("health:bot", "ok", ex=45)
            await asyncio.sleep(10)
    finally:
        await redis.aclose()
