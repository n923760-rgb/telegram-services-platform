from io import BytesIO

from docx import Document as Word
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm
from openpyxl import load_workbook
from pptx import Presentation

from app.builders import excel, pdf, pptx, word
from app.builders.direction import has_arabic, is_rtl
from app.builders.schema import Deck, Document, Section, Slide, Table


def test_direction_detects_arabic_english_and_mixed():
    assert is_rtl("تقرير سنوي") is True
    assert is_rtl("Annual Report") is False
    assert is_rtl("Annual Report 2024") is False
    assert is_rtl("تقرير Q3 2024") is True
    assert has_arabic("hello مرحبا") is True
    assert has_arabic("hello") is False


def test_word_builds_rtl_and_ltr_with_professional_layout():
    data = Document(
        title="Annual Report",
        sections=[
            Section(heading="Overview", paragraphs=["English content only."]),
            Section(heading="الملخص", paragraphs=["محتوى عربي."], bullets=["نقطة عربية"]),
        ],
    )
    doc = Word(BytesIO(word.build(data)))
    by_text = {paragraph.text: paragraph.alignment for paragraph in doc.paragraphs}
    assert "English content only." in by_text
    assert "محتوى عربي." in by_text
    assert "نقطة عربية" in by_text
    assert by_text["Overview"] == WD_ALIGN_PARAGRAPH.LEFT
    assert by_text["الملخص"] == WD_ALIGN_PARAGRAPH.RIGHT
    assert abs(doc.sections[0].top_margin - Cm(2.2)) <= 635
    assert "PAGE" in doc.sections[0].footer.paragraphs[0]._p.xml


def test_excel_preserves_protection_and_adaptive_direction():
    table = Table(
        title="بيانات",
        columns=["الاسم", "القيمة"],
        rows=[["منتج", 12], ['=HYPERLINK("evil")', "00123"]],
    )
    sheet = load_workbook(BytesIO(excel.build(table))).active
    assert sheet.sheet_view.rightToLeft is True
    assert sheet["B2"].value == 12
    assert sheet["A3"].data_type == "s" and sheet["A3"].value.startswith("'")
    assert sheet["B3"].value == "00123"
    assert sheet.freeze_panes == "A2"
    assert sheet.auto_filter.ref == sheet.dimensions

    english = Table(title="Data", columns=["Name", "Value"], rows=[["Item", 1]])
    assert load_workbook(BytesIO(excel.build(english))).active.sheet_view.rightToLeft is False


def test_pptx_builds_title_slide_and_content_within_bounds():
    deck = Deck(
        slides=[
            Slide(title="تقرير", bullets=["نقطة أولى"]),
            Slide(title="الملخص", bullets=["نقطة ثانية"]),
        ]
    )
    prs = Presentation(BytesIO(pptx.build(deck)))
    assert len(prs.slides) == 2
    first = "\n".join(shape.text for shape in prs.slides[0].shapes if shape.has_text_frame)
    assert "تقرير" in first and "نقطة أولى" in first
    for slide in prs.slides:
        for shape in slide.shapes:
            assert shape.left + shape.width <= prs.slide_width
            assert shape.top + shape.height <= prs.slide_height


def test_pdf_mixed_content_and_page_numbers():
    import pdfplumber

    data = Document(title="تقرير Report", sections=[Section(paragraphs=["Arabic اختبار 123"] * 40)])
    with pdfplumber.open(BytesIO(pdf.build(data))) as doc:
        assert len(doc.pages) >= 2
        text = "".join(page.extract_text() or "" for page in doc.pages)
        assert "123" in text
