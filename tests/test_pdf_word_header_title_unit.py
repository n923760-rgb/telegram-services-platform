from io import BytesIO

import pytest
from docx import Document

from app.builders.word import build
from app.builders.word_schema import WordDocument
from app.services.pdf_to_word.layout import include_conversion_title


def plan(columns=("ID", "Amount", "Note")):
    return WordDocument(
        title=" ".join(columns),
        sections=[
            {"tables": [{"columns": list(columns), "rows": [["00123", "125.50", "Pending"]]}]}
        ],
    )


@pytest.mark.parametrize("columns", [("ID", "Amount", "Note"), ("رقم", "مبلغ", "بيان")])
def test_untitled_table_renders_cells_without_header_cover_title(columns):
    document = plan(columns)
    source = " ".join(columns) + "\n00123 125.50 Pending"
    snapshot = document.model_dump()
    include = include_conversion_title(document, source)
    assert include is False
    output = Document(BytesIO(build(document, include_title=include)))
    assert not [p.text for p in output.paragraphs if p.text]
    assert [[c.text for c in row.cells] for row in output.tables[0].rows] == [
        list(columns),
        ["00123", "125.50", "Pending"],
    ]
    assert document.model_dump() == snapshot


@pytest.mark.parametrize(
    "source",
    [
        "Report\nID Amount Note\n00123 125.50 Pending",
        "ID Amount Note\nID Amount Note\n00123 125.50 Pending",
    ],
)
def test_distinct_title_or_ambiguous_extraction_keeps_title(source):
    assert include_conversion_title(plan(), source)


@pytest.mark.parametrize(
    "change",
    [
        {"heading": "Overview"},
        {"paragraphs": ["Source note"]},
        {"title": "Report", "page_break_before": True},
    ],
)
def test_surrounding_content_keeps_title(change):
    document = plan()
    document.sections[0] = document.sections[0].model_copy(update=change)
    assert include_conversion_title(document, "ID Amount Note\n00123 125.50 Pending")


@pytest.mark.parametrize("header", ["2026", "demo@example.invalid"])
def test_protected_header_is_never_suppressed(header):
    document = plan((header, "Amount", "Note"))
    assert include_conversion_title(document, document.title + "\n00123 125.50 Pending")


def test_separate_extracted_header_and_cell_lines_are_recognized():
    assert not include_conversion_title(plan(), "ID\nAmount\nNote\n00123\n125.50\nPending")


async def test_service_suppresses_header_title_after_review_without_mutating_plan(tmp_path):
    from app.ops.acceptance_cases import source_pdf
    from app.services.pdf_to_word.schema import WordPlan
    from app.services.pdf_to_word.test_service import configured_service

    service, artifact, store, ai = configured_service(tmp_path, source_pdf())
    reviewed = WordPlan(
        document=WordDocument(
            title="ID Amount Note",
            sections=[
                {
                    "tables": [
                        {
                            "columns": ["ID", "Amount", "Note"],
                            "rows": [["00123", "125.50", "Example"], ["00017", "0", "Pending"]],
                        }
                    ]
                }
            ],
        )
    )
    ai.extract.return_value = reviewed
    snapshot = reviewed.model_dump()
    result = await service.run({"pdf": artifact.key})
    output = Document(BytesIO(store.read(result.artifacts[0].key)))
    assert not [p.text for p in output.paragraphs if p.text]
    assert [[c.text for c in row.cells] for row in output.tables[0].rows] == [
        ["ID", "Amount", "Note"],
        ["00123", "125.50", "Example"],
        ["00017", "0", "Pending"],
    ]
    assert reviewed.model_dump() == snapshot
    assert ai.extract.await_count == 1
