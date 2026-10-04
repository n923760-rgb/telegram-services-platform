"""Retry only PostgreSQL-aborted, database-only operations."""

import asyncio
from functools import wraps

from sqlalchemy.exc import DBAPIError


def transaction_retry(function):
    @wraps(function)
    async def wrapped(*args, **kwargs):
        for attempt in range(3):
            try:
                return await function(*args, **kwargs)
            except DBAPIError as error:
                if getattr(error.orig, "sqlstate", None) not in {"40P01", "40001"} or attempt == 2:
                    raise
                await asyncio.sleep(0.02 * (attempt + 1))

    return wrapped
