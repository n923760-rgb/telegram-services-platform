import re
from io import BytesIO
from types import SimpleNamespace

import pdfplumber
import pytest
from docx import Document
from docx.oxml.ns import qn
from pypdf import PdfReader

from app.builders.word import build
from app.providers.documents.base import DocumentError
from app.providers.documents.rendering import WordFiles
from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.cv_formatting.schema import Inputs
from app.services.cv_formatting.service import CvFormatting
from tests.cv_fixtures import inputs
from tests.word_pdf_fixtures import renderer


@pytest.mark.parametrize("language", ["ar", "en"])
def test_cv_preserves_each_field_omits_empty_sections_and_remains_editable(language):
    source = inputs(language)
    source.pop("summary")
    source["skills"] = "  Excel  \n\n{{ 7 * 7 }} <tag> & {% if True %}"
    CvFormatting.input_schema.validate_inputs(source)
    assert not CvFormatting.needs_ai(source)
    plan = Inputs.parse(source).document()
    doc = Document(BytesIO(build(plan, professional_template=True, format_dates=True)))
    assert not doc.tables and doc.paragraphs[0].text == source["full_name"]
    content = [p.text.replace("\u200e", "") for p in doc.paragraphs]
    for name in ("contact", "experience", "education", "skills", "additional"):
        for line in source[name].split("\n"):
            assert line in content
    assert "نبذة مهنية" not in content and "Professional summary" not in content
    assert doc.paragraphs[1].text.startswith("0500123456")


@pytest.mark.parametrize(
    "patch",
    [
        {"full_name": "\nInvalid"},
        {"contact": "\x00"},
        {"skills": "   "},
        {"experience": None, "education": None},
        {"language": "bilingual"},
        {"summary": "x" * 1001},
        {"skills": "line\n" * 101},
        {"unexpected": "ignored?"},
        {"text": "not CV input"},
        {
            "experience": "x" * 4000,
            "education": "x" * 2000,
            "skills": "x" * 1500,
            "additional": "x" * 1500,
            "summary": "x" * 1000,
        },
    ],
)
def test_invalid_cv_is_rejected_before_reservation(patch):
    with pytest.raises(ServiceError, match="input_invalid"):
        CvFormatting.needs_ai(inputs() | patch)


def test_entry_level_cv_requires_no_invented_experience():
    source = inputs()
    source.pop("experience")
    plan = Inputs.parse(source).document()
    assert all(section.heading != "الخبرات العملية" for section in plan.sections)
    assert any(section.heading == "التعليم" for section in plan.sections)


@pytest.mark.parametrize("language", ["ar", "en"])
async def test_actual_cv_native_pdf_has_readable_bounds_and_preserves_contacts_dates(language):
    result = await renderer().word_pdf(Inputs.parse(inputs(language)).document())
    pages = PdfReader(BytesIO(result.pdf)).pages
    assert len(pages) == 1
    text = pages[0].extract_text()
    for token in (
        "0500123456",
        "sample@example.invalid",
        "2024-01-09",
        "2026-10-09",
        "00123",
        "125.50",
        "00017",
    ):
        assert len(re.findall(r"(?<!\d)" + re.escape(token) + r"(?!\d)", text)) == 1
    with pdfplumber.open(BytesIO(result.pdf)) as pdf:
        assert all(
            0 <= char["x0"] < char["x1"] <= pdf.pages[0].width for char in pdf.pages[0].chars
        )


@pytest.mark.parametrize("language", ["ar", "en"])
def test_cv_document_edge_keeps_numeric_and_arabic_script_directions(language):
    plan = Inputs.parse(inputs(language)).document()
    doc = Document(BytesIO(build(plan, professional_template=True)))
    contact = doc.paragraphs[1]._p.pPr
    assert contact.find(qn("w:bidi")).get(qn("w:val")) == "0"
    assert contact.find(qn("w:jc")).get(qn("w:val")) == ("end" if language == "ar" else "start")
    title = doc.paragraphs[0]._p.pPr
    assert title.find(qn("w:bidi")).get(qn("w:val")) == ("1" if language == "ar" else "0")
    assert title.find(qn("w:jc")).get(qn("w:val")) == "start"


async def test_long_cv_retains_every_record_and_wraps_across_pages():
    source = inputs("en")
    source["experience"] = "\n".join(
        f"Record {index:05d} | milestone 2026-10-09" for index in range(100, 190)
    )
    result = await renderer().word_pdf(Inputs.parse(source).document())
    pages = PdfReader(BytesIO(result.pdf)).pages
    assert 2 <= len(pages) <= 5
    text = "\n".join(page.extract_text() for page in pages)
    assert all(
        len(re.findall(r"(?<!\d)" + f"{index:05d}" + r"(?!\d)", text)) == 1
        for index in range(100, 190)
    )
    with pdfplumber.open(BytesIO(result.pdf)) as pdf:
        for page in pdf.pages:
            assert all(
                0 <= char["x0"] < char["x1"] <= page.width
                and 0 <= char["top"] < char["bottom"] <= page.height
                for char in page.chars
            )


async def test_cv_uses_owned_storage_and_partial_save_cleanup(tmp_path, monkeypatch):
    class Renderer:
        async def word_pdf(self, document, **kwargs):
            return WordFiles(b"word", b"pdf")

    storage = OwnedStorage(LocalStorage(tmp_path), 1)
    service = CvFormatting()
    service.runtime = SimpleNamespace(storage=storage, renderer=Renderer(), ai=None)
    result = await service.run(inputs())
    assert [artifact.filename for artifact in result.artifacts] == ["cv.docx", "cv.pdf"]
    for artifact in result.artifacts:
        with pytest.raises(ServiceError, match="not_allowed"):
            LocalStorage(tmp_path).read(artifact.key, 2)
        storage.delete(artifact.key)
    original = storage.save

    def save(filename, *args):
        if filename.endswith(".pdf"):
            raise ServiceError("storage_quota")
        return original(filename, *args)

    monkeypatch.setattr(storage, "save", save)
    with pytest.raises(ServiceError, match="storage_quota"):
        await service.run(inputs())
    assert not list(tmp_path.glob("[0-9]*/*/*"))


async def test_cv_render_failure_does_not_save_files(tmp_path):
    class Renderer:
        async def word_pdf(self, *args, **kwargs):
            raise DocumentError("document_render_timeout")

    service = CvFormatting()
    service.runtime = SimpleNamespace(
        storage=OwnedStorage(LocalStorage(tmp_path), 1), renderer=Renderer(), ai=None
    )
    with pytest.raises(ServiceError, match="document_render_timeout"):
        await service.run(inputs())
    assert not list(tmp_path.glob("[0-9]*/*/*"))
