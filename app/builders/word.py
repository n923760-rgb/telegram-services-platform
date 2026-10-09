import re
from copy import deepcopy
from io import BytesIO

from docx import Document as Word
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_DIRECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.text.run import Run

from app.builders.direction import is_rtl
from app.builders.quality import validate
from app.builders.schema import Document
from app.builders.word_schema import WordDocument, WordTable
from app.builders.word_template import render

BODY_FONT = "DejaVu Sans"
DARK = RGBColor(0, 0, 0)
DATE_TOKEN = re.compile(r"(?<!\d)(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4})(?!\d)")


def safe_text(value):
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", value)


def _direction(paragraph, rtl):
    # Isolate dates in LTR runs rather than forcing their separators into Arabic
    # ordering. Preserve the exact characters and existing formatting properties.
    if rtl:
        for run in list(paragraph.runs):
            if DATE_TOKEN.search(run.text):
                for text in DATE_TOKEN.split(run.text):
                    if text:
                        element = deepcopy(run._r)
                        run._r.addprevious(element)
                        Run(element, paragraph).text = text
                paragraph._p.remove(run._r)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT if rtl else WD_ALIGN_PARAGRAPH.LEFT
    ppr = paragraph._p.get_or_add_pPr()
    bidi = ppr.find(qn("w:bidi"))
    if bidi is None:
        bidi = OxmlElement("w:bidi")
        ppr.insert_element_before(bidi, "w:spacing", "w:ind", "w:jc", "w:sectPr")
    bidi.set(qn("w:val"), "1" if rtl else "0")
    # Logical leading-edge alignment (Office 2010+) avoids RTL mirroring differences
    # between Word and LibreOffice. start is right for RTL and left for LTR.
    ppr.find(qn("w:jc")).set(qn("w:val"), "start")
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
        rtl_el.set(qn("w:val"), "1" if rtl and not DATE_TOKEN.fullmatch(run.text) else "0")


def _heading(doc, text, level):
    style = "Title" if level == 0 else f"Heading {level}"
    paragraph = doc.add_paragraph(style=style)
    run = paragraph.add_run(safe_text(text))
    run.bold = True
    run.font.name = BODY_FONT
    run.font.size = Pt(22 if level == 0 else 14)
    run.font.color.rgb = DARK
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
    paragraph.paragraph_format.widow_control = True
    _direction(paragraph, is_rtl(text))
    return paragraph


def _table(doc, data: WordTable):
    # Separate adjacent uncaptained tables without adding a terminal blank paragraph
    # that could spill onto an otherwise empty page.
    if not data.caption and len(doc.element.body) > 1 and doc.element.body[-2].tag == qn("w:tbl"):
        spacer = doc.add_paragraph()
        spacer.paragraph_format.space_after = Pt(4)
        spacer.paragraph_format.space_before = Pt(0)
        spacer.paragraph_format.line_spacing = Pt(4)
    if data.caption:
        caption = _body(doc, data.caption)
        caption.runs[0].bold = True
        caption.paragraph_format.keep_with_next = True
        caption.paragraph_format.space_before = Pt(10)
    table = doc.add_table(rows=1, cols=len(data.columns))
    table.autofit = False
    table.table_direction = (
        WD_TABLE_DIRECTION.RTL if is_rtl(" ".join(data.columns)) else WD_TABLE_DIRECTION.LTR
    )
    properties = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for name in ("top", "left", "bottom", "right", "insideH", "insideV"):
        edge = OxmlElement(f"w:{name}")
        for key, value in {"val": "single", "sz": "4", "color": "D9D9D9"}.items():
            edge.set(qn(f"w:{key}"), value)
        borders.append(edge)
    properties.append(borders)
    margins = OxmlElement("w:tblCellMar")
    for name in ("top", "left", "bottom", "right"):
        edge = OxmlElement(f"w:{name}")
        edge.set(qn("w:w"), "100")
        edge.set(qn("w:type"), "dxa")
        margins.append(edge)
    properties.append(margins)
    # Give descriptive columns space without allowing a short identifier to dominate.
    weights = [
        max(12, min(48, max(len(data.columns[i]), *(len(row[i]) for row in data.rows))))
        for i in range(len(data.columns))
    ]
    section = doc.sections[0]
    available = section.page_width - section.left_margin - section.right_margin
    widths = [int(available * weight / sum(weights)) for weight in weights]
    if any(DATE_TOKEN.search(cell) for row in data.rows for cell in row):
        minimums = [
            Cm(2.7) if any(DATE_TOKEN.search(row[i]) for row in data.rows) else Cm(1)
            for i in range(len(data.columns))
        ]
        remaining = available - sum(minimums)
        widths = [
            int(minimum + remaining * weight / sum(weights))
            for minimum, weight in zip(minimums, weights, strict=True)
        ]
    for column, width in zip(table.columns, widths, strict=True):
        column.width = width
    header = OxmlElement("w:tblHeader")
    table.rows[0]._tr.get_or_add_trPr().append(header)
    for _values in data.rows:
        table.add_row()
    for index, (row, values) in enumerate(zip(table.rows, [data.columns, *data.rows], strict=True)):
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        for cell, text, width in zip(row.cells, values, widths, strict=True):
            cell.width = width
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            paragraph = cell.paragraphs[0]
            run = paragraph.add_run(safe_text(text))
            run.font.size = Pt(10)
            run.font.color.rgb = DARK
            run.bold = index == 0
            paragraph.paragraph_format.space_after = Pt(2)
            paragraph.paragraph_format.space_before = Pt(2)
            paragraph.paragraph_format.keep_with_next = index == 0
            _direction(paragraph, is_rtl(text))
            if re.fullmatch(r"[\d.,+% /:-]+", text):
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            shading = OxmlElement("w:shd")
            shading.set(qn("w:fill"), "E9EEF2" if index == 0 else "FFFFFF")
            cell._tc.get_or_add_tcPr().append(shading)


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


def build(
    data: Document,
    *,
    include_title: bool = True,
    format_dates: bool = False,
    professional_template: bool = False,
) -> bytes:
    data = WordDocument.model_validate(data.model_dump() if isinstance(data, Document) else data)
    doc, slots = (
        render(data, include_title=include_title) if professional_template else (Word(), {})
    )
    title_properties = doc.styles["Title"].element.get_or_add_pPr()
    for border in list(title_properties.findall(qn("w:pBdr"))):
        title_properties.remove(border)
    for name in ("Title", "Heading 1", "Heading 2", "List Bullet"):
        doc.styles[name].font.name = BODY_FONT
        doc.styles[name].font.color.rgb = DARK
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

    if professional_template:
        for paragraph in list(doc.paragraphs):
            if paragraph.text in slots:
                table = slots.pop(paragraph.text)
                previous = paragraph._p.getprevious()
                if not table.caption and previous is not None and previous.tag == qn("w:tbl"):
                    spacer = doc.add_paragraph()
                    spacer.paragraph_format.space_after = Pt(4)
                    spacer.paragraph_format.line_spacing = Pt(4)
                    _direction(spacer, False)
                    paragraph._p.addprevious(spacer._p)
                before = set(doc.element.body)
                _table(doc, table)
                for element in list(doc.element.body):
                    if element not in before:
                        paragraph._p.addprevious(element)
                doc.element.body.remove(paragraph._p)
            else:
                _direction(paragraph, is_rtl(paragraph.text))
        if slots:
            raise ValueError("unfilled professional table slots")
    elif include_title:
        _heading(doc, data.title, 0)
    for part in [] if professional_template else data.sections:
        if part.heading:
            _heading(doc, part.heading, 1)
        for paragraph in part.paragraphs:
            _body(doc, paragraph)
        for bullet in part.bullets:
            _body(doc, bullet, style="List Bullet")
        for table in part.tables:
            _table(doc, table)

    if format_dates:
        paragraphs = [
            *doc.paragraphs,
            *(
                p
                for table in doc.tables
                for row in table.rows
                for cell in row.cells
                for p in cell.paragraphs
            ),
        ]
        for paragraph in paragraphs:
            properties = paragraph._p.pPr
            bidi = properties.find(qn("w:bidi")) if properties is not None else None
            if bidi is not None and bidi.get(qn("w:val")) == "1":
                for run in paragraph.runs:
                    if DATE_TOKEN.fullmatch(run.text):
                        # Strong LTR boundaries are portable to Word and LibreOffice.
                        # Only professional mode adds these invisible formatting marks.
                        run.text = "\u200e" + run.text + "\u200e"
    _page_number_footer(doc)
    buffer = BytesIO()
    doc.save(buffer)
    return validate(buffer.getvalue(), "docx")
