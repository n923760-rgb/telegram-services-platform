from datetime import UTC, datetime

import pytest
from aiogram import Bot
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Chat, Message, Update, User

from app.bot.main import create_dispatcher
from app.core.db import sessions
from app.core.models import Order, Service
from app.orders.engine import submit
from app.services.base import BaseService, InputField, InputSchema, Result, ServiceError
from app.services.registry import registry
from app.wallet.ledger import balance
from app.workers.runner import execute_job
from tests.test_bot_flow import Session
from tests.test_foundation import Delivery, fund, job_for


async def test_plugin_upgrade_releases_old_pending_order(monkeypatch):
    await fund()
    oid = await submit(1, "echo", {"text": "old"}, 100, "version")
    monkeypatch.setattr(registry.types["echo"], "version", "2")
    async with sessions.begin() as db:
        await registry.sync(db)
    await execute_job({"delivery": Delivery()}, str(await job_for(oid)))
    async with sessions() as db:
        order = await db.get(Order, oid)
        assert order.status == "cancelled" and order.service_version == "1"
        assert (await balance(db, 1)).available == 1000
        assert (await db.get(Service, "echo")).version == "2"
    with pytest.raises(ServiceError, match="service_changed"):
        await submit(1, "echo", {"text": "new"}, 100, "stale", expected_version="1")


async def test_schema_rejects_bad_inputs_before_reserving():
    await fund()
    with pytest.raises(ServiceError, match="input_invalid"):
        await submit(1, "echo", {"text": ""}, 100, "empty")
    with pytest.raises(ServiceError, match="invalid_request"):
        await submit(1, "echo", {"text": "x", "__continuation": {}}, 100, "internal")
    async with sessions() as db:
        assert (await balance(db, 1)).reserved == 0


async def test_generic_bot_optional_nested_form_and_multiple_uploads(monkeypatch):
    class FixtureService(BaseService):
        slug = "fixture_service"
        name_ar = "خدمة اختبار"
        name_en = "Fixture service"
        description_ar = "اختبار التوسعة"
        price_sar = registry.types["echo"].price_sar
        input_schema = InputSchema(
            fields=[
                InputField(name="text", prompt_key="input_text"),
                InputField(name="note", prompt_key="input_text", required=False),
                InputField(
                    name="form",
                    kind="form",
                    prompt_key="input_text",
                    fields=[
                        InputField(
                            name="images", kind="image", prompt_key="ocr_images", multiple=True
                        ),
                    ],
                ),
            ]
        )

        async def run(self, inputs):
            return Result(text=inputs["text"])

    monkeypatch.setitem(registry.types, FixtureService.slug, FixtureService)
    async with sessions.begin() as db:
        await registry.sync(db)
    await fund()
    transport = Session()
    bot = Bot("123456:TEST_TOKEN_ONLY", session=transport)
    dp = create_dispatcher(MemoryStorage(), guard=False)
    user = User(id=1, is_bot=False, first_name="Customer")
    sequence = 0

    async def message(text):
        nonlocal sequence
        sequence += 1
        await dp.feed_update(
            bot,
            Update(
                update_id=sequence,
                message=Message(
                    message_id=sequence,
                    date=datetime.now(UTC),
                    chat=Chat(id=1, type="private"),
                    from_user=user,
                    text=text,
                ),
            ),
        )

    async def callback(data):
        nonlocal sequence
        sequence += 1
        await dp.feed_update(
            bot,
            Update(
                update_id=sequence,
                callback_query=CallbackQuery(
                    id=str(sequence),
                    from_user=user,
                    chat_instance="fixture",
                    message=transport.messages[-1],
                    data=data,
                ),
            ),
        )

    from app.files import telegram

    async def receive(*args):
        return "1/" + "a" * 32 + "/input.jpg"

    monkeypatch.setattr(telegram, "receive", receive)
    await message("/start")
    await callback("service:fixture_service")
    await message("طلب")
    await callback(transport.messages[-1].reply_markup.inline_keyboard[0][0].callback_data)
    await message("upload")
    await callback(transport.messages[-1].reply_markup.inline_keyboard[0][0].callback_data)
    await callback(transport.messages[-1].reply_markup.inline_keyboard[0][0].callback_data)
    from sqlalchemy import select

    async with sessions() as db:
        order = await db.scalar(select(Order))
        assert order.inputs == {"text": "طلب", "form": {"images": ["1/" + "a" * 32 + "/input.jpg"]}}
    await dp.storage.close()
    await bot.session.close()


async def test_registry_refuses_contract_change_without_version_bump(monkeypatch):
    from app.services.echo.service import Echo

    schema = InputSchema(fields=[InputField(name="text", prompt_key="input_text", max_length=100)])
    monkeypatch.setattr(Echo, "input_schema", schema)
    with pytest.raises(ValueError, match="Bump the plugin version"):
        async with sessions.begin() as db:
            await registry.sync(db)
