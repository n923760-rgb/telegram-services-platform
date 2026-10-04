from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.builders.schema import Document
from app.builders.word import safe_text

FONT_PATH = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")


def display(text):
    return escape(get_display(arabic_reshaper.reshape(safe_text(text))))


def build(data: Document) -> bytes:
    data = Document.model_validate(data)
    if "Arabic" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("Arabic", str(FONT_PATH)))
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42
    )
    normal = ParagraphStyle(
        "Arabic", fontName="Arabic", fontSize=11, leading=19, alignment=TA_RIGHT, wordWrap="CJK"
    )
    heading = ParagraphStyle("Heading", parent=normal, fontSize=15, leading=24, spaceAfter=10)

    def wrapped(text, size):
        width = A4[0] - 104
        lines = []
        current = ""
        for word in safe_text(text).split():
            candidate = (current + " " + word).strip()
            rendered = get_display(arabic_reshaper.reshape(candidate))
            if current and pdfmetrics.stringWidth(rendered, "Arabic", size) > width:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        return lines or [""]

    story = []
    for line in wrapped(data.title, 15):
        story.append(Paragraph(display(line), heading))
    for section in data.sections:
        if section.heading:
            for line in wrapped(section.heading, 15):
                story.append(Paragraph(display(line), heading))
        for text in section.paragraphs:
            for logical in text.splitlines() or [""]:
                for line in wrapped(logical, 11):
                    story.append(Paragraph(display(line), normal))
            story.append(Spacer(1, 8))
        for bullet in section.bullets:
            for line in wrapped("• " + bullet, 11):
                story.append(Paragraph(display(line), normal))
    doc.build(story)
    return buffer.getvalue()
