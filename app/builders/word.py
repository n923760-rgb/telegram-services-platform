import re
from io import BytesIO

from docx import Document as Word
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

from app.builders.schema import Document


def safe_text(value):
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", value)


def rtl(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    bidi = OxmlElement("w:bidi")
    bidi.set(qn("w:val"), "1")
    paragraph._p.get_or_add_pPr().append(bidi)
    for run in paragraph.runs:
        run.font.name = "DejaVu Sans"
        rpr = run._element.get_or_add_rPr()
        font = rpr.find(qn("w:rFonts"))
        if font is not None:
            font.set(qn("w:cs"), "DejaVu Sans")
        cs = OxmlElement("w:rtl")
        cs.set(qn("w:val"), "1")
        rpr.append(cs)


def build(data: Document) -> bytes:
    data = Document.model_validate(data)
    doc = Word()
    doc.styles["Normal"].font.name = "DejaVu Sans"
    doc.styles["Normal"].font.size = Pt(11)
    rtl(doc.add_heading(safe_text(data.title), 0))
    for section in data.sections:
        if section.heading:
            rtl(doc.add_heading(safe_text(section.heading), level=1))
        for paragraph in section.paragraphs:
            rtl(doc.add_paragraph(safe_text(paragraph)))
        for bullet in section.bullets:
            rtl(doc.add_paragraph(safe_text(bullet), style="List Bullet"))
    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
