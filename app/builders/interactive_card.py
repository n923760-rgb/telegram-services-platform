"""One-page contact PDF with explicit HTTPS URI annotations, no remote resources."""

from io import BytesIO
from math import ceil
from types import SimpleNamespace

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


def button_layout(count, top, columns, primary_wide, rtl=False):
    result = []
    offset = int(columns == 2 and primary_wide)
    for i in range(count):
        if columns == 1 or (offset and i == 0):
            result.append((i, 42, top - i * 56, 336))
        else:
            j = i - offset
            col = 1 - j % 2 if rtl else j % 2
            result.append((i, 42 + col * 173, top - (offset + j // 2) * 64, 163))
    return result


def build(values, presentation=None):
    _register_fonts()
    entries = values.entries()
    design = presentation or SimpleNamespace(
        accent="#2563eb",
        header="plain",
        alignment="center",
        columns=1,
        primary_wide=False,
        corner_radius=12,
        frame=False,
        tagline="",
        order=list(range(len(entries))),
    )
    accent = design.accent
    soft = "#" + "".join(
        f"{round(int(accent[i : i + 2], 16) * 0.08 + 255 * 0.92):02x}" for i in (1, 3, 5)
    )
    columns = design.columns
    # Readability overrides the grid, never the customer text or link targets.
    if len(entries) == 1 or any(len(wrapped(label, "DejaVu", 9, 117)) > 2 for label, _ in entries):
        columns = 1
    subtitle = values.subtitle or design.tagline
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
    rows = len(entries)
    if columns == 2:
        offset = int(design.primary_wide)
        rows = offset + ceil((rows - offset) / 2)
    step = 64 if columns == 2 else 56
    height = max(300, 65 + header_height + 30 + rows * step + 65)
    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=(420, height))
    pdf.setTitle(values.name)
    pdf.setFillColor(HexColor(soft))
    pdf.rect(0, 0, 420, height, fill=1, stroke=0)
    pdf.setFillColor(white)
    radius = design.corner_radius
    pdf.roundRect(20, 20, 380, height - 40, radius, fill=1, stroke=0)
    pdf.setStrokeColor(HexColor(accent))
    pdf.setLineWidth(0.7)
    if design.frame:
        pdf.roundRect(28, 28, 364, height - 56, radius, fill=0, stroke=1)
    pdf.setFillColor(HexColor(accent))
    if design.header == "plain":
        pdf.roundRect(174, height - 40, 72, 3, 1, fill=1, stroke=0)
    else:
        panel = design.header == "panel"
        pdf.setFillColor(HexColor(accent if panel else soft))
        pdf.roundRect(
            34,
            height - header_height - 85,
            352,
            header_height + 55,
            radius,
            fill=1,
            stroke=int(not panel),
        )
    y = height - 65
    hero = design.header == "panel"

    def header_line(line, baseline):
        if design.alignment == "center":
            pdf.drawCentredString(210, baseline, visual(line))
        elif values.language == "ar":
            pdf.drawRightString(372, baseline, visual(line))
        else:
            pdf.drawString(48, baseline, visual(line))

    pdf.setFillColor(white if hero else HexColor("#0f172a"))
    pdf.setFont("DejaVu-Bold", title_size)
    for line in title_lines:
        header_line(line, y)
        y -= title_size + 7
    pdf.setFillColor(white if hero else HexColor("#475569"))
    pdf.setFont("DejaVu", subtitle_size)
    for line in subtitle_lines:
        header_line(line, y)
        y -= subtitle_size + 7
    top = y - 30 - 46
    for position, x, y, width in button_layout(
        len(entries), top, columns, design.primary_wide, values.language == "ar"
    ):
        label, url = entries[design.order[position]]
        primary = position == 0
        pdf.setFillColor(HexColor(accent if primary else soft))
        pdf.roundRect(x, y, width, 46, radius, fill=1, stroke=0)
        pdf.setFillColor(white if primary else HexColor("#0f172a"))
        size = 11
        lines = wrapped(label, "DejaVu", size, width - 46)
        while len(lines) > 2 and size > 9:
            size -= 1
            lines = wrapped(label, "DejaVu", size, width - 46)
        if len(lines) > 2:
            raise ValueError("card label exceeds layout")
        pdf.setFont("DejaVu", size)
        for i, line in enumerate(lines):
            pdf.drawCentredString(
                x + width / 2 + 5, y + (27 if len(lines) == 2 else 18) - 15 * i, visual(line)
            )
        pdf.setStrokeColor(white if primary else HexColor(accent))
        pdf.setLineWidth(1.4)
        pdf.line(x + 12, y + 18, x + 17, y + 23)
        pdf.line(x + 17, y + 23, x + 12, y + 28)
        pdf.linkURL(url, (x, y, x + width, y + 46), relative=0, thickness=0)
    pdf.setFillColor(HexColor("#64748b"))
    pdf.setFont("DejaVu", 9)
    pdf.drawCentredString(210, 38, visual(tr("card_pdf_note", values.language)))
    pdf.save()
    return validate(output.getvalue(), "pdf")
