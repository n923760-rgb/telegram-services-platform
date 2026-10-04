import asyncio
import sys

import httpx
from redis.asyncio import Redis
from sqlalchemy import text

from app.core.db import sessions
from app.core.settings import config


async def check(kind):
    if kind == "api":
        async with httpx.AsyncClient(timeout=5, trust_env=False) as client:
            (await client.get("http://127.0.0.1:8000/health")).raise_for_status()
        return
    redis = Redis.from_url(config().redis_url.get_secret_value())
    try:
        await redis.ping()
        key = "health:bot" if kind == "bot" else "arq:queue:health-check"
        if not await redis.exists(key):
            raise RuntimeError("missing heartbeat")
    finally:
        await redis.aclose()
    async with sessions() as db:
        await db.execute(text("SELECT 1"))


if __name__ == "__main__":
    asyncio.run(check(sys.argv[1]))
