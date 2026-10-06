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
