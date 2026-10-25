from io import BytesIO
from types import SimpleNamespace

import numpy as np
import pypdfium2 as pdfium
import pytest
from pypdf import PdfReader, PdfWriter

from app.builders import pdf_tools
from app.core.i18n import tr
from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.pdf_tools.service import PdfTools
from app.services.pdf_tools.test_service import source
from tests.pdf_layer_fixtures import layered_pdf


@pytest.fixture(autouse=True)
def database():
    yield


def red_pixels(data):
    with pdfium.PdfDocument(data) as doc:
        page = doc[0]
        try:
            bitmap = page.render(scale=2)
            try:
                pixels = np.array(bitmap.to_pil().convert("RGB"))
                return int(
                    (
                        (pixels[:, :, 0] > 200) & (pixels[:, :, 1] < 50) & (pixels[:, :, 2] < 50)
                    ).sum()
                )
            finally:
                bitmap.close()
        finally:
            page.close()


def test_fixture_proves_page_copying_changes_real_hidden_layer_visibility():
    data = layered_pdf()
    assert data.startswith(b"%PDF-1.5")
    assert red_pixels(data) == 0
    # Reproduce the underlying writer's loss of catalog visibility defaults.
    writer = PdfWriter()
    writer.add_page(PdfReader(BytesIO(data)).pages[0])
    copied = BytesIO()
    writer.write(copied)
    assert "/OCProperties" not in PdfReader(BytesIO(copied.getvalue())).trailer["/Root"]
    assert red_pixels(copied.getvalue()) > 100000


@pytest.mark.parametrize("operation", ["merge", "extract", "rotate"])
@pytest.mark.parametrize("kind", ["off", "on", "empty", "indirect"])
@pytest.mark.parametrize("later", [False, True])
def test_declared_layers_reject_before_writer_even_in_later_file_or_unselected_page(
    monkeypatch, operation, kind, later
):
    def forbidden():
        pytest.fail("Unsupported input must reject before output construction")

    monkeypatch.setattr(pdf_tools, "PdfWriter", forbidden)
    files = [layered_pdf(kind, later=later)]
    if operation == "merge":
        files.insert(0, source())
    args = {"operation": operation}
    if operation != "merge":
        args["pages"] = "1"
    if operation == "rotate":
        args["rotation"] = "90"
    with pytest.raises(pdf_tools.PdfToolError, match="pdf_tools_layers"):
        pdf_tools.build(files, **args)


@pytest.mark.parametrize("lang,word", [("ar", "طبقات"), ("en", "layers")])
def test_intake_and_safe_error_explain_layer_limit(lang, word):
    assert word in tr("pdf_tools_files", lang)
    assert word in tr("pdf_tools_layers", lang)


@pytest.mark.parametrize("operation", ["merge", "extract", "rotate"])
async def test_service_rejection_preserves_input_and_creates_no_output(tmp_path, operation):
    store = OwnedStorage(LocalStorage(tmp_path), 1)
    data = layered_pdf(later=True)
    layer = store.save("layer.pdf", data, "application/pdf")
    keys = [layer.key]
    if operation == "merge":
        keys.insert(0, store.save("plain.pdf", source(), "application/pdf").key)
    service = PdfTools()
    service.runtime = SimpleNamespace(storage=store, ai=None)
    args = {"operation": operation, "files": keys}
    if operation != "merge":
        args["pages"] = "1"
    if operation == "rotate":
        args["rotation"] = "90"
    with pytest.raises(ServiceError, match="pdf_tools_layers"):
        await service.run(args)
    assert store.read(layer.key) == data
    assert store.storage.usage(1)[1] == len(keys)
