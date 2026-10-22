import json
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.ops.service_acceptance import DiagnosticAI
from app.providers.ai.validation import validation_categories
from app.services.base import ServiceError
from app.services.text_summary.prompt import SUMMARIZE
from app.services.text_summary.schema import Inputs, summary_schema


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize("length,limit", [("short", 3), ("standard", 7)])
@pytest.mark.parametrize("language", ["ar", "en"])
def test_provider_schema_and_runtime_share_selected_point_limit(length, limit, language):
    values = Inputs(text="Background", length=length, language=language)
    schema = summary_schema(values)
    before = schema.model_json_schema()
    assert before["properties"]["points"]["maxItems"] == limit
    assert before["properties"]["points"]["minItems"] == 1
    at_limit = {"points": [{"text": chr(65 + n), "source_ids": [1]} for n in range(limit)]}
    assert len(schema.model_validate(at_limit).points) == limit
    for count in (limit + 1, 9):
        with pytest.raises(ValidationError) as caught:
            schema.model_validate_json(
                json.dumps(
                    {"points": [{"text": chr(65 + n), "source_ids": [1]} for n in range(count)]}
                )
            )
        assert validation_categories(schema, caught.value) == ["summary_point_limit"]
    assert schema.model_json_schema() == before


def test_generated_schema_classes_do_not_share_the_previous_request_limit():
    for length, limit in [("short", 3), ("standard", 7), ("short", 3)]:
        schema = summary_schema(Inputs(text="Source", length=length, language="en"))
        assert schema.model_json_schema()["properties"]["points"]["maxItems"] == limit


@pytest.mark.parametrize("length,limit", [("short", 3), ("standard", 7)])
@pytest.mark.parametrize("repair_succeeds", [True, False])
async def test_actual_gateway_sends_same_selected_bound_on_generation_and_one_repair(
    monkeypatch, length, limit, repair_succeeds
):
    from app.providers.ai import gateway
    from app.providers.ai.base import AIResponse, Usage

    class Provider:
        calls = 0

        def __init__(self):
            self.schemas = []
            self.inputs = []

        def upper_bound(self, schema, *args):
            self.schemas.append(schema)
            return Decimal(".01")

        async def extract_from_text(self, schema, source, *args):
            self.calls += 1
            self.inputs.append(source)
            if schema.get("title") == "QualityReview":
                content = {"accepted": True, "issues": []}
            else:
                count = 1 if repair_succeeds and self.calls == 2 else limit + 1
                content = {
                    "points": [{"text": chr(65 + n), "source_ids": [1]} for n in range(count)]
                }
            return AIResponse(json.dumps(content), Usage(1, 2, Decimal(".001")))

    reserved, settled = [], []

    async def reserve(*args):
        reserved.append(args)
        return len(reserved)

    async def settle(*args, **kwargs):
        settled.append(args)

    monkeypatch.setattr(gateway, "reserve_call", reserve)
    monkeypatch.setattr(gateway, "settle_call", settle)
    values = Inputs(text="Private source", length=length, language="en")
    provider, events = Provider(), []
    ai = DiagnosticAI(provider, 1, 1, quality_review=True, diagnostics=events)
    prompt = SUMMARIZE.format(limit=limit, language=values.language)
    if repair_succeeds:
        assert len((await ai.extract(summary_schema(values), values.source(), prompt)).points) == 1
    else:
        with pytest.raises(ServiceError, match="provider_invalid"):
            await ai.extract(summary_schema(values), values.source(), prompt)
    assert provider.calls == len(reserved) == len(settled) == (3 if repair_succeeds else 2)
    assert all(s["properties"]["points"]["maxItems"] == limit for s in provider.schemas[:2])
    assert json.loads(provider.inputs[1])["validation_categories"] == ["summary_point_limit"]
    assert events[0]["categories"] == ["summary_point_limit"]
    assert "Private source" not in json.dumps(events)
