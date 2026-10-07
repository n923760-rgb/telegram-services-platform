"""Telegram Services UX v1: bilingual customer experience regression tests."""

from datetime import UTC, datetime

from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import AnswerCallbackQuery, SendMessage
from aiogram.types import CallbackQuery, Chat, Message, Update
from aiogram.types import User as TelegramUser

from app.bot.main import create_dispatcher
from app.core.db import sessions
from app.core.i18n import tr
from app.core.models import User as UserModel
from app.core.users import get_language, set_language
from tests.test_foundation import fund


class Session(BaseSession):
    def __init__(self):
        super().__init__()
        self.messages = []

    async def close(self):
        pass

    async def make_request(self, bot, method, timeout=None):
        if isinstance(method, AnswerCallbackQuery):
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
