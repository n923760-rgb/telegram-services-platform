from types import SimpleNamespace

import pytest

from app.bot.catalog import view
from app.services.catalog import CATEGORY_KEYS, ordered
from app.services.registry import Registry, registry


@pytest.fixture(autouse=True)
def database():
    yield


def row(slug):
    plugin = registry.types[slug]
    return SimpleNamespace(slug=slug, name_ar=plugin.name_ar, name_en=plugin.name_en)


@pytest.mark.parametrize("lang", ["ar", "en"])
def test_text_order_and_pdf_conversion_category_are_clear(lang):
    rows = [
        row(slug) for slug in ("text_summary", "text_editing", "text_translation", "pdf_to_word")
    ]
    _, items = view(rows, lang, category="text")
    assert [callback for _, callback in items[:-1]] == [
        "service:text_translation",
        "service:text_editing",
        "service:text_summary",
    ]
    _, pdf_items = view(rows, lang, category="pdf")
    assert pdf_items[0][1] == "service:pdf_to_word"
    _, doc_items = view(rows, lang, category="documents")
    assert all(callback != "service:pdf_to_word" for _, callback in doc_items)


def test_shared_order_is_independent_of_registered_slug_alphabet():
    rows = [row(slug) for slug in ("document_image_enhancement", "image_to_text", "text_editing")]
    assert [r.slug for r in ordered(rows, registry.types)] == [
        "text_editing",
        "image_to_text",
        "document_image_enhancement",
    ]
    assert list(CATEGORY_KEYS)[:3] == ["text", "images", "documents"]


@pytest.mark.parametrize("value", [-1, 1001, True, "1"])
def test_bad_plugin_presentation_order_is_rejected(monkeypatch, value):
    monkeypatch.setattr(registry.types["echo"], "menu_order", value)
    with pytest.raises(ValueError, match="invalid service menu order"):
        Registry().discover()
