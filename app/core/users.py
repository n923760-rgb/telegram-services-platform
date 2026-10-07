from app.core.db import sessions
from app.core.models import User


async def get_language(user_id: int) -> str:
    """Return the stored UI language for a user, defaulting to Arabic.

    Read-only: never creates a user row. A missing/unknown user or a transient
    database failure resolves to ``ar`` so customer routing keeps working.
    """
    if not user_id or user_id <= 0:
        return "ar"
    try:
        async with sessions() as db:
            user = await db.get(User, user_id)
        return user.language if user and user.language in {"ar", "en"} else "ar"
    except Exception:
        return "ar"


async def set_language(user_id: int, lang: str) -> None:
    """Persist the user's UI language, creating the user row only if missing."""
    if lang not in {"ar", "en"}:
        raise ValueError("unsupported language")
    async with sessions.begin() as db:
        user = await db.get(User, user_id)
        if user is None:
            user = User(id=user_id, language=lang, banned=False)
            db.add(user)
        else:
            user.language = lang
