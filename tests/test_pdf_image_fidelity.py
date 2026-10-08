from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from pypdf import PdfReader

from app.files.pdf_content import has_image_content
from app.services.base import ServiceError
from app.services.pdf_to_word.test_service import configured_service
from tests.pdf_image_fixtures import drawing_pdf, mixed_pdf


@pytest.mark.parametrize("kind", ["xobject", "inline", "nested", "later_page"])
async def test_mixed_text_image_pdf_is_rejected_before_ai_or_output(tmp_path, monkeypatch, kind):
    service, source, store, ai = configured_service(tmp_path, mixed_pdf(kind))
    # Detect PDF drawing instructions without rasterizing/decompressing image pixels.
    decode = Mock(side_effect=AssertionError("image pixels must not be decoded"))
    monkeypatch.setattr("PIL.Image.open", decode)
    with pytest.raises(ServiceError, match="pdf_image_content"):
        await service.run({"pdf": source.key})
    ai.extract.assert_not_awaited()
    decode.assert_not_called()
    assert store.storage.usage(1)[1] == 1


async def test_reusable_text_only_pdf_forms_remain_supported(tmp_path):
    service, source, _, ai = configured_service(tmp_path, mixed_pdf("text_form"))
    result = await service.run({"pdf": source.key})
    assert result.artifacts[0].filename == "result.docx"
    assert "Text in a reusable Form." in ai.extract.await_args.args[1]


@pytest.mark.parametrize(
    ("kind", "key"),
    [("cyclic", "file_invalid"), ("deep", "file_invalid"), ("huge", "pdf_image_content")],
)
async def test_drawing_limits_reject_without_ai_or_decoding(tmp_path, monkeypatch, kind, key):
    service, source, _, ai = configured_service(tmp_path, drawing_pdf(kind))
    monkeypatch.setattr("PIL.Image.open", Mock(side_effect=AssertionError("must not decode")))
    with pytest.raises(ServiceError, match=key):
        await service.run({"pdf": source.key})
    ai.extract.assert_not_awaited()


async def test_unused_image_resources_do_not_block_text_only_conversion(tmp_path, monkeypatch):
    data = drawing_pdf("unused")
    reader = PdfReader(BytesIO(data))
    assert not has_image_content(reader.pages[0], reader)
    service, source, _, ai = configured_service(tmp_path, data)
    monkeypatch.setattr("PIL.Image.open", Mock(side_effect=AssertionError("must not decode")))
    result = await service.run({"pdf": source.key})
    assert result.artifacts[0].filename == "result.docx"
    ai.extract.assert_awaited_once()


def test_drawing_instruction_budget_fails_honestly():
    stream = SimpleNamespace(operations=[([], b"q")] * 100001)
    page = SimpleNamespace(get_contents=lambda: stream, get=lambda *args: {})
    with pytest.raises(ValueError, match="inspection limit"):
        has_image_content(page, None)
