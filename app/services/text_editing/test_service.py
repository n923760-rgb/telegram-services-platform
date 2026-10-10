import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError, active_field
from app.services.text_editing.schema import Inputs, render, revision_schema
from app.services.text_editing.service import TextEditing

SOURCE = "order 00123 amount 125.50\n\ndate 2026-10-10 and zero 0\n"
PLAN = {
    "segments": [
        {"id": 2, "text": "Date 2026-10-10 and zero 0"},
        {"id": 1, "text": "Order 00123 amount 125.50"},
    ]
}
GOOD = "Order 00123 amount 125.50\n\nDate 2026-10-10 and zero 0\n"


def test_source_order_blank_lines_and_schema_privacy():
    values = Inputs.parse({"text": SOURCE.replace("\n", "\r\n"), "mode": "rewrite"})
    schema = revision_schema(values)
    assert render(values, schema.model_validate(PLAN)) == GOOD
    assert "00123" not in json.dumps(schema.model_json_schema())
    assert json.loads(values.source())["segments"][0] == {"id": 1, "text": SOURCE.splitlines()[0]}


@pytest.mark.parametrize(
    "segments",
    [
        [],
        [{"id": 1, "text": "Order 00123 amount 125.50"}],
        [PLAN["segments"][1], PLAN["segments"][1]],
        [{"id": 3, "text": "Date 2026-10-10 and zero 0"}, PLAN["segments"][1]],
        [{"id": True, "text": "Order 00123 amount 125.50"}, PLAN["segments"][0]],
        [{"id": "1", "text": "Order 00123 amount 125.50"}, PLAN["segments"][0]],
        [{"id": 1, "text": "Order 123 amount 125.50"}, PLAN["segments"][0]],
        [{"id": 1, "text": "Order 00123 amount 125.5"}, PLAN["segments"][0]],
        [{"id": 1, "text": "Order 00123 amount 125.50 extra 9"}, PLAN["segments"][0]],
        [{"id": 1, "text": "Order 00123\namount 125.50"}, PLAN["segments"][0]],
        [{"id": 1, "text": "Order 00123 amount 125.50\x00"}, PLAN["segments"][0]],
        [{"id": 1, "text": "Order 00123 amount 125.50", "invented": True}, PLAN["segments"][0]],
    ],
)
def test_incomplete_duplicate_unknown_or_changed_source_is_rejected(segments):
    with pytest.raises(ValidationError):
        revision_schema(Inputs.parse({"text": SOURCE, "mode": "rewrite"})).model_validate(
            {"segments": segments}
        )


def test_numeric_tokens_cannot_be_moved_between_source_lines():
    values = Inputs.parse({"text": "قيمة 125.50\nرقم 00123", "mode": "rewrite"})
    with pytest.raises(ValidationError):
        revision_schema(values).model_validate(
            {
                "segments": [
                    {"id": 1, "text": "Value 00123"},
                    {"id": 2, "text": "Number 125.50"},
                ]
            }
        )


def test_output_bound_and_request_isolation():
    first = revision_schema(Inputs.parse({"text": "00123", "mode": "rewrite"}))
    second = revision_schema(Inputs.parse({"text": "00124", "mode": "proofread"}))
    assert first.model_validate({"segments": [{"id": 1, "text": "00123"}]})
    assert second.model_validate({"segments": [{"id": 1, "text": "00124"}]})
    with pytest.raises(ValidationError):
        first.model_validate({"segments": [{"id": 1, "text": "00124"}]})
    values = Inputs.parse({"text": "hello\nworld", "mode": "proofread"})
    with pytest.raises(ValidationError):
        revision_schema(values).model_validate(
            {
                "segments": [
                    {"id": 1, "text": "a" * 12000},
                    {"id": 2, "text": "b" * 12000},
                ]
            }
        )


@pytest.mark.parametrize(
    "inputs",
    [
        {"text": " ", "mode": "rewrite"},
        {"text": "x" * 12001, "mode": "rewrite"},
        {"text": "a\n" * 81, "mode": "rewrite"},
        {"text": "hello\x00", "mode": "rewrite"},
        {"text": "hello", "mode": "invented"},
        {"text": "hello", "mode": "rewrite", "tone": "invented"},
        {"text": "hello", "mode": "rewrite", "unknown": True},
    ],
)
def test_invalid_input_is_rejected_during_admission(inputs):
    with pytest.raises(ServiceError, match="input_invalid"):
        TextEditing.needs_ai(inputs)


async def test_service_uses_injected_ai_and_owned_utf8_file(tmp_path):
    storage = OwnedStorage(LocalStorage(tmp_path), 7)
    calls = []

    async def extract(schema, source, prompt):
        calls.append((source, prompt))
        return schema.model_validate(PLAN)

    service = TextEditing()
    service.runtime = SimpleNamespace(storage=storage, ai=SimpleNamespace(extract=extract))
    result = await service.run({"text": SOURCE, "mode": "rewrite", "tone": "business"})
    assert result.text == GOOD and len(result.artifacts) == 1
    assert storage.read(result.artifacts[0].key).decode() == GOOD
    assert result.artifacts[0].filename == "revision.txt"
    assert len(calls) == 1 and "rewrite" in calls[0][1] and "business" in calls[0][1]
    assert not service.enabled_by_default and service.requires_ai


async def test_missing_ai_or_failed_provider_creates_no_output(tmp_path):
    storage = OwnedStorage(LocalStorage(tmp_path), 7)
    service = TextEditing()
    service.runtime = SimpleNamespace(storage=storage, ai=None)
    with pytest.raises(ServiceError, match="provider_config"):
        await service.run({"text": SOURCE, "mode": "rewrite"})
    service.runtime.ai = SimpleNamespace(
        extract=AsyncMock(side_effect=ServiceError("provider_invalid"))
    )
    with pytest.raises(ServiceError, match="provider_invalid"):
        await service.run({"text": SOURCE, "mode": "rewrite"})
    assert not list(tmp_path.glob("[0-9]*/*/*"))


@pytest.mark.parametrize(
    "source,edited",
    [
        ("Contact a@example.invalid", "Contact b@example.invalid"),
        ("Visit https://example.invalid/path?q=abc", "Visit https://example.invalid/path?q=def"),
        ("Visit www.example.invalid/path", "Visit www.changed.invalid/path"),
        ("a@example.invalid twice a@example.invalid", "a@example.invalid once"),
        ("source text", "added@example.invalid"),
    ],
)
def test_contact_change_addition_or_omission_is_rejected(source, edited):
    values = Inputs.parse({"text": source, "mode": "rewrite"})
    with pytest.raises(ValidationError):
        revision_schema(values).model_validate({"segments": [{"id": 1, "text": edited}]})


def test_contacts_cannot_move_between_lines_and_source_is_not_in_schema():
    values = Inputs.parse(
        {"text": "Email a@example.invalid\nVisit https://example.invalid", "mode": "proofread"}
    )
    schema = revision_schema(values)
    assert "example.invalid" not in json.dumps(schema.model_json_schema())
    with pytest.raises(ValidationError):
        schema.model_validate(
            {
                "segments": [
                    {"id": 1, "text": "Visit https://example.invalid"},
                    {"id": 2, "text": "Email a@example.invalid"},
                ]
            }
        )


@pytest.mark.parametrize("mode", ["proofread", "rewrite"])
async def test_arabic_draft_keeps_source_numbers_contacts_and_original_language(tmp_path, mode):
    values = {
        "text": "ارجو ارساله الى a@example.invalid بمبلغ ٠١٢٫٥٠",
        "mode": mode,
        "tone": "formal",
    }
    revised = "أرجو إرساله إلى a@example.invalid بمبلغ ٠١٢٫٥٠"

    async def extract(schema, source, prompt):
        assert mode in prompt and "original language" in prompt
        return schema.model_validate({"segments": [{"id": 1, "text": revised}]})

    storage = OwnedStorage(LocalStorage(tmp_path), 7)
    service = TextEditing()
    service.runtime = SimpleNamespace(storage=storage, ai=SimpleNamespace(extract=extract))
    result = await service.run(values)
    assert result.text == revised
    assert storage.read(result.artifacts[0].key).decode() == revised


def test_intake_only_requests_tone_for_rewriting():
    tone = TextEditing.input_schema.fields[2]
    assert not active_field(tone, {"mode": "proofread"})
    assert active_field(tone, {"mode": "rewrite"})
    TextEditing.input_schema.validate_inputs({"text": "source", "mode": "proofread"})
    with pytest.raises(ServiceError):
        TextEditing.input_schema.validate_inputs(
            {"text": "source", "mode": "proofread", "tone": "business"}
        )
    with pytest.raises(ServiceError):
        TextEditing.input_schema.validate_inputs({"text": "source", "mode": "rewrite"})
