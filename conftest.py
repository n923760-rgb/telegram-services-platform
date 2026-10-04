import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://services@127.0.0.1:55432/services_test")
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:56379/0")
os.environ.setdefault("BOT_TOKEN", "123456:TEST_TOKEN_ONLY")
