"""Telegram Services UX v1: bilingual customer experience regression tests."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import AnswerCallbackQuery, SendMessage
from aiogram.types import CallbackQuery, Chat, Message, Update
from aiogram.types import User as TelegramUser

from app.bot.main import create_dispatcher
from app.bot.middleware import Guard
from app.core.db import sessions
from app.core.i18n import tr
from app.core.models import User as UserModel
from app.core.users import get_language, set_language
from app.providers.delivery import TelegramDelivery
from app.services.base import Result
from tests.test_foundation import fund


class Session(BaseSession):
    def __init__(self):
        super().__init__()
        self.messages = []
        self.callback_answers = []

    async def close(self):
        pass

    async def make_request(self, bot, method, timeout=None):
        if isinstance(method, AnswerCallbackQuery):
            self.callback_answers.append(method)
            return True
        if isinstance(method, SendMessage):
            message = Message(
                message_id=len(self.messages) + 100,
                date=datetime.now(UTC),
                chat=Chat(id=int(method.chat_id), type="private"),
                text=method.text,
                reply_markup=method.reply_markup,
            )
            self.messages.append(message)
            return message
        return True

    async def stream_content(self, *args, **kwargs):
        if False:
            yield b""


def feeders(dp, bot, user, transport):
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

    async def callback(data):
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
                    message=transport.messages[-1],
                    data=data,
                ),
            ),
        )

    return message, callback


async def test_english_user_gets_localized_menu_and_service_names():
    await fund()
    await set_language(1, "en")
    transport = Session()
    bot = Bot("123456:TEST_TOKEN_ONLY", session=transport)
    dp = create_dispatcher(MemoryStorage(), guard=False)
    user = TelegramUser(id=1, is_bot=False, first_name="Customer")
    message, callback = feeders(dp, bot, user, transport)
    await message("/start")
    assert transport.messages[-1].text == tr("welcome", "en")
    await callback("menu:services")
    assert transport.messages[-1].text == tr("choose_service", "en")
    button_texts = [
        button.text for row in transport.messages[-1].reply_markup.inline_keyboard for button in row
    ]
    assert any("Echo demo" in text for text in button_texts)
    await dp.storage.close()
    await bot.session.close()


async def test_language_switch_persists_and_updates_menu():
    await fund()
    transport = Session()
    bot = Bot("123456:TEST_TOKEN_ONLY", session=transport)
    dp = create_dispatcher(MemoryStorage(), guard=False)
    user = TelegramUser(id=1, is_bot=False, first_name="Customer")
    message, callback = feeders(dp, bot, user, transport)
    await message("/start")
    assert transport.messages[-1].text == tr("welcome", "ar")
    await callback("menu:language")
    assert transport.messages[-1].text == tr("choose_language", "ar")
    await callback("lang:en")
    assert transport.messages[-1].text == tr("language_set", "en")
    assert await get_language(1) == "en"
    async with sessions() as db:
        assert (await db.get(UserModel, 1)).language == "en"
    await callback("menu:balance")
    assert transport.messages[-1].text == tr(
        "balance_details", "en", available="10.00", reserved="0.00"
    )
    await dp.storage.close()
    await bot.session.close()


async def test_unknown_user_defaults_to_arabic_without_creation():
    assert await get_language(999_999) == "ar"
    async with sessions() as db:
        assert await db.get(UserModel, 999_999) is None


async def test_invalid_language_button_uses_current_language_without_changing_it():
    await fund()
    await set_language(1, "en")
    transport = Session()
    bot = Bot("123456:TEST_TOKEN_ONLY", session=transport)
    dp = create_dispatcher(MemoryStorage(), guard=False)
    user = TelegramUser(id=1, is_bot=False, first_name="Customer")
    message, callback = feeders(dp, bot, user, transport)
    await message("/start")
    await callback("lang:invalid")
    assert transport.callback_answers[-1].text == tr("invalid_request", "en")
    assert transport.callback_answers[-1].show_alert is True
    assert await get_language(1) == "en"
    await dp.storage.close()
    await bot.session.close()


@pytest.mark.parametrize("callback", [False, True])
@pytest.mark.parametrize("lang", ["ar", "en"])
async def test_rate_limit_notice_uses_user_language(lang, callback):
    await fund()
    user = TelegramUser(id=1, is_bot=False, first_name="Customer")
    message = Message(
        message_id=1,
        date=datetime.now(UTC),
        chat=Chat(id=user.id, type="private"),
        from_user=user,
        text="/start",
    )
    transport = Session()
    bot = Bot("123456:TEST_TOKEN_ONLY", session=transport)
    event = (
        CallbackQuery(
            id="1", from_user=user, chat_instance="test", message=message, data="menu:balance"
        )
        if callback
        else message
    ).as_(bot)
    redis = AsyncMock()
    redis.eval.return_value = 31
    handler = AsyncMock()
    await Guard(redis)(handler, event, {"lang": lang})
    handler.assert_not_awaited()
    if callback:
        assert transport.callback_answers[-1].text == tr("rate_limited", lang)
        assert transport.callback_answers[-1].show_alert is True
    else:
        assert transport.messages[-1].text == tr("rate_limited", lang)
    await bot.session.close()


async def test_english_delivery_localizes_envelopes_and_preserves_customer_content():
    await fund()
    await set_language(1, "en")
    bot = AsyncMock()
    delivery = TelegramDelivery(bot)
    content = "محتوى العميل stays unchanged"
    preview = "هيكل الملف"
    await delivery.send(1, "order", Result(text=content, preview=preview))
    assert [call.args[1] for call in bot.send_message.await_args_list] == [
        tr("result_header", "en", order_id="order"),
        tr("structure_preview", "en", preview=preview),
        content,
    ]
    bot.reset_mock()
    await delivery.error(1, "order", "service_failed")
    bot.send_message.assert_awaited_once_with(
        1, tr("order_failed", "en", order_id="order", reason=tr("service_failed", "en"))
    )
    bot.reset_mock()
    await delivery.confirmation(1, "order", preview)
    call = bot.send_message.await_args
    assert call.args[1] == tr("confirmation_waiting", "en", order_id="order", preview=preview)
    buttons = call.kwargs["reply_markup"].inline_keyboard[0]
    assert [(button.text, button.callback_data) for button in buttons] == [
        (tr("approve_structure", "en"), "approve:order"),
        (tr("cancel_order", "en"), "reject:order"),
    ]
