"""Sparse PDF input is complete conversion input, not missing authoring context."""

import json
from io import BytesIO

import pytest
from docx import Document
from pydantic import ValidationError

from app.ops.acceptance_cases import source_pdf
from app.ops.service_acceptance import DiagnosticAI
from app.services.base import ServiceError
from app.services.pdf_to_word.schema import source_plan_schema
from app.services.pdf_to_word.test_service import configured_service
from tests.test_schema_repair_context_unit import Provider
from tests.test_schema_repair_context_unit import ledger as ledger


@pytest.fixture(autouse=True)
def database():
    yield


def plan(source):
    return {"document": {"title": "Document", "sections": [{"paragraphs": [source]}]}}


@pytest.mark.parametrize(
    "source",
    [
        "ID\nAmount\n00123\n125.50\n00017\n0",
        "سجل ٠٠١٢٣\nالمبلغ ١٢٥٫٥٠",
        "Partial note, owner unspecified.",
        "Account 00123\nContact a12@example.invalid\nhttps://demo.invalid،",
    ],
)
def test_sparse_notes_table_values_and_contacts_are_valid_conversion_input(source):
    schema = source_plan_schema(source)
    result = schema.model_validate(plan(source))
    assert schema.model_validate(result.model_dump(mode="json")) == result
    assert source not in json.dumps(schema.model_json_schema(), ensure_ascii=False)
    shape = schema.model_json_schema()
    assert "document" in shape["required"]
    assert "$ref" in shape["properties"]["document"]


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"document": None},
        {"missing_information": True},
        {"missing_information": True, **plan("Order 00123")},
    ],
)
def test_missing_body_disposition_is_rejected_with_a_fixed_content_free_category(data):
    schema = source_plan_schema("Order 00123")
    with pytest.raises(ValidationError) as error:
        schema.model_validate(data)
    items = error.value.errors(include_input=False, include_context=False)
    assert {item["type"] for item in items} == {"pdf_word_missing_body"}
    assert "00123" not in json.dumps(items)


@pytest.mark.parametrize("recover", [True, False])
async def test_live_path_shape_repairs_refusal_before_review_and_writes_only_valid_docx(
    tmp_path, ledger, recover
):
    from pypdf import PdfReader

    original = source_pdf()
    source = PdfReader(BytesIO(original)).pages[0].extract_text().strip()
    bad = '{"missing_information":true}'
    responses = (
        [bad, json.dumps(plan(source)), '{"accepted":true,"issues":[]}'] if recover else [bad, bad]
    )
    provider = Provider(responses)
    events = []
    service, artifact, store, _ = configured_service(tmp_path, original)
    service.runtime.ai = DiagnosticAI(provider, 1, 1, quality_review=True, diagnostics=events)
    if recover:
        result = await service.run({"pdf": artifact.key})
        document = Document(BytesIO(store.read(result.artifacts[0].key)))
        text = "\n".join(p.text for p in document.paragraphs)
        assert all(text.count(value) == 1 for value in ("00123", "125.50", "00017"))
        assert store.storage.usage(1)[1] == 2
        assert events[-1]["stage"] == "review" and events[-1]["accepted"]
    else:
        with pytest.raises(ServiceError, match="provider_invalid"):
            await service.run({"pdf": artifact.key})
        assert store.storage.usage(1)[1] == 1
        assert all(event["stage"] == "generation" for event in events)
    assert events[0]["categories"] == ["pdf_word_missing_body"]
    calls = 3 if recover else 2
    reserve, settle, uncertain = ledger
    assert provider.calls == reserve.await_count == settle.await_count == calls
    uncertain.assert_not_awaited()
    assert "00123" not in json.dumps(events)
    repair = json.loads(provider.requests[1][0])
    assert repair["validation_categories"] == ["pdf_word_missing_body"]
    assert repair["invalid_candidate"] == bad
