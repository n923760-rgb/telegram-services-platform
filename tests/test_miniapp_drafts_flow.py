"""Real PostgreSQL + Redis + bot dispatcher qualification of the shared draft."""

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest
from aiogram import Bot
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import User as TelegramUser
from pydantic import SecretStr
from redis.exceptions import LockError
from sqlalchemy import func, select

from app.api.main import app
from app.bot.main import create_dispatcher
from app.core.db import sessions
from app.core.models import Order, StarCheckout, User
from app.core.settings import config
from app.miniapp.drafts import runtime
from app.wallet.ledger import balance
from tests.test_bounded_fixes import button_by_prefix, feeders
from tests.test_draft_recovery import FlakyRecorder
from tests.test_foundation import fund
from tests.test_miniapp import TOKEN, signed

OWNER = 881991


@pytest.fixture
async def shared(monkeypatch):
    monkeypatch.setattr(config(), "bot_token", SecretStr(TOKEN))
    monkeypatch.setattr(config(), "miniapp_intake_enabled", True)
    monkeypatch.setattr(config(), "stars_enabled", False)
    await fund(OWNER)
    store = RedisStorage.from_url(
        config().redis_url.get_secret_value(), state_ttl=3600, data_ttl=3600
    )
    key = StorageKey(bot_id=12345, chat_id=OWNER, user_id=OWNER)
    keys = [store.key_builder.build(key, part) for part in ("state", "data", "lock")] + [
        f"rate:{OWNER}"
    ]
    await store.redis.delete(*keys)
    transport = FlakyRecorder()
    bot = Bot(TOKEN, session=transport)
    dp = create_dispatcher(store, guard=False)
    sender = TelegramUser(id=OWNER, is_bot=False, first_name="Synthetic customer")
    message, callback = feeders(dp, bot, sender, transport)
    state = dp.fsm.get_context(bot=bot, chat_id=OWNER, user_id=OWNER)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="https://test",
        headers={"Origin": "https://test", "Sec-Fetch-Site": "same-origin"},
    ) as client:
        # One Telegram launch supplies one initData string, as intake.js does.
        # Re-signing per request can cross a second boundary and changes the
        # replay-bound payload even when revision/operation/value are identical.
        raw = signed(user_id=OWNER, issued=int(datetime.now(UTC).timestamp()))

        async def call(action="view", **kwargs):
            return await client.post(
                "/miniapp/api/draft", json={"init_data": raw, "action": action, **kwargs}
            )

        yield call, message, callback, state, transport, store, key
    await store.redis.delete(*keys)
    await dp.storage.close()
    await bot.session.close()


async def test_http_intake_hands_off_to_exactly_one_normal_bot_purchase(shared):
    call, message, callback, state, transport, store, key = shared
    opened = await call("open", slug="echo")
    assert opened.status_code == 200
    view = opened.json()["draft"]
    args = {"revision": view["revision"], "operation": uuid4().hex, "value": "Synthetic content"}
    saved, duplicate = await asyncio.gather(call("answer", **args), call("answer", **args))
    assert saved.status_code == duplicate.status_code == 200 and saved.json() == duplicate.json()
    data = await state.get_data()
    assert data["inputs"] == {"text": "Synthetic content"}
    assert await state.get_state() == "confirm"
    assert 0 < await store.redis.ttl(store.key_builder.build(key, "data")) <= 3600
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0
        assert await db.scalar(select(func.count(StarCheckout.order_id))) == 0
        assert (await balance(db, OWNER)).reserved == 0
    await message("/start request_echo")
    confirm = button_by_prefix(transport.messages[-1].reply_markup, "confirm:")
    assert confirm == "confirm:" + data["key"]
    await callback(confirm)
    await callback(confirm)
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 1
        order = await db.scalar(select(Order))
        assert order.user_id == OWNER and order.inputs == data["inputs"]
        assert (await balance(db, OWNER)).reserved == 100


async def test_old_bot_confirmation_cannot_submit_browser_edited_content(shared):
    call, message, callback, state, transport, _, _ = shared
    await message("/start request_echo")
    await message("original")
    old_confirm = button_by_prefix(transport.messages[-1].reply_markup, "confirm:")
    view = (await call()).json()["draft"]
    edited = await call("edit", revision=view["revision"], operation=uuid4().hex, index=0)
    assert edited.status_code == 200
    view = edited.json()["draft"]
    result = await call("answer", revision=view["revision"], operation=uuid4().hex, value="updated")
    assert result.status_code == 200
    await callback(old_confirm)
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0
        assert (await balance(db, OWNER)).reserved == 0
    current = button_by_prefix(transport.messages[-1].reply_markup, "confirm:")
    assert current != old_confirm
    await callback(current)
    async with sessions() as db:
        order = await db.scalar(select(Order))
        assert order.inputs == {"text": "updated"}


async def test_api_lock_is_the_dispatcher_lock_and_rate_ban_fail_closed(shared):
    call, _, _, state, _, store, key = shared
    async with runtime(OWNER) as context:
        assert context.key == key
        assert await store.redis.exists(store.key_builder.build(key, "lock"))
        bot_isolation = store.create_isolation(
            lock_kwargs={"timeout": 60, "blocking_timeout": 0.05}
        )
        with pytest.raises(LockError):
            async with bot_isolation.lock(key):
                pytest.fail("The API must hold the same lock used by the dispatcher")
    await store.redis.set(f"rate:{OWNER}", 30, ex=60)
    response = await call("open", slug="echo")
    assert response.status_code == 429 and await state.get_data() == {}
    async with sessions.begin() as db:
        (await db.get(User, OWNER)).banned = True
    assert (await call()).status_code == 403
