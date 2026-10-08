"""Regression tests for the approved bounded fixes.

Covers: private-chat gating, HTTPS-only AI endpoints, truthful draft-cancel text,
per-admin support delivery with reusable ticket ids, retryable intake I/O errors,
user cost-cap labeling, and stale-plugin admin enablement.
"""

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import AnswerCallbackQuery, CopyMessage, EditMessageReplyMarkup, SendMessage
from aiogram.types import CallbackQuery, Chat, InlineKeyboardMarkup, Message, Update
from aiogram.types import User as TelegramUser
from pydantic import SecretStr, ValidationError
from sqlalchemy import func, select

from app.bot.main import create_dispatcher
from app.core.db import sessions
from app.core.i18n import tr
from app.core.models import CostBudget, Service, SupportTicket
from app.core.models import User as UserModel
from app.core.settings import Config, config
from app.orders.engine import register
from app.services.base import ServiceError
from app.wallet.ledger import balance
from tests.test_foundation import fund


class Recorder(BaseSession):
    """Bot transport that records messages, copies and callback answers, and can
    simulate transport failures for specific chat ids."""

    def __init__(self, fail_chats=()):
        super().__init__()
        self.messages = []
        self.copies = []
        self.callback_answers = []
        self.reply_markup_edits = []
        self.sent_methods = []
        self.fail_chats = set(fail_chats)

    async def close(self):
        pass

    async def make_request(self, bot, method, timeout=None):
        if isinstance(method, AnswerCallbackQuery):
            self.callback_answers.append(method)
            return True
        if isinstance(method, EditMessageReplyMarkup):
            self.reply_markup_edits.append(method)
            return True
        if isinstance(method, SendMessage):
            self.sent_methods.append(method)
            if method.chat_id in self.fail_chats:
                raise TelegramForbiddenError(method=method, message="blocked by user")
            message = Message(
                message_id=len(self.messages) + 100,
                date=datetime.now(UTC),
                chat=Chat(id=int(method.chat_id), type="private"),
                text=method.text,
                reply_markup=method.reply_markup
                if isinstance(method.reply_markup, InlineKeyboardMarkup)
                else None,
            )
            self.messages.append(message)
            return message
        if isinstance(method, CopyMessage):
            if method.chat_id in self.fail_chats:
                raise TelegramBadRequest(method=method, message="chat not found")
            self.copies.append(method)
            return True
        return True

    async def stream_content(self, *args, **kwargs):
        if False:
            yield b""


def button_by_prefix(markup, prefix):
    """Return the first button callback_data whose value starts with ``prefix``, else None."""
    if markup is None or markup.inline_keyboard is None:
        return None
    for row in markup.inline_keyboard:
        for button in row:
            if button.callback_data.startswith(prefix):
                return button.callback_data
    return None


def feeders(dp, bot, user, transport):
    """Return (message, callback) helpers that push private-chat updates through the dispatcher."""
    sequence = {"n": 0}

    async def message(text):
        sequence["n"] += 1
        n = sequence["n"]
        await dp.feed_update(
            bot,
            Update(
                update_id=n,
                message=Message(
                    message_id=n,
                    date=datetime.now(UTC),
                    chat=Chat(id=user.id, type="private"),
                    from_user=user,
                    text=text,
                ),
            ),
        )

    async def callback(data, on=None):
        sequence["n"] += 1
        n = sequence["n"]
        await dp.feed_update(
            bot,
            Update(
                update_id=n,
                callback_query=CallbackQuery(
                    id=str(n),
                    from_user=user,
                    chat_instance="test",
                    message=on if on is not None else transport.messages[-1],
                    data=data,
                ),
            ),
        )

    return message, callback


async def test_group_message_is_not_routed_to_customer_flow():
    transport = Recorder()
    bot = Bot("123456:TEST_TOKEN_ONLY", session=transport)
    dp = create_dispatcher(MemoryStorage(), guard=False)
    event = Message(
        message_id=1,
        date=datetime.now(UTC),
        chat=Chat(id=-100123, type="supergroup"),
        from_user=TelegramUser(id=555, is_bot=False, first_name="Member"),
        text="/start",
    )
    await dp.feed_update(bot, Update(update_id=1, message=event))
    assert transport.messages[-1].text == tr("private_only")
    async with sessions() as db:
        assert await db.get(UserModel, 555) is None
    await dp.storage.close()
    await bot.session.close()


async def test_message_less_callback_is_answered_safely():
    transport = Recorder()
    bot = Bot("123456:TEST_TOKEN_ONLY", session=transport)
    dp = create_dispatcher(MemoryStorage(), guard=False)
    event = CallbackQuery(
        id="1",
        from_user=TelegramUser(id=1, is_bot=False, first_name="Customer"),
        chat_instance="test",
        message=None,
        data="menu:services",
    )
    await dp.feed_update(bot, Update(update_id=1, callback_query=event))
    assert transport.callback_answers
    assert transport.callback_answers[-1].show_alert is True
    assert transport.callback_answers[-1].text == tr("private_only")
    await dp.storage.close()
    await bot.session.close()


async def test_draft_cancel_uses_truthful_text_and_scopes_buttons():
    transport = Recorder()
    bot = Bot("123456:TEST_TOKEN_ONLY", session=transport)
    dp = create_dispatcher(MemoryStorage(), guard=False)
    user = TelegramUser(id=1, is_bot=False, first_name="Customer")
    message, callback = feeders(dp, bot, user, transport)
    await message("/start")
    await callback("menu:services")
    await callback("service:echo")
    await message("نص العميل")
    confirm_markup = transport.messages[-1].reply_markup
    confirm_data = button_by_prefix(confirm_markup, "confirm:")
    cancel_data = button_by_prefix(confirm_markup, "cancel:")
    assert confirm_data and cancel_data
    assert cancel_data != "cancel"  # the cancel callback is scoped to the draft key
    await callback(cancel_data)
    assert transport.messages[-1].text == tr("draft_cancelled")
    assert transport.reply_markup_edits  # the stale confirmation keyboard was removed
    # A stale confirm button from the abandoned draft must not resume it.
    await callback(confirm_data, on=transport.messages[-2])
    assert transport.callback_answers[-1].show_alert is True
    assert transport.callback_answers[-1].text == tr("stale_button")
    await dp.storage.close()
    await bot.session.close()


async def test_stale_cancel_does_not_clear_new_draft():
    transport = Recorder()
    bot = Bot("123456:TEST_TOKEN_ONLY", session=transport)
    dp = create_dispatcher(MemoryStorage(), guard=False)
    user = TelegramUser(id=1, is_bot=False, first_name="Customer")
    message, callback = feeders(dp, bot, user, transport)
    await message("/start")
    await callback("menu:services")
    await callback("service:echo")
    await message("النص الأول")
    stale_cancel = button_by_prefix(transport.messages[-1].reply_markup, "cancel:")
    # Start a newer draft without cancelling the first one.
    await callback("menu:services")
    await callback("service:echo")
    # A stale cancel from the older draft must be rejected and leave the new draft active.
    await callback(stale_cancel)
    assert transport.callback_answers[-1].show_alert is True
    assert transport.callback_answers[-1].text == tr("stale_button")
    await message("النص الثاني")
    assert button_by_prefix(transport.messages[-1].reply_markup, "confirm:")
    await dp.storage.close()
    await bot.session.close()


async def test_post_submit_stale_cancel_preserves_ledger():
    from app.core.models import Order as OrderModel

    await fund()
    transport = Recorder()
    bot = Bot("123456:TEST_TOKEN_ONLY", session=transport)
    dp = create_dispatcher(MemoryStorage(), guard=False)
    user = TelegramUser(id=1, is_bot=False, first_name="Customer")
    message, callback = feeders(dp, bot, user, transport)
    await message("/start")
    await callback("menu:services")
    await callback("service:echo")
    await message("نص الطلب")
    confirm_data = button_by_prefix(transport.messages[-1].reply_markup, "confirm:")
    cancel_data = button_by_prefix(transport.messages[-1].reply_markup, "cancel:")
    await callback(confirm_data)
    async with sessions() as db:
        order = await db.scalar(select(OrderModel))
        assert order.status == "queued"
        after_submit = await balance(db, 1)
    assert after_submit.reserved == 100  # echo is 100 halalas
    # A stale cancel button from the submitted order must not mutate the ledger or the order.
    await callback(cancel_data, on=transport.messages[-2])
    assert transport.callback_answers[-1].show_alert is True
    assert transport.callback_answers[-1].text == tr("stale_button")
    async with sessions() as db:
        order = await db.scalar(select(OrderModel))
        assert order.status == "queued"
        final = await balance(db, 1)
    assert (final.available, final.reserved) == (after_submit.available, after_submit.reserved)
    await dp.storage.close()
    await bot.session.close()


def test_config_requires_https_when_ai_enabled():
    base = dict(
        ai_enabled=True,
        ai_api_key=SecretStr("key"),
        ai_input_usd_per_million=Decimal("1"),
        ai_output_usd_per_million=Decimal("1"),
    )
    with pytest.raises(ValidationError):
        Config(_env_file=None, ai_base_url="http://api.example.com/v1", **base)
    assert Config(_env_file=None, ai_base_url="https://api.example.com/v1", **base).ai_enabled


async def test_intake_telegram_download_failure_is_retryable(monkeypatch, tmp_path):
    from app.files.telegram import receive

    monkeypatch.setattr(config(), "storage_root", tmp_path)

    class BrokenBot:
        async def download(self, file_id, destination=None):
            raise OSError("network unavailable")

    message = SimpleNamespace(
        bot=BrokenBot(),
        photo=[SimpleNamespace(file_id="file", file_size=100)],
    )
    with pytest.raises(ServiceError, match="input_retry") as info:
        await receive(message, "image", 1)
    assert info.value.transient is True


async def test_intake_storage_failure_is_retryable(monkeypatch, tmp_path):
    from app.files import telegram

    monkeypatch.setattr(config(), "storage_root", tmp_path)

    class FakeBot:
        async def download(self, file_id, destination=None):
            destination.write(b"data")
            return destination

    class BrokenStorage:
        def ensure_quota(self, *args, **kwargs):
            return None

        def save(self, *args, **kwargs):
            raise OSError("disk full")

    monkeypatch.setattr(telegram, "validate_file", lambda content, mime, max_bytes: content)
    monkeypatch.setattr(telegram, "storage", lambda: BrokenStorage())
    message = SimpleNamespace(
        bot=FakeBot(),
        document=SimpleNamespace(file_id="file", file_size=4, mime_type="text/plain"),
    )
    with pytest.raises(ServiceError, match="input_retry"):
        await telegram.receive(message, "file", 1)


async def test_intake_quota_precheck_io_failure_is_retryable(monkeypatch, tmp_path):
    from app.files import telegram

    monkeypatch.setattr(config(), "storage_root", tmp_path)

    class FakeBot:
        async def download(self, file_id, destination=None):
            destination.write(b"data")
            return destination

    class BrokenQuotaStorage:
        def ensure_quota(self, *args, **kwargs):
            raise OSError("quota lock unavailable")

        def save(self, *args, **kwargs):
            raise AssertionError("save must not run after the pre-check failed")

    monkeypatch.setattr(telegram, "storage", lambda: BrokenQuotaStorage())
    message = SimpleNamespace(
        bot=FakeBot(),
        document=SimpleNamespace(file_id="file", file_size=4, mime_type="text/plain"),
    )
    with pytest.raises(ServiceError, match="input_retry") as info:
        await telegram.receive(message, "file", 1)
    assert info.value.transient is True


async def test_intake_storage_construction_failure_is_retryable(monkeypatch, tmp_path):
    from app.files import telegram

    monkeypatch.setattr(config(), "storage_root", tmp_path)

    class FakeBot:
        async def download(self, file_id, destination=None):
            destination.write(b"data")
            return destination

    def broken_storage():
        raise OSError("storage root unavailable")

    monkeypatch.setattr(telegram, "storage", broken_storage)
    message = SimpleNamespace(
        bot=FakeBot(),
        document=SimpleNamespace(file_id="file", file_size=4, mime_type="text/plain"),
    )
    with pytest.raises(ServiceError, match="input_retry") as info:
        await telegram.receive(message, "file", 1)
    assert info.value.transient is True


async def test_intake_quota_precheck_service_error_is_preserved(monkeypatch, tmp_path):
    from app.files import telegram

    monkeypatch.setattr(config(), "storage_root", tmp_path)

    class FakeBot:
        async def download(self, file_id, destination=None):
            destination.write(b"data")
            return destination

    class FullStorage:
        def ensure_quota(self, *args, **kwargs):
            raise ServiceError("storage_quota")

        def save(self, *args, **kwargs):
            raise AssertionError("save must not run after the pre-check failed")

    monkeypatch.setattr(telegram, "storage", lambda: FullStorage())
    message = SimpleNamespace(
        bot=FakeBot(),
        document=SimpleNamespace(file_id="file", file_size=4, mime_type="text/plain"),
    )
    with pytest.raises(ServiceError, match="storage_quota"):
        await telegram.receive(message, "file", 1)


async def test_user_admission_cap_uses_user_cost_cap_key():
    from app.ops.costs import check_admission, keys

    await register(1)
    async with sessions.begin() as db:
        db.add(CostBudget(key=keys(1)[1], spent=50, reserved=0))
    with pytest.raises(ServiceError, match="user_cost_cap"):
        async with sessions.begin() as db:
            await check_admission(db, 1)


async def test_global_admission_cap_still_uses_cost_cap_key():
    from app.ops.costs import check_admission, keys

    await register(1)
    async with sessions.begin() as db:
        db.add(CostBudget(key=keys(1)[0], spent=50, reserved=0))
    with pytest.raises(ServiceError, match="cost_cap"):
        async with sessions.begin() as db:
            await check_admission(db, 1)


async def test_enabling_removed_plugin_raises_unavailable_not_keyerror():
    from app.ops.admin import set_service

    async with sessions.begin() as db:
        db.add(
            Service(
                slug="removed_plugin",
                version="1",
                name_ar="محذوفة",
                name_en="Removed",
                description_ar="محذوفة",
                price_halala=100,
                input_schema={},
                enabled=False,
            )
        )
    with pytest.raises(ServiceError, match="unavailable"):
        await set_service("removed_plugin", enabled=True)
    async with sessions() as db:
        assert not (await db.get(Service, "removed_plugin")).enabled


async def test_support_one_failing_admin_still_delivers(monkeypatch):
    await register(1)
    monkeypatch.setattr(config(), "admin_ids", [100, 200])
    transport = Recorder(fail_chats={200})
    bot = Bot("123456:TEST_TOKEN_ONLY", session=transport)
    dp = create_dispatcher(MemoryStorage(), guard=False)
    user = TelegramUser(id=1, is_bot=False, first_name="Customer")
    message, callback = feeders(dp, bot, user, transport)
    await message("/start")
    await callback("menu:support")
    await message("مساعدة")
    assert transport.messages[-1].text == tr("support_sent")
    assert len(transport.copies) == 1 and transport.copies[0].chat_id == 100
    async with sessions() as db:
        assert await db.scalar(select(func.count(SupportTicket.id))) == 1
    await dp.storage.close()
    await bot.session.close()


async def test_support_retry_reuses_ticket_id(monkeypatch):
    await register(1)
    monkeypatch.setattr(config(), "admin_ids", [100])
    transport = Recorder(fail_chats={100})
    bot = Bot("123456:TEST_TOKEN_ONLY", session=transport)
    dp = create_dispatcher(MemoryStorage(), guard=False)
    user = TelegramUser(id=1, is_bot=False, first_name="Customer")
    message, callback = feeders(dp, bot, user, transport)
    await message("/start")
    await callback("menu:support")
    await message("first attempt")
    assert transport.messages[-1].text == tr("support_failed")
    # The admin becomes reachable; retrying must reuse the same ticket, not create a new one.
    transport.fail_chats = set()
    await message("second attempt")
    assert transport.messages[-1].text == tr("support_sent")
    async with sessions() as db:
        assert await db.scalar(select(func.count(SupportTicket.id))) == 1
    await dp.storage.close()
    await bot.session.close()


async def test_support_no_admin_reports_failure(monkeypatch):
    await register(1)
    monkeypatch.setattr(config(), "admin_ids", [])
    transport = Recorder()
    bot = Bot("123456:TEST_TOKEN_ONLY", session=transport)
    dp = create_dispatcher(MemoryStorage(), guard=False)
    user = TelegramUser(id=1, is_bot=False, first_name="Customer")
    message, callback = feeders(dp, bot, user, transport)
    await message("/start")
    await callback("menu:support")
    await message("مساعدة")
    assert transport.messages[-1].text == tr("support_failed")
    await dp.storage.close()
    await bot.session.close()


async def test_reply_send_failure_reports_to_admin(monkeypatch):
    await register(1)
    async with sessions.begin() as db:
        ticket = SupportTicket(user_id=1, order_id=None)
        db.add(ticket)
        await db.flush()
        ticket_id = ticket.id
    monkeypatch.setattr(config(), "admin_ids", [100])
    transport = Recorder(fail_chats={1})
    bot = Bot("123456:TEST_TOKEN_ONLY", session=transport)
    dp = create_dispatcher(MemoryStorage(), guard=False)
    admin = TelegramUser(id=100, is_bot=False, first_name="Admin")
    message, _ = feeders(dp, bot, admin, transport)
    await message(f"/reply {ticket_id} مرحبًا")
    assert transport.messages[-1].text == tr("support_reply_failed")
    await dp.storage.close()
    await bot.session.close()


async def test_draft_cancel_does_not_touch_wallet():
    await fund()
    async with sessions() as db:
        before = await balance(db, 1)
    transport = Recorder()
    bot = Bot("123456:TEST_TOKEN_ONLY", session=transport)
    dp = create_dispatcher(MemoryStorage(), guard=False)
    user = TelegramUser(id=1, is_bot=False, first_name="Customer")
    message, callback = feeders(dp, bot, user, transport)
    await message("/start")
    await callback("menu:services")
    await callback("service:echo")
    await message("نص")
    await callback(button_by_prefix(transport.messages[-1].reply_markup, "cancel:"))
    async with sessions() as db:
        after = await balance(db, 1)
    assert (before.available, before.reserved) == (after.available, after.reserved)
    await dp.storage.close()
    await bot.session.close()


async def test_negative_choice_index_is_rejected():
    async with sessions.begin() as db:
        (await db.get(Service, "text_to_office")).enabled = True
    transport = Recorder()
    bot = Bot("123456:TEST_TOKEN_ONLY", session=transport)
    dp = create_dispatcher(MemoryStorage(), guard=False)
    user = TelegramUser(id=1, is_bot=False, first_name="Customer")
    message, callback = feeders(dp, bot, user, transport)
    await message("/start")
    await callback("menu:services")
    await callback("service:text_to_office")
    await message("المحتوى")
    valid = button_by_prefix(transport.messages[-1].reply_markup, "choice:")
    malicious = ":".join(valid.split(":")[:-1] + ["-1"])
    await callback(malicious)
    assert transport.callback_answers[-1].show_alert is True
    assert transport.callback_answers[-1].text == tr("invalid_request")
    await dp.storage.close()
    await bot.session.close()


async def test_malformed_done_callback_is_rejected(monkeypatch):
    import app.files.telegram as telegram_module

    async def fake_receive(message, kind, user_id):
        return f"1/{'a' * 32}/input.jpg"

    monkeypatch.setattr(telegram_module, "receive", fake_receive)
    async with sessions.begin() as db:
        (await db.get(Service, "image_to_text")).enabled = True
    transport = Recorder()
    bot = Bot("123456:TEST_TOKEN_ONLY", session=transport)
    dp = create_dispatcher(MemoryStorage(), guard=False)
    user = TelegramUser(id=1, is_bot=False, first_name="Customer")
    message, callback = feeders(dp, bot, user, transport)
    await message("/start")
    await callback("menu:services")
    await callback("service:image_to_text")
    await message("fake-image")
    answered_before = len(transport.callback_answers)
    await callback("done:malformed")
    # Exactly one callback acknowledgement on the malformed path (no double-answer).
    assert len(transport.callback_answers) == answered_before + 1
    assert transport.callback_answers[-1].show_alert is True
    assert transport.callback_answers[-1].text == tr("invalid_request")
    await dp.storage.close()
    await bot.session.close()


async def test_empty_services_menu_shows_no_services():
    async with sessions.begin() as db:
        (await db.get(Service, "echo")).enabled = False
    transport = Recorder()
    bot = Bot("123456:TEST_TOKEN_ONLY", session=transport)
    dp = create_dispatcher(MemoryStorage(), guard=False)
    user = TelegramUser(id=1, is_bot=False, first_name="Customer")
    message, callback = feeders(dp, bot, user, transport)
    await message("/start")
    await callback("menu:services")
    assert transport.messages[-1].text == tr("no_services")
    await dp.storage.close()
    await bot.session.close()
