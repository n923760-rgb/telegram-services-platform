from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from docx import Document
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.pdf_to_word.schema import WordPlan
from app.services.pdf_to_word.service import PdfToWord
from app.services.registry import Registry

SOURCE = "Invoice 12345 customer Example. Total SAR 250.00. Date 2026-10-07."


def pdf_bytes(text=SOURCE, *, encrypted=False, drawn_page=False):
    output = BytesIO()
    document = canvas.Canvas(output, pageCompression=0)
    if text:
        document.drawString(30, 750, text)
    document.showPage()
    if drawn_page:
        document.rect(30, 30, 100, 100, fill=1)
        document.showPage()
    document.save()
    if encrypted:
        writer = PdfWriter()
        writer.append(PdfReader(BytesIO(output.getvalue())))
        writer.encrypt("test-password")
        output = BytesIO()
        writer.write(output)
    return output.getvalue()


def configured_service(tmp_path, data):
    store = OwnedStorage(LocalStorage(tmp_path), 1)
    artifact = store.save("source.pdf", data, "application/pdf")
    ai = SimpleNamespace(extract=AsyncMock())
    ai.extract.return_value = WordPlan.model_validate(
        {"document": {"title": "Invoice", "sections": [{"paragraphs": [SOURCE]}]}}
    )
    service = PdfToWord()
    service.runtime = SimpleNamespace(storage=store, ai=ai)
    return service, artifact, store, ai


def test_plugin_is_discovered_and_disabled_by_default():
    assert Registry().discover().types["pdf_to_word"] is PdfToWord
    assert PdfToWord.enabled_by_default is False


async def test_pdf_to_word_builds_editable_docx_from_real_pdf(tmp_path):
    service, artifact, store, ai = configured_service(tmp_path, pdf_bytes())
    result = await service.run({"pdf": artifact.key})
    assert result.artifacts[0].filename == "result.docx"
    document = Document(BytesIO(store.read(result.artifacts[0].key)))
    assert SOURCE in [paragraph.text for paragraph in document.paragraphs]
    assert "[Page 1]" in ai.extract.await_args.args[1]
    assert SOURCE in ai.extract.await_args.args[1]
    ai.extract.assert_awaited_once()
    assert "\n" in result.preview and "\\n" not in result.preview


@pytest.mark.parametrize(
    ("data", "key"),
    [
        (b"not a pdf", "file_invalid"),
        (pdf_bytes(encrypted=True), "file_invalid"),
        (pdf_bytes(text=""), "pdf_text_unreadable"),
        (pdf_bytes(text="", drawn_page=True), "pdf_text_unreadable"),
        (pdf_bytes(drawn_page=True), "pdf_text_unreadable"),
    ],
    ids=["malformed", "encrypted", "blank", "drawn", "mixed"],
)
async def test_unusable_pdf_rejected_before_ai_and_without_output(tmp_path, data, key):
    service, artifact, store, ai = configured_service(tmp_path, data)
    with pytest.raises(ServiceError, match=key):
        await service.run({"pdf": artifact.key})
    ai.extract.assert_not_awaited()
    assert store.storage.usage(1)[1] == 1


async def test_foreign_owner_file_is_rejected_before_ai(tmp_path):
    service, artifact, _, ai = configured_service(tmp_path, pdf_bytes())
    service.runtime.storage = OwnedStorage(service.runtime.storage.storage, 2)
    with pytest.raises(ServiceError, match="not_allowed"):
        await service.run({"pdf": artifact.key})
    ai.extract.assert_not_awaited()


async def test_extract_limit_stops_before_later_pages_or_ai(tmp_path, monkeypatch):
    service, artifact, _, ai = configured_service(tmp_path, pdf_bytes())
    later = Mock(return_value=SOURCE)
    monkeypatch.setattr(
        "app.services.pdf_to_word.service.PdfReader",
        lambda *args, **kwargs: SimpleNamespace(
            is_encrypted=False,
            pages=[
                SimpleNamespace(
                    extract_text=lambda **kwargs: kwargs["visitor_text"](
                        "x" * 50001, None, None, None, None
                    ),
                    get_contents=lambda: None,
                ),
                SimpleNamespace(extract_text=later, get_contents=lambda: None),
            ],
        ),
    )
    with pytest.raises(ServiceError, match="pdf_text_too_long"):
        await service.run({"pdf": artifact.key})
    later.assert_not_called()
    ai.extract.assert_not_awaited()


async def test_missing_information_does_not_write_output(tmp_path):
    service, artifact, store, ai = configured_service(tmp_path, pdf_bytes())
    ai.extract.return_value = WordPlan(missing_information=True)
    with pytest.raises(ServiceError, match="needs_information"):
        await service.run({"pdf": artifact.key})
    assert store.storage.usage(1)[1] == 1


async def test_page_count_limit_rejects_before_ai(tmp_path):
    writer = PdfWriter()
    for _ in range(201):
        writer.add_blank_page(width=300, height=300)
    output = BytesIO()
    writer.write(output)
    service, artifact, _, ai = configured_service(tmp_path, output.getvalue())
    with pytest.raises(ServiceError, match="file_invalid"):
        await service.run({"pdf": artifact.key})
    ai.extract.assert_not_awaited()
