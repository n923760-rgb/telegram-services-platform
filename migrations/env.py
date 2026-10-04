import asyncio

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.models import Base
from app.core.settings import config


def offline():
    context.configure(
        url=config().database_url.get_secret_value(),
        target_metadata=Base.metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def sync(connection):
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()


async def online():
    engine = create_async_engine(config().database_url.get_secret_value())
    async with engine.connect() as connection:
        await connection.run_sync(sync)
    await engine.dispose()


if context.is_offline_mode():
    offline()
else:
    asyncio.run(online())
