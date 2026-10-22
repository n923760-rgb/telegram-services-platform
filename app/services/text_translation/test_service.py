import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.text_translation.schema import Inputs, render, translation_schema
from app.services.text_translation.service import TextTranslation

SOURCE = "الطلب 00123 بمبلغ 125.50\n\nالتاريخ 2026-10-10 والصفر 0\n"
PLAN = {
    "segments": [
        {"id": 2, "text": "Date 2026-10-10 and zero 0"},
        {"id": 1, "text": "Order 00123 amount 125.50"},
    ]
}
GOOD = "Order 00123 amount 125.50\n\nDate 2026-10-10 and zero 0\n"


def test_source_order_blank_lines_and_schema_privacy():
    values = Inputs.parse({"text": SOURCE.replace("\n", "\r\n"), "language": "en"})
    schema = translation_schema(values)
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
        translation_schema(Inputs.parse({"text": SOURCE, "language": "en"})).model_validate(
            {"segments": segments}
        )


def test_numeric_tokens_cannot_be_moved_between_source_lines():
    values = Inputs.parse({"text": "قيمة 125.50\nرقم 00123", "language": "en"})
    with pytest.raises(ValidationError):
        translation_schema(values).model_validate(
            {
                "segments": [
                    {"id": 1, "text": "Value 00123"},
                    {"id": 2, "text": "Number 125.50"},
                ]
            }
        )


def test_output_bound_and_request_isolation():
    first = translation_schema(Inputs.parse({"text": "00123", "language": "en"}))
    second = translation_schema(Inputs.parse({"text": "00124", "language": "ar"}))
    assert first.model_validate({"segments": [{"id": 1, "text": "00123"}]})
    assert second.model_validate({"segments": [{"id": 1, "text": "00124"}]})
    with pytest.raises(ValidationError):
        first.model_validate({"segments": [{"id": 1, "text": "00124"}]})
    values = Inputs.parse({"text": "hello\nworld", "language": "ar"})
    with pytest.raises(ValidationError):
        translation_schema(values).model_validate(
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
        {"text": " ", "language": "en"},
        {"text": "x" * 12001, "language": "en"},
        {"text": "a\n" * 81, "language": "en"},
        {"text": "hello\x00", "language": "en"},
        {"text": "hello", "language": "fr"},
        {"text": "hello", "language": "en", "style": "invented"},
        {"text": "hello", "language": "en", "unknown": True},
    ],
)
def test_invalid_input_is_rejected_during_admission(inputs):
    with pytest.raises(ServiceError, match="input_invalid"):
        TextTranslation.needs_ai(inputs)


async def test_service_uses_injected_ai_and_owned_utf8_file(tmp_path):
    storage = OwnedStorage(LocalStorage(tmp_path), 7)
    calls = []

    async def extract(schema, source, prompt):
        calls.append((source, prompt))
        return schema.model_validate(PLAN)

    service = TextTranslation()
    service.runtime = SimpleNamespace(storage=storage, ai=SimpleNamespace(extract=extract))
    result = await service.run({"text": SOURCE, "language": "en", "style": "business"})
    assert result.text == GOOD and len(result.artifacts) == 1
    assert storage.read(result.artifacts[0].key).decode() == GOOD
    assert result.artifacts[0].filename == "translation.txt"
    assert len(calls) == 1 and "English" in calls[0][1] and "business" in calls[0][1]
    assert not service.enabled_by_default and service.requires_ai


async def test_missing_ai_or_failed_provider_creates_no_output(tmp_path):
    storage = OwnedStorage(LocalStorage(tmp_path), 7)
    service = TextTranslation()
    service.runtime = SimpleNamespace(storage=storage, ai=None)
    with pytest.raises(ServiceError, match="provider_config"):
        await service.run({"text": SOURCE, "language": "en"})
    service.runtime.ai = SimpleNamespace(
        extract=AsyncMock(side_effect=ServiceError("provider_invalid"))
    )
    with pytest.raises(ServiceError, match="provider_invalid"):
        await service.run({"text": SOURCE, "language": "en"})
    assert not list(tmp_path.glob("[0-9]*/*/*"))
