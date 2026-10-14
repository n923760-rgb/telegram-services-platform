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
DATE_PATTERN = r"(?<!\d)(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4})(?!\d)"
DATE_TOKEN = re.compile("(" + DATE_PATTERN + ")")
INLINE_LTR = re.compile(
    "(" + DATE_PATTERN + r"|https?://[^\s<>]+|www\.[^\s<>]+|[a-z0-9.+_-]+@[a-z0-9.-]+\.[a-z0-9-]+)",
    re.IGNORECASE,
)


def safe_text(value):
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", value)


def _direction(paragraph, rtl):
    # Isolate dates and ASCII contacts in LTR runs rather than forcing them into Arabic
    # ordering. Preserve the exact characters and existing formatting properties.
    # A long email/URL is an identifier, not evidence that Arabic prose is English.
    if INLINE_LTR.search(paragraph.text):
        rtl = is_rtl(INLINE_LTR.sub("", paragraph.text))
    if rtl:
        for run in list(paragraph.runs):
            if INLINE_LTR.search(run.text):
                for text in INLINE_LTR.split(run.text):
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
        rtl_el.set(qn("w:val"), "1" if rtl and not INLINE_LTR.fullmatch(run.text) else "0")


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
        alignment = "auto"
        for paragraph in list(doc.paragraphs):
            if paragraph.text in slots:
                table = slots.pop(paragraph.text)
                if isinstance(table, str):
                    alignment = table
                    doc.element.body.remove(paragraph._p)
                    continue
                if table is None:
                    following = paragraph._p.getnext()
                    following.get_or_add_pPr().append(OxmlElement("w:pageBreakBefore"))
                    doc.element.body.remove(paragraph._p)
                    continue
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
                _align(paragraph, alignment)
        if slots:
            raise ValueError("unfilled professional table slots")
    elif include_title:
        _heading(doc, data.title, 0)
    for part in [] if professional_template else data.sections:
        paragraph_start = len(doc.paragraphs)
        first = None
        if part.title:
            first = _heading(doc, part.title, 0)
        if part.subtitle:
            subtitle = _body(doc, part.subtitle, style="Subtitle")
            first = first or subtitle
        if part.heading:
            heading = _heading(doc, part.heading, 1)
            first = first or heading
        if part.page_break_before:
            first.paragraph_format.page_break_before = True
        for paragraph in part.paragraphs:
            _body(doc, paragraph)
        for bullet in part.bullets:
            _body(doc, bullet, style="List Bullet")
        for block in part.blocks:
            if block.kind == "lead":
                _heading(doc, block.text, 2)
            else:
                _body(doc, block.text, style="List Bullet" if block.kind == "bullet" else None)
        for table in part.tables:
            _table(doc, table)
        for paragraph in doc.paragraphs[paragraph_start:]:
            _align(paragraph, part.alignment)

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
                    if INLINE_LTR.fullmatch(run.text):
                        # Strong LTR boundaries are portable to Word and LibreOffice.
                        # Only professional mode adds these invisible formatting marks.
                        run.text = "\u200e" + run.text + "\u200e"
    if data.alignment != "auto":
        # Align the document edge consistently while preserving each paragraph's script direction.
        for paragraph in doc.paragraphs:
            properties = paragraph._p.get_or_add_pPr()
            bidi = properties.find(qn("w:bidi"))
            rtl = bidi is not None and bidi.get(qn("w:val")) == "1"
            properties.find(qn("w:jc")).set(
                qn("w:val"), "start" if (data.alignment == "right") == rtl else "end"
            )
    if data.layout == "resume":
        # Keep content in the body and retain script-aware runs from the shared builder.
        normal.paragraph_format.space_after = Pt(4)
        normal.paragraph_format.line_spacing = 1.08
        for name, size in (("Title", 20), ("Heading 1", 12)):
            style = doc.styles[name]
            style.font.size = Pt(size)
            style.paragraph_format.space_before = Pt(0 if name == "Title" else 10)
            style.paragraph_format.space_after = Pt(8 if name == "Title" else 4)
        for paragraph in doc.paragraphs:
            if paragraph.style.name == "Heading 1":
                paragraph.paragraph_format.keep_with_next = True
    if data.design is not None:
        _design(doc, data.design)
    else:
        _page_number_footer(doc)
    buffer = BytesIO()
    doc.save(buffer)
    return validate(buffer.getvalue(), "docx")


def _design(doc, design):
    """Generic source-owned typography; all content remains editable body paragraphs."""
    compact = design.density == "compact"
    sizes = {"modern": (28, 12), "classic": (24, 12), "editorial": (26, 11)}
    title_size, heading_size = sizes[design.theme]
    normal = doc.styles["Normal"]
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(3 if compact else 5)
    normal.paragraph_format.line_spacing = 1.08 if compact else 1.15
    for name, size in (
        ("Title", title_size),
        ("Heading 1", heading_size),
        ("Heading 2", 11),
        ("Subtitle", 12),
    ):
        style = doc.styles[name]
        style.font.name = BODY_FONT
        style.font.size = Pt(size)
        style.font.color.rgb = DARK
        style.font.bold = name != "Subtitle"
        style.font.italic = False
        properties = style.element.get_or_add_rPr()
        for tag, value in (
            ("szCs", str(size * 2)),
            ("bCs", "0" if name == "Subtitle" else "1"),
            ("iCs", "0"),
        ):
            item = properties.find(qn("w:" + tag))
            if item is None:
                item = OxmlElement("w:" + tag)
                properties.append(item)
            item.set(qn("w:val"), value)
        style.paragraph_format.keep_with_next = True
        style.paragraph_format.space_before = Pt(
            0 if name != "Heading 1" else 10 if compact else 14
        )
        style.paragraph_format.space_after = Pt(5 if name == "Title" else 4)
    doc.styles["List Bullet"].paragraph_format.space_after = Pt(3 if compact else 5)
    doc.styles["List Bullet"].paragraph_format.line_spacing = 1.08 if compact else 1.15
    for section in doc.sections:
        section.top_margin = section.bottom_margin = Cm(1.9)
        section.left_margin = section.right_margin = Cm(2.1)
    bullet_ids = {rtl: _bullet_numbering(doc, rtl) for rtl in (False, True)}
    in_header = True
    for paragraph in doc.paragraphs:
        name = paragraph.style.name
        if name == "Title":
            in_header = True
        elif name == "Heading 1":
            in_header = False
        if design.theme == "modern" and in_header:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if name in {"Title", "Heading 1", "Heading 2", "Subtitle"}:
            for run in paragraph.runs:
                # Also replace direct formatting from the non-template authoring path.
                run.font.size = doc.styles[name].font.size
                run.font.color.rgb = DARK
            if design.theme == "modern" and name in {"Title", "Subtitle"}:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if name == "List Bullet":
            rtl = is_rtl(INLINE_LTR.sub("", paragraph.text))
            paragraph.paragraph_format.left_indent = Cm(0 if rtl else 0.45)
            paragraph.paragraph_format.right_indent = Cm(0.45 if rtl else 0)
            paragraph.paragraph_format.first_line_indent = Cm(-0.22)
            num = paragraph._p.get_or_add_pPr().get_or_add_numPr()
            num.get_or_add_ilvl().val = 0
            num.get_or_add_numId().val = bullet_ids[rtl]


def _align(paragraph, alignment):
    if alignment == "auto":
        return
    properties = paragraph._p.get_or_add_pPr()
    rtl = properties.find(qn("w:bidi")).get(qn("w:val")) == "1"
    properties.find(qn("w:jc")).set(
        qn("w:val"), "start" if (alignment == "right") == rtl else "end"
    )


def _bullet_numbering(doc, rtl):
    """Request-local native bullets with an explicit space after the glyph."""
    root = doc.part.numbering_part.element
    abstract_id = (
        max(int(n.get(qn("w:abstractNumId"))) for n in root.findall(qn("w:abstractNum"))) + 1
    )
    num_id = max(int(n.get(qn("w:numId"))) for n in root.findall(qn("w:num"))) + 1
    abstract = OxmlElement("w:abstractNum")
    abstract.set(qn("w:abstractNumId"), str(abstract_id))
    level = OxmlElement("w:lvl")
    level.set(qn("w:ilvl"), "0")
    for tag, value in (
        ("start", "1"),
        ("numFmt", "bullet"),
        ("lvlText", "•"),
        ("lvlJc", "right" if rtl else "left"),
        ("suff", "space"),
    ):
        item = OxmlElement("w:" + tag)
        item.set(qn("w:val"), value)
        level.append(item)
    abstract.append(level)
    root.append(abstract)
    number = OxmlElement("w:num")
    number.set(qn("w:numId"), str(num_id))
    link = OxmlElement("w:abstractNumId")
    link.set(qn("w:val"), str(abstract_id))
    number.append(link)
    root.append(number)
    return num_id
