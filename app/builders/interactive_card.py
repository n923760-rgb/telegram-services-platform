"""One-page contact PDF with explicit HTTPS URI annotations, no remote resources."""

from io import BytesIO
from math import ceil
from types import SimpleNamespace
from urllib.parse import urlsplit

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


def card_lines(text, font, size, width):
    """Prefer whole words; split only a token that cannot fit by itself."""
    lines = []
    remaining = text.strip()
    while remaining:
        end = 1
        while (
            end < len(remaining)
            and pdfmetrics.stringWidth(visual(remaining[: end + 1]), font, size) <= width
        ):
            end += 1
        cut = remaining.rfind(" ", 0, end + 1) if end < len(remaining) else -1
        if cut > 0:
            end = cut
        lines.append(remaining[:end].rstrip())
        remaining = remaining[end:].lstrip()
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


def tint(color, strength):
    return "#" + "".join(
        f"{round(int(color[i : i + 2], 16) * strength + 255 * (1 - strength)):02x}"
        for i in (1, 3, 5)
    )


def action_icon(pdf, x, y, message, color):
    """Small generic vector action marks, never a logo or verification badge."""
    pdf.setStrokeColor(color)
    pdf.setLineWidth(1.1)
    if message:
        path = pdf.beginPath()
        path.moveTo(x - 6, y + 5)
        path.lineTo(x + 6, y + 5)
        path.lineTo(x + 6, y - 3)
        path.lineTo(x - 1, y - 3)
        path.lineTo(x - 5, y - 6)
        path.lineTo(x - 4, y - 3)
        path.lineTo(x - 6, y - 3)
        path.close()
        pdf.drawPath(path, stroke=1, fill=0)
        pdf.line(x - 3, y + 1, x + 3, y + 1)
    else:
        pdf.roundRect(x - 6, y - 6, 10, 10, 2, stroke=1, fill=0)
        pdf.line(x - 1, y - 1, x + 7, y + 7)
        pdf.line(x + 2, y + 7, x + 7, y + 7)
        pdf.line(x + 7, y + 2, x + 7, y + 7)


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
    soft = tint(accent, 0.06)
    columns = design.columns
    if len(entries) == 1 or any(
        len(card_lines(label, font, 9, 79)) > 2
        for label, _ in entries
        for font in ("DejaVu", "DejaVu-Bold")
    ):
        columns = 1
    subtitle = values.subtitle or design.tagline
    alignment = design.alignment
    # Move the name initial above very long text rather than squeezing the prose.
    if any(
        len(card_lines(text, "DejaVu-Bold" if i == 0 else "DejaVu", 9, 246)) > 2
        for i, text in enumerate((values.name, subtitle))
        if text
    ):
        alignment = "center"
    width = 324 if alignment == "center" else 246
    title_size = 22
    title_lines = card_lines(values.name, "DejaVu-Bold", title_size, width)
    while len(title_lines) > 2 and title_size > 9:
        title_size -= 1
        title_lines = card_lines(values.name, "DejaVu-Bold", title_size, width)
    subtitle_size = 10
    subtitle_lines = card_lines(subtitle, "DejaVu", subtitle_size, width) if subtitle else []
    while len(subtitle_lines) > 2 and subtitle_size > 9:
        subtitle_size -= 1
        subtitle_lines = card_lines(subtitle, "DejaVu", subtitle_size, width)
    if len(title_lines) > 2 or len(subtitle_lines) > 2:
        raise ValueError("card text exceeds layout")
    text_height = len(title_lines) * (title_size + 7) + len(subtitle_lines) * (subtitle_size + 7)
    anchor = 117 if alignment == "center" else 74
    last_step = subtitle_size + 7 if subtitle_lines else title_size + 7
    header_height = anchor + text_height - last_step + 22
    rows = len(entries)
    if columns == 2:
        offset = int(design.primary_wide)
        rows = offset + ceil((rows - offset) / 2)
    step = 64 if columns == 2 else 56
    height = max(300, header_height + 130 + (rows - 1) * step)
    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=(420, height))
    pdf.setTitle(values.name)
    pdf.setFillColor(HexColor("#f3f5f8"))
    pdf.rect(0, 0, 420, height, fill=1, stroke=0)
    pdf.setFillColor(HexColor("#e6eaf0"))
    pdf.roundRect(20, 17, 380, height - 40, 18, fill=1, stroke=0)
    pdf.setFillColor(white)
    pdf.roundRect(20, 20, 380, height - 40, 18, fill=1, stroke=0)
    pdf.setStrokeColor(HexColor(tint(accent, 0.18)))
    pdf.setLineWidth(0.6)
    if design.frame:
        pdf.roundRect(20, 20, 380, height - 40, 18, fill=0, stroke=1)
    bottom = height - header_height
    hero = design.header == "panel"
    radius = design.corner_radius
    if design.header != "plain":
        pdf.setFillColor(HexColor(accent if hero else soft))
        pdf.roundRect(30, bottom, 360, height - bottom - 30, radius, fill=1, stroke=int(not hero))
    # Restrained decoration is clipped to the identity area, clear of the actions.
    pdf.saveState()
    clip = pdf.beginPath()
    clip.rect(31, bottom + 1, 358, height - bottom - 32)
    pdf.clipPath(clip, stroke=0, fill=0)
    pdf.setStrokeColor(HexColor(tint(accent, 0.7 if hero else 0.12)))
    pdf.setLineWidth(0.65)
    edge = 42 if values.language == "ar" else 378
    for r in (30, 46, 62):
        pdf.circle(edge, height - 34, r, fill=0, stroke=1)
    pdf.restoreState()
    rtl = values.language == "ar"
    badge_x = 210 if alignment == "center" else (348 if rtl else 72)
    badge_y = height - (72 if alignment == "center" else 88)
    pdf.setFillColor(white if design.header in {"panel", "outline"} else HexColor(soft))
    pdf.circle(badge_x, badge_y, 22, fill=1, stroke=0)
    initial = next((c for c in values.name if c.isalpha()), "")
    pdf.setFillColor(HexColor(accent))
    pdf.setFont("DejaVu-Bold", 20)
    if initial:
        pdf.drawCentredString(badge_x, badge_y - 7, visual(initial))
    else:
        pdf.circle(badge_x, badge_y, 4, fill=1, stroke=0)
    y = height - anchor

    def header_line(line, baseline):
        if alignment == "center":
            pdf.drawCentredString(210, baseline, visual(line))
        elif rtl:
            pdf.drawRightString(306, baseline, visual(line))
        else:
            pdf.drawString(114, baseline, visual(line))

    pdf.setFillColor(white if hero else HexColor("#172338"))
    pdf.setFont("DejaVu-Bold", title_size)
    for line in title_lines:
        header_line(line, y)
        y -= title_size + 7
    pdf.setFillColor(HexColor(tint(accent, 0.12)) if hero else HexColor("#607086"))
    pdf.setFont("DejaVu", subtitle_size)
    for line in subtitle_lines:
        header_line(line, y)
        y -= subtitle_size + 7
    top = bottom - 14 - 46
    for position, x, y, button_width in button_layout(
        len(entries), top, columns, design.primary_wide, rtl
    ):
        label, url = entries[design.order[position]]
        primary = position == 0
        pdf.setFillColor(HexColor(accent) if primary else white)
        pdf.setStrokeColor(HexColor(accent if primary else "#e1e6ed"))
        pdf.setLineWidth(0.7)
        pdf.roundRect(x, y, button_width, 46, radius, fill=1, stroke=1)
        icon_x = x + button_width - 24 if rtl else x + 24
        color = white if primary else HexColor(accent)
        pdf.setFillColor(HexColor(tint(accent, 0.78)) if primary else HexColor(soft))
        pdf.circle(icon_x, y + 23, 13, fill=1, stroke=0)
        action_icon(
            pdf, icon_x, y + 23, urlsplit(url).hostname in {"wa.me", "api.whatsapp.com"}, color
        )
        size = 11 if primary else 10
        font = "DejaVu-Bold" if primary else "DejaVu"
        lines = card_lines(label, font, size, button_width - 84)
        while len(lines) > 2 and size > 9:
            size -= 1
            lines = card_lines(label, font, size, button_width - 84)
        if len(lines) > 2:
            raise ValueError("card label exceeds layout")
        pdf.setFillColor(white if primary else HexColor("#26364a"))
        pdf.setFont(font, size)
        center = x + button_width / 2 + (-3 if rtl else 3)
        for i, line in enumerate(lines):
            pdf.drawCentredString(
                center, y + (27 if len(lines) == 2 else 18) - 15 * i, visual(line)
            )
        arrow_x = x + 14 if rtl else x + button_width - 14
        direction = -1 if rtl else 1
        pdf.setStrokeColor(white if primary else HexColor("#8794a7"))
        pdf.setLineWidth(1)
        pdf.line(arrow_x - direction * 2, y + 20, arrow_x + direction * 1, y + 23)
        pdf.line(arrow_x + direction * 1, y + 23, arrow_x - direction * 2, y + 26)
        pdf.linkURL(url, (x, y, x + button_width, y + 46), relative=0, thickness=0)
    pdf.setStrokeColor(HexColor("#edf0f4"))
    pdf.setLineWidth(0.6)
    pdf.line(150, 55, 270, 55)
    pdf.setFillColor(HexColor("#64748b"))
    pdf.setFont("DejaVu", 8)
    pdf.drawCentredString(210, 36, visual(tr("card_pdf_note", values.language)))
    pdf.save()
    return validate(output.getvalue(), "pdf")
