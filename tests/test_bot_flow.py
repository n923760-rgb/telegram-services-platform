from datetime import UTC, datetime

from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import AnswerCallbackQuery, SendMessage
from aiogram.types import CallbackQuery, Chat, Message, Update, User
from sqlalchemy import select

from app.bot.main import create_dispatcher
from app.core.db import sessions
from app.core.i18n import tr
from app.core.models import Order
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


async def test_actual_dispatcher_dynamic_echo_conversation():
    await fund()
    transport = Session()
    bot = Bot("123456:TEST_TOKEN_ONLY", session=transport)
    dp = create_dispatcher(MemoryStorage(), guard=False)
    user = User(id=1, is_bot=False, first_name="Customer")
    sequence = 0

    async def message(text):
        nonlocal sequence
        sequence += 1
        event = Message(
            message_id=sequence,
            date=datetime.now(UTC),
            chat=Chat(id=1, type="private"),
            from_user=user,
            text=text,
        )
        await dp.feed_update(bot, Update(update_id=sequence, message=event))

    async def callback(data):
        nonlocal sequence
        sequence += 1
        event = CallbackQuery(
            id=str(sequence),
            from_user=user,
            chat_instance="test",
            message=transport.messages[-1],
            data=data,
        )
        await dp.feed_update(bot, Update(update_id=sequence, callback_query=event))

    await message("/start")
    assert transport.messages[-1].text == tr("welcome")
    await callback("menu:services")
    assert transport.messages[-1].reply_markup.inline_keyboard[0][0].callback_data == "service:echo"
    await callback("service:echo")
    assert transport.messages[-1].text == tr("input_text")
    await message("/cancel")
    assert transport.messages[-1].text == tr("draft_cancelled")
    await callback("service:echo")
    await message("نص العميل")
    confirmation = transport.messages[-1].reply_markup.inline_keyboard[0][0].callback_data
    await callback(confirmation)
    async with sessions() as db:
        order = await db.scalar(select(Order))
        assert order.inputs == {"text": "نص العميل"} and order.status == "queued"
    await dp.storage.close()
    await bot.session.close()


async def test_registry_dynamic_choices_nested_forms_and_localizations():
    import string

    from app.core.i18n import CATALOGS
    from app.services.base import InputField, InputSchema

    form = InputSchema(
        fields=[
            InputField(
                name="address",
                kind="form",
                prompt_key="input_text",
                fields=[InputField(name="city", prompt_key="input_text")],
            )
        ]
    )
    assert form.conversation()[0].name == "address.city"
    for key in CATALOGS["ar"]:
        ar = {name for _, name, _, _ in string.Formatter().parse(CATALOGS["ar"][key]) if name}
        en = {name for _, name, _, _ in string.Formatter().parse(CATALOGS["en"][key]) if name}
        assert ar == en, key
