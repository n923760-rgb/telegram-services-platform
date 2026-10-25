import asyncio
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from docx import Document

from app.providers.storage import LocalStorage, OwnedStorage
from app.services.image_to_text import service as module
from app.services.image_to_text.schema import Extracted
from tests.images_pdf_fixtures import picture


@pytest.fixture(autouse=True)
def database():
    yield


def prepare(tmp_path):
    store = OwnedStorage(LocalStorage(tmp_path), 1)
    source = store.save("source.png", picture(), "image/png")
    text = ("السجل 00123 | amount 125.50 | Contact a@example.invalid\n" * 100).strip()
    ai = SimpleNamespace(
        extract=AsyncMock(return_value=Extracted(readable=True, confidence=0.99, text=text))
    )
    service = module.ImageToText()
    service.runtime = SimpleNamespace(storage=store, ai=ai)
    return service, store, source, text, ai


@pytest.mark.parametrize("failure", ["build", "text_save", "word_save", "cancel_word_save"])
async def test_long_output_failure_retains_only_the_input_and_original_error(
    tmp_path, monkeypatch, failure
):
    service, store, source, _, ai = prepare(tmp_path)
    error = (
        asyncio.CancelledError()
        if failure == "cancel_word_save"
        else RuntimeError("synthetic output failure")
    )

    def fail_build(*args, **kwargs):
        raise error

    save = store.save

    def fail_save(name, *args, **kwargs):
        if name == ("result.txt" if failure == "text_save" else "result.docx"):
            raise error
        return save(name, *args, **kwargs)

    if failure == "build":
        monkeypatch.setattr(module, "build", fail_build)
    else:
        monkeypatch.setattr(store, "save", fail_save)
    with pytest.raises(type(error)) as caught:
        await service.run({"images": [source.key]})
    assert caught.value is error
    assert store.storage.usage(1)[1] == 1
    assert store.read(source.key)
    assert ai.extract.await_count == 1


async def test_success_keeps_both_editable_and_literal_outputs_with_one_ai_call(tmp_path):
    service, store, source, text, ai = prepare(tmp_path)
    result = await service.run({"images": [source.key]})
    assert result.text == text
    assert [a.filename for a in result.artifacts] == ["result.txt", "result.docx"]
    assert store.read(result.artifacts[0].key).decode("utf-8") == text
    document = Document(BytesIO(store.read(result.artifacts[1].key)))
    assert "".join(p.text for p in document.paragraphs[1:]) == text
    assert ai.extract.await_count == 1
