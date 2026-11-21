import shutil
import subprocess
from io import BytesIO

import pytest
from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from pypdf import PdfReader

from app.builders.direction import is_rtl
from app.builders.pptx import _reading_rtl, build
from app.builders.schema import Deck

TASK_ACTION = "سامي مسؤول عن إرسال التقرير 00017 والإيصال الناقص"


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize(
    "text,rtl",
    [
        ("تواصل: help@demo.invalid", True),
        ("راجع https://example.invalid/report", True),
        ("زر www.example.invalid", True),
        ("موعد 2026-10-18", True),
        ("عنوان عربي واضح", True),
        ("English source text مرحبا", False),
        ("Contact help@demo.invalid", False),
        ("help@demo.invalid", False),
        ("https://example.invalid/مسار/عربي/طويل", False),
        ("", False),
    ],
)
def test_identifiers_do_not_vote_as_prose_in_direction_detection(text, rtl):
    assert _reading_rtl(text) is rtl


@pytest.mark.parametrize("text", ["تواصل: help@demo.invalid", "زر www.example.invalid"])
def test_reproduced_dominant_contact_regression(text):
    assert not is_rtl(text) and _reading_rtl(text)


@pytest.mark.parametrize("contact", ["demo@example.invalid", "2026-10-24@e.invalid"])
def test_long_arabic_task_keeps_recipient_and_deadline_on_the_same_continuation(contact):
    deadline = f"إلى {contact} قبل 2026-11-18"
    short_bullet = f"أرسل إلى {contact} قبل 2026-11-18"
    task = f"{TASK_ACTION} {deadline}"
    data = Deck.model_validate(
        {"slides": [{"title": "المهمة التالية", "bullets": [task, short_bullet]}]}
    )
    deck = Presentation(BytesIO(build(data)))
    body = next(
        shape.text_frame for shape in deck.slides[0].shapes if shape.name == "Slide content"
    )
    long, short = body.paragraphs
    assert long.text.replace("\u200e", "") == f"{TASK_ACTION}\v{deadline}"
    assert short.text.replace("\u200e", "") == short_bullet
    assert long._p.pPr.get("rtl") == "1"
    assert long._p.pPr.find(qn("a:buChar")) is not None
    assert data.slides[0].bullets == [task, short_bullet]


def test_impress_renders_recipient_and_deadline_together_in_reading_order(tmp_path):
    soffice = shutil.which("soffice")
    if not soffice:
        pytest.skip("LibreOffice Impress is needed to verify the rendered slide")
    task = f"{TASK_ACTION} إلى demo@example.invalid قبل 2026-11-18"
    deck = Deck.model_validate({"slides": [{"title": "المهمة التالية", "bullets": [task]}]})
    source = tmp_path / "task.pptx"
    source.write_bytes(build(deck))
    subprocess.run(
        [
            soffice,
            f"-env:UserInstallation={(tmp_path / 'profile').as_uri()}",
            "--headless",
            "--convert-to",
            "pdf:impress_pdf_Export",
            "--outdir",
            str(tmp_path),
            str(source),
        ],
        check=True,
        capture_output=True,
        timeout=45,
    )
    pages = PdfReader(source.with_suffix(".pdf")).pages
    assert len(pages) == 1
    lines = pages[0].extract_text().splitlines()
    action_index = next(index for index, line in enumerate(lines) if "00017" in line)
    assert lines[action_index].endswith(TASK_ACTION)
    assert "".join(lines[action_index + 1].split()) == "إلىdemo@example.invalidقبل2026-11-18"


@pytest.mark.parametrize("cover", [False, True])
@pytest.mark.parametrize(
    "text,rtl",
    [
        ("تواصل: help@demo.invalid", True),
        ("زر www.example.invalid", True),
        ("Contact help@demo.invalid", False),
    ],
)
def test_native_titles_and_bullets_keep_text_and_use_correct_direction(cover, text, rtl):
    slides = [{"title": text, "bullets": [text]}]
    if cover:
        slides.append({"title": "Next", "bullets": ["Source text"]})
    data = Deck.model_validate({"slides": slides})
    deck = Presentation(BytesIO(build(data)))
    for name in ("Slide title", "Slide content"):
        frame = next(shape.text_frame for shape in deck.slides[0].shapes if shape.name == name)
        paragraph = frame.paragraphs[0]
        assert paragraph.text == text
        assert paragraph._p.pPr.get("rtl") == str(int(rtl))
        assert paragraph.alignment == (
            PP_ALIGN.CENTER if cover else PP_ALIGN.RIGHT if rtl else PP_ALIGN.LEFT
        )
        if name == "Slide content" and not cover:
            assert paragraph._p.pPr.get("marR" if rtl else "marL") is not None
    assert (
        next(shape.text for shape in deck.slides[0].shapes if shape.name == "Slide number")
        == f"1 / {len(slides)}"
    )
    assert data.slides[0].title == text and data.slides[0].bullets == [text]


def test_native_table_direction_is_per_prose_and_per_cell_with_exact_contacts():
    columns = ["مرجع: help@demo.invalid", "بيان"]
    rows = [
        ["للتواصل: help@demo.invalid", "Visit www.example.invalid"],
        ["help@demo.invalid", "English record"],
    ]
    deck = Presentation(
        BytesIO(
            build(
                Deck.model_validate(
                    {"slides": [{"title": "السجل", "table": {"columns": columns, "rows": rows}}]}
                )
            )
        )
    )
    table = next(shape.table for shape in deck.slides[0].shapes if shape.has_table)
    assert table._tbl.tblPr.get("rtl") == "0"
    assert [[cell.text for cell in row.cells] for row in table.rows] == [
        row[::-1] for row in [columns, *rows]
    ]
    for row, flags in zip(table.rows, [(1, 1), (0, 1), (0, 0)], strict=True):
        assert [cell.text_frame.paragraphs[0]._p.pPr.get("rtl") for cell in row.cells] == list(
            map(str, flags)
        )
