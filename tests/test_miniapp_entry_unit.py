"""Optional keyboard launch button stays hidden until a validated HTTPS URL is configured."""

import pytest
from pydantic import ValidationError

from app.bot.ui import home_keyboard
from app.core.settings import Config, config


def test_default_has_no_webapp_button(monkeypatch):
    monkeypatch.setattr(config(), "miniapp_url", "")
    keyboard = home_keyboard("ar")
    assert all(item.web_app is None for row in keyboard.keyboard for item in row)


@pytest.mark.parametrize("lang, label", [("ar", "فتح التطبيق"), ("en", "Open app")])
def test_configured_launch_button_is_native_telegram_web_app(monkeypatch, lang, label):
    monkeypatch.setattr(config(), "miniapp_url", "https://mini.example.com/miniapp")
    keyboard = home_keyboard(lang)
    assert keyboard.keyboard[0][0].text == label
    assert keyboard.keyboard[0][0].web_app.url == "https://mini.example.com/miniapp"


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
