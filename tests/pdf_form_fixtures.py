"""Synthetic interactive PDF fixtures, not cryptographically signed documents."""

from io import BytesIO

from pypdf import PdfReader, PdfWriter
from pypdf.generic import DictionaryObject, NameObject
from reportlab.pdfgen import canvas

SOURCE = "Invoice 12345 customer Example. Total SAR 250.00. Date 2026-10-07."


def form_pdf(kind="acroform", *, later=False):
    output = BytesIO()
    document = canvas.Canvas(output, pageCompression=0)
    if later:
        document.drawString(30, 750, SOURCE)
        document.showPage()
    document.drawString(30, 750, SOURCE)
    document.acroForm.textfield(
        name="account", value="Account 00999", x=30, y=650, width=200, height=30
    )
    document.showPage()
    document.save()
    reader = PdfReader(BytesIO(output.getvalue()))
    if kind == "acroform":
        return output.getvalue()
    writer = PdfWriter(clone_from=reader)
    if kind in {"widget", "widget_indirect"}:
        del writer.root_object["/AcroForm"]
        if kind == "widget_indirect":
            for page in writer.pages:
                for annotation in page.get("/Annots", []):
                    annotation.get_object()[NameObject("/Subtype")] = writer._add_object(
                        NameObject("/Widget")
                    )
    elif kind == "permissions":
        del writer.root_object["/AcroForm"]
        for page in writer.pages:
            page.pop("/Annots", None)
        writer.root_object[NameObject("/Perms")] = DictionaryObject(
            {NameObject("/DocMDP"): DictionaryObject({NameObject("/Type"): NameObject("/Sig")})}
        )
    elif kind == "empty_form":
        writer.root_object[NameObject("/AcroForm")] = DictionaryObject()
        for page in writer.pages:
            page.pop("/Annots", None)
    else:
        raise ValueError("unknown form fixture")
    output = BytesIO()
    writer.write(output)
    return output.getvalue()
