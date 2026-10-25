from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

import numpy as np
import pypdfium2 as pdfium
import pytest
from pypdf import PdfReader

from app.core.i18n import tr
from app.files.pdf_layers import has_layer_declaration
from app.files.pdf_text import extract_page_text
from app.providers.documents.base import DocumentError
from app.providers.storage import LocalStorage, OwnedStorage
from app.providers.tables.camelot import CamelotTables
from app.services.base import ServiceError
from app.services.pdf_tables_excel.service import PdfTablesExcel
from app.services.pdf_to_word.test_service import configured_service, pdf_bytes
from tests.pdf_extraction_layer_fixtures import layered_table_pdf, layered_text_pdf


@pytest.fixture(autouse=True)
def database():
    yield


def test_hidden_text_is_selectable_even_when_not_part_of_the_visible_page():
    data = layered_text_pdf()
    reader = PdfReader(BytesIO(data))
    assert has_layer_declaration(reader)
    assert "Hidden 00999" in extract_page_text(reader.pages[0], limit=50000)
    assert not has_layer_declaration(PdfReader(BytesIO(pdf_bytes())))
    regions = []
    for variant in (data, layered_text_pdf("on")):
        with pdfium.PdfDocument(variant) as doc:
            page = doc[0]
            bitmap = page.render(scale=2)
            try:
                regions.append(np.array(bitmap.to_pil().convert("RGB"))[130:170, 50:320])
            finally:
                bitmap.close()
                page.close()
    assert np.all(regions[0] == 255)  # Hidden text region is visually empty.
    assert np.any(regions[1] < 100)  # Same text renders when the layer is on.


@pytest.mark.parametrize("method", ["lattice", "stream"])
def test_underlying_table_backend_can_read_hidden_values(tmp_path, method):
    import camelot

    path = tmp_path / "layer.pdf"
    path.write_bytes(layered_table_pdf())
    # This intentionally bypasses the app preflight to reproduce the backend gap.
    tables = camelot.read_pdf(str(path), pages="1", flavor=method, suppress_stdout=True)
    assert any("00999" in str(cell) for table in tables for row in table.df.values for cell in row)


@pytest.mark.parametrize("kind", ["off", "on", "empty", "indirect"])
@pytest.mark.parametrize("later", [False, True])
async def test_word_rejects_before_any_ai_call_or_output(tmp_path, kind, later):
    service, source, store, ai = configured_service(tmp_path, layered_text_pdf(kind, later=later))
    with pytest.raises(ServiceError, match="pdf_word_layers"):
        await service.run({"pdf": source.key})
    ai.extract.assert_not_awaited()
    assert store.storage.usage(1)[1] == 1


@pytest.mark.parametrize("method", ["lattice", "stream"])
@pytest.mark.parametrize("kind", ["off", "on", "empty", "indirect"])
async def test_real_table_child_rejects_layer_configuration_before_native_extraction(method, kind):
    with pytest.raises(DocumentError, match="pdf_tables_layers"):
        await CamelotTables().extract(layered_table_pdf(kind), method)


@pytest.mark.parametrize("mode", ["direct", "source", "labels"])
async def test_table_service_does_not_fallback_call_ai_or_write_output(tmp_path, mode):
    store = OwnedStorage(LocalStorage(tmp_path), 1)
    source = store.save("layer.pdf", layered_table_pdf(), "application/pdf")
    tables = SimpleNamespace(extract=AsyncMock(wraps=CamelotTables().extract))
    ai = SimpleNamespace(extract=AsyncMock(side_effect=AssertionError("no AI calls")))
    service = PdfTablesExcel()
    service.runtime = SimpleNamespace(storage=store, tables=tables, ai=ai)
    with pytest.raises(ServiceError, match="pdf_tables_layers"):
        await service.run({"pdf": source.key, "mode": mode, "language": "en"})
    assert tables.extract.await_count == 1
    ai.extract.assert_not_awaited()
    assert store.storage.usage(1)[1] == 1


@pytest.mark.parametrize("lang,word", [("ar", "طبقات"), ("en", "layers")])
@pytest.mark.parametrize(
    "prompt,key",
    [("pdf_to_word_file", "pdf_word_layers"), ("pdf_tables_file", "pdf_tables_layers")],
)
def test_localized_intake_and_rejection_disclose_optional_layers(lang, word, prompt, key):
    assert word in tr(prompt, lang) and word in tr(key, lang)
