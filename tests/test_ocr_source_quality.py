from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from PIL import Image

from app.files.validation import image
from app.providers.documents.base import Recognition
from app.providers.documents.tesseract import TesseractDocuments
from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.image_to_text.schema import Extracted
from app.services.image_to_text.service import ImageToText
from tests.ocr_fixtures import detailed


@pytest.fixture(autouse=True)
def database():
    yield


def test_native_preparation_retains_detail_without_jpeg_recompression_or_metadata():
    data = detailed()
    prepared = TesseractDocuments._prepare(data)
    with Image.open(BytesIO(data)) as original, Image.open(BytesIO(prepared)) as actual:
        assert actual.format == "PNG" and actual.size == (1800, 540)
        assert actual.convert("RGB").tobytes() == original.convert("RGB").tobytes()
        assert not actual.info
    with Image.open(BytesIO(image(data, 10 * 1024 * 1024))) as legacy:
        assert legacy.width == 1024


async def test_native_review_receives_sanitized_high_detail_original_evidence(tmp_path):
    store = OwnedStorage(LocalStorage(tmp_path), 1)
    file = store.save("source.png", detailed(), "image/png")
    corrected = Extracted(readable=True, confidence=0.99, text="Invoice 00123")
    ai = SimpleNamespace(review_candidate=AsyncMock(return_value=corrected), extract=AsyncMock())
    service = ImageToText()
    service.runtime = SimpleNamespace(
        storage=store,
        ai=ai,
        documents=SimpleNamespace(
            recognize=AsyncMock(return_value=Recognition("Invoice 0123", 0.99))
        ),
    )
    assert (await service.run({"images": [file.key]})).text == corrected.text
    call = ai.review_candidate.await_args
    assert call.args[0].text == "Invoice 0123"
    with Image.open(BytesIO(call.kwargs["images"][0])) as evidence:
        assert evidence.format == "JPEG" and evidence.width == 1800
        assert "Private" not in evidence.info
    ai.extract.assert_not_awaited()
    assert service.input_schema.fields[0].preserve_image


async def test_invalid_stored_source_never_reaches_ai(tmp_path):
    store = OwnedStorage(LocalStorage(tmp_path), 1)
    file = store.save("source.jpg", b"broken", "image/jpeg")
    ai = SimpleNamespace(extract=AsyncMock(), review_candidate=AsyncMock())
    service = ImageToText()
    service.runtime = SimpleNamespace(storage=store, ai=ai, documents=None)
    with pytest.raises(ServiceError, match="file_invalid"):
        await service.run({"images": [file.key]})
    ai.extract.assert_not_awaited()
    ai.review_candidate.assert_not_awaited()
