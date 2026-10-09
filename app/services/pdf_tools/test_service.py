from io import BytesIO
from types import SimpleNamespace

import pytest
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, DictionaryObject, NameObject
from reportlab.pdfgen import canvas

from app.builders.pdf_tools import PdfToolError, build
from app.files.pdf_selection import page_selection
from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.pdf_tools.service import PdfTools


def source(labels=("00123", "00124"), *, encrypted=False, form=False):
    buffer = BytesIO()
    document = canvas.Canvas(buffer)
    for label in labels:
        document.drawString(80, 700, f"Record {label} 125.50 2026-10-09")
        document.showPage()
    document.save()
    if not encrypted and not form:
        return buffer.getvalue()
    writer = PdfWriter()
    writer.append(PdfReader(BytesIO(buffer.getvalue())))
    if encrypted:
        writer.encrypt("private")
    if form:
        writer._root_object[NameObject("/AcroForm")] = DictionaryObject(
            {NameObject("/Fields"): ArrayObject()}
        )
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def records(data):
    return [page.extract_text().split()[1] for page in PdfReader(BytesIO(data)).pages]


def test_merge_preserves_source_order_identifiers_and_page_content():
    output = build([source(), source(("00999",))], operation="merge")
    assert records(output) == ["00123", "00124", "00999"]
    assert all(
        "125.50 2026-10-09" in page.extract_text() for page in PdfReader(BytesIO(output)).pages
    )


def test_extract_preserves_requested_order_rotated_page_geometry_and_images():
    from tests.pdf_image_fixtures import mixed_pdf

    data = mixed_pdf("xobject")
    reader = PdfReader(BytesIO(data))
    writer = PdfWriter()
    writer.add_page(reader.pages[0]).rotate(90)
    buffer = BytesIO()
    writer.write(buffer)
    output = PdfReader(BytesIO(build([buffer.getvalue()], operation="extract", pages="1")))
    assert output.pages[0].rotation == 90
    assert len(output.pages[0].images) == len(reader.pages[0].images) == 1
    assert output.pages[0].images[0].data == reader.pages[0].images[0].data
    assert output.pages[0].mediabox == reader.pages[0].mediabox
    assert records(
        build([source(("00123", "00124", "00125"))], operation="extract", pages="3,1")
    ) == ["00125", "00123"]


@pytest.mark.parametrize(
    "selection", ["0", "2-1", "1,1", "1-3,2", "201", "1-201", "", "1;2", "1,,2", "x"]
)
def test_selection_rejects_invalid_and_duplicate_pages(selection):
    with pytest.raises(ValueError):
        page_selection(selection)


def test_selection_supports_arabic_digits_and_comma_with_order():
    assert page_selection("٣، ١-٢") == [3, 1, 2]


@pytest.mark.parametrize(
    "data,key",
    [
        (b"broken", "file_invalid"),
        (source(encrypted=True), "file_invalid"),
        (source(form=True), "pdf_tools_form"),
    ],
)
def test_rejects_unreadable_encrypted_or_form_input(data, key):
    with pytest.raises(PdfToolError, match=key):
        build([data], operation="extract", pages="1")


def test_out_of_range_page_and_total_page_limit_fail_without_partial_result():
    with pytest.raises(PdfToolError, match="pdf_page_selection"):
        build([source()], operation="extract", pages="3")
    writer = PdfWriter()
    for _ in range(101):
        writer.add_blank_page(width=100, height=100)
    buffer = BytesIO()
    writer.write(buffer)
    with pytest.raises(PdfToolError, match="pdf_tools_limit"):
        build([buffer.getvalue()] * 2, operation="merge")


@pytest.mark.parametrize(
    "inputs",
    [
        {"operation": "merge", "files": ["one"]},
        {"operation": "merge", "files": ["one", "one"]},
        {"operation": "merge", "files": ["one", "two"], "pages": "1"},
        {"operation": "extract", "files": ["one", "two"], "pages": "1"},
        {"operation": "extract", "files": ["one"]},
        {"operation": "extract", "files": ["one"], "pages": "1,1"},
    ],
)
def test_cross_field_inputs_fail_before_ai_admission(inputs):
    with pytest.raises(ServiceError, match="input_invalid"):
        PdfTools.needs_ai(inputs)


async def test_service_runs_without_ai_and_saves_a_valid_pdf(tmp_path):
    storage = OwnedStorage(LocalStorage(tmp_path), 1)
    files = [storage.save(f"{i}.pdf", source((str(i),)), "application/pdf").key for i in range(2)]
    service = PdfTools()
    service.runtime = SimpleNamespace(storage=storage, ai=None)
    inputs = {"operation": "merge", "files": files}
    service.input_schema.validate_inputs(inputs)
    assert not service.needs_ai(inputs)
    result = await service.run(inputs)
    assert records(storage.read(result.artifacts[0].key)) == ["0", "1"]
