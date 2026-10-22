"""Real dispatcher handoff: reuse bot intake, never purchase or overwrite on opening."""

import pytest
from aiogram import Bot
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import User as TelegramUser
from sqlalchemy import func, select

from app.bot.main import create_dispatcher
from app.core.db import sessions
from app.core.i18n import tr
from app.core.models import Order, Service, StarCheckout, User
from app.core.settings import config
from app.core.users import set_language
from app.wallet.ledger import balance
from tests.test_bounded_fixes import button_by_prefix, feeders
from tests.test_draft_recovery import FlakyRecorder, SimulatedSendFailure
from tests.test_foundation import fund


@pytest.fixture
async def flow():
    transport = FlakyRecorder()
    bot = Bot("123456:TEST_TOKEN_ONLY", session=transport)
    dp = create_dispatcher(MemoryStorage(), guard=False)
    user = TelegramUser(id=1, is_bot=False, first_name="Customer")
    message, callback = feeders(dp, bot, user, transport)
    state = dp.fsm.get_context(bot=bot, chat_id=user.id, user_id=user.id)
    yield transport, message, callback, state, dp
    await dp.storage.close()
    await bot.session.close()


@pytest.mark.parametrize("lang", ["ar", "en"])
async def test_link_collects_then_confirms_through_existing_purchase(flow, lang):
    transport, message, callback, state, _ = flow
    await fund()
    await set_language(1, lang)
    await message("/start request_echo")
    draft = await state.get_data()
    assert draft["slug"] == "echo" and draft["inputs"] == {}
    assert await state.get_state() == "collect"
    assert transport.messages[-1].text.endswith(tr("input_text", lang))
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0
        assert (await balance(db, 1)).reserved == 0
    await message("Customer content")
    saved = await state.get_data()
    await message("/start request_echo")
    assert await state.get_data() == saved
    assert await state.get_state() == "confirm"
    await callback("draft:resume")
    confirm = button_by_prefix(transport.messages[-1].reply_markup, "confirm:")
    await callback(confirm)
    await callback(confirm)
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 1
        order = await db.scalar(select(Order))
        assert order.user_id == 1 and order.inputs == {"text": "Customer content"}
        assert order.idempotency_key == draft["key"]
        assert (await balance(db, 1)).reserved == 100


async def test_opening_different_service_preserves_existing_draft(flow):
    transport, message, _, state, _ = flow
    await message("/start request_echo")
    saved = await state.get_data()
    await message("/start request_text_summary")
    assert await state.get_data() == saved
    assert transport.messages[-1].text == tr("draft_saved")
    assert button_by_prefix(transport.messages[-1].reply_markup, "draft:resume")


async def test_link_snapshots_current_bot_price_and_stars_terms_without_checkout(flow, monkeypatch):
    _, message, _, state, _ = flow
    monkeypatch.setattr(config(), "stars_enabled", True)
    monkeypatch.setattr(config(), "stars_terms_version", "test-v1")
    async with sessions.begin() as db:
        row = await db.get(Service, "echo")
        row.price_stars = 9
        row.price_halala = 250
        version, schema = row.version, row.input_schema
    await message("/start request_echo")
    draft = await state.get_data()
    assert draft["payment_mode"] == "stars" and draft["stars_price"] == 9
    assert draft["price"] == 250 and draft["version"] == version and draft["schema"] == schema
    assert draft["terms_version"] == "test-v1" and draft["terms_hash"]
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0
        assert await db.scalar(select(func.count(StarCheckout.order_id))) == 0


@pytest.mark.parametrize(
    "payload",
    [
        "request_",
        "request_missing",
        "request_echo extra",
        "request_../echo",
        "request_echo?user_id=2",
    ],
)
async def test_invalid_hint_cannot_become_customer_content_or_order(flow, payload):
    transport, message, _, state, _ = flow
    await message("/start " + payload)
    assert transport.messages[-1].text == tr("unavailable")
    assert not (await state.get_data()).get("key")
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0


@pytest.mark.parametrize("gate", ["disabled", "admin", "stars", "ai"])
async def test_link_rechecks_current_service_gates(flow, monkeypatch, gate):
    transport, message, _, state, _ = flow
    slug = "echo"
    async with sessions.begin() as db:
        row = await db.get(Service, slug)
        if gate == "disabled":
            row.enabled = False
        elif gate == "admin":
            from app.services.registry import registry

            monkeypatch.setattr(registry.types[slug], "admin_only", True)
        elif gate == "stars":
            monkeypatch.setattr(config(), "stars_enabled", True)
            row.price_stars = None
        else:
            slug = "text_summary"
            (await db.get(Service, slug)).enabled = True
            monkeypatch.setattr(config(), "ai_enabled", False)
    await message("/start request_" + slug)
    assert transport.messages[-1].text == tr(
        "service_ai_unavailable" if gate == "ai" else "unavailable"
    )
    assert not (await state.get_data()).get("key")


async def test_failed_prompt_reopening_recovers_same_draft(flow):
    transport, message, _, state, _ = flow
    transport.fail_next_sends = 1
    with pytest.raises(SimulatedSendFailure):
        await message("/start request_echo")
    saved = await state.get_data()
    assert saved["pending_prompt"] is True
    await message("/start request_echo")
    recovered = await state.get_data()
    assert recovered == {**saved, "pending_prompt": False}
    assert transport.messages[-1].text.endswith(tr("input_text"))


async def test_banned_sender_is_blocked_by_existing_guard(flow):
    from app.bot.middleware import Guard

    transport, message, _, state, dp = flow
    await fund()
    async with sessions.begin() as db:
        (await db.get(User, 1)).banned = True

    class Rate:
        async def eval(self, *args):
            return 1

    dp.message.outer_middleware(Guard(Rate()))
    await message("/start request_echo")
    assert not (await state.get_data()).get("key")
    assert transport.messages[-1].text == tr("rate_limited")
