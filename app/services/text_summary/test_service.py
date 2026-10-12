import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.text_summary.schema import Inputs, render, summary_schema
from app.services.text_summary.service import TextSummary

SOURCE = "  لم أوافق على الطلب 00123  \n\nالمبلغ 125.50 والتاريخ 2026-10-10\nالتواصل a@example.invalid\nمعلومة خلفية\n"
PLAN = {
    "points": [
        {"text": "لم أوافق على الطلب 00123.", "source_ids": [1]},
        {"text": "التواصل a@example.invalid", "source_ids": [3]},
    ]
}


def values(**changes):
    return {"text": SOURCE, "length": "short", "language": "ar", **changes}


@pytest.fixture(autouse=True)
def database():
    """These contracts and injected storage tests need no database."""
    yield


def test_grounded_summary_and_exact_source_only_in_report():
    inputs = Inputs.parse(values())
    schema = summary_schema(inputs)
    summary, report = render(inputs, schema.model_validate(PLAN))
    assert "لم أوافق على الطلب 00123." in summary
    assert "125.50" not in summary
    assert "[2] المبلغ 125.50 والتاريخ 2026-10-10" in report
    assert report.endswith(inputs.text)
    assert "00123" not in json.dumps(schema.model_json_schema())
    assert "example.invalid" not in json.dumps(schema.model_json_schema())
    assert json.loads(inputs.source())["paragraphs"][0]["text"] == inputs.lines()[0]


@pytest.mark.parametrize(
    "point",
    [
        {"text": "طلب 123", "source_ids": [1]},
        {"text": "طلب 00123", "source_ids": [2]},
        {"text": "المبلغ 999", "source_ids": [2]},
        {"text": "mail b@example.invalid", "source_ids": [3]},
        {"text": "طلب 00123", "source_ids": [1, 1]},
        {"text": "النص", "source_ids": [0]},
        {"text": "النص", "source_ids": [5]},
        {"text": "النص", "source_ids": [True]},
        {"text": "النص", "source_ids": ["1"]},
        {"text": "النص", "source_ids": [1.0]},
        {"text": "النص", "source_ids": []},
        {"text": "النص\nآخر", "source_ids": [1]},
        {"text": " النص ", "source_ids": [1]},
        {"text": "نص\x00", "source_ids": [1]},
        {"text": "x" * 1201, "source_ids": [1]},
        {"text": "نص", "source_ids": [1], "extra": "secret"},
    ],
)
def test_invalid_or_ungrounded_content_rejected(point):
    with pytest.raises(ValidationError):
        summary_schema(Inputs.parse(values())).model_validate({"points": [point]})


@pytest.mark.parametrize(
    "changes",
    [
        {"text": " "},
        {"text": "a\nb\x00"},
        {"text": "a\nb\ud800"},
        {"text": "a\nb\uffff"},
        {"text": "x" * 12001},
        {"text": "a\n" * 81},
        {"length": "invented"},
        {"language": "fr"},
        {"unknown": True},
    ],
)
def test_input_rejected_before_admission(changes):
    with pytest.raises(ServiceError, match="text_summary_invalid"):
        TextSummary.needs_ai(values(**changes))


@pytest.mark.parametrize(
    "text", ["one paragraph only", "فقرة واحدة متصلة. بلا تقسيم يدوي.", "one\r\ntwo"]
)
def test_single_paragraph_and_crlf_accepted(text):
    assert TextSummary.needs_ai(values(text=text))


@pytest.mark.parametrize("length,limit", [("short", 3), ("standard", 7)])
def test_requested_point_limit_and_request_isolation(length, limit):
    inputs = Inputs.parse(values(length=length))
    schema = summary_schema(inputs)
    points = [{"text": f"نقطة {i}", "source_ids": [1]} for i in range(limit + 1)]
    # Use nonnumeric unique text so only the point bound is exercised.
    for i, point in enumerate(points):
        point["text"] = "point " + chr(65 + i)
    assert schema.model_validate({"points": points[:limit]})
    with pytest.raises(ValidationError):
        schema.model_validate({"points": points})
    short_source = summary_schema(Inputs.parse(values(text="one paragraph")))
    with pytest.raises(ValidationError):
        short_source.model_validate(PLAN)
    with pytest.raises(ValidationError):
        schema.model_validate({"points": [points[0], points[0]]})


def test_copying_long_source_is_rejected():
    source = " ".join(["background"] * 50)
    schema = summary_schema(Inputs.parse(values(text=source)))
    with pytest.raises(ValidationError):
        schema.model_validate({"points": [{"text": source, "source_ids": [1]}]})


@pytest.mark.parametrize("language", ["ar", "en"])
async def test_injected_ai_summary_owned_report_and_source(tmp_path, language):
    storage = OwnedStorage(LocalStorage(tmp_path), 7)
    calls = []

    async def extract(schema, source, prompt):
        calls.append((source, prompt))
        return schema.model_validate(PLAN)

    service = TextSummary()
    service.runtime = SimpleNamespace(storage=storage, ai=SimpleNamespace(extract=extract))
    inputs = values(language=language)
    result = await service.run(inputs)
    expected, report = render(
        Inputs.parse(inputs), summary_schema(Inputs.parse(inputs)).model_validate(PLAN)
    )
    assert result.text == expected
    assert len(result.artifacts) == 1 and result.artifacts[0].filename == "summary-source.txt"
    assert storage.read(result.artifacts[0].key).decode() == report
    with pytest.raises(ServiceError, match="not_allowed"):
        storage.storage.read(result.artifacts[0].key, 8)
    assert len(calls) == 1 and "at most 3" in calls[0][1] and "untrusted data" in calls[0][1]
    assert "next meetings" in calls[0][1] and "rejected proposals" in calls[0][1]
    assert service.version == "2" and not service.enabled_by_default and service.requires_ai


async def test_missing_or_failed_ai_saves_no_file(tmp_path):
    storage = OwnedStorage(LocalStorage(tmp_path), 7)
    service = TextSummary()
    service.runtime = SimpleNamespace(storage=storage, ai=None)
    with pytest.raises(ServiceError, match="provider_config"):
        await service.run(values())
    service.runtime.ai = SimpleNamespace(
        extract=AsyncMock(side_effect=ServiceError("provider_invalid"))
    )
    with pytest.raises(ServiceError, match="provider_invalid"):
        await service.run(values())
    assert not list(tmp_path.glob("[0-9]*/*/*"))
