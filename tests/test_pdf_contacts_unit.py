from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pdfplumber
import pytest

from app.builders import pdf
from app.builders.schema import Document, Section
from app.providers.storage import LocalStorage, OwnedStorage
from app.services.text_to_pdf.schema import PdfPlan
from app.services.text_to_pdf.service import TextToPdf
from tests.pdf_contact_fixtures import CONTACTS, check_contacts, contact_document


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize("contact", CONTACTS)
@pytest.mark.parametrize("position", ["start", "middle", "end"])
def test_complete_contacts_have_ordered_glyphs_in_every_arabic_text_role(contact, position):
    source = contact_document(contact, position)
    snapshot = source.model_dump_json()
    check_contacts(pdf.build(source), contact)
    assert source.model_dump_json() == snapshot


@pytest.mark.parametrize("contact", CONTACTS)
@pytest.mark.parametrize("prefix", ["", "Contact "])
def test_english_and_standalone_identifiers_remain_ltr_and_literal(contact, prefix):
    text = prefix + contact
    assert not pdf._reading_rtl(text)
    assert pdf._visual(text) == text
    with pdfplumber.open(
        BytesIO(pdf.build(Document(title="Contact", sections=[Section(paragraphs=[text])])))
    ) as document:
        chars = [c for c in document.pages[0].chars if c["size"] == 11]
        assert "".join(c["text"] for c in chars) == text
        assert min(c["x0"] for c in chars) == pytest.approx(48)


def test_long_contact_does_not_make_short_arabic_prose_left_aligned():
    text = "راجع 00123@very.long.support.example.invalid"
    assert pdf._reading_rtl(text)
    with pdfplumber.open(
        BytesIO(pdf.build(Document(title="متابعة", sections=[Section(paragraphs=[text])])))
    ) as document:
        page = document.pages[0]
        chars = [c for c in page.chars if c["size"] == 11]
        assert max(c["x1"] for c in chars) == pytest.approx(page.width - 48)


def test_wrapped_contact_only_last_line_retains_its_arabic_paragraph_alignment():
    pdf._register_fonts()
    contact = "00123@very.long.support.example.invalid"
    text = next(
        "راجع " * n + contact
        for n in range(1, 50)
        if pdf._wrap("راجع " * n + contact, "DejaVu", 11, 595.2756 - 84)[-1] == contact
    )
    source = Document(title="متابعة", sections=[Section(paragraphs=[text])])
    with pdfplumber.open(BytesIO(pdf.build(source))) as document:
        page = document.pages[0]
        chars = page.chars
        stream = "".join(c["text"] for c in chars)
        index = stream.index(contact)
        glyphs = chars[index : index + len(contact)]
        assert max(c["x1"] for c in glyphs) == pytest.approx(page.width - 48)


@pytest.mark.parametrize("mode", ["direct", "smart", "continuation"])
async def test_service_paths_preserve_numeric_email_without_extra_provider_calls(tmp_path, mode):
    contact = CONTACTS[0]
    plan = PdfPlan(document=contact_document(contact))
    ai = SimpleNamespace(extract=AsyncMock(return_value=plan))
    store = OwnedStorage(LocalStorage(tmp_path), 1)
    service = TextToPdf()
    service.runtime = SimpleNamespace(storage=store, ai=ai)
    text = f"راجع {contact} لتأكيد الطلب"
    inputs = {
        "text": text if mode == "direct" else "\n".join([text] * 4),
        "mode": "direct" if mode == "direct" else "smart",
    }
    if mode == "direct":
        inputs["title"] = text
    if mode == "continuation":
        inputs["__continuation"] = plan.model_dump(mode="json")
    result = await service.run(inputs)
    content = store.read(result.artifacts[0].key)
    if mode == "direct":
        with pdfplumber.open(BytesIO(content)) as document:
            assert "".join(c["text"] for c in document.pages[0].chars).count(contact) == 2
    else:
        check_contacts(content, contact)
    assert ai.extract.await_count == (1 if mode == "smart" else 0)
    assert not result.needs_confirmation
