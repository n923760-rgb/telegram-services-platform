"""Exercise native aiogram routing without contacting either Telegram environment."""

import ast
import json
from contextlib import asynccontextmanager
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from aiogram.exceptions import TelegramNetworkError
from aiogram.types import LabeledPrice
from pydantic import SecretStr, ValidationError

from app.core.settings import Config, config
from app.providers.stars import TelegramStars
from app.providers.telegram import create_bot

TOKEN = "123456:TEST_TOKEN_ONLY"


def test_environment_default_is_independent_of_app_environment():
    for app_env in ("development", "test", "production"):
        assert Config(_env_file=None, app_env=app_env).telegram_api_environment == "production"


@pytest.mark.parametrize("value", ["", "staging", "TEST", "https://example.invalid", True])
def test_invalid_environment_does_not_silently_select_production(value):
    with pytest.raises(ValidationError):
        Config(_env_file=None, telegram_api_environment=value)


class Response:
    status = 200

    def __init__(self, result):
        self.result = result

    async def text(self):
        return json.dumps({"ok": True, "result": self.result})


class Transport:
    def __init__(self):
        self.urls = []

    @asynccontextmanager
    async def post(self, url, **kwargs):
        self.urls.append(url)
        method = url.rsplit("/", 1)[-1]
        if method == "sendInvoice":
            result = {"message_id": 1, "date": 0, "chat": {"id": 42, "type": "private"}}
        elif method == "getFile":
            result = {"file_id": "fixture", "file_unique_id": "unique", "file_path": "docs/a"}
        elif method == "getStarTransactions":
            result = {"transactions": []}
        else:
            result = True
        yield Response(result)

    @asynccontextmanager
    async def get(self, url, **kwargs):
        self.urls.append(url)

        class Content:
            async def iter_chunked(self, size):
                yield b"fixture-file"

        response = Response(None)
        response.content = Content()
        yield response


@pytest.mark.parametrize("environment,suffix", [("production", ""), ("test", "test/")])
async def test_native_transport_routes_payment_recovery_webhook_and_files(
    environment, suffix, monkeypatch
):
    monkeypatch.setattr(config(), "telegram_api_environment", environment)
    monkeypatch.setattr(config(), "bot_token", SecretStr(TOKEN))
    bot = create_bot()
    transport = Transport()
    monkeypatch.setattr(bot.session, "create_session", AsyncMock(return_value=transport))
    try:
        await bot.send_invoice(
            chat_id=42,
            title="Fixture",
            description="Fixture invoice only",
            payload="fixture",
            currency="XTR",
            prices=[LabeledPrice(label="Fixture", amount=1)],
            provider_token="",
        )
        payments = TelegramStars(bot)
        assert await payments.refund(42, "fixture-charge") is True
        assert await payments.transactions(0, 100) == []
        await bot.set_webhook("https://example.invalid/webhooks/telegram", secret_token="fixture")
        result = await bot.download("fixture")
        assert result.getvalue() == b"fixture-file"
        assert transport.urls == [
            f"https://api.telegram.org/bot{TOKEN}/{suffix}{method}"
            for method in (
                "sendInvoice",
                "refundStarPayment",
                "getStarTransactions",
                "setWebhook",
                "getFile",
            )
        ] + [f"https://api.telegram.org/file/bot{TOKEN}/{suffix}docs/a"]
    finally:
        await bot.session.close()


async def test_test_api_transport_failure_never_falls_back_to_production(monkeypatch):
    monkeypatch.setattr(config(), "telegram_api_environment", "test")
    monkeypatch.setattr(config(), "bot_token", SecretStr(TOKEN))
    bot = create_bot()
    transport = Transport()

    @asynccontextmanager
    async def fail(url, **kwargs):
        transport.urls.append(url)
        raise TimeoutError
        yield  # async context manager; transport failure occurs before any response.

    transport.post = fail
    monkeypatch.setattr(bot.session, "create_session", AsyncMock(return_value=transport))
    try:
        with pytest.raises(TelegramNetworkError):
            await TelegramStars(bot).refund(42, "fixture-charge")
        assert transport.urls == [f"https://api.telegram.org/bot{TOKEN}/test/refundStarPayment"]
    finally:
        await bot.session.close()


def test_runtime_bot_construction_is_centralized():
    root = Path(__file__).resolve().parents[1] / "app"
    constructors = []
    for path in root.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Call) and (
                isinstance(node.func, ast.Name)
                and node.func.id == "Bot"
                or isinstance(node.func, ast.Attribute)
                and node.func.attr == "Bot"
            ):
                constructors.append(path.relative_to(root).as_posix())
    assert constructors == ["providers/telegram.py"]
