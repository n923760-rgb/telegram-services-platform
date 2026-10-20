"""Reject unsupported form declarations before page copying in every operation."""

from io import BytesIO

import pytest
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, DictionaryObject, NameObject, TextStringObject

from app.builders.pdf_tools import PdfToolError, build
from app.core.i18n import tr
from app.services.pdf_tools.test_service import source
from tests.pdf_form_fixtures import form_pdf


@pytest.fixture(autouse=True)
def database():
    yield


def operation_args(operation):
    return (
        {"operation": operation}
        | ({} if operation == "merge" else {"pages": "1"})
        | ({"rotation": "90"} if operation == "rotate" else {})
    )


@pytest.mark.parametrize("operation", ["merge", "extract", "rotate"])
@pytest.mark.parametrize(
    "kind",
    ["acroform", "widget", "widget_indirect", "permissions", "empty_form", "empty_permissions"],
)
@pytest.mark.parametrize("later", [False, True])
def test_forms_reject_in_all_files_and_even_unselected_pages(operation, kind, later):
    data = form_pdf(kind, later=later)
    # The form is in the second source for merges, or the unselected later page.
    files = [source(), data] if operation == "merge" else [data]
    with pytest.raises(PdfToolError, match="pdf_tools_form"):
        build(files, **operation_args(operation))


def annotated_pdf(kind):
    writer = PdfWriter(clone_from=PdfReader(BytesIO(source())))
    link = DictionaryObject(
        {
            NameObject("/Subtype"): NameObject("/Link"),
            NameObject("/A"): DictionaryObject(
                {
                    NameObject("/S"): NameObject("/URI"),
                    NameObject("/URI"): TextStringObject("https://example.invalid"),
                }
            ),
        }
    )
    annotation = {
        "link": link,
        "broken": TextStringObject("broken"),
        "missing_subtype": DictionaryObject(),
    }[kind]
    writer.pages[0][NameObject("/Annots")] = writer._add_object(
        ArrayObject([writer._add_object(annotation)])
    )
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


@pytest.mark.parametrize("operation", ["merge", "extract", "rotate"])
@pytest.mark.parametrize("kind", ["link", "broken", "missing_subtype"])
def test_indirect_annotation_arrays_preserve_links_and_fail_closed(operation, kind):
    data = annotated_pdf(kind)
    files = [source(), data] if operation == "merge" else [data]
    if kind != "link":
        with pytest.raises(PdfToolError, match="file_invalid"):
            build(files, **operation_args(operation))
    else:
        result = PdfReader(BytesIO(build(files, **operation_args(operation))))
        page = result.pages[2] if operation == "merge" else result.pages[0]
        assert page["/Annots"][0].get_object()["/A"]["/URI"] == "https://example.invalid"
        assert page.extract_text() == PdfReader(BytesIO(data)).pages[0].extract_text()


@pytest.mark.parametrize("language", ["ar", "en"])
def test_intake_and_rejection_disclose_unsupported_forms(language):
    assert ("نماذج" if language == "ar" else "forms") in tr("pdf_tools_files", language)
    assert ("توقيع" if language == "ar" else "signature") in tr("pdf_tools_form", language)
