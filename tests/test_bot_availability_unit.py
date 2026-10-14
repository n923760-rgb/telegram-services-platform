from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.bot.availability import ai_admission_available
from app.bot.catalog import view
from app.core.i18n import tr
from app.core.settings import config
from app.services.registry import registry


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize(
    "value,available",
    [
        (None, True),
        ({"value": False}, True),
        ({"value": True}, False),
        ({"value": "false"}, False),
        ({}, False),
        ("secret", False),
    ],
)
async def test_pause_state_is_read_only_and_fail_closed(monkeypatch, value, available):
    monkeypatch.setattr(config(), "ai_enabled", True)
    db = SimpleNamespace(
        get=AsyncMock(return_value=None if value is None else SimpleNamespace(value=value))
    )
    assert await ai_admission_available(db) is available
    db.get.assert_awaited_once()


async def test_ai_off_does_not_open_provider_or_query_state(monkeypatch):
    monkeypatch.setattr(config(), "ai_enabled", False)
    db = SimpleNamespace(get=AsyncMock(side_effect=AssertionError("must not query")))
    assert not await ai_admission_available(db)
    db.get.assert_not_awaited()


@pytest.mark.parametrize("lang", ["ar", "en"])
def test_catalog_warning_preserves_labels_callbacks_and_direct_categories(monkeypatch, lang):
    row = SimpleNamespace(slug="future_service", name_ar="Future", name_en="Future")
    monkeypatch.setitem(
        registry.types, row.slug, SimpleNamespace(category="other", requires_ai=True)
    )
    normal, items = view([row], lang, category="other")
    blocked, blocked_items = view([row], lang, category="other", ai_available=False)
    assert blocked_items == items and tr("catalog_ai_notice", lang) in blocked
    assert tr("catalog_ai_notice", lang) not in normal
    direct = SimpleNamespace(slug="csv_review", name_ar="CSV", name_en="CSV")
    text, _ = view([direct], lang, category="data", ai_available=False)
    assert tr("catalog_ai_notice", lang) not in text
