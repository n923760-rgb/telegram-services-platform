from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

from pypdf import PdfWriter

from app.providers.storage import LocalStorage, OwnedStorage
from app.services.pdf_to_word.schema import WordPlan
from app.services.pdf_to_word.service import PdfToWord


async def test_pdf_to_word_builds_editable_docx(tmp_path, monkeypatch):
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    raw = BytesIO()
    writer.write(raw)
    store = OwnedStorage(LocalStorage(tmp_path), 1)
    artifact = store.save("source.pdf", raw.getvalue(), "application/pdf")
    service = PdfToWord()
    service.runtime = SimpleNamespace(storage=store, ai=SimpleNamespace(extract=AsyncMock()))
    monkeypatch.setattr("app.services.pdf_to_word.service.PdfReader", lambda *a, **k: SimpleNamespace(
        is_encrypted=False,
        pages=[SimpleNamespace(extract_text=lambda: "Invoice 12345 customer Example")],
    ))
    service.runtime.ai.extract.return_value = WordPlan.model_validate({
        "document": {"title": "Invoice", "sections": [{"paragraphs": ["Invoice 12345 customer Example"]}]}
    })
    result = await service.run({"pdf": artifact.key})
    assert result.artifacts[0].filename == "result.docx"
    assert store.read(result.artifacts[0].key).startswith(b"PK")
    assert service.runtime.ai.extract.await_count == 1
