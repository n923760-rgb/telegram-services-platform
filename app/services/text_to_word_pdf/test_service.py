from types import SimpleNamespace

import pytest

from app.providers.documents.base import DocumentError
from app.providers.documents.rendering import WordFiles
from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.text_to_word_pdf.service import TextToWordPdf


class Renderer:
    def __init__(self, error=None):
        self.calls = []
        self.error = error

    async def word_pdf(self, document, *, include_title=True):
        self.calls.append((document, include_title))
        if self.error:
            raise self.error
        return WordFiles(b"docx", b"pdf")


@pytest.mark.parametrize("title", [None, "تقرير الطلبات"])
async def test_service_preserves_text_uses_injected_renderer_and_saves_two_files(tmp_path, title):
    text = "  Invoice 00123\n\nالطلب 2026-10-09 بقيمة 125.50"
    inputs = {"text": text, **({"title": title} if title else {})}
    service = TextToWordPdf()
    storage = OwnedStorage(LocalStorage(tmp_path), 1)
    renderer = Renderer()
    service.runtime = SimpleNamespace(storage=storage, ai=None, renderer=renderer)
    service.input_schema.validate_inputs(inputs)
    assert not service.needs_ai(inputs)
    result = await service.run(inputs)
    document, include_title = renderer.calls[0]
    assert [p for section in document.sections for p in section.paragraphs] == text.splitlines()
    assert include_title == bool(title)
    assert [storage.read(file.key) for file in result.artifacts] == [b"docx", b"pdf"]


@pytest.mark.parametrize(
    "inputs",
    [
        {"text": ""},
        {"text": "x", "title": "two\nlines"},
        {"text": "x", "mode": "smart"},
        {"text": "x", "upload": "foreign.docx"},
        {"text": "x" * 12001},
    ],
)
def test_invalid_input_rejected_before_reservation(inputs):
    with pytest.raises(ServiceError, match="input_invalid"):
        TextToWordPdf.needs_ai(inputs)


@pytest.mark.parametrize(
    "key,transient",
    [
        ("document_render_timeout", False),
        ("document_render_busy", True),
        ("document_render_invalid", False),
        ("document_render_limit", False),
    ],
)
async def test_render_failures_never_save_partial_artifacts(tmp_path, key, transient):
    service = TextToWordPdf()
    service.runtime = SimpleNamespace(
        ai=None,
        storage=OwnedStorage(LocalStorage(tmp_path), 1),
        renderer=Renderer(DocumentError(key, transient=transient)),
    )
    with pytest.raises(ServiceError) as error:
        await service.run({"text": "Invoice 00123"})
    assert error.value.key == ("input_invalid" if key == "document_render_limit" else key)
    assert error.value.transient == transient
    assert not list(tmp_path.glob("[0-9]*/*/*"))


async def test_second_save_failure_deletes_first_artifact(tmp_path, monkeypatch):
    storage = OwnedStorage(LocalStorage(tmp_path), 1)
    original = storage.save

    def save(filename, data, mime):
        if filename.endswith(".pdf"):
            raise ServiceError("storage_quota")
        return original(filename, data, mime)

    monkeypatch.setattr(storage, "save", save)
    service = TextToWordPdf()
    service.runtime = SimpleNamespace(ai=None, storage=storage, renderer=Renderer())
    with pytest.raises(ServiceError, match="storage_quota"):
        await service.run({"text": "Invoice 00123"})
    assert not list(tmp_path.glob("[0-9]*/*/*"))
