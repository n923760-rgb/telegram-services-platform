from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pdfplumber
import pytest

from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.text_to_pdf.schema import PdfPlan
from app.services.text_to_pdf.service import TextToPdf


async def test_pdf_service_builds_document(tmp_path):
    plan = PdfPlan.model_validate(
        {"document": {"title": "عنوان", "sections": [{"paragraphs": ["نص 123"]}]}}
    )
    service = TextToPdf()
    store = OwnedStorage(LocalStorage(tmp_path), 1)
    service.runtime = SimpleNamespace(
        storage=store, ai=SimpleNamespace(extract=AsyncMock(return_value=plan))
    )
    result = await service.run({"text": "نص 123"})
    assert not result.needs_confirmation
    with pdfplumber.open(BytesIO(store.read(result.artifacts[0].key))) as doc:
        assert "123" in "".join(page.extract_text() or "" for page in doc.pages)


async def test_pdf_service_missing_information_releases(tmp_path):
    plan = PdfPlan.model_validate({"missing_information": True})
    service = TextToPdf()
    service.runtime = SimpleNamespace(
        storage=OwnedStorage(LocalStorage(tmp_path), 1),
        ai=SimpleNamespace(extract=AsyncMock(return_value=plan)),
    )
    with pytest.raises(ServiceError, match="needs_information"):
        await service.run({"text": "غير كافٍ"})


async def test_pdf_service_ambiguous_confirmation_then_resume(tmp_path):
    plan = PdfPlan.model_validate(
        {
            "ambiguous": True,
            "question": "اعتماد هذا الهيكل؟",
            "document": {"title": "عنوان", "sections": [{"paragraphs": ["نص 123"]}]},
        }
    )
    service = TextToPdf()
    store = OwnedStorage(LocalStorage(tmp_path), 1)
    service.runtime = SimpleNamespace(
        storage=store, ai=SimpleNamespace(extract=AsyncMock(return_value=plan))
    )
    first = await service.run({"text": "نص 123"})
    assert first.needs_confirmation and first.continuation
    # Resuming with the continuation must not call the AI provider again.
    second = await service.run({"text": "نص 123", "__continuation": first.continuation})
    assert not second.needs_confirmation
    assert service.runtime.ai.extract.await_count == 1
    with pdfplumber.open(BytesIO(store.read(second.artifacts[0].key))) as doc:
        assert "123" in "".join(page.extract_text() or "" for page in doc.pages)


@pytest.mark.parametrize(
    "text",
    [
        "Arabic نص عربي 00123\n\nEnglish <tag> & data 456\nLast 789",
        "Data 00123\n" * 120 + "Last 789",
    ],
)
async def test_direct_pdf_preserves_content_without_ai(tmp_path, text):
    service = TextToPdf()
    store = OwnedStorage(LocalStorage(tmp_path), 1)
    service.runtime = SimpleNamespace(storage=store, ai=None)
    inputs = {"text": text, "mode": "direct", "title": "عنوان 2026"}
    assert service.needs_ai(inputs) is False
    result = await service.run(inputs)
    assert not result.needs_confirmation
    with pdfplumber.open(BytesIO(store.read(result.artifacts[0].key))) as doc:
        rendered = "\n".join(page.extract_text() or "" for page in doc.pages)
        assert rendered.count("00123") == text.count("00123")
        assert "789" in rendered
        assert "789" in (doc.pages[-1].extract_text() or "")
        if "<tag>" in text:
            assert "<tag> & data 456" in rendered
        else:
            assert len(doc.pages) > 1


def test_pdf_schema_requires_explicit_mode_with_optional_direct_title():
    with pytest.raises(ServiceError, match="input_invalid"):
        TextToPdf.input_schema.validate_inputs({"text": "text"})
    TextToPdf.input_schema.validate_inputs({"text": "text", "mode": "direct"})
    TextToPdf.input_schema.validate_inputs({"text": "text", "mode": "smart"})


async def test_direct_pdf_without_title_renders_body_once(tmp_path):
    service = TextToPdf()
    store = OwnedStorage(LocalStorage(tmp_path), 1)
    service.runtime = SimpleNamespace(storage=store, ai=None)
    inputs = {"text": "نص 00123\n\nEnglish 125.50", "mode": "direct"}
    assert not service.needs_ai(inputs)
    result = await service.run(inputs)
    with pdfplumber.open(BytesIO(store.read(result.artifacts[0].key))) as doc:
        assert len(doc.pages) == 1
        text = doc.pages[0].extract_text()
        assert text.count("00123") == 1 and text.count("125.50") == 1
        assert "Document" not in text
    assert "Document" not in result.preview
