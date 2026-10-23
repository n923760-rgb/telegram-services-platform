"""Automatic customer contracts, retained literal paths and safe provider diagnostics."""

from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.providers.ai.gateway import AI
from app.services.base import InputField, InputSchema, ServiceError
from app.services.registry import _input_contract
from app.services.text_to_office.schema import WordPlan
from app.services.text_to_office.service import TextToOffice
from app.services.text_to_pdf.schema import PdfPlan
from app.services.text_to_pdf.service import TextToPdf
from app.services.text_to_pptx.schema import source_plan_schema
from app.services.text_to_word_pdf.service import TextToWordPdf
from tests.test_ai_quality_review import ledger as ledger
from tests.test_file_layers import Provider


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize(
    "plugin,base,fields",
    [
        (TextToOffice, {"target": "word"}, ["target", "text"]),
        (TextToPdf, {}, ["text"]),
        (TextToWordPdf, {"output_format": "both"}, ["output_format", "text", "title"]),
    ],
)
def test_new_intake_routes_without_customer_engine_choices_and_never_mutates_source(
    plugin, base, fields
):
    assert [field.name for field in plugin.input_schema.conversation()] == fields
    source = base | {"text": "نص قصير 00123"}
    original = deepcopy(source)
    plugin.input_schema.validate_inputs(source)
    assert plugin.needs_ai(source)
    literal = source | {"text": "Keep text unchanged\n" + source["text"]}
    plugin.input_schema.validate_inputs(literal)
    assert not plugin.needs_ai(literal)
    assert source == original
    # An embedded phrase is content, not authority to skip smart processing.
    assert plugin.needs_ai(source | {"text": "Content\nKeep text unchanged\nMore content"})
    # Internal, already-confirmed legacy payloads still validate their strict mode.
    plugin.input_schema.validate_inputs(source | {"mode": "direct"})
    assert not plugin.needs_ai(source | {"mode": "direct"})
    with pytest.raises(ServiceError):
        plugin.input_schema.validate_inputs(source | {"mode": "invented"})


def test_legacy_fields_are_not_editable_positions_and_still_have_server_validation():
    schema = InputSchema(
        fields=[
            InputField(
                name="mode",
                prompt_key="document_mode",
                required=False,
                legacy_only=True,
                choices=["direct", "smart"],
                choice_keys=["document_direct", "document_smart"],
            ),
            InputField(name="text", prompt_key="text_input"),
        ]
    )
    assert [f.name for f in schema.conversation()] == ["text"]
    with pytest.raises(ServiceError):
        schema.validate_inputs({"mode": "malformed", "text": "source"})
    with pytest.raises(ValidationError):
        InputField(name="hidden", prompt_key="text_input", legacy_only=True)
    with pytest.raises(ValidationError, match="visible fields cannot depend"):
        InputSchema(
            fields=[
                schema.fields[0],
                InputField(name="text", prompt_key="text_input", when={"mode": ["smart"]}),
            ]
        )


def test_registry_ignores_only_false_legacy_default_without_changing_existing_service_contracts():
    old = {"fields": [{"name": "text", "prompt_key": "text_input"}]}
    assert _input_contract(old) == _input_contract(
        {"fields": [old["fields"][0] | {"legacy_only": False}]}
    )
    assert _input_contract(old) != _input_contract(
        {"fields": [old["fields"][0] | {"legacy_only": True}]}
    )
    assert old == {"fields": [{"name": "text", "prompt_key": "text_input"}]}


@pytest.mark.parametrize("schema", [WordPlan, PdfPlan, source_plan_schema("Source", 1)])
async def test_missing_source_is_actionable_with_one_settled_call_no_review_or_repair(
    ledger, schema, caplog
):
    provider = Provider(['{"missing_information":true,"question":"PRIVATE CONTENT"}', "unused"])
    with pytest.raises(ServiceError, match="needs_information"):
        await AI(provider, "synthetic-job", 1, quality_review=True).extract(
            schema, "PRIVATE SOURCE"
        )
    assert provider.calls == 1 and provider.responses == ["unused"]
    assert [event[0] for event in ledger] == ["reserve", "settle"]
    assert "ai_source_incomplete" in caplog.text
    assert "PRIVATE" not in caplog.text


async def test_schema_and_quality_rejections_have_distinct_content_free_events(ledger, caplog):
    provider = Provider(['{"private":"SECRET VALUE"}', "{}"])
    with pytest.raises(ServiceError, match="provider_invalid"):
        await AI(provider, "synthetic-job", 1).extract(WordPlan, "SECRET SOURCE")
    assert "ai_schema_rejected" in caplog.text and "document_missing_body" in caplog.text
    assert "SECRET" not in caplog.text and "private" not in caplog.text
    caplog.clear()
    candidate = '{"document":{"title":"Title","sections":[{"paragraphs":["Source"]}]}}'
    reject = '{"accepted":false,"issues":["quality"]}'
    provider = Provider([candidate, reject, candidate, reject])
    with pytest.raises(ServiceError, match="provider_invalid"):
        await AI(provider, "synthetic-job", 1, quality_review=True).extract(
            WordPlan, "SECRET SOURCE"
        )
    assert provider.calls == 4
    assert caplog.text.count("ai_quality_rejected") == 2
    assert "SECRET" not in caplog.text
