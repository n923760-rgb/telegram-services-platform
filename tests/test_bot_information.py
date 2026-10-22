from types import SimpleNamespace

import pytest

from app.bot import ui
from app.bot.profile import update_profile
from app.core.i18n import tr
from app.services.base import ServiceError


@pytest.fixture(autouse=True)
def database():
    yield


async def test_profile_updates_default_and_both_languages():
    calls = []

    class ProfileFixture:
        async def set_my_description(self, **kwargs):
            assert len(kwargs["description"]) <= 512
            calls.append(("description", kwargs["language_code"]))
            return True

        async def set_my_short_description(self, **kwargs):
            assert len(kwargs["short_description"]) <= 120
            calls.append(("short", kwargs["language_code"]))
            return True

    await update_profile(ProfileFixture())
    assert calls == [(kind, lang) for lang in ("", "ar", "en") for kind in ("description", "short")]


async def test_profile_false_response_stops_without_claiming_success():
    class ProfileFixture:
        async def set_my_description(self, **kwargs):
            return False

        async def set_my_short_description(self, **kwargs):
            pytest.fail("must stop after failed write")

    with pytest.raises(ServiceError, match="profile_update_failed"):
        await update_profile(ProfileFixture())


@pytest.mark.parametrize("enabled", [False, True])
def test_payment_labels_remain_compatible_and_admin_button_is_separate(monkeypatch, enabled):
    monkeypatch.setattr(ui, "config", lambda: SimpleNamespace(stars_enabled=enabled))
    for lang in ("ar", "en"):
        expected = tr("payments" if enabled else "balance", lang)
        keyboard = ui.home_keyboard(lang, admin=True)
        assert keyboard.keyboard[1][0].text == expected
        assert keyboard.keyboard[-1][0].text == tr("admin_panel", lang)
        assert len(ui.home_keyboard(lang).keyboard) == 3
        controls = [button for row in ui.menu(lang).inline_keyboard for button in row]
        assert any(
            button.text == expected and button.callback_data == "menu:balance"
            for button in controls
        )
        assert tr("balance", lang) in ui.MenuButton("balance").labels
        assert tr("payments", lang) in ui.MenuButton("balance").labels
