"""Synthetic optional-content visibility; no customer content or external objects."""

from io import BytesIO

from pypdf import PdfWriter
from pypdf.generic import (
    ArrayObject,
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
    TextStringObject,
)


def layered_pdf(kind="off", *, later=False):
    writer = PdfWriter()
    writer.pdf_header = "%PDF-1.5"
    if later:
        writer.add_blank_page(width=300, height=200)
    page = writer.add_blank_page(width=300, height=200)
    group = writer._add_object(
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/OCG"),
                NameObject("/Name"): TextStringObject("Synthetic layer"),
            }
        )
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Properties"): DictionaryObject({NameObject("/Layer"): group})}
    )
    content = DecodedStreamObject()
    content.set_data(b"/OC /Layer BDC 1 0 0 rg 30 30 240 140 re f EMC")
    page[NameObject("/Contents")] = writer._add_object(content)
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
                        NameObject("/Order"): ArrayObject([group]),
                    }
                ),
            }
        )
    )
    writer._root_object[NameObject("/OCProperties")] = (
        writer._add_object(properties) if kind == "indirect" else properties
    )
    output = BytesIO()
    writer.write(output)
    return output.getvalue()
