"""One-page contact PDF with explicit HTTPS URI annotations, no remote resources."""

from io import BytesIO

import arabic_reshaper
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

from app.builders.pdf import _reading_rtl, _register_fonts, _visual
from app.builders.quality import validate
from app.core.i18n import tr


def visual(text):
    shaped = arabic_reshaper.ArabicReshaper(configuration={"support_ligatures": False}).reshape(
        text
    )
    return _visual(shaped, rtl=_reading_rtl(text))


def wrapped(text, font, size, width):
    lines, current = [], ""
    for char in text:
        if current and pdfmetrics.stringWidth(visual(current + char), font, size) > width:
            lines.append(current)
            current = ""
        current += char
    if current:
        lines.append(current)
    return lines


def build(values):
    _register_fonts()
    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=(420, 595))
    pdf.setTitle(values.name)
    pdf.setFillColor(HexColor("#f1f5f9"))
    pdf.rect(0, 0, 420, 595, fill=1, stroke=0)
    pdf.setFillColor(HexColor("#0f172a"))
    pdf.roundRect(20, 20, 380, 555, 16, fill=1, stroke=0)
    pdf.setFillColor(white)
    y = 541
    for text, size, font in [
        (values.name, 20, "DejaVu-Bold"),
        (values.subtitle or "", 11, "DejaVu"),
    ]:
        lines = wrapped(text, font, size, 324)
        while len(lines) > 2 and size > 9:
            size -= 1
            lines = wrapped(text, font, size, 324)
        if len(lines) > 2:
            raise ValueError("card text exceeds layout")
        pdf.setFont(font, size)
        for line in lines:
            pdf.drawCentredString(210, y, visual(line))
            y -= size + 7
    y = 419
    for label, url in values.entries():
        pdf.setFillColor(HexColor("#1e3a5f"))
        pdf.roundRect(42, y, 336, 46, 8, fill=1, stroke=0)
        pdf.setFillColor(white)
        pdf.setFont("DejaVu", 11)
        lines = wrapped(label, "DejaVu", 11, 302)
        if len(lines) > 2:
            raise ValueError("card label exceeds layout")
        for i, line in enumerate(lines):
            pdf.drawCentredString(210, y + (27 if len(lines) == 2 else 18) - 15 * i, visual(line))
        pdf.linkURL(url, (42, y, 378, y + 46), relative=0, thickness=0)
        y -= 56
    pdf.setFillColor(HexColor("#cbd5e1"))
    pdf.setFont("DejaVu", 9)
    pdf.drawCentredString(210, 50, visual(tr("card_pdf_note", values.language)))
    pdf.save()
    return validate(output.getvalue(), "pdf")
