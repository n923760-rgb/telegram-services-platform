import json
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.ops.service_acceptance import DiagnosticAI
from app.providers.ai.validation import repair_input, validation_categories
from app.services.base import ServiceError
from app.services.text_summary.schema import Inputs, summary_schema


@pytest.fixture(autouse=True)
def database():
    yield


def values(text="Private source 00123 demo@example.invalid", length="short"):
    return Inputs(text=text, language="en", length=length)


def point(text="Private source 00123", ids=None):
    return {"text": text, "source_ids": [1] if ids is None else ids}


@pytest.mark.parametrize(
    "source,points,label",
    [
        (
            values(),
            [point("one"), point("two"), point("three"), point("four")],
            "summary_point_limit",
        ),
        (values(), [point(ids=[1, 1])], "summary_source_ids"),
        (values(), [point(ids=[2])], "summary_source_ids"),
        (values(), [point("00123\nprivate")], "summary_point_text"),
        (values(), [point(" 00123")], "summary_point_text"),
        (values(), [point("00123\x00")], "summary_point_text"),
        (values(), [point(), point()], "summary_duplicate_point"),
        (values(), [point("00124")], "summary_source_tokens"),
        (values(), [point("00123 00123")], "summary_source_tokens"),
        (values(), [point("other@example.invalid")], "summary_source_tokens"),
        (
            values("Private source", "standard"),
            [point(chr(97 + n) * 1100) for n in range(6)],
            "summary_output_limit",
        ),
        (values("private " * 40), [point("private " * 39 + "private")], "summary_not_shorter"),
    ],
)
def test_fixed_labels_identify_rejection_without_exposing_source_or_candidate(
    source, points, label
):
    schema = summary_schema(source)
    candidate = json.dumps({"points": points})
    with pytest.raises(ValidationError) as caught:
        schema.model_validate_json(candidate)
    labels = validation_categories(schema, caught.value)
    assert labels == [label]
    repair = json.loads(repair_input(schema, source.source(), candidate, caught.value))
    assert repair["validation_categories"] == labels
    # Only explicitly allowed fixed codes are diagnostic data, never exception text/context.
    assert set(labels).issubset(schema.diagnostic_categories)
    assert "Private source" not in json.dumps(labels) and "00123" not in json.dumps(labels)


def test_valid_payload_and_public_schema_use_the_selected_bound():
    schema = summary_schema(values())
    payload = {"points": [point()]}
    assert schema.model_validate(payload).model_dump() == payload
    public = schema.model_json_schema()
    assert set(public["properties"]) == {"points"}
    assert public["properties"]["points"]["maxItems"] == 3
    assert "diagnostic_categories" not in json.dumps(public)


@pytest.mark.parametrize("repair_succeeds", [True, False])
async def test_acceptance_diagnostics_keep_single_repair_and_no_raw_error_data(
    monkeypatch, repair_succeeds
):
    from app.providers.ai import gateway
    from app.providers.ai.base import AIResponse, Usage

    class Provider:
        calls = 0

        def upper_bound(self, *args):
            return Decimal(".01")

        async def extract_from_text(self, *args):
            self.calls += 1
            text = "00123" if repair_succeeds and self.calls == 2 else "PRIVATE 99999"
            return AIResponse(json.dumps({"points": [point(text)]}), Usage(1, 2, Decimal(".001")))

    reservations, settlements = [], []

    async def reserve(*args):
        reservations.append(args)
        return len(reservations)

    async def settle(*args, **kwargs):
        settlements.append(args)

    monkeypatch.setattr(gateway, "reserve_call", reserve)
    monkeypatch.setattr(gateway, "settle_call", settle)
    provider, events = Provider(), []
    ai = DiagnosticAI(provider, 1, 1, diagnostics=events)
    schema = summary_schema(values())
    if repair_succeeds:
        assert (await ai._extract(schema, values().source())).points[0].text == "00123"
    else:
        with pytest.raises(ServiceError, match="provider_invalid"):
            await ai._extract(schema, values().source())
    assert provider.calls == len(reservations) == len(settlements) == 2
    assert events[0]["categories"] == ["summary_source_tokens"]
    assert events[-1]["outcome"] == ("valid" if repair_succeeds else "invalid")
    assert all(
        token not in json.dumps(events)
        for token in ("PRIVATE", "99999", "00123", "invalid_candidate")
    )
