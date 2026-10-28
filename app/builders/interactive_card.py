"""One-page contact PDF with explicit HTTPS URI annotations, no remote resources."""

from io import BytesIO
from math import ceil

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

ACTIVITY_PALETTES = {
    "professional": "navy",
    "legal": "graphite",
    "shop": "emerald",
    "restaurant": "emerald",
    "creative": "navy",
}


def button_layout(activity, count, top, rtl=False):
    """Return source positions and non-overlapping full button hit areas."""
    if activity == "shop" and count > 1:
        return [
            (i, 42 + ((1 - i % 2) if rtl else i % 2) * 173, top - (i // 2) * 64, 163)
            for i in range(count)
        ]
    if activity == "creative" and count > 2:
        return [(0, 42, top, 336)] + [
            (
                i,
                42 + ((1 - (i - 1) % 2) if rtl else (i - 1) % 2) * 173,
                top - (1 + (i - 1) // 2) * 64,
                163,
            )
            for i in range(1, count)
        ]
    return [(i, 42, top - i * 56, 336) for i in range(count)]


def build(values, presentation=None):
    _register_fonts()
    ink, accent, soft = PALETTES[
        presentation.palette if presentation else ACTIVITY_PALETTES[values.activity]
    ]
    entries = values.entries()
    order = presentation.order if presentation else list(range(len(entries)))
    # Long customer labels retain readable type by expanding the button grid.
    layout_activity = values.activity
    if any(len(wrapped(label, "DejaVu", 9, 117)) > 2 for label, _ in entries):
        layout_activity = "professional"
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
    rows = len(entries)
    if layout_activity == "shop" and rows > 1:
        rows = ceil(rows / 2)
    elif layout_activity == "creative" and rows > 2:
        rows = 1 + ceil((rows - 1) / 2)
    step = 64 if rows != len(entries) else 56
    header_extra = 20 if values.activity in {"restaurant", "creative"} else 0
    height = max(300, 65 + header_height + header_extra + 30 + rows * step + 65)
    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=(420, height))
    pdf.setTitle(values.name)
    pdf.setFillColor(HexColor(soft if values.style != "minimal" else "#ffffff"))
    pdf.rect(0, 0, 420, height, fill=1, stroke=0)
    pdf.setFillColor(white)
    radius = {"modern": 16, "classic": 2, "minimal": 0}[values.style]
    pdf.roundRect(20, 20, 380, height - 40, radius, fill=1, stroke=0)
    pdf.setFillColor(HexColor(accent))
    if values.activity == "legal":
        pdf.setStrokeColor(HexColor(accent))
        pdf.setLineWidth(0.6)
        pdf.rect(28, 28, 364, height - 56, fill=0, stroke=1)
        pdf.rect(32, 32, 356, height - 64, fill=0, stroke=1)
        pdf.rect(174, height - 43, 72, 2, fill=1, stroke=0)
    elif values.activity == "restaurant":
        pdf.roundRect(
            30, height - header_height - 98, 360, header_height + 68, radius, fill=1, stroke=0
        )
    elif values.activity == "shop":
        pdf.rect(30, height - header_height - 85, 360, header_height + 55, fill=1, stroke=0)
        pdf.setFillColor(HexColor(soft))
        pdf.rect(34, height - header_height - 81, 352, header_height + 47, fill=1, stroke=0)
    elif values.activity == "creative":
        pdf.circle(60, height - 46, 10, fill=1, stroke=0)
        pdf.setFillColor(HexColor(soft))
        pdf.circle(64, height - 42, 7, fill=1, stroke=0)
        pdf.setFillColor(HexColor(accent))
        pdf.rect(112, height - 40, 266, 3, fill=1, stroke=0)
    else:
        pdf.roundRect(174, height - 40, 72, 4, 2, fill=1, stroke=0)
    y = height - 65 - header_extra
    hero = values.activity == "restaurant"
    pdf.setFillColor(white if hero else HexColor(ink))
    pdf.setFont("DejaVu-Bold", title_size)
    for line in title_lines:
        pdf.drawCentredString(210, y, visual(line))
        y -= title_size + 7
    pdf.setFillColor(white if hero else HexColor("#475569"))
    pdf.setFont("DejaVu", subtitle_size)
    for line in subtitle_lines:
        pdf.drawCentredString(210, y, visual(line))
        y -= subtitle_size + 7
    top = y - 30 - 46
    for position, x, y, width in button_layout(
        layout_activity, len(entries), top, values.language == "ar"
    ):
        index = order[position]
        label, url = entries[index]
        primary = position == 0
        filled = primary and values.style != "minimal"
        pdf.setFillColor(
            HexColor(accent if filled else ("#ffffff" if values.style == "minimal" else soft))
        )
        pdf.setStrokeColor(HexColor(accent))
        pdf.setLineWidth(0.6)
        pdf.roundRect(x, y, width, 46, radius, fill=1, stroke=int(values.style != "modern"))
        pdf.setFillColor(white if filled else HexColor(ink))
        size = 11
        lines = wrapped(label, "DejaVu", size, width - 46)
        while len(lines) > 2 and size > 8:
            size -= 1
            lines = wrapped(label, "DejaVu", size, width - 46)
        if len(lines) > 2:
            raise ValueError("card label exceeds layout")
        pdf.setFont("DejaVu", size)
        for i, line in enumerate(lines):
            pdf.drawCentredString(
                x + width / 2 + 5, y + (27 if len(lines) == 2 else 18) - 15 * i, visual(line)
            )
        # A vector arrow makes the entire linked button's action visible.
        pdf.setStrokeColor(white if filled else HexColor(accent))
        pdf.setLineWidth(1.4)
        pdf.line(x + 12, y + 18, x + 17, y + 23)
        pdf.line(x + 17, y + 23, x + 12, y + 28)
        pdf.linkURL(url, (x, y, x + width, y + 46), relative=0, thickness=0)
    pdf.setFillColor(HexColor("#64748b"))
    pdf.setFont("DejaVu", 9)
    pdf.drawCentredString(210, 38, visual(tr("card_pdf_note", values.language)))
    pdf.save()
    return validate(output.getvalue(), "pdf")
