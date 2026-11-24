import json
from io import BytesIO
from types import SimpleNamespace

import pdfplumber
import pytest
from docx import Document
from docx.oxml.ns import qn
from reportlab.pdfgen.canvas import Canvas

from app.builders.word import build
from app.providers.documents.rendering import WordFiles
from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.cv_formatting.service import CvFormatting
from tests.cv_fixtures import inputs, planned
from tests.word_pdf_fixtures import renderer


@pytest.fixture(autouse=True)
def database():
    yield


def cv_pdf(lines):
    output = BytesIO()
    canvas = Canvas(output)
    for index, line in enumerate(lines):
        canvas.drawString(60, 780 - 18 * index, line)
    canvas.showPage()
    canvas.save()
    return output.getvalue()


@pytest.mark.parametrize("mode", ["edit_text", "edit_pdf"])
async def test_import_uses_owned_source_and_delivers_editable_cv(mode, tmp_path):
    storage = OwnedStorage(LocalStorage(tmp_path), 1)
    lines = ["Sam Example", "Skills", "Excel", "Contact: sample@example.invalid"]
    request = {"language": "en", "mode": mode}
    if mode == "edit_text":
        request["source_text"] = "\n".join(lines)
    else:
        request["source_pdf"] = storage.save("input.pdf", cv_pdf(lines), "application/pdf").key
    calls = []

    async def extract(schema, source, _prompt):
        calls.append(json.loads(source))
        if len(calls) == 1:
            assert calls[-1] == [lines[0], *lines[2:]]
            return schema.model_validate({"fields": ["full_name", "skills", "contact"]})
        segments = calls[-1]["segments"]
        assert {item["text"] for item in segments.values()} == set(lines[2:])
        return schema.model_validate(
            {
                "design": {"theme": "classic"},
                "section_order": ["summary", "skills"],
                "bodies": [
                    {
                        "language": "en",
                        "full_name": lines[0],
                        "summary": {
                            "text": "Knowledge of spreadsheets.",
                            "source_ids": ["skills:1"],
                        },
                        "segments": [
                            {"id": key, "text": item["text"], "presentation": "paragraph"}
                            for key, item in segments.items()
                        ],
                    }
                ],
            }
        )

    async def render(doc, *, include_title):
        return WordFiles(
            docx=build(doc, professional_template=True, include_title=include_title),
            pdf=cv_pdf(["PDF preview"]),
        )

    service = CvFormatting()
    service.runtime = SimpleNamespace(
        ai=SimpleNamespace(extract=extract),
        renderer=SimpleNamespace(word_pdf=render),
        storage=storage,
    )
    service.input_schema.validate_inputs(request)
    assert service.needs_ai(request)
    result = await service.run(request)
    assert [item.filename for item in result.artifacts] == ["cv.docx", "cv.pdf"]
    doc = Document(BytesIO(storage.read(result.artifacts[0].key)))
    assert [p.text for p in doc.paragraphs] == [
        lines[0],
        lines[-1],
        "Professional summary",
        "Knowledge of spreadsheets.",
        "Skills",
        "Excel",
    ]
    assert not doc.tables


async def test_unreadable_upload_is_rejected_before_provider(tmp_path):
    storage = OwnedStorage(LocalStorage(tmp_path), 1)
    file = storage.save("input.pdf", cv_pdf([]), "application/pdf")

    async def unexpected(*args):
        pytest.fail("unreadable input must not reach AI")

    service = CvFormatting()
    service.runtime = SimpleNamespace(ai=SimpleNamespace(extract=unexpected), storage=storage)
    with pytest.raises(ServiceError, match="cv_source_unreadable"):
        await service.run({"language": "en", "mode": "edit_pdf", "source_pdf": file.key})


async def test_split_cv_uses_editable_columns_and_one_rendered_page():
    source = inputs("ar") | {"language": "bilingual_split"}
    doc = planned(source)
    result = await renderer().word_pdf(doc)
    word = Document(BytesIO(result.docx))
    assert not word.tables
    assert word.sections[0]._sectPr.find(qn("w:cols")).get(qn("w:num")) == "2"
    with pdfplumber.open(BytesIO(result.pdf)) as pdf:
        assert len(pdf.pages) == 1
        page = pdf.pages[0]
        halves = [
            page.crop((0, 0, page.width / 2, page.height)),
            page.crop((page.width / 2, 0, page.width, page.height)),
        ]
        left, right = [half.extract_text() for half in halves]
        assert "Sam Example" in left and "Sam Example" not in right
        assert all("sample@example.invalid" in text for text in (left, right))
        assert "00017" in left and "00017" in right
