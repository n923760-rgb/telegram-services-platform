"""Native output and synthetic AI contract checks; no live-provider evidence."""

import json
from html import unescape
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import UUID

import cv2
import numpy as np
import pytest
from PIL import Image

from app.core.settings import config
from app.providers.storage import LocalStorage, OwnedStorage
from app.publications import prepared_page
from app.publications.offering import CONTRACT
from app.services.base import ServiceError
from app.services.hosted_profile.schema import Inputs
from app.services.hosted_profile.service import HostedProfile
from app.services.registry import registry
from tests.profile_page_fixtures import plan


@pytest.fixture(autouse=True)
def database():
    pass


def inputs(**changes):
    return {
        "language": "ar",
        "name": "استوديو مدى 00123",
        "role": "تصميم هويات وتجارب رقمية",
        "intro": "نص تعريفي يكتبه العميل دون اختراع معلومات.",
        "phone": "٠٥٠١٢٣٤٥٦٧",
        "links": "https://www.instagram.com/example/?id=00123&source=profile",
        "sections": "خدماتنا | تصميم الهويات البصرية والتجارب الرقمية.",
        "brief": "تصميم هادئ وفريد يناسب الاستوديو، باللون الأخضر مع إبراز إنستغرام.",
        "qr": "embedded",
        **changes,
    }


def design_plan(**changes):
    return plan(action_order=[0, 1], section_order=[0], **changes)


def test_pilot_is_hidden_disabled_ai_required_and_has_six_month_contract():
    plugin = registry.types["hosted_profile"]
    assert plugin is HostedProfile and plugin.admin_only and not plugin.enabled_by_default
    assert not registry.can_request(plugin.slug)
    assert registry.can_request(plugin.slug, admin=True)
    assert plugin.needs_ai(inputs()) is True
    assert plugin.purchase_contract == CONTRACT and plugin.purchase_contract["months"] == 6
    assert plugin.price_sar == 29
    assert plugin.input_schema.validate_inputs(inputs()) is None
    assert next(f for f in plugin.input_schema.fields if f.name == "role").choices == []


@pytest.mark.parametrize("role", ["محامٍ", "مطعم", "متجر", "مهنة جديدة غير مصنفة"])
def test_professions_are_literal_free_text_with_exact_contact_destinations(role):
    value = Inputs.parse(inputs(role=role)).profile()
    assert value.role == role
    assert value.actions[0].url == inputs()["links"]
    assert value.actions[1].url == "https://wa.me/966501234567"
    assert value.actions[0].label == "إنستغرام"


@pytest.mark.parametrize(
    "changes",
    [
        {"name": "\n"},
        {"role": "a\nb"},
        {"intro": " "},
        {"brief": " "},
        {"brief": "a\u202eb"},
        {"language": "xx"},
        {"qr": True},
        {"phone": "call me"},
        {"phone": "12345"},
        {"links": "javascript:alert(1)"},
        {"links": "https://user:pass@example.invalid"},
        {"links": "http://example.invalid"},
        {"links": "https://example.invalid/%0a"},
        {"links": "x | https://example.invalid/\\path"},
        {"links": "https://example.invalid\n" * 7},
        {"links": "", "phone": ""},
        {"sections": "a"},
        {"sections": "title | "},
        {"sections": "a | b\n" * 7},
        {"sections": "a | " + "b" * 801},
        {"unexpected": "content"},
    ],
)
async def test_bad_intake_cannot_call_ai_or_write_outputs(changes, monkeypatch):
    monkeypatch.setattr(config(), "publications_enabled", True)
    service = HostedProfile()
    service.runtime = SimpleNamespace(ai=SimpleNamespace(extract=AsyncMock()), storage=Mock())
    with pytest.raises(ServiceError, match="input_invalid"):
        await service.run(inputs(**changes))
    service.runtime.ai.extract.assert_not_awaited()
    service.runtime.storage.save.assert_not_called()


def test_labels_and_urls_remain_literal_and_whatsapp_is_not_duplicated():
    value = Inputs.parse(inputs(links="تواصل | https://wa.me/966501234567")).profile()
    assert len(value.actions) == 1 and value.actions[0].label == "تواصل"
    value = Inputs.parse(inputs(links="https://instagram.com.attacker.invalid/account")).profile()
    assert value.actions[0].label != "إنستغرام"


@pytest.mark.parametrize("language", ["ar", "en"])
@pytest.mark.parametrize("qr", ["embedded", "separate"])
async def test_ai_design_produces_exact_private_bundle_and_native_whole_page_qr(
    tmp_path, monkeypatch, language, qr
):
    monkeypatch.setattr(config(), "publications_enabled", True)
    monkeypatch.setattr(config(), "publication_origin", "https://profiles.example.invalid")
    captured = []

    async def extract(schema, source, prompt):
        captured.append(json.loads(source))
        return schema.model_validate(design_plan())

    ai = SimpleNamespace(extract=AsyncMock(side_effect=extract))
    store = OwnedStorage(LocalStorage(tmp_path), 1)
    service = HostedProfile()
    service.runtime = SimpleNamespace(ai=ai, storage=store)
    result = await service.run(inputs(language=language, qr=qr))
    assert ai.extract.await_count == 1
    assert captured[0]["brief"] == inputs()["brief"]
    assert captured[0]["role"] == inputs()["role"]
    assert all("url" not in action for action in captured[0]["actions"])
    assert result.completion and result.completion.kind == "profile_page_v1"
    snapshot = prepared_page.Snapshot.model_validate(result.completion.payload)
    identity = UUID(snapshot.publication_id)
    url = prepared_page.public_url(config().publication_origin, identity)
    verified = prepared_page.render(
        result.completion.payload, publication_id=identity, origin=config().publication_origin
    )
    files = {a.filename: store.read(a.key) for a in result.artifacts}
    assert files == verified
    assert set(files) == {"profile.html", "qr.png", "qr.svg", "share-card.png"}
    html = files["profile.html"].decode()
    assert inputs()["links"] in unescape(html) and "https://wa.me/966501234567" in html
    assert "<script" not in html.lower()
    assert ("data:image/png;base64," in html) == (qr == "embedded")
    image = np.array(Image.open(BytesIO(files["qr.png"])).convert("RGB"))
    decoded, points, _ = cv2.QRCodeDetectorAruco().detectAndDecode(image)
    assert points is not None and decoded == url
    assert "غير منشورة" in result.preview_localizations["ar"]
    assert "Unpublished" in result.preview_localizations["en"]


@pytest.mark.parametrize("block", ["disabled", "missing_ai", "invalid_origin"])
async def test_runtime_gates_fail_before_ai_or_storage(monkeypatch, block):
    monkeypatch.setattr(config(), "publications_enabled", block != "disabled")
    monkeypatch.setattr(
        config(),
        "publication_origin",
        "http://invalid" if block == "invalid_origin" else "https://profiles.example.invalid",
    )
    service = HostedProfile()
    ai = SimpleNamespace(extract=AsyncMock())
    service.runtime = SimpleNamespace(ai=None if block == "missing_ai" else ai, storage=Mock())
    with pytest.raises(ServiceError):
        await service.run(inputs())
    ai.extract.assert_not_awaited()
    service.runtime.storage.save.assert_not_called()
