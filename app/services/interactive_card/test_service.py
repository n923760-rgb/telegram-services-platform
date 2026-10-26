from io import BytesIO
from types import SimpleNamespace

import pytest
from pypdf import PdfReader
from reportlab.pdfbase import pdfmetrics

from app.builders.interactive_card import build, visual
from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.interactive_card.schema import Inputs
from app.services.interactive_card.service import InteractiveCard


@pytest.fixture(autouse=True)
def database():
    yield


def inputs(**changes):
    return {
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
