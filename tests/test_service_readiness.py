"""Pure, non-network configuration evidence; runtime acceptance is deliberately absent."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.bot.admin_panel import readiness_text
from app.core.i18n import tr
from app.ops import readiness
from app.services.base import ServiceError
from app.services.registry import registry


@pytest.fixture(autouse=True)
def database():
    pass


def row(slug="image_to_text", **changes):
    return SimpleNamespace(
        **{
            "slug": slug,
            "name_ar": "خدمة اختبار",
            "name_en": "Test service",
            "version": registry.types[slug].version,
            "enabled": True,
            "price_stars": None,
            **changes,
        }
    )


@pytest.mark.parametrize("enabled", [True, False])
@pytest.mark.parametrize("stars", [True, False])
@pytest.mark.parametrize("price", [None, 25])
def test_listing_matches_current_customer_activation_and_price_filters(enabled, stars, price):
    source = row(enabled=enabled, price_stars=price)
    evidence = readiness.checks(source, ai_state="off", stars_enabled=stars)
    assert evidence["listed"] == (enabled and (not stars or price is not None))
    assert evidence["stars_price_missing"] == (stars and price is None)
    assert vars(source) == vars(row(enabled=enabled, price_stars=price))


@pytest.mark.parametrize("lang", ["ar", "en"])
def test_details_disclose_mismatch_provider_limits_and_manual_price(lang):
    source = row(version="old", price_stars=37)
    evidence = readiness.checks(source, ai_state="configured", stars_enabled=True)
    result = readiness_text(source, evidence, lang)
    assert not evidence["version_matches"] and evidence["ai_required"]
    assert "old" in result and "37" in result
    assert tr("admin_ai_configured", lang) in result
    assert tr("admin_readiness_limits", lang) in result
    assert tr("admin_ai_required", lang) in result


def test_mixed_plugin_does_not_guess_ai_need_from_empty_input(monkeypatch):
    def forbidden(*args):
        raise AssertionError("No fabricated customer inputs")

    monkeypatch.setattr(registry.types["text_to_office"], "needs_ai", forbidden)
    source = row("text_to_office")
    evidence = readiness.checks(source, ai_state="off", stars_enabled=False)
    assert not evidence["ai_required"]
    assert tr("admin_ai_input_dependent") in readiness_text(source, evidence, "ar")


@pytest.mark.parametrize("slug", ["local_ocr", "missing"])
def test_retired_or_unknown_plugins_are_not_exposed(slug):
    with pytest.raises(ServiceError, match="unavailable"):
        readiness.checks(SimpleNamespace(slug=slug), ai_state="off", stars_enabled=False)


@pytest.mark.parametrize("state", ["off", "paused", "invalid", "configured"])
async def test_provider_probe_is_local_only_and_suppresses_error_details(monkeypatch, state):
    monkeypatch.setattr(readiness, "config", lambda: SimpleNamespace(ai_enabled=state != "off"))
    paused = AsyncMock(return_value=state == "paused")
    monkeypatch.setattr(readiness, "setting", paused)
    adapter = SimpleNamespace(
        upper_bound=Mock(
            return_value=1, side_effect=ValueError("private") if state == "invalid" else None
        ),
        call=AsyncMock(side_effect=AssertionError("No network or provider usage")),
    )
    factory = Mock(return_value=adapter)
    monkeypatch.setattr(readiness, "provider", factory)
    assert await readiness.ai_configuration(object()) == state
    adapter.call.assert_not_awaited()
    if state in {"off", "paused"}:
        factory.assert_not_called()
    else:
        adapter.upper_bound.assert_called_once_with({}, "", "", [])


@pytest.mark.parametrize("value", [0, -1])
async def test_nonpositive_provider_exposure_is_not_configured(monkeypatch, value):
    monkeypatch.setattr(readiness, "config", lambda: SimpleNamespace(ai_enabled=True))
    monkeypatch.setattr(readiness, "setting", AsyncMock(return_value=False))
    monkeypatch.setattr(
        readiness, "provider", lambda: SimpleNamespace(upper_bound=lambda *a: value)
    )
    assert await readiness.ai_configuration(object()) == "invalid"
