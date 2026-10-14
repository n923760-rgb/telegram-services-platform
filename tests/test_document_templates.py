from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock
from zipfile import ZipFile

import pytest
from docx import Document
from docx.oxml.ns import qn

from app.builders import word
from app.builders.quality import ROOTS, validate
from app.builders.word_schema import WordDocument
from app.services.text_to_office.schema import WordPlan
from app.services.text_to_office.service import TextToOffice


def plan(title="تقرير الطلبات"):
    return WordDocument.model_validate(
        {
            "title": title,
            "sections": [
                {
                    "heading": "الطلبات",
                    "paragraphs": ["الطلب 00123 بتاريخ 2026-10-09 وقيمته 125.50 ريال"],
                    "tables": [
                        {"caption": "السجل", "columns": ["الرقم"], "rows": [["00123"]]},
                        {"columns": ["الرقم"], "rows": [["00124"]]},
                    ],
                },
                {"heading": "Follow up", "bullets": ["Keep all identifiers"]},
            ],
        }
    )


def test_template_escapes_customer_values_and_preserves_native_order_and_dates():
    title = "تقرير <tag> & {{ 7 * 7 }} {% if True %}"
    doc = Document(BytesIO(word.build(plan(title), professional_template=True, format_dates=True)))
    assert doc.paragraphs[0].text == title
    assert [t.cell(1, 0).text for t in doc.tables] == ["00123", "00124"]
    children = list(doc.element.body)
    assert children.index(doc.tables[1]._tbl) < children.index(doc.paragraphs[-2]._p)
    assert doc.tables[0]._tbl.getnext().tag == qn("w:p")  # separate native tables
    assert "\u200e2026-10-09\u200e" in doc.paragraphs[2].text
    assert doc.paragraphs[-1].style.name == "List Bullet"
    assert doc.paragraphs[0].style.name == "Title"
    assert children[-2] == doc.paragraphs[-1]._p  # no trailing template control paragraph
    assert "PAGE" in doc.sections[0].footer.paragraphs[0]._p.xml
    assert "w:pBdr" not in doc.styles["Title"].element.xml


def test_parallel_template_requests_do_not_share_customer_content():
    def render(index):
        doc = Document(BytesIO(word.build(plan(f"Customer {index}"), professional_template=True)))
        return doc.paragraphs[0].text

    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(render, range(12))) == [f"Customer {i}" for i in range(12)]


def test_template_table_only_and_hidden_title_have_no_terminal_blank_paragraph():
    value = WordDocument(title="Hidden", sections=[{"tables": plan().sections[0].tables}])
    doc = Document(BytesIO(word.build(value, professional_template=True, include_title=False)))
    assert len(doc.tables) == 2
    assert [p.text for p in doc.paragraphs] == ["السجل", ""]
    assert doc.element.body[-2].tag == qn("w:tbl")


@pytest.mark.parametrize("kind", ["docx", "xlsx", "pptx", "pdf"])
def test_structural_gate_rejects_truncated_output(kind):
    with pytest.raises(ValueError):
        validate(b"corrupt file", kind)


@pytest.mark.parametrize("kind", ["docx", "xlsx", "pptx"])
@pytest.mark.parametrize("defect", ["missing_part", "malformed_xml", "wrong_root"])
def test_structural_gate_rejects_broken_office_packages(kind, defect):
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("_rels/.rels", "<Relationships/>")
        if defect != "missing_part":
            archive.writestr(ROOTS[kind][0], "<broken" if defect == "malformed_xml" else "<wrong/>")
    with pytest.raises(ValueError, match="structural validation"):
        validate(buffer.getvalue(), kind)


async def test_template_service_requires_one_plan_and_checks_file_before_storage():
    service = TextToOffice()
    ai = SimpleNamespace(extract=AsyncMock(return_value=WordPlan(document=plan())))
    storage = SimpleNamespace(save=lambda *args: (_ for _ in ()).throw(AssertionError()))
    service.runtime = SimpleNamespace(ai=ai, storage=storage)
    # Prove the rendered result reaches storage only after passing the gate.
    seen = []

    def save(name, content, mime):
        assert validate(content, "docx") is content
        seen.append(Document(BytesIO(content)).paragraphs[0].text)
        from app.services.base import Artifact

        return Artifact(key="1/" + "a" * 32 + "/result.docx", filename=name, mime=mime)

    storage.save = save
    await service.run({"text": "00123 2026-10-09 125.50 00123 00124", "target": "word"})
    ai.extract.assert_awaited_once()
    assert seen == ["تقرير الطلبات"]


@pytest.mark.parametrize("template", [False, True])
def test_named_design_mixed_blocks_and_section_alignment_preserve_order(template):
    value = WordDocument.model_validate(
        {
            "title": "العربية",
            "layout": "resume",
            "design": {"theme": "classic", "density": "comfortable"},
            "sections": [
                {
                    "alignment": "right",
                    "heading": "التعليم",
                    "blocks": [
                        {"text": "دبلوم إدارة", "kind": "lead"},
                        {"text": "2023", "kind": "paragraph"},
                        {"text": "مهمة فعلية 00123", "kind": "bullet"},
                    ],
                },
                {
                    "title": "English",
                    "page_break_before": True,
                    "alignment": "left",
                    "blocks": [
                        {"text": "Diploma", "kind": "lead"},
                        {"text": "2023", "kind": "paragraph"},
                    ],
                },
            ],
        }
    )
    doc = Document(BytesIO(word.build(value, professional_template=template)))
    assert [p.text for p in doc.paragraphs] == [
        "العربية",
        "التعليم",
        "دبلوم إدارة",
        "2023",
        "مهمة فعلية 00123",
        "English",
        "Diploma",
        "2023",
    ]
    assert [p.style.name for p in doc.paragraphs[2:5]] == ["Heading 2", "Normal", "List Bullet"]
    assert doc.paragraphs[3]._p.pPr.find(qn("w:jc")).get(qn("w:val")) == "end"
    assert doc.paragraphs[3]._p.pPr.find(qn("w:bidi")).get(qn("w:val")) == "0"
    assert doc.paragraphs[5].paragraph_format.page_break_before
    assert doc.paragraphs[7]._p.pPr.find(qn("w:jc")).get(qn("w:val")) == "start"
    assert doc.styles["Subtitle"].element.rPr.find(qn("w:iCs")).get(qn("w:val")) == "0"


@pytest.mark.parametrize(
    "patch",
    [
        {"design": {"theme": "/tmp/arbitrary-font"}},
        {"sections": [{"heading": "Section", "blocks": [{"text": "invalid\x00"}]}]},
        {"sections": [{"page_break_before": True, "paragraphs": ["untitled"]}]},
        {"sections": [{"heading": "Section", "blocks": [{"text": "data", "kind": "execute"}]}]},
    ],
)
def test_word_design_and_blocks_reject_executable_or_invalid_shapes(patch):
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        WordDocument.model_validate(plan().model_dump() | patch)
