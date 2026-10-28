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
        activity="creative",
        style="minimal",
        profile="Independent design studio",
        links=(
            "Website | https://example.invalid/?id=00123\nContact | https://example.invalid/contact"
        ),
    )

    async def extract(schema, content, prompt):
        assert '"activity": "creative"' in content
        assert '"style": "minimal"' in content
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


@pytest.mark.parametrize("activity", ["professional", "legal", "shop", "restaurant", "creative"])
@pytest.mark.parametrize("style", ["modern", "classic", "minimal"])
@pytest.mark.parametrize("language", ["ar", "en"])
def test_activity_layouts_preserve_order_targets_and_nonoverlapping_hitboxes(
    activity, style, language
):
    values = Inputs.parse(
        inputs(
            activity=activity,
            style=style,
            language=language,
            name="متجر التصميم" if language == "ar" else "Design Studio",
            subtitle="منتجات وخدمات" if language == "ar" else "Products and services",
            links="\n".join(f"Link {i}|https://example.invalid/?id=00{i}" for i in range(6)),
        )
    )
    plan = presentation_schema(values).model_validate(
        {"palette": "navy", "order": [5, 4, 3, 2, 1, 0]}
    )
    page = PdfReader(BytesIO(build(values, plan))).pages[0]
    annotations = [ref.get_object() for ref in page["/Annots"]]
    assert [a["/A"]["/URI"] for a in annotations] == [
        f"https://example.invalid/?id=00{i}" for i in range(5, -1, -1)
    ]
    rects = [list(a["/Rect"]) for a in annotations]
    for i, (x1, y1, x2, y2) in enumerate(rects):
        assert 30 <= x1 < x2 <= 390 and 60 < y1 < y2 < float(page.mediabox.height) - 30
        for a, b, c, d in rects[i + 1 :]:
            assert x2 <= a or c <= x1 or y2 <= b or d <= y1
    if activity in {"shop", "creative"}:
        assert any(float(r[2] - r[0]) < 200 for r in rects)


@pytest.mark.parametrize("activity", ["shop", "creative"])
def test_long_labels_expand_grid_instead_of_shrinking_below_readable_size(activity):
    values = Inputs.parse(
        inputs(
            activity=activity,
            name="W" * 48,
            subtitle="W" * 60,
            links="\n".join("W" * 48 + f"|https://example.invalid/{i}" for i in range(6)),
        )
    )
    page = PdfReader(BytesIO(build(values))).pages[0]
    assert all(
        float(ref.get_object()["/Rect"][2] - ref.get_object()["/Rect"][0]) == 336
        for ref in page["/Annots"]
    )


@pytest.mark.parametrize("changes", [{"activity": "invented"}, {"style": "remote-css"}])
def test_unrecognized_design_choices_reject_before_ai(changes):
    with pytest.raises(ServiceError, match="input_invalid"):
        InteractiveCard.needs_ai(inputs(**changes))


def test_public_intake_accepts_design_choice_and_phone_only_or_default_layout():
    for options in ({}, {"activity": "restaurant", "style": "classic"}):
        source = {
            "mode": "direct",
            "language": "ar",
            "name": "مطعم",
            "phone": "0501234567",
            **options,
        }
        InteractiveCard.input_schema.validate_inputs(source)
        assert not InteractiveCard.needs_ai(source)


@pytest.mark.parametrize("activity,first_column", [("shop", 0), ("creative", 1)])
def test_grid_order_follows_customer_language(activity, first_column):
    sources = {
        lang: Inputs.parse(
            inputs(
                language=lang,
                activity=activity,
                links="\n".join(f"Link {i}|https://example.invalid/{i}" for i in range(4)),
            )
        )
        for lang in ("ar", "en")
    }
    rects = {
        lang: [
            a.get_object()["/Rect"] for a in PdfReader(BytesIO(build(source))).pages[0]["/Annots"]
        ]
        for lang, source in sources.items()
    }
    assert rects["ar"][first_column][0] > rects["en"][first_column][0]
