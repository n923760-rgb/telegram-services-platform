from types import SimpleNamespace

import pytest

from app.bot.catalog import view
from app.services.echo.service import Echo
from app.services.registry import Registry, registry


@pytest.fixture(autouse=True)
def database():
    yield


def test_production_verification_is_private_but_admin_can_request():
    assert Echo.admin_only is True
    assert not registry.can_request("echo")
    assert registry.can_request("echo", admin=True)
    assert registry.customer_visible("echo")  # Still managed and historically resolvable.
    assert not registry.can_request("local_ocr", admin=True)


@pytest.mark.parametrize("lang", ["ar", "en"])
def test_customer_catalog_omits_empty_internal_group_and_stale_category(lang):
    row = SimpleNamespace(slug="echo", name_ar="اختبار", name_en="Test")
    assert view([row], lang)[1] == []
    assert view([row], lang, category="other")[1] == [
        ("العودة إلى الأقسام" if lang == "ar" else "Back to categories", "menu:services")
    ]
    assert view([row], lang, admin=True)[1][0][1] == "catalog:other:0"


@pytest.mark.parametrize("value", [1, "yes", None])
def test_audience_metadata_must_be_boolean(monkeypatch, value):
    monkeypatch.setattr(Echo, "admin_only", value)
    with pytest.raises(ValueError, match="invalid service audience"):
        Registry().discover()
