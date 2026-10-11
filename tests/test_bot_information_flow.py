from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import SetMyDescription, SetMyShortDescription
from aiogram.types import User

from app.core.i18n import tr
from tests.test_admin_prices import Conversation
from tests.test_admin_prices import owner as owner
from tests.test_stars import stars as stars


async def test_stars_customer_page_avoids_test_balance_and_preserves_draft(
    stars, owner, monkeypatch
):
    from app.bot import navigation

    async def forbidden(*args):
        raise AssertionError("Stars page must not query historic test balance")

    monkeypatch.setattr(navigation, "balance", forbidden)
    app = Conversation()
    state = app.dp.fsm.get_context(bot=app.bot, chat_id=7, user_id=7)
    try:
        await app.message("/start")
        assert app.transport.messages[-1].text == tr("stars_welcome")
        await state.set_state("intake")
        await state.set_data({"key": "draft", "inputs": {"text": "original"}})
        await app.callback("menu:balance")
        assert app.transport.messages[-1].text == tr("stars_balance_details")
        assert await state.get_state() == "intake"
        assert (await state.get_data())["inputs"] == {"text": "original"}
        await app.message("/help")
        assert app.transport.messages[-1].text == tr("stars_help_text")
    finally:
        await app.close()


async def test_profile_command_authorization_and_partial_failure(owner, monkeypatch):
    app = Conversation()
    writes = []
    original = app.transport.make_request

    async def transport(bot, method, timeout=None):
        if isinstance(method, (SetMyDescription, SetMyShortDescription)):
            writes.append(method.language_code)
            return True
        return await original(bot, method, timeout=timeout)

    monkeypatch.setattr(app.transport, "make_request", transport)
    try:
        app.actor = User(id=1, is_bot=False, first_name="Customer")
        await app.message("/syncprofile")
        assert app.transport.messages[-1].text == tr("not_allowed") and not writes
        app.actor = User(id=7, is_bot=False, first_name="Owner")
        await app.message("/syncprofile")
        assert writes == ["", "", "ar", "ar", "en", "en"]
        assert app.transport.messages[-1].text == tr("profile_updated")

        async def fail(bot, method, timeout=None):
            if isinstance(method, SetMyDescription):
                raise TelegramBadRequest(method=method, message="fixture failure")
            return await original(bot, method, timeout=timeout)

        monkeypatch.setattr(app.transport, "make_request", fail)
        await app.message("/syncprofile")
        assert app.transport.messages[-1].text == tr("profile_update_failed")
    finally:
        await app.close()
