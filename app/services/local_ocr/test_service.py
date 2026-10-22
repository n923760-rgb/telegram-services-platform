from types import SimpleNamespace

import pytest

from app.providers.documents.base import DocumentError, Recognition
from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.local_ocr.service import LocalOcr


class Processor:
    def __init__(self, result=None, error=None):
        self.result = result or Recognition("مرحبا 00123", 0.99)
        self.error = error
        self.calls = []

    async def recognize(self, images, language):
        self.calls.append((images, language))
        if self.error:
            raise self.error
        return self.result


async def test_service_uses_injected_documents_without_ai_and_keeps_source_order(tmp_path):
    storage = OwnedStorage(LocalStorage(tmp_path), 1)
    files = [storage.save(f"{i}.jpg", str(i).encode(), "image/jpeg").key for i in range(2)]
    processor = Processor()
    service = LocalOcr()
    service.runtime = SimpleNamespace(storage=storage, ai=None, documents=processor)
    inputs = {"images": files, "language": "mixed"}
    service.input_schema.validate_inputs(inputs)
    assert not service.needs_ai(inputs)
    result = await service.run(inputs)
    assert result.text == "مرحبا 00123" and result.preview and not result.artifacts
    assert processor.calls == [([b"0", b"1"], "mixed")]


async def test_long_local_result_produces_utf8_text_without_replanning(tmp_path):
    storage = OwnedStorage(LocalStorage(tmp_path), 1)
    image = storage.save("input.jpg", b"input", "image/jpeg")
    text = "مرحبا 00123\n" * 400
    service = LocalOcr()
    service.runtime = SimpleNamespace(
        storage=storage, ai=None, documents=Processor(Recognition(text, 0.99))
    )
    result = await service.run({"images": [image.key], "language": "ar"})
    assert result.text == text
    assert storage.read(result.artifacts[0].key).decode("utf-8") == text


@pytest.mark.parametrize(
    "inputs",
    [
        {"images": [], "language": "en"},
        {"images": ["one", "one"], "language": "en"},
        {"images": ["one"], "language": "none"},
        {"images": ["one"], "language": "en", "style": "formal"},
    ],
)
def test_invalid_input_fails_before_ai_admission(inputs):
    with pytest.raises(ServiceError, match="input_invalid"):
        LocalOcr.needs_ai(inputs)


@pytest.mark.parametrize(
    "key,transient",
    [("ocr_unclear", False), ("local_ocr_timeout", False), ("local_ocr_busy", True)],
)
async def test_safe_error_mapping_has_no_ai_fallback(tmp_path, key, transient):
    storage = OwnedStorage(LocalStorage(tmp_path), 1)
    image = storage.save("input.jpg", b"input", "image/jpeg")
    service = LocalOcr()
    service.runtime = SimpleNamespace(
        storage=storage, ai=None, documents=Processor(error=DocumentError(key, transient=transient))
    )
    with pytest.raises(ServiceError) as error:
        await service.run({"images": [image.key], "language": "en"})
    assert (error.value.key, error.value.transient) == (key, transient)
