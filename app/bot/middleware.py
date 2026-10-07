from contextlib import suppress

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery

from app.core.db import sessions
from app.core.i18n import tr
from app.core.models import User
from app.core.users import get_language

RATE_LUA = """local n=redis.call('INCR',KEYS[1]); if n==1 then redis.call('EXPIRE',KEYS[1],ARGV[1]) end; return n"""


class PrivateChatGate(BaseMiddleware):
    """Reject group/unknown-chat updates before any customer routing or FSM state mutation.

    Callback queries without a reachable message cannot be verified as a private chat, so they
    are answered with an alert and dropped instead of being routed into a customer flow.
    """

    async def __call__(self, handler, event, data):
        if isinstance(event, CallbackQuery):
            message = event.message
            private = (
                message is not None
                and getattr(message, "chat", None) is not None
                and message.chat.type == "private"
            )
            if not private:
                with suppress(Exception):
                    await event.answer(tr("private_only"), show_alert=True)
                return
        else:
            chat = getattr(event, "chat", None)
            if chat is None or chat.type != "private":
                with suppress(Exception):
                    await event.answer(tr("private_only"))
                return
        return await handler(event, data)


class UserContext(BaseMiddleware):
    """Resolve the user's stored UI language once per update and expose it as ``lang``."""

    async def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        user_id = getattr(user, "id", None) if user is not None else None
        data["lang"] = await get_language(user_id) if user_id else "ar"
        return await handler(event, data)


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
            lang = data.get("lang", "ar")
            if hasattr(event, "message"):
                await event.answer(tr("rate_limited", lang), show_alert=True)
            else:
                await event.answer(tr("rate_limited", lang))
            return
        return await handler(event, data)
