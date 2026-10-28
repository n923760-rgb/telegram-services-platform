from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pypdf import PdfReader
from reportlab.pdfbase import pdfmetrics

from app.builders.interactive_card import build, visual
from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.interactive_card.schema import Inputs, presentation_schema, whatsapp_url
from app.services.interactive_card.service import InteractiveCard


@pytest.fixture(autouse=True)
def database():
    yield


def inputs(**changes):
    return {
        "mode": "direct",
        "language": "en",
        "name": "Demo 00123",
        "links": "Website | https://example.invalid/?id=00123",
        **changes,
    }


@pytest.mark.parametrize("language", ["ar", "en"])
async def test_native_pdf_has_exact_click_targets_and_no_active_content(tmp_path, language):
    service = InteractiveCard()
    service.runtime = SimpleNamespace(storage=OwnedStorage(LocalStorage(tmp_path), 1), ai=None)
    values = inputs(language=language)
    assert service.needs_ai(values) is False
    result = await service.run(values)
    assert len(result.artifacts) == 1
    reader = PdfReader(BytesIO(service.runtime.storage.read(result.artifacts[0].key)))
    assert len(reader.pages) == 1 and "/OpenAction" not in reader.trailer["/Root"]
    annotations = [a.get_object() for a in reader.pages[0]["/Annots"]]
    assert [a["/A"]["/URI"] for a in annotations] == ["https://example.invalid/?id=00123"]
    assert all(a["/A"]["/S"] == "/URI" for a in annotations)


@pytest.mark.parametrize(
    "changes",
    [
        {"links": "JavaScript | javascript:alert(1)"},
        {"links": "HTTP | http://example.invalid"},
        {"links": "Incomplete | https:example.invalid"},
        {"links": "Backslash | https://example.invalid/\\path"},
        {"links": "File | file:///tmp/test"},
        {"links": "Auth | https://user:password@example.invalid"},
        {"links": "Broken"},
        {"links": " | https://example.invalid"},
        {"links": "Link | https://example.invalid/%0a"},
        {"links": "Link | https://example.invalid\n" * 7},
        {"name": "\n"},
        {"name": "a" * 49},
        {"subtitle": "a" * 61},
        {"links": ""},
        {"language": "xx"},
        {"unexpected": "value"},
    ],
)
def test_invalid_inputs_fail_before_reservation(changes):
    with pytest.raises(ServiceError, match="input_invalid"):
        InteractiveCard.needs_ai(inputs(**changes))


def test_arabic_and_maximum_six_links_remain_within_page():
    values = Inputs.parse(
        inputs(
            name="W" * 48,
            subtitle="W" * 60,
            links="\n".join("W" * 48 + " | https://example.invalid/" + str(i) for i in range(6)),
        )
    )
    page = PdfReader(BytesIO(build(values))).pages[0]
    assert len(page["/Annots"]) == 6
    for ref in page["/Annots"]:
        x1, y1, x2, y2 = ref.get_object()["/Rect"]
        assert 0 <= x1 < x2 <= 420 and 60 < y1 < y2 < 480
    font = pdfmetrics.getFont("DejaVu-Bold")
    assert all(ord(c) in font.face.charWidths for c in visual("محمد عبدالله"))


async def test_smart_design_uses_injected_ai_and_preserves_exact_source_targets(tmp_path):
    source = inputs(
        mode="smart",
        profile="Independent design studio",
        links=(
            "Website | https://example.invalid/?id=00123\nContact | https://example.invalid/contact"
        ),
    )

    async def extract(schema, content, prompt):
        assert "Independent design studio" in content
        assert "https://" not in content
        return schema.model_validate(
            {"palette": "emerald", "tagline": "design studio", "order": [1, 0]}
        )

    ai = SimpleNamespace(extract=AsyncMock(side_effect=extract))
    service = InteractiveCard()
    service.runtime = SimpleNamespace(storage=OwnedStorage(LocalStorage(tmp_path), 1), ai=ai)
    assert service.needs_ai(source) is True
    result = await service.run(source)
    page = PdfReader(BytesIO(service.runtime.storage.read(result.artifacts[0].key))).pages[0]
    assert [r.get_object()["/A"]["/URI"] for r in page["/Annots"]] == [
        "https://example.invalid/contact",
        "https://example.invalid/?id=00123",
    ]
    assert "Demo 00123" in page.extract_text()
    ai.extract.assert_awaited_once()


@pytest.mark.parametrize(
    "change",
    [
        {"order": [0, 0]},
        {"order": [True]},
        {"order": [1]},
        {"tagline": "Award-winning studio"},
        {"palette": "remote-css"},
    ],
)
def test_smart_plan_rejects_fabricated_content_and_missing_or_duplicate_buttons(change):
    from pydantic import ValidationError

    values = Inputs.parse(inputs(mode="smart", profile="Design studio"))
    with pytest.raises(ValidationError):
        presentation_schema(values).model_validate(
            {"palette": "navy", "tagline": "Design studio", "order": [0], **change}
        )


async def test_smart_mode_without_provider_does_not_save_a_native_fallback():
    service = InteractiveCard()
    service.runtime = SimpleNamespace(ai=None, storage=None)
    with pytest.raises(ServiceError, match="provider_config"):
        await service.run(inputs(mode="smart"))


def test_single_button_card_is_compact_and_batch_retains_non_overlapping_hit_targets():
    single = PdfReader(BytesIO(build(Inputs.parse(inputs())))).pages[0]
    assert float(single.mediabox.height) <= 350
    values = Inputs.parse(
        inputs(links="\n".join(f"Link {i}|https://example.invalid/{i}" for i in range(6)))
    )
    page = PdfReader(BytesIO(build(values))).pages[0]
    rectangles = [list(r.get_object()["/Rect"]) for r in page["/Annots"]]
    assert len(rectangles) == 6
    assert all(rectangles[i][1] > rectangles[i + 1][3] for i in range(5))


@pytest.mark.parametrize(
    "phone",
    [
        "0501234567",
        "+966501234567",
        "00966501234567",
        "966501234567",
        "٠٥٠١٢٣٤٥٦٧",
        "+966 (50) 123-4567",
    ],
)
def test_phone_only_card_generates_exact_whatsapp_target(phone):
    values = Inputs.parse(inputs(links="", phone=phone, language="ar"))
    assert values.entries() == [("واتساب", "https://wa.me/966501234567")]
    page = PdfReader(BytesIO(build(values))).pages[0]
    assert page["/Annots"][0].get_object()["/A"]["/URI"] == "https://wa.me/966501234567"


@pytest.mark.parametrize(
    "phone",
    [
        "501234567",
        "+00012345678",
        "+9660501234567",
        "+966501234567x",
        "0501234567?text=Hi",
        "+1234567890123456",
        "+966501234567\n",
        "https://example.com",
    ],
)
def test_ambiguous_or_injected_phone_is_rejected(phone):
    with pytest.raises(ValueError):
        whatsapp_url(phone)


def test_explicit_matching_whatsapp_is_not_duplicated_and_total_buttons_are_bounded():
    values = Inputs.parse(inputs(phone="0501234567", links="Message|https://wa.me/966501234567"))
    assert values.entries() == [("Message", "https://wa.me/966501234567")]
    with pytest.raises(ServiceError):
        Inputs.parse(
            inputs(
                phone="0501234567",
                links="\n".join(f"Link {i}|https://example.com/{i}" for i in range(6)),
            )
        )
