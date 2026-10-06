from io import BytesIO

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from app.builders.direction import is_rtl
from app.builders.schema import Deck
from app.builders.word import safe_text

ACCENT = RGBColor(0x17, 0x6B, 0x55)
DARK = RGBColor(0x33, 0x33, 0x33)
MUTED = RGBColor(0x66, 0x66, 0x66)
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


def _style_run(run, size, bold, color):
    run.font.name = "DejaVu Sans"
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color


def _paragraph(paragraph, text, rtl, align):
    paragraph.text = safe_text(text)
    paragraph.alignment = align
    paragraph._p.get_or_add_pPr().set("rtl", "1" if rtl else "0")


def _fit_size(bullets, base=20, minimum=12):
    size = base
    if len(bullets) > 4:
        size -= (len(bullets) - 4) * 1.5
    longest = max((len(bullet) for bullet in bullets), default=0)
    if longest > 70:
        size -= (longest - 70) // 25
    return max(minimum, int(size))


def build(data: Deck) -> bytes:
    data = Deck.model_validate(data)
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    blank = prs.slide_layouts[6]

    first = data.slides[0]
    title_slide = prs.slides.add_slide(blank)
    title_box = title_slide.shapes.add_textbox(Inches(1.0), Inches(2.4), Inches(11.3), Inches(1.6))
    title_frame = title_box.text_frame
    title_frame.word_wrap = True
    _paragraph(title_frame.paragraphs[0], first.title, is_rtl(first.title), PP_ALIGN.CENTER)
    for run in title_frame.paragraphs[0].runs:
        _style_run(run, 40, True, ACCENT)

    sub_box = title_slide.shapes.add_textbox(Inches(1.5), Inches(4.1), Inches(10.3), Inches(2.0))
    sub_frame = sub_box.text_frame
    sub_frame.word_wrap = True
    for index, bullet in enumerate(first.bullets):
        paragraph = sub_frame.paragraphs[0] if index == 0 else sub_frame.add_paragraph()
        _paragraph(paragraph, bullet, is_rtl(bullet), PP_ALIGN.CENTER)
        for run in paragraph.runs:
            _style_run(run, 20, False, MUTED)

    for item in data.slides[1:]:
        slide = prs.slides.add_slide(blank)
        header_box = slide.shapes.add_textbox(Inches(0.7), Inches(0.45), Inches(12.0), Inches(1.1))
        header_frame = header_box.text_frame
        header_frame.word_wrap = True
        header_rtl = is_rtl(item.title)
        _paragraph(
            header_frame.paragraphs[0],
            item.title,
            header_rtl,
            PP_ALIGN.RIGHT if header_rtl else PP_ALIGN.LEFT,
        )
        for run in header_frame.paragraphs[0].runs:
            _style_run(run, 28, True, ACCENT)

        size = _fit_size(item.bullets)
        body_box = slide.shapes.add_textbox(Inches(0.9), Inches(1.7), Inches(11.5), Inches(5.2))
        body_frame = body_box.text_frame
        body_frame.word_wrap = True
        for index, bullet in enumerate(item.bullets):
            paragraph = body_frame.paragraphs[0] if index == 0 else body_frame.add_paragraph()
            rtl = is_rtl(bullet)
            _paragraph(paragraph, bullet, rtl, PP_ALIGN.RIGHT if rtl else PP_ALIGN.LEFT)
            paragraph.space_after = Pt(10)
            for run in paragraph.runs:
                _style_run(run, size, False, DARK)

    buffer = BytesIO()
    prs.save(buffer)
    return buffer.getvalue()
