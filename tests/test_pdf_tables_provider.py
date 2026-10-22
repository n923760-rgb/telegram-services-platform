import asyncio
from io import BytesIO

import pytest
from pypdf import PdfReader, PdfWriter

from app.providers.documents.base import DocumentError
from app.providers.documents.execution import slot
from app.providers.tables.base import Extraction
from app.providers.tables.camelot import CamelotTables
from tests.pdf_image_fixtures import mixed_pdf
from tests.pdf_tables_fixtures import table_pdf


@pytest.mark.parametrize("language", ["ar", "en"])
@pytest.mark.parametrize("method", ["lattice", "stream"])
async def test_real_bounded_child_extracts_exact_unicode_cells(language, method):
    data, rows = table_pdf(language, ruled=method == "lattice", pages=2)
    result = await CamelotTables().extract(data, method)
    assert result.pages == 2 and len(result.tables) == 2
    assert [table.page for table in result.tables] == [1, 2]
    assert all(table.rows == rows for table in result.tables)
    assert all(table.accuracy == 100.0 for table in result.tables)


@pytest.mark.parametrize(
    "kind,key",
    [
        ("invalid", "file_invalid"),
        ("encrypted", "file_invalid"),
        ("six", "pdf_tables_limit"),
        ("image", "pdf_image_content"),
        ("blank", "pdf_tables_missing"),
    ],
)
async def test_rejected_pdf_types_fail_closed(kind, key):
    data = table_pdf()[0]
    if kind == "invalid":
        data = b"not pdf"
    elif kind == "encrypted":
        writer = PdfWriter()
        writer.append(PdfReader(BytesIO(data)))
        writer.encrypt("private")
        output = BytesIO()
        writer.write(output)
        data = output.getvalue()
    elif kind == "six":
        data = table_pdf(pages=6)[0]
    elif kind == "image":
        data = mixed_pdf("direct")
    elif kind == "blank":
        writer = PdfWriter()
        writer.add_blank_page(width=600, height=800)
        output = BytesIO()
        writer.write(output)
        data = output.getvalue()
    with pytest.raises(DocumentError, match=key):
        await CamelotTables().extract(data, "lattice")


@pytest.mark.parametrize(
    "change",
    [
        {"pages": 2},
        {"tables": [{"page": 1, "rows": [["x"]], "accuracy": 100, "whitespace": 0}]},
        {"tables": [{"page": 1, "rows": [["x", "y"], ["z"]], "accuracy": 100, "whitespace": 0}]},
        {"tables": [{"page": 1, "rows": [["x", "y"], ["z", ""]], "accuracy": 94, "whitespace": 0}]},
        {
            "tables": [
                {"page": 1, "rows": [["x", "y"], ["z", ""]], "accuracy": 100, "whitespace": 31}
            ]
        },
        {
            "tables": [
                {"page": 1, "rows": [["x", "y"], ["z\x00", ""]], "accuracy": 100, "whitespace": 0}
            ]
        },
    ],
)
def test_extractor_contract_rejects_missing_pages_shapes_and_quality(change):
    from pydantic import ValidationError

    source = {
        "pages": 1,
        "tables": [{"page": 1, "rows": [["x", "y"], ["z", ""]], "accuracy": 100, "whitespace": 0}],
    }
    with pytest.raises(ValidationError):
        Extraction.model_validate({**source, **change})


async def test_cancellation_releases_shared_slot(monkeypatch):
    import app.providers.tables.camelot as module

    entered = asyncio.Event()

    async def wait(*args, **kwargs):
        entered.set()
        await asyncio.Event().wait()

    monkeypatch.setattr(module, "run_child", wait)
    task = asyncio.create_task(CamelotTables().extract(table_pdf()[0], "lattice"))
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert not slot().locked()
