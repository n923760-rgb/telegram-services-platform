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


PALETTES = {
    "navy": ("#0f172a", "#2563eb", "#eff6ff"),
    "emerald": ("#064e3b", "#047857", "#ecfdf5"),
    "graphite": ("#27272a", "#52525b", "#f4f4f5"),
}


def build(values, presentation=None):
    _register_fonts()
    ink, accent, soft = PALETTES[presentation.palette if presentation else "navy"]
    entries = values.entries()
    order = presentation.order if presentation else list(range(len(entries)))
    subtitle = values.subtitle or (presentation.tagline if presentation else "")
    title_size = 20
    title_lines = wrapped(values.name, "DejaVu-Bold", title_size, 324)
    while len(title_lines) > 2 and title_size > 9:
        title_size -= 1
        title_lines = wrapped(values.name, "DejaVu-Bold", title_size, 324)
    subtitle_size = 11
    subtitle_lines = wrapped(subtitle, "DejaVu", subtitle_size, 324) if subtitle else []
    while len(subtitle_lines) > 2 and subtitle_size > 9:
        subtitle_size -= 1
        subtitle_lines = wrapped(subtitle, "DejaVu", subtitle_size, 324)
    if len(title_lines) > 2 or len(subtitle_lines) > 2:
        raise ValueError("card text exceeds layout")
    header_height = len(title_lines) * (title_size + 7) + len(subtitle_lines) * (subtitle_size + 7)
    height = max(300, 65 + header_height + 30 + len(entries) * 56 + 65)
    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=(420, height))
    pdf.setTitle(values.name)
    pdf.setFillColor(HexColor("#eef2f6"))
    pdf.rect(0, 0, 420, height, fill=1, stroke=0)
    pdf.setFillColor(white)
    pdf.roundRect(20, 20, 380, height - 40, 16, fill=1, stroke=0)
    pdf.setFillColor(HexColor(accent))
    pdf.roundRect(174, height - 40, 72, 4, 2, fill=1, stroke=0)
    y = height - 65
    pdf.setFillColor(HexColor(ink))
    pdf.setFont("DejaVu-Bold", title_size)
    for line in title_lines:
        pdf.drawCentredString(210, y, visual(line))
        y -= title_size + 7
    pdf.setFillColor(HexColor("#475569"))
    pdf.setFont("DejaVu", subtitle_size)
    for line in subtitle_lines:
        pdf.drawCentredString(210, y, visual(line))
        y -= subtitle_size + 7
    y -= 30 + 46
    for position, index in enumerate(order):
        label, url = entries[index]
        primary = position == 0
        pdf.setFillColor(HexColor(accent if primary else soft))
        pdf.roundRect(42, y, 336, 46, 10, fill=1, stroke=0)
        pdf.setFillColor(white if primary else HexColor(ink))
        pdf.setFont("DejaVu", 11)
        lines = wrapped(label, "DejaVu", 11, 270)
        if len(lines) > 2:
            raise ValueError("card label exceeds layout")
        for i, line in enumerate(lines):
            pdf.drawCentredString(210, y + (27 if len(lines) == 2 else 18) - 15 * i, visual(line))
        # A vector arrow makes the entire linked button's action visible.
        pdf.setStrokeColor(white if primary else HexColor(accent))
        pdf.setLineWidth(1.4)
        pdf.line(61, y + 18, 66, y + 23)
        pdf.line(66, y + 23, 61, y + 28)
        pdf.linkURL(url, (42, y, 378, y + 46), relative=0, thickness=0)
        y -= 56
    pdf.setFillColor(HexColor("#64748b"))
    pdf.setFont("DejaVu", 9)
    pdf.drawCentredString(210, 38, visual(tr("card_pdf_note", values.language)))
    pdf.save()
    return validate(output.getvalue(), "pdf")
