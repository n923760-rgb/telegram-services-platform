from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.services.base import ServiceError
from app.services.document_fidelity import source_document_schema
from app.services.text_to_office.schema import WordPlan
from app.services.text_to_office.service import TextToOffice
from app.services.text_to_pdf.schema import PdfPlan
from app.services.text_to_pdf.service import TextToPdf


@pytest.fixture(autouse=True)
def database():
    yield


SOURCE = (
    "طلب 00123 بقيمة 125.50 بتاريخ 2026-10-14\n+966500000001 a@example.com https://example.com/path"
)


def payload():
    return {"document": {"title": "مذكرة", "sections": [{"paragraphs": [SOURCE]}]}}


@pytest.mark.parametrize("kind", [WordPlan, PdfPlan])
@pytest.mark.parametrize(
    "old,new",
    [
        ("00123", "123"),
        ("125.50", "125.5"),
        ("2026-10-14", "14/10/2026"),
        ("+966500000001", "966500000001"),
        ("a@example.com", "b@example.com"),
        ("https://example.com/path", "https://example.com/other"),
        ("125.50", ""),
        ("00123", "00123 00123"),
    ],
)
def test_source_bound_document_rejects_changed_removed_or_repeated_tokens(kind, old, new):
    candidate = payload()
    candidate["document"]["sections"][0]["paragraphs"][0] = SOURCE.replace(old, new)
    with pytest.raises(ValidationError, match="preserve source"):
        source_document_schema(kind, SOURCE).model_validate(candidate)


@pytest.mark.parametrize(
    "field", ["title", "heading", "subtitle", "blocks", "caption", "columns", "rows"]
)
def test_every_visible_word_location_is_checked(field):
    candidate = payload()
    section = candidate["document"]["sections"][0]
    if field == "title":
        candidate["document"][field] = "Invoice 999"
    elif field in {"heading", "subtitle"}:
        section[field] = "Invoice 999"
    elif field == "blocks":
        section[field] = [{"text": "999"}]
    else:
        table = {"columns": ["Value"], "rows": [["Data"]]}
        table[field] = "999" if field == "caption" else ["999"] if field == "columns" else [["999"]]
        section["tables"] = [table]
    with pytest.raises(ValidationError, match="preserve source"):
        source_document_schema(WordPlan, SOURCE).model_validate(candidate)


def test_request_local_schema_has_no_source_values_and_accepts_structural_reordering():
    schema = source_document_schema(WordPlan, SOURCE)
    assert SOURCE not in str(schema.model_json_schema())
    candidate = payload()
    candidate["document"]["sections"] = [
        {
            "heading": "بيانات",
            "tables": [
                {
                    "columns": ["البيان", "القيمة"],
                    "rows": [
                        ["الطلب", "00123"],
                        ["القيمة", "125.50"],
                        ["التاريخ", "2026-10-14"],
                    ],
                }
            ],
            "blocks": [{"text": "+966500000001 a@example.com https://example.com/path"}],
        }
    ]
    assert schema.model_validate(candidate).document.title == "مذكرة"
    with pytest.raises(ValidationError):
        source_document_schema(WordPlan, "other 999").model_validate(candidate)


@pytest.mark.parametrize("kind", [WordPlan, PdfPlan])
def test_unicode_digits_signs_repetitions_and_adjacent_arabic_email_are_literal(kind):
    source = "٠٠١٢٣ -12.50 12.5% ٠٠١٢٣ للتواصل:a@example.com"
    candidate = payload()
    candidate["document"]["sections"][0]["paragraphs"] = [source]
    schema = source_document_schema(kind, source)
    assert schema.model_validate(candidate)
    candidate["document"]["sections"][0]["paragraphs"] = [source.replace("للتواصل:", "Email: ")]
    assert schema.model_validate(candidate)


@pytest.mark.parametrize("kind", [WordPlan, PdfPlan])
def test_missing_information_can_exit_without_inventing_document(kind):
    assert source_document_schema(kind, SOURCE).model_validate({"missing_information": True})


@pytest.mark.parametrize("service,kind", [(TextToOffice, WordPlan), (TextToPdf, PdfPlan)])
@pytest.mark.parametrize("continuation", [False, True])
async def test_injected_and_continued_output_checked_before_storage(service, kind, continuation):
    candidate = payload()
    candidate["document"]["title"] = "Invented 999"
    instance = service()
    save = AsyncMock(side_effect=AssertionError("must not write"))
    ai = SimpleNamespace(extract=AsyncMock(return_value=kind.model_validate(candidate)))
    instance.runtime = SimpleNamespace(ai=ai, storage=SimpleNamespace(save=save))
    inputs = {"text": SOURCE, "mode": "smart"}
    if service is TextToOffice:
        inputs["target"] = "word"
    if continuation:
        inputs["__continuation"] = deepcopy(candidate)
    with pytest.raises(ServiceError, match="provider_invalid"):
        await instance.run(inputs)
    assert not save.called
    assert ai.extract.await_count == (0 if continuation else 1)


@pytest.mark.parametrize("service", [TextToOffice, TextToPdf])
async def test_smart_document_without_provider_fails_safely(service):
    instance = service()
    instance.runtime = SimpleNamespace(ai=None)
    inputs = {"text": SOURCE, "mode": "smart"}
    if service is TextToOffice:
        inputs["target"] = "word"
    with pytest.raises(ServiceError, match="provider_config"):
        await instance.run(inputs)
