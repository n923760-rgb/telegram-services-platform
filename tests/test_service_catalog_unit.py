from types import SimpleNamespace

import pytest

from app.bot.catalog import parse_callback, view
from app.core.i18n import CATALOGS, tr
from app.services.catalog import CATEGORY_KEYS
from app.services.registry import Registry, registry


def row(slug, name=None):
    return SimpleNamespace(slug=slug, name_ar=name or slug, name_en=name or slug)


@pytest.mark.parametrize("lang", ["ar", "en"])
def test_root_only_nonempty_categories_and_no_service_or_prices(lang):
    text, items = view([row("csv_review"), row("cv_formatting")], lang)
    assert text == tr("catalog_choose", lang)
    assert [value for _, value in items] == ["catalog:data:0", "catalog:professional:0"]
    assert not any(value.startswith("service:") for _, value in items)
    assert all(label in CATALOGS[lang].values() for label, _ in items)


@pytest.mark.parametrize("lang", ["ar", "en"])
def test_group_only_its_services_and_back_navigation(lang):
    text, items = view(
        [row("csv_review", "Customer-visible name"), row("local_ocr")], lang, category="data"
    )
    assert items == [
        ("Customer-visible name", "service:csv_review"),
        (tr("catalog_back", lang), "menu:services"),
    ]
    assert tr("catalog_data_description", lang) in text
    assert "local_ocr" not in text


def test_default_and_unknown_plugin_fallback():
    _, items = view([row("echo"), row("future_service")], "en")
    assert [value for _, value in items] == ["catalog:other:0"]
    _, items = view([row("future_service")], "en", category="other")
    assert items[0][1] == "service:future_service"


def test_bounded_pages_and_stale_page_clamping(monkeypatch):
    for i in range(14):
        monkeypatch.setitem(registry.types, f"future_{i}", SimpleNamespace(category="data"))
    rows = [row(f"future_{i}") for i in range(14)]
    first, items = view(rows, "en", category="data")
    assert len([i for i in items if i[1].startswith("service:")]) == 6
    assert "catalog:data:1" in [value for _, value in items]
    assert "Page 1 of 3" in first
    _, middle = view(rows, "en", category="data", page=1)
    assert [value for _, value in middle][-3:] == [
        "catalog:data:0",
        "catalog:data:2",
        "menu:services",
    ]
    last, items = view(rows, "en", category="data", page=999999)
    assert "Page 3 of 3" in last
    assert [value for _, value in items if value.startswith("service:")] == [
        "service:future_12",
        "service:future_13",
    ]


@pytest.mark.parametrize(
    "value",
    [
        "catalog:data:-1",
        "catalog:data:1000000",
        "catalog:unknown:0",
        "catalog:data:01",
        "catalog:data:١",
        "catalog:data:1:extra",
        None,
    ],
)
def test_invalid_callbacks_rejected(value):
    assert parse_callback(value) is None


def test_generated_callbacks_valid_and_fit_telegram_limit():
    for category in CATEGORY_KEYS:
        value = f"catalog:{category}:999999"
        assert parse_callback(value) == (category, 999999)
        assert len(value.encode()) <= 64


def test_empty_catalog_and_empty_category():
    assert view([], "ar") == (tr("no_services"), [])
    text, items = view([], "ar", category="data")
    assert text == tr("catalog_empty") and items == [(tr("catalog_back"), "menu:services")]


def test_invalid_category_fails_registration(monkeypatch):
    monkeypatch.setattr(registry.types["echo"], "category", "typo")
    with pytest.raises(ValueError, match="invalid service category"):
        Registry().discover()
