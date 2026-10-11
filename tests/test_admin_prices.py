"""Real PostgreSQL price audit and actual dispatcher controls; no Telegram writes."""

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from aiogram import Bot
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Chat, Message, Update, User
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError

from app.bot.main import create_dispatcher
from app.core.db import sessions
from app.core.i18n import tr
from app.core.models import CostUsage, Job, Order, Service, StarPriceChange
from app.core.settings import config
from app.ops.prices import change_stars_price
from app.services.base import ServiceError
from app.services.registry import registry
from tests.test_bot_flow import Session
from tests.test_stars import pay, prepare
from tests.test_stars import stars as stars


@pytest.fixture
def owner(monkeypatch):
    monkeypatch.setattr(config(), "admin_ids", [7, 8])


async def change(price=25, old=None, actor=7, key=None, slug="echo"):
    await change_stars_price(
        slug, price, expected_price=old, actor_id=actor, change_id=key or uuid4()
    )


async def test_price_and_audit_atomic_idempotent_and_registry_sync_preserves(owner):
    key = uuid4()
    await asyncio.gather(change(key=key), change(key=key))
    async with sessions.begin() as db:
        await registry.sync(db)
    async with sessions() as db:
        row = await db.get(Service, "echo")
        audit = await db.get(StarPriceChange, key)
        assert row.price_stars == 25 and row.price_halala == 100 and row.enabled
        assert audit.actor_id == 7 and audit.old_price is None and audit.new_price == 25
        assert await db.scalar(select(func.count(StarPriceChange.id))) == 1
    with pytest.raises(ServiceError, match="invalid_request"):
        await change(price=26, key=key)


async def test_concurrent_edit_detects_stale_snapshot(owner):
    results = await asyncio.gather(change(25), change(30, actor=8), return_exceptions=True)
    assert sum(isinstance(result, ServiceError) for result in results) == 1
    error = next(result for result in results if isinstance(result, ServiceError))
    assert error.key == "price_changed"
    async with sessions() as db:
        assert await db.scalar(select(func.count(StarPriceChange.id))) == 1


@pytest.mark.parametrize("price", [0, -1, 1000001, True, 1.5, "25"])
async def test_invalid_price_reserves_nothing(owner, price):
    with pytest.raises(ServiceError, match="input_invalid"):
        await change(price=price)
    async with sessions() as db:
        assert (await db.get(Service, "echo")).price_stars is None
        assert await db.scalar(select(func.count(StarPriceChange.id))) == 0


@pytest.mark.parametrize("snapshot", [True, 0, -1, "25"])
async def test_invalid_price_snapshot_rejected(owner, snapshot):
    with pytest.raises(ServiceError, match="input_invalid"):
        await change(old=snapshot)


async def test_unauthorized_price_change_fails_server_side(owner):
    with pytest.raises(ServiceError, match="not_allowed"):
        await change(actor=1)
    async with sessions() as db:
        assert (await db.get(Service, "echo")).price_stars is None


@pytest.mark.parametrize(
    "sql", ["UPDATE star_price_changes SET new_price=26", "DELETE FROM star_price_changes"]
)
async def test_price_audit_is_immutable(owner, sql):
    await change()
    with pytest.raises(DBAPIError):
        async with sessions.begin() as db:
            await db.execute(text(sql))


async def test_price_change_invalidates_unpaid_invoice_preserves_paid_price(stars, owner):
    from app.payments.stars import payload, pre_checkout

    first = await prepare(key="paid")
    await pay(first, charge="paid-price")
    second = await prepare(key="unpaid", user_id=2)
    await change(price=25, old=20)
    with pytest.raises(ServiceError):
        await pre_checkout(2, payload(second), "XTR", 20, "old-invoice")
    async with sessions() as db:
        assert (await db.get(Service, "echo")).price_stars == 25
        assert (await db.get(Order, first)).price_stars == 20
        assert (await db.get(Order, second)).price_stars == 20


class Conversation:
    def __init__(self):
        self.transport = Session()
        self.bot = Bot("123456:TEST_TOKEN_ONLY", session=self.transport)
        self.dp = create_dispatcher(MemoryStorage(), guard=False)
        self.sequence = 0
        self.actor = User(id=7, is_bot=False, first_name="Owner")

    async def message(self, value, reply=None):
        self.sequence += 1
        event = Message(
            message_id=self.sequence,
            date=datetime.now(UTC),
            chat=Chat(id=self.actor.id, type="private"),
            from_user=self.actor,
            text=value,
            reply_to_message=reply,
        )
        await self.dp.feed_update(self.bot, Update(update_id=self.sequence, message=event))

    async def callback(self, value):
        self.sequence += 1
        event = CallbackQuery(
            id=str(self.sequence),
            from_user=self.actor,
            chat_instance="fixture",
            message=self.transport.messages[-1],
            data=value,
        )
        await self.dp.feed_update(self.bot, Update(update_id=self.sequence, callback_query=event))

    async def close(self):
        await self.dp.storage.close()
        await self.bot.session.close()


async def test_actual_panel_price_reply_confirmation_and_no_draft_loss(owner):
    app = Conversation()
    state = app.dp.fsm.get_context(bot=app.bot, chat_id=7, user_id=7)
    await state.set_state("intake")
    await state.set_data({"key": "draft-owned", "inputs": {"text": "original"}})
    try:
        await app.message("/admin")
        assert app.transport.messages[-1].text == tr("admin_panel_intro")
        await app.callback("admin:services:0")
        markup = app.transport.messages[-1].reply_markup
        assert (
            len(
                [
                    button
                    for row in markup.inline_keyboard
                    for button in row
                    if button.callback_data.startswith("admin:price:")
                ]
            )
            == 6
        )
        await app.callback("admin:price:echo")
        prompt = app.transport.messages[-1]
        await app.message("٢٥", reply=prompt)
        confirm = app.transport.messages[-1].reply_markup.inline_keyboard[0][0].callback_data
        assert "25" in app.transport.messages[-1].text
        async with sessions() as db:
            assert (await db.get(Service, "echo")).price_stars is None
        await app.message("30", reply=prompt)
        assert app.transport.messages[-1].text == tr("stale_button")
        await app.callback(confirm)
        await app.callback(confirm)
        async with sessions() as db:
            assert (await db.get(Service, "echo")).price_stars == 25
            assert await db.scalar(select(func.count(StarPriceChange.id))) == 1
            assert await db.scalar(select(func.count(Order.id))) == 0
        data = await state.get_data()
        assert data["key"] == "draft-owned" and data["inputs"] == {"text": "original"}
        assert await state.get_state() == "intake"
        await app.callback("admin:history")
        assert "echo" in app.transport.messages[-1].text and "25" in app.transport.messages[-1].text
        await app.callback("admin:orders")
        assert tr("admin_no_orders") in app.transport.messages[-1].text
        await app.callback("admin:stars")
        assert "0" in app.transport.messages[-1].text
    finally:
        await app.close()


@pytest.mark.parametrize("reason", ["cancel", "expiry", "revoked", "wrong_owner", "invalid"])
async def test_panel_rejects_cancelled_expired_revoked_or_foreign_confirmation(owner, reason):
    app = Conversation()
    state = app.dp.fsm.get_context(bot=app.bot, chat_id=7, user_id=7)
    try:
        await app.message("/admin")
        await app.callback("admin:price:echo")
        prompt = app.transport.messages[-1]
        if reason == "invalid":
            await app.message("0", reply=prompt)
            assert app.transport.messages[-1].text == tr("admin_price_invalid")
            return
        await app.message("25", reply=prompt)
        confirm = app.transport.messages[-1].reply_markup.inline_keyboard[0][0].callback_data
        if reason == "cancel":
            await app.callback("admin:cancel")
        elif reason == "expiry":
            pending = (await state.get_data())["admin_price"]
            pending["expires"] = 0
            await state.update_data(admin_price=pending)
        elif reason == "revoked":
            config().admin_ids = []
        elif reason == "wrong_owner":
            app.actor = User(id=8, is_bot=False, first_name="Other owner")
        await app.callback(confirm)
        async with sessions() as db:
            assert (await db.get(Service, "echo")).price_stars is None
            assert await db.scalar(select(func.count(StarPriceChange.id))) == 0
    finally:
        await app.close()


async def test_non_admin_command_and_callback_have_no_effect(owner):
    app = Conversation()
    app.actor = User(id=1, is_bot=False, first_name="Customer")
    try:
        await app.message("/admin")
        assert app.transport.messages[-1].text == tr("not_allowed")
        await app.callback("admin:price:echo")
        async with sessions() as db:
            assert (await db.get(Service, "echo")).price_stars is None
            assert await db.scalar(select(func.count(StarPriceChange.id))) == 0
    finally:
        await app.close()


async def test_setstars_command_writes_audit_with_authenticated_actor(owner):
    app = Conversation()
    try:
        await app.message("/setstars echo 27")
        assert app.transport.messages[-1].text == tr("admin_done")
        async with sessions() as db:
            change = await db.scalar(select(StarPriceChange))
            assert change.actor_id == 7 and change.new_price == 27 and change.old_price is None
    finally:
        await app.close()


async def test_configuration_panel_refresh_preserves_prices_flags_draft_and_ledgers(owner):
    app = Conversation()
    state = app.dp.fsm.get_context(bot=app.bot, chat_id=7, user_id=7)
    await state.set_state("support")
    await state.set_data({"key": "draft-owned", "inputs": {"text": "original"}})
    try:
        await app.message("/admin")
        assert any(
            button.callback_data == "admin:readiness:0"
            for line in app.transport.messages[-1].reply_markup.inline_keyboard
            for button in line
        )
        await app.callback("admin:readiness:99999")
        assert tr("admin_readiness_intro") == app.transport.messages[-1].text
        assert all(
            button.callback_data != "admin:inspect:local_ocr"
            for line in app.transport.messages[-1].reply_markup.inline_keyboard
            for button in line
        )
        await app.callback("admin:inspect:image_to_text")
        assert tr("admin_ai_off") in app.transport.messages[-1].text
        assert tr("admin_disabled") in app.transport.messages[-1].text
        assert tr("admin_version_ok", stored="5", source="5") in app.transport.messages[-1].text
        async with sessions.begin() as db:
            source = await db.get(Service, "image_to_text")
            source.enabled = True
            source.price_stars = 31
            source.version = "old"
        await app.callback("admin:inspect:image_to_text")
        assert "31" in app.transport.messages[-1].text
        assert tr("admin_enabled") in app.transport.messages[-1].text
        assert (
            tr("admin_version_mismatch", stored="old", source="5")
            in app.transport.messages[-1].text
        )
        async with sessions() as db:
            source = await db.get(Service, "image_to_text")
            assert source.enabled and source.price_stars == 31 and source.version == "old"
            for model in (Order, Job, CostUsage, StarPriceChange):
                assert await db.scalar(select(func.count()).select_from(model)) == 0
        assert (await state.get_data())["key"] == "draft-owned"
        assert (await state.get_data())["inputs"] == {"text": "original"}
        assert await state.get_state() == "support"
    finally:
        await app.close()


async def test_configuration_callback_rechecks_owner_before_query(owner, monkeypatch):
    from app.bot import admin_panel

    app = Conversation()
    try:
        await app.message("/admin")
        config().admin_ids = []

        def forbidden():
            raise AssertionError("Unauthorized report must not query services/provider")

        monkeypatch.setattr(admin_panel, "sessions", forbidden)
        await app.callback("admin:inspect:image_to_text")
        await app.callback("admin:readiness:0")
    finally:
        await app.close()
