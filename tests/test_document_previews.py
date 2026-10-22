from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from PIL import Image
from pydantic import ValidationError
from pypdf import PdfWriter
from reportlab.pdfgen.canvas import Canvas

from app.core.i18n import tr
from app.files.retention import artifact_keys
from app.providers.delivery import TelegramDelivery
from app.providers.documents import previews
from app.providers.documents.base import DocumentError
from app.providers.documents.previews import PdfPreviews
from app.providers.documents.rendering import WordFiles
from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import Artifact, Result, ServiceError
from app.services.document_results import word_pdf_result
from tests.word_pdf_fixtures import document


def sample_pdf(pages=2):
    stream = BytesIO()
    canvas = Canvas(stream)
    for number in range(pages):
        canvas.drawString(40, 700, f"Invoice 00123 / 125.50 / page {number + 1}")
        canvas.showPage()
    canvas.save()
    return stream.getvalue()


async def test_real_first_page_is_bounded_png_with_content_and_total_pages():
    result = await PdfPreviews().first_page(sample_pdf())
    assert result.pages == 2
    with Image.open(BytesIO(result.png)) as image:
        assert image.format == "PNG" and image.mode == "RGB"
        assert image.width <= 960 and image.height <= 1440
        assert min(image.convert("L").getextrema()) < 100
    assert len(result.png) < 3 * 1024 * 1024


@pytest.mark.parametrize("pdf", [b"", b"corrupt PDF", "not bytes"])
async def test_invalid_pdf_is_rejected(pdf):
    with pytest.raises(DocumentError, match="document_preview_invalid"):
        await PdfPreviews().first_page(pdf)


@pytest.mark.parametrize("pages,width", [(51, 595), (1, 20001)])
async def test_native_page_and_dimension_limits(pages, width):
    writer, stream = PdfWriter(), BytesIO()
    for _ in range(pages):
        writer.add_blank_page(width, 842)
    writer.write(stream)
    with pytest.raises(DocumentError, match="document_preview_invalid"):
        await PdfPreviews().first_page(stream.getvalue())


@pytest.mark.parametrize("error", [DocumentError("document_preview_timeout"), RuntimeError()])
async def test_preview_failure_releases_slot_and_removes_private_files(monkeypatch, error):
    directories = []

    async def fail(module, args, **kwargs):
        directories.append(Path(args[0]).parent)
        raise error

    monkeypatch.setattr(previews, "run_child", fail)
    with pytest.raises(type(error)):
        await PdfPreviews().first_page(sample_pdf())
    assert not directories[0].exists()
    assert not previews.slot().locked()


async def test_visual_result_preserves_prepared_files_and_original_inputs(tmp_path):
    pdf = sample_pdf()
    renderer = SimpleNamespace(word_pdf=AsyncMock(return_value=WordFiles(b"docx", pdf)))
    store = OwnedStorage(LocalStorage(tmp_path), 1)
    runtime = SimpleNamespace(renderer=renderer, previews=PdfPreviews(), storage=store)
    result = await word_pdf_result(runtime, document(), preview="Prepared source")
    assert result.prepared_delivery and result.needs_confirmation
    assert store.read(result.artifacts[1].key) == pdf
    assert len(result.preview_artifacts) == 1
    assert len(artifact_keys(result.model_dump())) == 3
    assert "2" in result.preview_localizations["ar"]
    assert renderer.word_pdf.await_count == 1


async def test_preview_storage_failure_removes_prepared_artifacts(tmp_path):
    base = OwnedStorage(LocalStorage(tmp_path), 1)

    def save(filename, data, mime):
        if mime == "image/png":
            raise ServiceError("storage_quota")
        return base.save(filename, data, mime)

    runtime = SimpleNamespace(
        renderer=SimpleNamespace(word_pdf=AsyncMock(return_value=WordFiles(b"docx", sample_pdf()))),
        previews=PdfPreviews(),
        storage=SimpleNamespace(save=save, delete=base.delete),
    )
    with pytest.raises(ServiceError, match="storage_quota"):
        await word_pdf_result(runtime, document(), preview="Ready")
    assert not list(tmp_path.glob("[0-9]*/*/*"))


@pytest.mark.parametrize("lang", ["ar", "en"])
async def test_visual_confirmation_sends_owner_photo_before_controls(tmp_path, lang):
    store = LocalStorage(tmp_path)
    artifact = store.save(1, "preview.png", b"preview", "image/png")
    final = Artifact(
        key="1/" + "a" * 32 + "/final.pdf", filename="final.pdf", mime="application/pdf"
    )
    result = Result(
        artifacts=[final],
        preview_artifacts=[artifact],
        prepared_delivery=True,
        needs_confirmation=True,
        continuation={"prepared": True},
        preview_localizations={lang: "Review all pages"},
    )
    bot = AsyncMock()
    delivery = TelegramDelivery(bot, store)
    delivery._lang = AsyncMock(return_value=lang)
    oid = uuid4()
    await delivery.visual_confirmation(1, oid, result)
    assert bot.method_calls[0][0] == "send_photo"
    assert bot.send_photo.await_args.kwargs["caption"] == tr("document_preview_caption", lang)
    controls = bot.send_message.await_args.kwargs["reply_markup"].inline_keyboard
    assert controls[0][0].text == tr("approve_delivery", lang)
    assert controls[0][0].callback_data == f"approve:{oid}:visual"
    with pytest.raises(ServiceError, match="not_allowed"):
        await delivery.visual_confirmation(2, oid, result)
    assert bot.send_photo.await_count == 1


@pytest.mark.parametrize(
    "values",
    [
        {"prepared_delivery": True},
        {"preview_artifacts": [{"key": "k", "filename": "f", "mime": "image/jpeg"}]},
    ],
)
def test_invalid_visual_result_contract(values):
    with pytest.raises(ValidationError):
        Result(text="body", **values)
