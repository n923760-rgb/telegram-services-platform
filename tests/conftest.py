import pytest
from sqlalchemy import text

from app.core.db import sessions
from app.core.settings import config
from app.services.registry import registry


@pytest.fixture(autouse=True)
async def database():
    if not config().database_url.get_secret_value().split("?")[0].endswith("_test"):
        pytest.fail("Tests require a disposable database ending in _test")
    async with sessions.begin() as db:
        from app.core.models import Base

        names = ", ".join(table.name for table in Base.metadata.sorted_tables)
        await db.execute(text(f"TRUNCATE {names} CASCADE"))
        await registry.sync(db)
    yield
