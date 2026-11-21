from io import BytesIO

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches, Pt

from app.builders.direction import has_arabic, is_rtl
from app.builders.pptx_layout import BULLET_WIDTH, FONT, plan_slide, wrapped_lines
from app.builders.quality import validate
from app.builders.schema import Deck
from app.builders.word import DATE_TOKEN, INLINE_LTR, safe_text

ACCENT = RGBColor(0x17, 0x6B, 0x55)
DARK = RGBColor(0x22, 0x36, 0x3D)
MUTED = RGBColor(0x58, 0x68, 0x6D)
PAPER = RGBColor(0xF7, 0xFA, 0xF8)
COVER = RGBColor(0x14, 0x2D, 0x36)
COVER_TEXT = RGBColor(0xFF, 0xFF, 0xFF)
COVER_MUTED = RGBColor(0xD6, 0xE5, 0xE0)
CARD_DARK = RGBColor(0x20, 0x46, 0x50)
CARD_PAPER = RGBColor(0xFF, 0xFF, 0xFF)
CARD_ACCENT = RGBColor(0x45, 0xBA, 0x96)
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


def _reading_rtl(text):
    # Contacts/dates are identifiers, not English prose. Use the same contact-first
    # matcher as display formatting, including addresses starting with a date.
    return is_rtl(INLINE_LTR.sub("", text))


def _wrap_contact_and_date(text, size):
    if "\n" in text or "\t" in text:
        return text
    tokens = list(INLINE_LTR.finditer(text))
    if len(tokens) != 2:
        return text
    contact, deadline = tokens
    if (
        "@" not in contact[0]
        or contact[0].lower().startswith(("http://", "https://", "www."))
        or not DATE_TOKEN.fullmatch(deadline[0])
        or len(text[contact.end() : deadline.start()].split()) > 1
    ):
        return text

    # Move the word introducing the contact along with the contact and date.
    # A native soft break keeps the second line part of the same editable bullet.
    split_at = text[: contact.start()].rstrip().rfind(" ")
    if split_at <= 0:
        return text
    first, continuation = text[:split_at], text[split_at + 1 :]
    if wrapped_lines(text, size, BULLET_WIDTH) == 2 and all(
        wrapped_lines(line, size, BULLET_WIDTH) == 1 for line in (first, continuation)
    ):
        return first + "\n" + continuation
    return text


def _style_run(run, size, bold, color, *, ltr_token=False):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    properties = run._r.get_or_add_rPr()
    properties.set("lang", "ar-SA" if has_arabic(run.text) else "en-US")
    for tag in ("a:ea", "a:cs"):
        element = OxmlElement(tag)
        element.set("typeface", FONT)
        properties.append(element)
    if ltr_token:
        direction = OxmlElement("a:rtl")
        direction.set("val", "0")
        properties.append(direction)


def _paragraph(paragraph, text, rtl, align, size, bold, color, *, bullet=False):
    visible = safe_text(text)
    # Give each date or date-leading contact its own LTR run. The Microsoft
    # mobile preview can reverse a date inside a mixed Arabic run despite LRMs.
    ltr_runs = set()
    if rtl:
        paragraph.clear()
        offset = 0
        for match in INLINE_LTR.finditer(visible):
            if not DATE_TOKEN.match(match[0]):
                continue
            paragraph._p.append_text(visible[offset : match.start()])
            ltr_runs.add(paragraph._p.add_r("\u200e" + match[0] + "\u200e"))
            offset = match.end()
        paragraph._p.append_text(visible[offset:])
    else:
        paragraph.text = visible
    paragraph.alignment = align
    properties = paragraph._p.get_or_add_pPr()
    properties.set("rtl", "1" if rtl else "0")
    if bullet:
        properties.set("marR" if rtl else "marL", str(int(Pt(20))))
        properties.set("indent", str(-int(Pt(12))))
    marker = OxmlElement("a:buChar" if bullet else "a:buNone")
    if bullet:
        marker.set("char", "•")
    properties.append(marker)
    paragraph.space_before = Pt(0)
    paragraph.space_after = Pt(10 if bullet else 0)
    paragraph.line_spacing = Pt(size * 1.2)
    paragraph.font.name = FONT
    paragraph.font.size = Pt(size)
    paragraph.font.bold = bold
    paragraph.font.color.rgb = color
    for run in paragraph.runs:
        _style_run(run, size, bold, color, ltr_token=run._r in ltr_runs)


def _frame(frame):
    frame.word_wrap = True
    frame.auto_size = MSO_AUTO_SIZE.NONE
    frame.vertical_anchor = MSO_ANCHOR.TOP
    frame.margin_left = frame.margin_right = Inches(0.1)
    frame.margin_top = frame.margin_bottom = Inches(0.1)


def _textbox(slide, name, x, y, width, height):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(width), Inches(height))
    shape.name = name
    _frame(shape.text_frame)
    return shape.text_frame


def _table(slide, item, layout):
    data = item.table
    native = slide.shapes.add_table(
        len(data.rows) + 1,
        len(data.columns),
        Inches(0.85),
        Inches(1.8),
        Inches(11.6),
        Pt(sum(layout.row_heights)),
    )
    native.name = "Source records"
    table = native.table
    column_order = range(len(data.columns))
    if _reading_rtl(" ".join(data.columns)):
        column_order = column_order[::-1]
    # Some viewers ignore the table's RTL flag. Serialize columns in visual
    # order and keep text direction independent for each cell.
    table._tbl.tblPr.set("rtl", "0")
    # Match the exact widths used by the layout gate. Keep the native table's
    # total width exact after converting point measurements to integer EMUs.
    remaining_width = native.width
    for index, source_index in enumerate(column_order):
        width = layout.column_widths[source_index]
        native_width = remaining_width if index == len(column_order) - 1 else Pt(width)
        table.columns[index].width = native_width
        remaining_width -= native_width
    table.first_row = True
    table.horz_banding = False  # Explicit colors, consistent across Office themes.
    for row_index, values in enumerate([data.columns, *data.rows]):
        table.rows[row_index].height = Pt(layout.row_heights[row_index])
        for column_index, source_index in enumerate(column_order):
            value = values[source_index]
            cell = table.cell(row_index, column_index)
            _frame(cell.text_frame)
            cell.fill.solid()
            cell.fill.fore_color.rgb = (
                ACCENT
                if row_index == 0
                else RGBColor(0xF0, 0xF6, 0xF3)
                if row_index % 2
                else RGBColor(0xFF, 0xFF, 0xFF)
            )
            for edge in ("L", "R", "T", "B"):
                border = OxmlElement("a:ln" + edge)
                border.set("w", "9525")  # 0.75pt native cell borders.
                fill = OxmlElement("a:solidFill")
                color = OxmlElement("a:srgbClr")
                color.set("val", "FFFFFF" if row_index == 0 else "DFE8E4")
                fill.append(color)
                border.append(fill)
                cell._tc.get_or_add_tcPr().insert_element_before(border, "a:solidFill")
            rtl = _reading_rtl(value)
            _paragraph(
                cell.text_frame.paragraphs[0],
                value,
                rtl,
                PP_ALIGN.RIGHT if rtl else PP_ALIGN.LEFT,
                21 if row_index == 0 else layout.body_size,
                row_index == 0,
                RGBColor(0xFF, 0xFF, 0xFF) if row_index == 0 else DARK,
            )


def _native_card(slide, text, index, *, x, y, width, height, size, dark):
    """Editable source text in a bounded native PowerPoint shape."""
    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(x),
        Inches(y),
        Inches(width),
        Inches(height),
    )
    card.name = f"Content card {index + 1}"
    card.fill.solid()
    card.fill.fore_color.rgb = CARD_DARK if dark else CARD_PAPER
    card.line.fill.background()
    _frame(card.text_frame)
    card.text_frame.margin_left = Inches(0.28)
    card.text_frame.margin_right = Inches(0.28)
    card.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    rtl = _reading_rtl(text)
    _paragraph(
        card.text_frame.paragraphs[0],
        text,
        rtl,
        PP_ALIGN.CENTER if dark else PP_ALIGN.RIGHT if rtl else PP_ALIGN.LEFT,
        size,
        dark,
        COVER_TEXT if dark else DARK,
    )
    accent = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(x + width - 0.08 if rtl else x + 0.02),
        Inches(y + 0.23),
        Inches(0.06),
        Inches(height - 0.46),
    )
    accent.name = f"Card accent {index + 1}"
    accent.fill.solid()
    accent.fill.fore_color.rgb = CARD_ACCENT
    accent.line.fill.background()


def _render_cards(slide, item, layout):
    rtl_order = _reading_rtl(item.title)
    for index, value in enumerate(item.bullets):
        if layout.kind == "agenda":
            column = 2 - index if rtl_order else index
            x, y, width, height = 0.85 + column * 3.96, 3.55, 3.68, 2.35
        elif layout.kind == "steps":
            x, y, width, height = 0.85, 1.85 + index * 1.58, 11.6, 1.36
        else:
            column = 1 - index % 2 if rtl_order else index % 2
            x = 0.85 + column * 5.96
            y = 1.85 + (index // 2) * 1.58
            width, height = 5.64, 1.36
        _native_card(
            slide,
            value,
            index,
            x=x,
            y=y,
            width=width,
            height=height,
            size=layout.body_size,
            dark=layout.kind == "agenda",
        )


def build(data: Deck) -> bytes:
    data = Deck.model_validate(data)
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    blank = prs.slide_layouts[6]

    prs.core_properties.title = safe_text(data.slides[0].title)
    prs.core_properties.author = "Telegram Services"
    for index, item in enumerate(data.slides):
        slide = prs.slides.add_slide(blank)
        layout = plan_slide(item, cover_candidate=index == 0 and len(data.slides) > 1)
        cover = layout.kind in {"cover", "agenda"}
        # Native fills keep every foreground item editable and require no image assets.
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = COVER if cover else PAPER
        title_frame = _textbox(
            slide, "Slide title", 0.85, 1.55 if cover else 0.45, 11.6, 1.6 if cover else 1.3
        )
        rtl = _reading_rtl(item.title)
        _paragraph(
            title_frame.paragraphs[0],
            item.title,
            rtl,
            PP_ALIGN.CENTER if cover else PP_ALIGN.RIGHT if rtl else PP_ALIGN.LEFT,
            layout.title_size,
            True,
            COVER_TEXT if cover else ACCENT,
        )
        if item.table is not None:
            _table(slide, item, layout)
        elif layout.kind in {"agenda", "steps", "grid"}:
            _render_cards(slide, item, layout)
        else:
            body = _textbox(
                slide, "Slide content", 0.85, 3.55 if cover else 1.8, 11.6, 1.9 if cover else 4.85
            )
            for bullet_index, text in enumerate(item.bullets):
                paragraph = body.paragraphs[0] if bullet_index == 0 else body.add_paragraph()
                rtl = _reading_rtl(text)
                if rtl and not cover:
                    text = _wrap_contact_and_date(text, layout.body_size)
                _paragraph(
                    paragraph,
                    text,
                    rtl,
                    PP_ALIGN.CENTER if cover else PP_ALIGN.RIGHT if rtl else PP_ALIGN.LEFT,
                    layout.body_size,
                    False,
                    COVER_MUTED if cover else DARK,
                    bullet=not cover,
                )
                if cover:
                    paragraph.space_after = Pt(10 if bullet_index < len(item.bullets) - 1 else 0)
                elif bullet_index == len(item.bullets) - 1:
                    paragraph.space_after = Pt(0)
        footer = _textbox(slide, "Slide number", 11.15, 7.0, 1.3, 0.35)
        footer.margin_top = footer.margin_bottom = Pt(0)
        _paragraph(
            footer.paragraphs[0],
            f"{index + 1} / {len(data.slides)}",
            False,
            PP_ALIGN.RIGHT,
            12,
            False,
            COVER_MUTED if cover else MUTED,
        )

    buffer = BytesIO()
    prs.save(buffer)
    return validate(buffer.getvalue(), "pptx")
