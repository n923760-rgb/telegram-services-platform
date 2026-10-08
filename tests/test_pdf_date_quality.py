"""Source date order survives Arabic PDF shaping, wrapping and actual export."""

from io import BytesIO

import pdfplumber
import pytest

from app.builders import pdf
from app.builders.schema import Document, Section


@pytest.mark.parametrize(
    "date",
    ["2026-10-08", "2026/10/08", "08-10-2026", "08/10/2026", "٢٠٢٦-١٠-٠٨", "٠٨/١٠/٢٠٢٦"],
)
def test_pdf_date_tokens_keep_source_order_in_all_text_roles(date):
    text = f"الطلب 00123 بمبلغ 125.50 ريال، التاريخ {date}."
    data = Document(
        title=text,
        sections=[Section(heading=text, paragraphs=[text], bullets=[text])],
    )
    original = data.model_dump_json()
    visual = pdf.display(text)
    assert date in visual and "00123" in visual and "125.50" in visual
    assert not any(c in visual for c in "\u202d\u202c\u200e")
    content = pdf.build(data)
    assert data.model_dump_json() == original
    with pdfplumber.open(BytesIO(content)) as document:
        assert len(document.pages) == 1
        # Check the rendered character stream, rather than logical JSON alone.
        chars = "".join(c["text"] for c in document.pages[0].chars)
        assert chars.count(date) == 4
        assert chars.count("00123") == 4 and chars.count("125.50") == 4
        assert not any(c in chars for c in "\u202d\u202c\u200e")


def test_pdf_preserves_multiple_dates_and_escapes_markup_without_guessing():
    text = "الفترة من 2026-10-01 إلى 2026-10-08 والتسليم 02/10/2026 <b> & قيمة 0"
    visual = pdf.display(text)
    assert all(date in visual for date in ("2026-10-01", "2026-10-08", "02/10/2026"))
    assert "<" not in visual and ">" not in visual and "&amp;" in visual
    assert pdf.display("<b> & English") == "&lt;b&gt; &amp; English"
    assert "08-10-2026" not in visual
    # Preserve ambiguous source notation and English-only content verbatim.
    assert pdf.display("Date 08/10/2026. ID 00123, amount 125.50.") == (
        "Date 08/10/2026. ID 00123, amount 125.50."
    )


def test_pdf_wrapping_and_multipage_export_keep_dates_ids_and_page_bounds():
    lines = [
        f"الطلب {i:05d}: بتاريخ 2026-10-08 ومبلغ 125.50 ريال؛ ملاحظة المصدر محفوظة."
        for i in range(1, 81)
    ]
    data = Document(title="سجل الطلبات", sections=[Section(paragraphs=lines)])
    pdf._register_fonts()
    wrapped = pdf._wrap(" ".join(lines[:5]), "DejaVu", 11, 220)
    assert len(wrapped) > 5
    assert " ".join(wrapped) == " ".join(lines[:5])
    assert sum(pdf.display(line).count("2026-10-08") for line in wrapped) == 5
    with pdfplumber.open(BytesIO(pdf.build(data))) as document:
        assert len(document.pages) >= 3
        chars = "".join(c["text"] for page in document.pages for c in page.chars)
        assert chars.count("2026-10-08") == 80 and chars.count("125.50") == 80
        assert all(f"{i:05d}" in chars for i in range(1, 81))
        assert "00080" in "".join(c["text"] for c in document.pages[-1].chars)
        for page in document.pages:
            assert all(40 <= c["x0"] <= c["x1"] <= page.width - 40 for c in page.chars)
            assert all(40 <= c["top"] <= c["bottom"] <= page.height - 18 for c in page.chars)
