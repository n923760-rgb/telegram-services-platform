from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.settings import config

engine = create_async_engine(
    config().database_url.get_secret_value(),
    pool_pre_ping=True,
    echo=False,
    hide_parameters=True,
    **({"poolclass": NullPool} if config().app_env == "test" else {}),
)
sessions = async_sessionmaker(engine, expire_on_commit=False)
