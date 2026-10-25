from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.i18n import tr
from app.providers.documents.rendering import WordFiles
from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.document_results import word_pdf_result
from app.services.text_to_word_pdf.schema import Inputs
from app.services.text_to_word_pdf.service import TextToWordPdf
from tests.word_pdf_ai_fixtures import inputs, revision


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize("output_format", ["word", "pdf", "both"])
@pytest.mark.parametrize("mode", ["direct", "smart"])
@pytest.mark.parametrize("visual", [False, True])
async def test_only_selected_files_are_saved_in_each_mode_and_review(
    tmp_path, output_format, mode, visual
):
    source = inputs() | {"mode": mode, "output_format": output_format}
    TextToWordPdf.input_schema.validate_inputs(source)
    store = OwnedStorage(LocalStorage(tmp_path), 1)
    renderer = SimpleNamespace(word_pdf=AsyncMock(return_value=WordFiles(b"docx", b"pdf")))

    async def extract(schema, *args):
        return schema.model_validate(revision(source))

    ai = SimpleNamespace(extract=AsyncMock(side_effect=extract))
    service = TextToWordPdf()
    service.runtime = SimpleNamespace(
        storage=store,
        renderer=renderer,
        ai=ai,
        previews=SimpleNamespace(
            first_page=AsyncMock(return_value=SimpleNamespace(png=b"png", pages=2))
        )
        if visual
        else None,
    )
    result = await service.run(source)
    assert [store.read(a.key) for a in result.artifacts] == {
        "word": [b"docx"],
        "pdf": [b"pdf"],
        "both": [b"docx", b"pdf"],
    }[output_format]
    assert ai.extract.await_count == (1 if mode == "smart" else 0)
    assert renderer.word_pdf.await_count == 1
    assert result.prepared_delivery is visual
    for lang in ("ar", "en"):
        assert tr("document_output_" + output_format, lang) in result.preview_localizations[lang]


@pytest.mark.parametrize("value", [None, "", "zip", "WORD"])
def test_public_format_is_required_and_bounded(value):
    source = {"text": "Source"}
    if value is not None:
        source["output_format"] = value
    with pytest.raises(ServiceError, match="input_invalid"):
        TextToWordPdf.input_schema.validate_inputs(source)


def test_legacy_internal_inputs_still_default_to_both():
    assert Inputs.parse({"text": "Source"}).output_format == "both"


@pytest.mark.parametrize("value", ["zip", [], True])
async def test_invalid_internal_selection_does_not_render(value):
    renderer = SimpleNamespace(word_pdf=AsyncMock())
    with pytest.raises(ServiceError, match="input_invalid"):
        await word_pdf_result(
            SimpleNamespace(renderer=renderer), None, preview="Ready", output_format=value
        )
    renderer.word_pdf.assert_not_awaited()


@pytest.mark.parametrize("output_format", ["word", "pdf", "both"])
async def test_preview_save_failure_removes_all_selected_files(
    tmp_path, monkeypatch, output_format
):
    store = OwnedStorage(LocalStorage(tmp_path), 1)
    save = store.save

    def fail_preview(name, *args):
        if name == "preview.png":
            raise ServiceError("storage_quota")
        return save(name, *args)

    monkeypatch.setattr(store, "save", fail_preview)
    runtime = SimpleNamespace(
        storage=store,
        renderer=SimpleNamespace(word_pdf=AsyncMock(return_value=WordFiles(b"docx", b"pdf"))),
        previews=SimpleNamespace(
            first_page=AsyncMock(return_value=SimpleNamespace(png=b"png", pages=1))
        ),
    )
    with pytest.raises(ServiceError, match="storage_quota"):
        await word_pdf_result(runtime, None, preview="Ready", output_format=output_format)
    assert not list(tmp_path.glob("[0-9]*/*/*"))


@pytest.mark.parametrize("cancelled", [False, True])
@pytest.mark.parametrize("failed_delete", [0, 1])
async def test_cleanup_attempts_every_saved_file_and_preserves_original_failure(
    tmp_path, monkeypatch, cancelled, failed_delete
):
    import asyncio

    store = OwnedStorage(LocalStorage(tmp_path), 1)
    original = asyncio.CancelledError() if cancelled else ServiceError("storage_quota")
    save, delete = store.save, store.delete
    saved, attempted = [], []

    def fail_preview(name, *args):
        if name == "preview.png":
            raise original
        artifact = save(name, *args)
        saved.append(artifact)
        return artifact

    def flaky_delete(key):
        attempted.append(key)
        if key == saved[failed_delete].key:
            raise OSError("synthetic cleanup failure")
        delete(key)

    monkeypatch.setattr(store, "save", fail_preview)
    monkeypatch.setattr(store, "delete", flaky_delete)
    runtime = SimpleNamespace(
        storage=store,
        renderer=SimpleNamespace(word_pdf=AsyncMock(return_value=WordFiles(b"docx", b"pdf"))),
        previews=SimpleNamespace(
            first_page=AsyncMock(return_value=SimpleNamespace(png=b"png", pages=1))
        ),
    )
    with pytest.raises(type(original)) as caught:
        await word_pdf_result(runtime, None, preview="Ready", output_format="both")
    assert caught.value is original
    assert attempted == [a.key for a in saved]
    assert store.storage.usage(1)[1] == 1  # Only the failed deletion awaits existing TTL cleanup.
