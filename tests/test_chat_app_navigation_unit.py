"""Exercise real Telegram routing without database or outbound Telegram calls."""

from unittest.mock import AsyncMock

import pytest
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import User

from app.bot import handlers, navigation
from app.core.i18n import tr
from app.core.settings import config
from tests.test_bounded_fixes import Recorder, button_by_prefix, feeders


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.fixture
async def chat(monkeypatch):
    monkeypatch.setattr(config(), "miniapp_url", "https://mini.example.com/miniapp")
    monkeypatch.setattr(config(), "miniapp_intake_enabled", True)
    monkeypatch.setattr(config(), "admin_ids", [])
    monkeypatch.setattr(navigation, "register", AsyncMock())

    def forbidden():
        pytest.fail("App navigation must not query the legacy service catalog")

    monkeypatch.setattr(navigation, "sessions", forbidden)
    monkeypatch.setattr(handlers, "sessions", forbidden)
    transport = Recorder()
    bot = Bot("123456:TEST_TOKEN_ONLY", session=transport)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(navigation.create_router())
    dp.include_router(handlers.create_router())
    user = User(id=1, is_bot=False, first_name="Synthetic")
    message, callback = feeders(dp, bot, user, transport)
    state = dp.fsm.get_context(bot=bot, chat_id=1, user_id=1)
    yield dp, transport, message, callback, state
    await dp.storage.close()
    await bot.session.close()


@pytest.mark.parametrize("lang", ["ar", "en"])
@pytest.mark.parametrize("stars", [False, True])
@pytest.mark.parametrize("admin", [False, True])
async def test_app_home_is_one_message_removes_old_keyboard_and_preserves_draft(
    chat, monkeypatch, lang, stars, admin
):
    dp, transport, message, _, state = chat
    dp["lang"] = lang
    monkeypatch.setattr(config(), "stars_enabled", stars)
    monkeypatch.setattr(config(), "admin_ids", [1] if admin else [])
    saved = {"key": "saved", "inputs": {"text": "Original draft"}}
    await state.set_state("collect")
    await state.set_data(saved)
    await message("/start")
    assert len(transport.sent_methods) == 1
    welcome = transport.sent_methods[0]
    assert welcome.text == tr("miniapp_stars_welcome" if stars else "miniapp_welcome", lang)
    assert welcome.reply_markup.remove_keyboard
    edit = transport.reply_markup_edits[0]
    assert edit.message_id == transport.messages[0].message_id
    controls = edit.reply_markup
    assert controls.inline_keyboard[0][0].web_app.url == config().miniapp_url
    assert button_by_prefix(controls, "draft:resume")
    assert bool(button_by_prefix(controls, "admin:home")) is admin
    assert button_by_prefix(controls, "menu:support")
    assert not button_by_prefix(controls, "menu:services")
    assert not button_by_prefix(controls, "menu:orders")
    assert await state.get_data() == saved
    assert await state.get_state() == "collect"


@pytest.mark.parametrize("data", ["menu:services", "catalog:text:0", "service:text_editing"])
async def test_old_catalog_buttons_open_app_without_overwriting_draft(chat, data):
    _, transport, message, callback, state = chat
    await message("/start")
    saved = {"key": "saved", "inputs": {"text": "Original draft"}}
    await state.set_state("collect")
    await state.set_data(saved)
    await callback(data)
    response = transport.sent_methods[-1]
    assert response.text == tr("miniapp_services_entry")
    assert response.reply_markup.inline_keyboard[0][0].web_app.url == config().miniapp_url
    assert button_by_prefix(response.reply_markup, "draft:resume")
    assert await state.get_data() == saved
    assert await state.get_state() == "collect"


async def test_disabled_intake_preserves_legacy_home(chat, monkeypatch):
    _, transport, message, _, _ = chat
    monkeypatch.setattr(config(), "miniapp_intake_enabled", False)
    await message("/start")
    assert len(transport.sent_methods) == 1
    assert transport.sent_methods[0].reply_markup.is_persistent
    assert not transport.reply_markup_edits


@pytest.mark.parametrize("lang", ["ar", "en"])
@pytest.mark.parametrize("text", ["/cancel", "Unrecognized customer message"])
async def test_recovery_messages_keep_one_app_entry_without_legacy_menus(chat, lang, text):
    dp, transport, message, _, _ = chat
    dp["lang"] = lang
    await message(text)
    assert len(transport.sent_methods) == 1
    controls = transport.sent_methods[0].reply_markup
    buttons = [button for row in controls.inline_keyboard for button in row]
    assert [button.web_app.url for button in buttons if button.web_app] == [config().miniapp_url]
    assert [button.callback_data for button in buttons if button.callback_data] == [
        "menu:support",
        "menu:help",
    ]


async def test_cancelling_saved_bot_draft_clears_it_and_returns_to_app(chat):
    _, transport, message, _, state = chat
    await state.set_state("collect")
    await state.set_data({"key": "saved", "inputs": {"text": "Synthetic draft"}})
    await message("/cancel")
    response = transport.sent_methods[-1]
    assert response.text == tr("draft_cancelled")
    assert response.reply_markup.inline_keyboard[0][0].web_app.url == config().miniapp_url
    assert not button_by_prefix(response.reply_markup, "menu:services")
    assert not button_by_prefix(response.reply_markup, "menu:orders")
    assert await state.get_state() is None and await state.get_data() == {}
