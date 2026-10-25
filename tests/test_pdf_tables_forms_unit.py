from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pypdf import PdfReader

from app.core.i18n import tr
from app.providers.documents.base import DocumentError
from app.providers.storage import LocalStorage, OwnedStorage
from app.providers.tables.camelot import CamelotTables
from app.services.base import ServiceError
from app.services.pdf_tables_excel.service import PdfTablesExcel
from tests.pdf_form_fixtures import form_pdf
from tests.pdf_tables_fixtures import table_pdf


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize("method", ["lattice", "stream"])
def test_native_backend_omits_field_value_even_when_it_accepts_the_table(tmp_path, method):
    import camelot

    data, rows = table_pdf(form=True)
    reader = PdfReader(BytesIO(data))
    assert reader.get_fields()["account"]["/V"] == "00999"
    assert reader.pages[0]["/Annots"][0].get_object()["/AP"]["/N"].get_data()
    path = tmp_path / "form.pdf"
    path.write_bytes(data)
    found = camelot.read_pdf(str(path), pages="1", flavor=method, suppress_stdout=True)
    assert found[0].df.values.tolist() == rows
    assert "00999" not in str(found[0].df.values.tolist())


@pytest.mark.parametrize(
    "kind",
    ["acroform", "widget", "widget_indirect", "permissions", "empty_form", "empty_permissions"],
)
@pytest.mark.parametrize("later", [False, True])
@pytest.mark.parametrize("method", ["lattice", "stream"])
async def test_real_child_rejects_forms_before_extraction(kind, later, method):
    with pytest.raises(DocumentError, match="pdf_tables_form"):
        await CamelotTables().extract(form_pdf(kind, later=later), method)


@pytest.mark.parametrize("method", ["lattice", "stream"])
async def test_plain_tables_still_extract_exact_source_values(method):
    data, rows = table_pdf()
    assert (await CamelotTables().extract(data, method)).tables[0].rows == rows


@pytest.mark.parametrize("mode", ["direct", "source", "labels"])
async def test_service_has_no_fallback_ai_or_output_for_form_table(tmp_path, mode):
    store = OwnedStorage(LocalStorage(tmp_path), 1)
    source = store.save("form.pdf", table_pdf(form=True)[0], "application/pdf")
    tables = SimpleNamespace(extract=AsyncMock(wraps=CamelotTables().extract))
    ai = SimpleNamespace(extract=AsyncMock())
    service = PdfTablesExcel()
    service.runtime = SimpleNamespace(storage=store, tables=tables, ai=ai)
    with pytest.raises(ServiceError, match="pdf_tables_form"):
        await service.run({"pdf": source.key, "mode": mode, "language": "en"})
    assert tables.extract.await_count == 1
    ai.extract.assert_not_awaited()
    assert store.storage.usage(1)[1] == 1


@pytest.mark.parametrize("lang,word", [("ar", "نماذج"), ("en", "form")])
def test_intake_and_error_explain_unsupported_form_content(lang, word):
    assert word in tr("pdf_tables_file", lang)
    assert ("نموذج" if lang == "ar" else word) in tr("pdf_tables_form", lang)
