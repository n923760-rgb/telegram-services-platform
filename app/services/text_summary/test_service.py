import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.text_summary.schema import Inputs, render, selection_schema
from app.services.text_summary.service import TextSummary

SOURCE = "  لم أوافق على الطلب 00123  \n\nالمبلغ 125.50 والتاريخ 2026-10-10\nالتواصل a@example.invalid\nمعلومة خلفية\n"
PLAN = {"source_ids": [3, 1]}


def values(**changes):
    return {"text": SOURCE, "length": "short", "language": "ar", **changes}


def test_verbatim_order_references_and_full_source_report():
    inputs = Inputs.parse(values(text=SOURCE.replace("\n", "\r\n")))
    schema = selection_schema(inputs)
    summary, report = render(inputs, schema.model_validate(PLAN))
    assert "[1]   لم أوافق على الطلب 00123  " in summary
    assert "[3] التواصل a@example.invalid" in summary
    assert summary.index("[1]") < summary.index("[3]")
    assert "[2] المبلغ 125.50 والتاريخ 2026-10-10" not in summary
    assert "[2] المبلغ 125.50 والتاريخ 2026-10-10" in report
    assert "[4] معلومة خلفية" in report
    assert "00123" not in json.dumps(schema.model_json_schema())
    assert "example.invalid" not in json.dumps(schema.model_json_schema())
    assert json.loads(inputs.source())["paragraphs"][0] == {"id": 1, "text": inputs.lines()[0]}


@pytest.mark.parametrize(
    "plan",
    [
        {"source_ids": []},
        {"source_ids": [1, 1]},
        {"source_ids": [0]},
        {"source_ids": [5]},
        {"source_ids": [81]},
        {"source_ids": [True]},
        {"source_ids": ["1"]},
        {"source_ids": [1.0]},
        {"source_ids": [1, 2, 3, 4]},
        {"source_ids": [1], "text": "invented prose"},
        {"source_ids": [1], "reason": "private or invented rationale"},
        {"source_ids": None},
    ],
)
def test_invalid_or_generated_content_is_rejected(plan):
    with pytest.raises(ValidationError):
        selection_schema(Inputs.parse(values())).model_validate(plan)


@pytest.mark.parametrize(
    "changes",
    [
        {"text": " "},
        {"text": "one paragraph only"},
        {"text": "a\n\n\t"},
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
    with pytest.raises(ServiceError, match="input_invalid"):
        TextSummary.needs_ai(values(**changes))


@pytest.mark.parametrize("length,limit", [("short", 3), ("standard", 7)])
def test_requested_limit_and_exact_source_coverage_bound(length, limit):
    inputs = Inputs.parse(values(text="\n".join(f"line {i}" for i in range(20)), length=length))
    schema = selection_schema(inputs)
    assert inputs.limit() == limit
    assert schema.model_validate({"source_ids": list(range(1, limit + 1))})
    with pytest.raises(ValidationError):
        schema.model_validate({"source_ids": list(range(1, limit + 2))})
    two = Inputs.parse(values(text="one\ntwo", length=length))
    assert two.limit() == 1
    with pytest.raises(ValidationError):
        selection_schema(two).model_validate({"source_ids": [1, 2]})


def test_request_isolation_and_bounded_large_source_output():
    small = selection_schema(Inputs.parse(values(text="a\nb")))
    large_inputs = Inputs.parse(
        values(text="a" * 11842 + "\n" + "\n".join(["b"] * 79), length="standard")
    )
    large = selection_schema(large_inputs)
    assert len(large_inputs.text) == 12000
    assert large.model_validate({"source_ids": [80]})
    with pytest.raises(ValidationError):
        small.model_validate({"source_ids": [80]})
    summary, report = render(
        large_inputs, large.model_validate({"source_ids": [1, 2, 3, 4, 5, 6, 7]})
    )
    assert len(summary) < 13000 and len(report) < 26000


@pytest.mark.parametrize("language", ["ar", "en"])
async def test_injected_ai_only_selects_ids_owned_report_retains_source(tmp_path, language):
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
        Inputs.parse(inputs), selection_schema(Inputs.parse(inputs)).model_validate(PLAN)
    )
    assert result.text == expected
    assert len(result.artifacts) == 1 and result.artifacts[0].filename == "summary-source.txt"
    assert result.artifacts[0].mime == "text/plain"
    assert storage.read(result.artifacts[0].key).decode() == report
    assert result.artifacts[0].key.startswith("7/")
    with pytest.raises(ServiceError, match="not_allowed"):
        storage.storage.read(result.artifacts[0].key, 8)
    assert len(calls) == 1 and "at most 3" in calls[0][1] and "untrusted data" in calls[0][1]
    assert not service.enabled_by_default and service.requires_ai


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
