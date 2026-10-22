"""Authenticated Mini App uses the bot menu, never a simple reply-keyboard launch."""

import pytest
from pydantic import ValidationError

from app.bot.ui import home_keyboard
from app.core.settings import Config, config


def test_default_has_no_webapp_button(monkeypatch):
    monkeypatch.setattr(config(), "miniapp_url", "")
    keyboard = home_keyboard("ar")
    assert all(item.web_app is None for row in keyboard.keyboard for item in row)


@pytest.mark.parametrize("lang", ["ar", "en"])
def test_reply_keyboard_never_opens_an_unauthenticated_simple_webapp(monkeypatch, lang):
    monkeypatch.setattr(config(), "miniapp_url", "https://mini.example.com/miniapp")
    keyboard = home_keyboard(lang)
    assert all(item.web_app is None for row in keyboard.keyboard for item in row)


async def test_explicit_menu_setup_uses_authenticated_menu_button():
    from app.ops.miniapp_menu import configure_menu

    class Bot:
        async def set_chat_menu_button(self, **kwargs):
            button = kwargs["menu_button"]
            assert button.type == "web_app"
            assert button.web_app.url == "https://mini.example.com/miniapp"
            assert button.text == "فتح التطبيق"
            assert "chat_id" not in kwargs
            return True

    await configure_menu(Bot(), "https://mini.example.com/miniapp")


async def test_menu_setup_does_not_claim_success_on_false_response():
    from app.ops.miniapp_menu import configure_menu

    class Bot:
        async def set_chat_menu_button(self, **kwargs):
            return False

    with pytest.raises(RuntimeError, match="menu_setup_failed"):
        await configure_menu(Bot(), "https://mini.example.com/miniapp")


async def test_missing_menu_url_does_not_call_telegram():
    from app.ops.miniapp_menu import configure_menu

    with pytest.raises(RuntimeError, match="miniapp_url_required"):
        await configure_menu(object(), "")


@pytest.mark.parametrize(
    "bad",
    [
        "http://example.com/miniapp",
        "https://example.com/other",
        "https://someone:secret@example.com/miniapp",
        "https://example.com/miniapp?token=secret",
        "https://example.com/miniapp#fragment",
    ],
)
def test_invalid_launch_configuration_rejected(bad):
    with pytest.raises(ValidationError, match="Mini App requires"):
        Config(miniapp_url=bad)


@pytest.mark.parametrize("username", ["abbot", "Example_Bot", "a" * 29 + "bot", ""])
def test_plain_bot_username_configuration(username):
    assert Config(miniapp_bot_username=username).miniapp_bot_username == username


@pytest.mark.parametrize(
    "username",
    [
        "@ExampleBot",
        "https://t.me/ExampleBot",
        "OtherUser",
        "ExampleBot?start=other",
        "ab bot",
        "a" * 30 + "bot",
        "بوت",
    ],
)
def test_reject_bot_username_url_or_payload_injection(username):
    with pytest.raises(ValidationError, match="plain bot username"):
        Config(miniapp_bot_username=username)


@pytest.mark.parametrize("matches", [False, True])
async def test_menu_configuration_checks_actual_bot_identity_before_writing(matches):
    from types import SimpleNamespace

    from app.ops.miniapp_menu import configure_menu

    class Bot:
        written = False

        async def get_me(self):
            return SimpleNamespace(username="ExampleBot" if matches else "DifferentBot")

        async def set_chat_menu_button(self, **kwargs):
            self.written = True
            return True

    bot = Bot()
    if matches:
        await configure_menu(bot, "https://mini.example.com/miniapp", username="examplebot")
    else:
        with pytest.raises(RuntimeError, match="username_mismatch"):
            await configure_menu(bot, "https://mini.example.com/miniapp", username="examplebot")
    assert bot.written is matches
