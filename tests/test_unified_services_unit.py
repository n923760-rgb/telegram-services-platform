from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.bot.catalog import view
from app.providers.documents.base import DocumentError, Recognition
from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.image_to_text.schema import Extracted
from app.services.image_to_text.service import ImageToText
from app.services.pdf_tables_excel.service import PdfTablesExcel
from app.services.pdf_tables_excel.test_service import extraction, inputs
from app.services.registry import Registry, registry


def ocr(tmp_path, recognition=None, error=None):
    storage = OwnedStorage(LocalStorage(tmp_path), 1)
    image = storage.save("image.jpg", b"synthetic", "image/jpeg")
    documents = SimpleNamespace(recognize=AsyncMock(return_value=recognition, side_effect=error))
    ai = SimpleNamespace(
        extract=AsyncMock(return_value=Extracted(readable=True, confidence=0.99, text="AI 00123"))
    )
    service = ImageToText()
    service.runtime = SimpleNamespace(storage=storage, documents=documents, ai=ai)
    return service, {"images": [image.key]}, documents, ai


async def test_one_native_result_preserves_original_and_does_not_call_ai(tmp_path):
    service, request, documents, ai = ocr(tmp_path, Recognition("Original 00123", 0.95))
    result = await service.run(request)
    assert result.text == "Original 00123" and not result.needs_confirmation
    documents.recognize.assert_awaited_once_with([b"synthetic"], "mixed")
    ai.extract.assert_not_awaited()


@pytest.mark.parametrize("confidence", [0.0, 0.7, 0.899])
async def test_weak_native_result_uses_one_job_scoped_fallback(tmp_path, confidence):
    service, request, _, ai = ocr(tmp_path, Recognition("Weak 0123", confidence))
    assert (await service.run(request)).text == "AI 00123"
    ai.extract.assert_awaited_once()


@pytest.mark.parametrize("key", ["ocr_unclear", "local_ocr_unavailable"])
async def test_only_classified_native_failure_allows_fallback(tmp_path, key):
    service, request, _, ai = ocr(tmp_path, error=DocumentError(key))
    assert (await service.run(request)).text == "AI 00123"
    ai.extract.assert_awaited_once()


@pytest.mark.parametrize(
    "key",
    ["input_invalid", "file_invalid", "local_ocr_limit", "local_ocr_busy", "local_ocr_timeout"],
)
async def test_resource_security_and_invalid_input_failures_do_not_call_ai(tmp_path, key):
    service, request, _, ai = ocr(tmp_path, error=DocumentError(key, transient=True))
    with pytest.raises(ServiceError) as caught:
        await service.run(request)
    assert caught.value.key == key and caught.value.transient
    ai.extract.assert_not_awaited()


async def test_fallback_unclear_result_is_not_delivered(tmp_path):
    service, request, _, ai = ocr(tmp_path, Recognition("Weak", 0.7))
    ai.extract.return_value = Extracted(readable=False, confidence=0, text="")
    with pytest.raises(ServiceError, match="ocr_unclear"):
        await service.run(request)


async def test_foreign_image_does_not_reach_either_engine(tmp_path):
    service, _, documents, ai = ocr(tmp_path)
    foreign = OwnedStorage(LocalStorage(tmp_path), 2).save("image.jpg", b"test", "image/jpeg")
    with pytest.raises(ServiceError):
        await service.run({"images": [foreign.key]})
    documents.recognize.assert_not_awaited()
    ai.extract.assert_not_awaited()


@pytest.mark.parametrize("lang", ["ar", "en"])
def test_only_one_extraction_card_and_generic_legacy_resolution(lang):
    rows = [SimpleNamespace(slug=s, name_ar=s, name_en=s) for s in ("local_ocr", "image_to_text")]
    _, items = view(rows, lang, category="images")
    assert [data for _, data in items if data.startswith("service:")] == ["service:image_to_text"]
    assert registry.customer_slug("local_ocr") == "image_to_text"
    assert not registry.customer_visible("local_ocr")
    assert registry.customer_slug("unknown") is None


@pytest.mark.parametrize("replacement", ["missing", "local_ocr"])
def test_invalid_replacement_fails_discovery(monkeypatch, replacement):
    monkeypatch.setattr(registry.types["local_ocr"], "replaced_by", replacement)
    with pytest.raises(ValueError, match="invalid service replacement"):
        Registry().discover()


async def test_table_method_is_internal_and_alternate_is_bounded(tmp_path):
    storage = OwnedStorage(LocalStorage(tmp_path), 1)
    file = storage.save("source.pdf", b"synthetic", "application/pdf")
    extractor = AsyncMock(side_effect=[DocumentError("pdf_tables_missing"), extraction()])
    service = PdfTablesExcel()
    service.runtime = SimpleNamespace(
        storage=storage, tables=SimpleNamespace(extract=extractor), ai=None
    )
    result = await service.run(inputs(pdf=file.key))
    assert result.needs_confirmation
    assert [call.args[1] for call in extractor.await_args_list] == ["lattice", "stream"]
    assert "method" not in [field.name for field in service.input_schema.conversation()]


@pytest.mark.parametrize("key", ["file_invalid", "pdf_tables_limit", "pdf_image_content"])
async def test_table_unsafe_failure_does_not_try_another_method(tmp_path, key):
    storage = OwnedStorage(LocalStorage(tmp_path), 1)
    file = storage.save("source.pdf", b"synthetic", "application/pdf")
    extractor = AsyncMock(side_effect=DocumentError(key))
    service = PdfTablesExcel()
    service.runtime = SimpleNamespace(
        storage=storage, tables=SimpleNamespace(extract=extractor), ai=None
    )
    with pytest.raises(ServiceError, match=key):
        await service.run(inputs(pdf=file.key))
    extractor.assert_awaited_once()
