import re
from io import BytesIO

from docx import Document as Word
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from app.builders.direction import is_rtl
from app.builders.schema import Document

BODY_FONT = "DejaVu Sans"
ACCENT = RGBColor(0x17, 0x6B, 0x55)
DARK = RGBColor(0x20, 0x20, 0x20)


def safe_text(value):
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", value)


def _direction(paragraph, rtl):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT if rtl else WD_ALIGN_PARAGRAPH.LEFT
    ppr = paragraph._p.get_or_add_pPr()
    bidi = ppr.find(qn("w:bidi"))
    if bidi is None:
        bidi = OxmlElement("w:bidi")
        ppr.append(bidi)
    bidi.set(qn("w:val"), "1" if rtl else "0")
    for run in paragraph.runs:
        run.font.name = BODY_FONT
        rpr = run._element.get_or_add_rPr()
        fonts = rpr.find(qn("w:rFonts"))
        if fonts is None:
            fonts = OxmlElement("w:rFonts")
            rpr.append(fonts)
        fonts.set(qn("w:cs"), BODY_FONT)
        rtl_el = rpr.find(qn("w:rtl"))
        if rtl_el is None:
            rtl_el = OxmlElement("w:rtl")
            rpr.append(rtl_el)
        rtl_el.set(qn("w:val"), "1" if rtl else "0")


def _heading(doc, text, level):
    style = "Title" if level == 0 else f"Heading {level}"
    paragraph = doc.add_paragraph(style=style)
    run = paragraph.add_run(safe_text(text))
    run.bold = True
    run.font.name = BODY_FONT
    run.font.size = Pt(22 if level == 0 else 14)
    run.font.color.rgb = ACCENT if level == 0 else DARK
    paragraph.paragraph_format.space_before = Pt(0 if level == 0 else 14)
    paragraph.paragraph_format.space_after = Pt(14 if level == 0 else 6)
    paragraph.paragraph_format.keep_with_next = True
    _direction(paragraph, is_rtl(text))
    return paragraph


def _body(doc, text, style=None):
    paragraph = doc.add_paragraph(style=style)
    run = paragraph.add_run(safe_text(text))
    run.font.name = BODY_FONT
    run.font.size = Pt(11)
    run.font.color.rgb = DARK
    _direction(paragraph, is_rtl(text))
    return paragraph


def _page_number_footer(document):
    paragraph = document.sections[0].footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    run.font.name = BODY_FONT
    run.font.size = Pt(9)
    run.font.color.rgb = DARK
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(instr)
    run._r.append(end)


def build(data: Document) -> bytes:
    data = Document.model_validate(data)
    doc = Word()
    normal = doc.styles["Normal"]
    normal.font.name = BODY_FONT
    normal.font.size = Pt(11)
    normal.font.color.rgb = DARK
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    normal.paragraph_format.line_spacing = 1.15

    section = doc.sections[0]
    section.top_margin = Cm(2.2)
    section.bottom_margin = Cm(2.2)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)

    _heading(doc, data.title, 0)
    for part in data.sections:
        if part.heading:
            _heading(doc, part.heading, 1)
        for paragraph in part.paragraphs:
            _body(doc, paragraph)
        for bullet in part.bullets:
            _body(doc, bullet, style="List Bullet")

    _page_number_footer(doc)
    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
