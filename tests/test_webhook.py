from datetime import UTC, datetime

import httpx
from aiogram import Bot
from aiogram.fsm.storage.memory import MemoryStorage
from pydantic import SecretStr

from app.api.main import app, lifespan
from app.bot.main import create_dispatcher
from app.core.db import sessions
from app.core.models import User
from app.core.settings import config
from tests.test_bot_flow import Session


async def test_webhook_lifespan_uses_the_selected_test_api(monkeypatch):
    monkeypatch.setattr(config(), "telegram_mode", "webhook")
    monkeypatch.setattr(config(), "telegram_api_environment", "test")
    monkeypatch.setattr(config(), "telegram_webhook_secret", SecretStr("fixture-secret"))
    async with lifespan(app):
        token = config().bot_token.get_secret_value()
        assert app.state.bot.session.api.api_url(token, "sendInvoice") == (
            f"https://api.telegram.org/bot{token}/test/sendInvoice"
        )


async def test_webhook_secret_stream_limit_and_real_dispatch(monkeypatch):
    monkeypatch.setattr(config(), "telegram_mode", "webhook")
    monkeypatch.setattr(config(), "telegram_webhook_secret", SecretStr("fixture-secret"))
    bot = Bot("123456:TEST_TOKEN_ONLY", session=Session())
    dispatcher = create_dispatcher(MemoryStorage(), guard=False)
    monkeypatch.setattr(app.state, "bot", bot, raising=False)
    monkeypatch.setattr(app.state, "dispatcher", dispatcher, raising=False)
    update = {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "date": int(datetime.now(UTC).timestamp()),
            "chat": {"id": 52, "type": "private"},
            "from": {"id": 52, "is_bot": False, "first_name": "Customer"},
            "text": "/start",
        },
    }
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        assert (await client.post("/webhooks/telegram", json=update)).status_code == 403
        headers = {"X-Telegram-Bot-Api-Secret-Token": "fixture-secret"}
        assert (
            await client.post(
                "/webhooks/telegram", content=b"x" * (1024 * 1024 + 1), headers=headers
            )
        ).status_code == 413
        assert (
            await client.post("/webhooks/telegram", content=b"{bad}", headers=headers)
        ).status_code == 422
        assert (
            await client.post("/webhooks/telegram", json=update, headers=headers)
        ).status_code == 200
    async with sessions() as db:
        assert await db.get(User, 52)
    assert len(bot.session.messages) == 1
    await dispatcher.storage.close()
    await bot.session.close()
