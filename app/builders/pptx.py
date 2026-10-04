from io import BytesIO

from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from app.builders.schema import Deck
from app.builders.word import safe_text


def format_paragraph(p, size):
    p.alignment = PP_ALIGN.RIGHT
    p._p.get_or_add_pPr().set("rtl", "1")
    for run in p.runs:
        run.font.name = "DejaVu Sans"
        run.font.size = Pt(size)


def build(data: Deck) -> bytes:
    data = Deck.model_validate(data)
    presentation = Presentation()
    presentation.slide_width = Inches(13.333)
    presentation.slide_height = Inches(7.5)
    for item in data.slides:
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        title = slide.shapes.add_textbox(
            Inches(0.6), Inches(0.4), Inches(12), Inches(1.2)
        ).text_frame
        title.word_wrap = True
        title.paragraphs[0].text = safe_text(item.title)
        format_paragraph(title.paragraphs[0], 28)
        body = slide.shapes.add_textbox(
            Inches(0.8), Inches(1.8), Inches(11.7), Inches(5.1)
        ).text_frame
        body.word_wrap = True
        for i, bullet in enumerate(item.bullets):
            p = body.paragraphs[0] if i == 0 else body.add_paragraph()
            p.text = safe_text(bullet)
            format_paragraph(p, 20)
    buffer = BytesIO()
    presentation.save(buffer)
    return buffer.getvalue()
