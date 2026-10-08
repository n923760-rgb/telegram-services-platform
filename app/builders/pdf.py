from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.builders.direction import is_rtl
from app.builders.schema import Document
from app.builders.word import DATE_TOKEN, safe_text

_FONT_FILES = {
    "DejaVu": (
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
    ),
    "DejaVu-Bold": (
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"),
    ),
}


def _first_font(candidates):
    for path in candidates:
        if path.is_file():
            return str(path)
    return None


def _register_fonts():
    if "DejaVu" in pdfmetrics.getRegisteredFontNames():
        return
    regular = _first_font(_FONT_FILES["DejaVu"])
    if regular is None:
        raise RuntimeError("No DejaVu Sans TTF available for PDF rendering")
    pdfmetrics.registerFont(TTFont("DejaVu", regular))
    bold = _first_font(_FONT_FILES["DejaVu-Bold"]) or regular
    pdfmetrics.registerFont(TTFont("DejaVu-Bold", bold))


def _visual(text):
    # Numeric date tokens have a source-defined order, including Arabic-Indic
    # digits. A temporary LTR override protects that order during bidi shaping;
    # get_display consumes the override, so no added controls enter the PDF text.
    protected = DATE_TOKEN.sub(lambda match: "\u202d" + match[0] + "\u202c", safe_text(text))
    return get_display(arabic_reshaper.reshape(protected))


def display(text):
    return escape(_visual(text))


def _wrap(text, font, size, width):
    lines = []
    current = ""
    for word in safe_text(text).split():
        candidate = (current + " " + word).strip()
        rendered = _visual(candidate)
        if current and pdfmetrics.stringWidth(rendered, font, size) > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines or [""]


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("DejaVu", 8)
    canvas.setFillColorRGB(0.4, 0.4, 0.4)
    canvas.drawCentredString(A4[0] / 2, 24, str(doc.page))
    canvas.restoreState()


def build(data: Document, *, include_title: bool = True) -> bytes:
    data = Document.model_validate(data)
    _register_fonts()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=42,
        leftMargin=42,
        topMargin=48,
        bottomMargin=48,
        title=safe_text(data.title),
    )
    title_rtl = ParagraphStyle(
        "TitleRTL",
        fontName="DejaVu-Bold",
        fontSize=18,
        leading=26,
        alignment=TA_RIGHT,
        wordWrap="CJK",
        spaceAfter=12,
    )
    title_ltr = ParagraphStyle("TitleLTR", parent=title_rtl, alignment=TA_LEFT)
    heading_rtl = ParagraphStyle(
        "HeadingRTL",
        fontName="DejaVu-Bold",
        fontSize=14,
        leading=20,
        alignment=TA_RIGHT,
        wordWrap="CJK",
        spaceBefore=8,
        spaceAfter=6,
    )
    heading_ltr = ParagraphStyle("HeadingLTR", parent=heading_rtl, alignment=TA_LEFT)
    normal_rtl = ParagraphStyle(
        "NormalRTL",
        fontName="DejaVu",
        fontSize=11,
        leading=18,
        alignment=TA_RIGHT,
        wordWrap="CJK",
        spaceAfter=6,
    )
    normal_ltr = ParagraphStyle("NormalLTR", parent=normal_rtl, alignment=TA_LEFT)

    width = A4[0] - 84
    story = []
    if include_title:
        for line in _wrap(data.title, "DejaVu-Bold", 18, width):
            story.append(Paragraph(display(line), title_rtl if is_rtl(line) else title_ltr))
        story.append(Spacer(1, 4))

    for section in data.sections:
        if section.heading:
            for line in _wrap(section.heading, "DejaVu-Bold", 14, width):
                story.append(Paragraph(display(line), heading_rtl if is_rtl(line) else heading_ltr))
        for text in section.paragraphs:
            for logical in safe_text(text).splitlines() or [""]:
                if not logical.strip():
                    story.append(Spacer(1, 18))
                    continue
                for line in _wrap(logical, "DejaVu", 11, width):
                    story.append(
                        Paragraph(display(line), normal_rtl if is_rtl(line) else normal_ltr)
                    )
            story.append(Spacer(1, 8))
        for bullet in section.bullets:
            for line in _wrap("• " + bullet, "DejaVu", 11, width):
                story.append(Paragraph(display(line), normal_rtl if is_rtl(line) else normal_ltr))

    # A terminal spacer can overflow an otherwise full page and create a blank page.
    while story and isinstance(story[-1], Spacer):
        story.pop()
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buffer.getvalue()
