"""Inspect real PDF page transitions, glyph positions and literal source retention."""

from io import BytesIO

import pdfplumber
import pytest

from app.builders import pdf
from app.builders.schema import Document, Section
from tests.pdf_pagination_fixtures import boundary_document


@pytest.fixture(autouse=True)
def database():
    yield


def page_chars(page):
    return "".join(char["text"] for char in page.chars)


@pytest.mark.parametrize("lang", ["ar", "en"])
@pytest.mark.parametrize("body", ["paragraph", "bullet"])
@pytest.mark.parametrize("blank", [False, True])
def test_section_heading_stays_with_first_content_on_page_boundary(lang, body, blank):
    data = boundary_document(lang, body=body, blank=blank)
    original = data.model_dump_json()
    with pdfplumber.open(BytesIO(pdf.build(data))) as document:
        assert len(document.pages) == 2
        heading_pages = [i for i, page in enumerate(document.pages) if "00123" in page_chars(page)]
        content_pages = [i for i, page in enumerate(document.pages) if "125.50" in page_chars(page)]
        assert heading_pages == content_pages == [1]
        chars = "".join(page_chars(page) for page in document.pages)
        assert chars.count("00123") == chars.count("125.50") == 1
        assert all(f"Record {i:02d} retained." in chars for i in range(20))
    assert data.model_dump_json() == original


@pytest.mark.parametrize("lang", ["ar", "en"])
def test_wrapped_heading_lines_stay_with_first_body_line(lang):
    data = boundary_document(lang, wrapped=True)
    with pdfplumber.open(BytesIO(pdf.build(data))) as document:
        assert len(document.pages) == 2
        assert "00123" not in page_chars(document.pages[0])
        second = page_chars(document.pages[1])
        assert "00123" in second and "125.50" in second
        heading_size = [
            char for page in document.pages for char in page.chars if char["size"] == 14
        ]
        assert heading_size
        assert all(char in document.pages[1].chars for char in heading_size)


@pytest.mark.parametrize("lang", ["ar", "en"])
def test_heading_does_not_force_an_entire_long_section_onto_one_page(lang):
    data = boundary_document(lang)
    data.sections[-1].paragraphs.extend(f"Body row {i:03d} retained." for i in range(80))
    with pdfplumber.open(BytesIO(pdf.build(data))) as document:
        assert len(document.pages) >= 5
        texts = [page_chars(page) for page in document.pages]
        assert "00123" in texts[1] and "125.50" in texts[1]
        assert all(f"Body row {i:03d} retained." in "".join(texts) for i in range(80))
        for page in document.pages:
            assert all(40 <= c["x0"] <= c["x1"] <= page.width - 40 for c in page.chars)
            assert all(40 <= c["top"] <= c["bottom"] <= page.height - 18 for c in page.chars)


def test_heading_only_section_and_large_leading_whitespace_still_render():
    data = Document(
        title="Source",
        sections=[
            Section(heading="Heading only 00123"),
            Section(heading="Blank source lines", paragraphs=["\n" * 90 + "Final 125.50"]),
        ],
    )
    with pdfplumber.open(BytesIO(pdf.build(data))) as document:
        chars = "".join(page_chars(page) for page in document.pages)
        assert "Heading only 00123" in chars and "Final 125.50" in chars
        assert len(document.pages) >= 3
