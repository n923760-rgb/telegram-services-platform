"""Small real PDFs covering rendered raster images and text-only Forms."""

from io import BytesIO

from PIL import Image, ImageDraw
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject,
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
    NumberObject,
)
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app.services.pdf_to_word.test_service import SOURCE


def mixed_pdf(kind="xobject"):
    picture = Image.new("RGB", (240, 40), "white")
    ImageDraw.Draw(picture).text((5, 10), "Important source note 00124", fill="black")
    output = BytesIO()
    document = canvas.Canvas(output, pageCompression=0)
    document.drawString(30, 750, SOURCE)
    if kind == "later_page":
        document.showPage()
        document.drawString(30, 750, "Page 2 has a text label and scanned content.")
    if kind in {"nested", "text_form"}:
        document.beginForm("Inner")
    if kind == "inline":
        document.drawInlineImage(picture, 30, 600)
    elif kind != "text_form":
        document.drawImage(ImageReader(picture), 30, 600)
    else:
        document.drawString(30, 650, "Text in a reusable Form.")
    if kind in {"nested", "text_form"}:
        document.endForm()
        document.beginForm("Outer")
        document.doForm("Inner")
        document.endForm()
        document.doForm("Outer")
    document.save()
    return output.getvalue()


def drawing_pdf(kind):
    writer = PdfWriter()
    if kind == "unused":
        reader = PdfReader(BytesIO(mixed_pdf()))
        content = reader.pages[0].get_contents()
        content.operations = [(args, op) for args, op in content.operations if op != b"Do"]
        reader.pages[0][NameObject("/Contents")] = content
        writer.append(reader)
        output = BytesIO()
        writer.write(output)
        return output.getvalue()
    page = writer.add_blank_page(600, 800)
    resources = DictionaryObject()
    objects = DictionaryObject()
    resources[NameObject("/XObject")] = writer._add_object(objects)
    page[NameObject("/Resources")] = writer._add_object(resources)
    content = DecodedStreamObject()
    content.set_data(b"/Object Do")
    page[NameObject("/Contents")] = writer._add_object(content)
    count = 18 if kind == "deep" else 1
    for _ in range(count):
        target = DecodedStreamObject()
        if kind in {"cyclic", "deep"}:
            target[NameObject("/Subtype")] = NameObject("/Form")
            target[NameObject("/BBox")] = ArrayObject([NumberObject(n) for n in (0, 0, 600, 800)])
            target.set_data(b"/Object Do")
            next_resources = resources if kind == "cyclic" else DictionaryObject()
            next_objects = objects if kind == "cyclic" else DictionaryObject()
            next_resources[NameObject("/XObject")] = writer._add_object(next_objects)
            target[NameObject("/Resources")] = writer._add_object(next_resources)
        else:
            target[NameObject("/Subtype")] = NameObject("/Image")
            target[NameObject("/Width")] = NumberObject(10**9)
            target[NameObject("/Height")] = NumberObject(10**9)
            target[NameObject("/ColorSpace")] = NameObject("/DeviceRGB")
            target[NameObject("/BitsPerComponent")] = NumberObject(8)
            target.set_data(b"")
        objects[NameObject("/Object")] = writer._add_object(target)
        if kind == "deep":
            resources, objects = next_resources, next_objects
    output = BytesIO()
    writer.write(output)
    return output.getvalue()
