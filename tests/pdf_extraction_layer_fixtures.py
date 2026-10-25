"""Selectable hidden text and table values in ordinary optional-content groups."""

from io import BytesIO

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject,
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
    TextStringObject,
)
from reportlab.pdfgen import canvas

from tests.pdf_tables_fixtures import table_pdf


def with_layer(data, commands, kind, later):
    reader = PdfReader(BytesIO(data))
    writer = PdfWriter()
    if later:
        writer.add_blank_page(width=600, height=800)
    writer.append(reader)
    writer.pdf_header = "%PDF-1.5"
    page = writer.pages[-1]
    group = writer._add_object(
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/OCG"),
                NameObject("/Name"): TextStringObject("Hidden source text"),
            }
        )
    )
    page["/Resources"][NameObject("/Properties")] = DictionaryObject({NameObject("/Hidden"): group})
    stream = DecodedStreamObject()
    stream.set_data(b"/OC /Hidden BDC " + commands + b" EMC")
    page[NameObject("/Contents")] = ArrayObject(
        [page.raw_get("/Contents"), writer._add_object(stream)]
    )
    properties = (
        DictionaryObject()
        if kind == "empty"
        else DictionaryObject(
            {
                NameObject("/OCGs"): ArrayObject([group]),
                NameObject("/D"): DictionaryObject(
                    {
                        NameObject("/BaseState"): NameObject("/ON"),
                        NameObject("/OFF"): ArrayObject([] if kind == "on" else [group]),
                    }
                ),
            }
        )
    )
    writer._root_object[NameObject("/OCProperties")] = (
        writer._add_object(properties) if kind == "indirect" else properties
    )
    result = BytesIO()
    writer.write(result)
    return result.getvalue()


def layered_text_pdf(kind="off", *, later=False):
    stream = BytesIO()
    document = canvas.Canvas(stream, pagesize=(300, 200))
    document.drawString(30, 170, "Visible 00123")
    document.save()
    return with_layer(
        stream.getvalue(), b"BT /F1 12 Tf 30 120 Td (Hidden 00999) Tj ET", kind, later
    )


def layered_table_pdf(kind="off", *, later=False):
    return with_layer(
        table_pdf()[0],
        b"BT /F1 12 Tf 60 655 Td (00999) Tj ET BT /F1 12 Tf 220 655 Td (999) Tj ET BT /F1 12 Tf 380 655 Td (Hidden) Tj ET",
        kind,
        later,
    )
