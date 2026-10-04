from aiogram import BaseMiddleware

from app.core.db import sessions
from app.core.i18n import tr
from app.core.models import User

RATE_LUA = """local n=redis.call('INCR',KEYS[1]); if n==1 then redis.call('EXPIRE',KEYS[1],ARGV[1]) end; return n"""


class Guard(BaseMiddleware):
    def __init__(self, redis):
        self.redis = redis

    async def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        if not user:
            return
        try:
            count = await self.redis.eval(RATE_LUA, 1, f"rate:{user.id}", 60)
            async with sessions() as db:
                row = await db.get(User, user.id)
            allowed = not (row and row.banned) and count <= 30
        except Exception:
            allowed = False
        if not allowed:
            if hasattr(event, "message"):
                await event.answer(tr("rate_limited"), show_alert=True)
            else:
                await event.answer(tr("rate_limited"))
            return
        return await handler(event, data)
