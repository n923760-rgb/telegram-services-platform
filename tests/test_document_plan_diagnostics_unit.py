"""Safe isolated diagnosis preserves the same rejection and repair boundaries."""

import json
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.ops.service_acceptance import DiagnosticAI
from app.providers.ai import gateway
from app.providers.ai.base import AIResponse, Usage
from app.services.base import ServiceError
from app.services.document_fidelity import source_document_schema
from app.services.text_to_office.schema import WordPlan
from app.services.text_to_pdf.schema import PdfPlan
from app.services.text_to_pptx.schema import source_plan_schema


@pytest.fixture(autouse=True)
def database():
    yield


SOURCE = "Private note 00123 contact@example.invalid"


def document_payload(text=SOURCE):
    return {"document": {"title": "Note", "sections": [{"paragraphs": [text]}]}}


def deck_payload(text=SOURCE):
    return {"deck": {"slides": [{"title": "Note", "bullets": [text]}]}}


def failures():
    for kind in (WordPlan, PdfPlan):
        schema = source_document_schema(kind, SOURCE)
        yield schema, {}, "document_missing_body"
        yield schema, document_payload() | {"ambiguous": True}, "document_missing_question"
        yield schema, document_payload(SOURCE + " 99999"), "document_source_tokens"
    schema = source_plan_schema(SOURCE, 1)
    yield schema, {}, "pptx_missing_deck"
    yield schema, deck_payload() | {"ambiguous": True}, "pptx_missing_question"
    yield schema, deck_payload(SOURCE + " 99999"), "pptx_source_tokens"
    yield source_plan_schema(SOURCE, 3), deck_payload(), "pptx_slide_count"
    yield (
        source_document_schema(PdfPlan, SOURCE),
        document_payload(SOURCE + "\x00"),
        "document_invalid_text",
    )


class Provider:
    def __init__(self, payload):
        self.payload = payload
        self.calls = 0
        self.schemas = []

    def upper_bound(self, schema, *args):
        self.schemas.append(schema)
        return Decimal(".01")

    async def extract_from_text(self, *args):
        self.calls += 1
        return AIResponse(json.dumps(self.payload), Usage(1, 2, Decimal(".001")))


@pytest.mark.parametrize("schema,payload,code", list(failures()))
async def test_fixed_rejection_code_reaches_acceptance_without_content_or_extra_calls(
    monkeypatch, schema, payload, code
):
    with pytest.raises(ValidationError) as rejected:
        schema.model_validate(payload)
    assert code in {error["type"] for error in rejected.value.errors()}
    reserve = AsyncMock(return_value=1)
    settle = AsyncMock()
    monkeypatch.setattr(gateway, "reserve_call", reserve)
    monkeypatch.setattr(gateway, "settle_call", settle)
    provider, events = Provider(payload), []
    ai = DiagnosticAI(provider, 1, 1, quality_review=True, diagnostics=events)
    with pytest.raises(ServiceError, match="provider_invalid"):
        await ai.extract(schema, SOURCE)
    assert provider.calls == reserve.await_count == settle.await_count == 2
    assert [event["categories"] for event in events] == [[code], [code]]
    assert all(event["stage"] == "generation" for event in events)
    assert "diagnostic_categories" not in str(provider.schemas)
    for private in (SOURCE, "99999", "contact@example.invalid", "Private note"):
        assert private not in json.dumps(events)


@pytest.mark.parametrize("kind", [WordPlan, PdfPlan])
def test_schema_explains_existing_output_rules_without_rejecting_short_or_missing_content(kind):
    schema = source_document_schema(kind, SOURCE)
    shape = schema.model_json_schema()["properties"]
    assert "essential source facts" in shape["missing_information"]["description"]
    assert "unless missing_information" in shape["document"]["description"]
    assert "ambiguous" in shape["question"]["description"]
    assert schema.model_validate(document_payload()).document is not None
    assert schema.model_validate({"missing_information": True}).document is None
    assert SOURCE not in str(shape)


@pytest.mark.parametrize("schema", [PdfPlan, WordPlan, source_plan_schema(SOURCE, 1)])
async def test_valid_missing_information_is_observable_without_clarification_content(
    monkeypatch, schema
):
    monkeypatch.setattr(gateway, "reserve_call", AsyncMock(return_value=1))
    monkeypatch.setattr(gateway, "settle_call", AsyncMock())
    events = []
    ai = DiagnosticAI(
        Provider({"missing_information": True, "question": "Private clarification"}),
        1,
        1,
        diagnostics=events,
    )
    assert (await ai._extract(schema, SOURCE)).missing_information
    assert events == [
        {
            "call": 1,
            "stage": "generation",
            "outcome": "valid",
            "missing_information": True,
            "ambiguous": False,
        }
    ]
