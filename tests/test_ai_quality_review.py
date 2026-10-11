import json
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.builders.schema import Document
from app.providers.ai import gateway
from app.providers.ai.gateway import AI
from app.providers.ai.review import QualityReview
from app.services.base import ServiceError
from tests.test_file_layers import Provider

CONTENT = '{"title":"Order 00123","sections":[{"paragraphs":["125.50 SAR"]}]}'


@pytest.fixture(autouse=True)
def database():
    # Gateway unit tests replace the ledger boundary, not the integration suite.
    yield


@pytest.fixture
def ledger(monkeypatch):
    events = []

    async def reserve(job, user, bound):
        events.append(("reserve", bound))
        return len(events)

    async def settle(hold, cost, *args, **kwargs):
        events.append(("settle", cost))

    async def uncertain(hold):
        events.append(("uncertain", hold))

    monkeypatch.setattr(gateway, "reserve_call", reserve)
    monkeypatch.setattr(gateway, "settle_call", settle)
    monkeypatch.setattr(gateway, "uncertain_call", uncertain)
    return events


async def test_disabled_review_keeps_single_call(ledger):
    provider = Provider([CONTENT])
    result = await AI(provider, "job", 1).extract(Document, "original")
    assert result.title == "Order 00123" and provider.calls == 1
    assert [event[0] for event in ledger] == ["reserve", "settle"]


async def test_review_approval_preserves_candidate_and_accounts_both_calls(ledger):
    provider = Provider([CONTENT, '{"accepted":true,"issues":[]}'])
    result = await AI(provider, "job", 1, quality_review=True).extract(Document, "original")
    assert result == Document.model_validate_json(CONTENT)
    assert provider.calls == 2
    assert [event[0] for event in ledger] == ["reserve", "settle"] * 2
    assert sum(value for key, value in ledger if key == "settle") == Decimal(".008")


async def test_second_rejection_never_delivers_or_retries_again(ledger):
    provider = Provider(
        [
            CONTENT,
            '{"accepted":false,"issues":["numbers"]}',
            CONTENT,
            '{"accepted":false,"issues":["numbers"]}',
            "unused",
        ]
    )
    with pytest.raises(ServiceError, match="provider_invalid"):
        await AI(provider, "job", 1, quality_review=True).extract(Document, "original")
    assert provider.calls == 4
    assert len(ledger) == 8
    assert provider.responses == ["unused"]


async def test_invalid_review_is_repaired_once_without_recursive_review(ledger):
    provider = Provider([CONTENT, '{"accepted":true,"issues":["meaning"]}', "{}", "unused"])
    with pytest.raises(ServiceError, match="provider_invalid"):
        await AI(provider, "job", 1, quality_review=True).extract(Document, "original")
    assert provider.calls == 3
    assert [event[0] for event in ledger] == ["reserve", "settle"] * 3


async def test_review_budget_denial_prevents_second_provider_call(ledger, monkeypatch):
    async def deny(*args):
        raise ServiceError("job_cost_cap")

    provider = Provider([CONTENT, "unused"])
    original = provider.extract_from_text

    async def initial(*args):
        response = await original(*args)
        monkeypatch.setattr(gateway, "reserve_call", deny)
        return response

    provider.extract_from_text = initial
    with pytest.raises(ServiceError, match="job_cost_cap"):
        await AI(provider, "job", 1, quality_review=True).extract(Document, "original")
    assert provider.calls == 1


async def test_review_provider_failure_retains_uncertain_exposure(ledger):
    provider = Provider([CONTENT])
    with pytest.raises(IndexError):
        await AI(provider, "job", 1, quality_review=True).extract(Document, "original")
    assert [event[0] for event in ledger] == ["reserve", "settle", "reserve", "uncertain"]


async def test_image_review_receives_same_source_images_and_task(ledger):
    class Images(Provider):
        async def extract_from_image(self, schema, source, prompt, images):
            assert images == [b"source image"]
            if self.calls:
                payload = json.loads(source)
                assert payload["source"] == "untrusted source"
                assert payload["task"] == "Verbatim OCR"
                assert payload["candidate"]["title"] == "Order 00123"
            return await self.extract_from_text(schema, source, prompt)

    provider = Images([CONTENT, '{"accepted":true,"issues":[]}'])
    await AI(provider, "job", 1, quality_review=True).extract(
        Document, "untrusted source", "Verbatim OCR", images=[b"source image"]
    )
    assert provider.calls == 2


@pytest.mark.parametrize(
    "payload",
    [
        {"accepted": "true", "issues": []},
        {"accepted": False, "issues": []},
        {"accepted": False, "issues": ["numbers", "numbers"]},
        {"accepted": False, "issues": ["raw customer content"]},
    ],
)
def test_review_schema_rejects_ambiguous_or_unbounded_findings(payload):
    with pytest.raises(ValidationError):
        QualityReview.model_validate(payload)


async def test_content_repair_keeps_source_and_contract_and_reviews_corrected_output(ledger):
    corrected = CONTENT.replace("125.50", "125.75")

    class Checking(Provider):
        async def extract_from_text(self, schema, source, prompt):
            if self.calls in (1, 3):
                payload = json.loads(source)
                assert payload["source"] == "Order 00123: 125.75 SAR"
                assert payload["task"] == "Preserve all numeric values"
                expected = "125.50" if self.calls == 1 else "125.75"
                assert expected in json.dumps(payload["candidate"])
            elif self.calls == 2:
                payload = json.loads(source)
                assert payload["source"] == "Order 00123: 125.75 SAR"
                assert "numbers" in prompt and "Preserve all numeric values" in prompt
            return await super().extract_from_text(schema, source, prompt)

    provider = Checking(
        [
            CONTENT,
            '{"accepted":false,"issues":["numbers"]}',
            corrected,
            '{"accepted":true,"issues":[]}',
        ]
    )
    result = await AI(provider, "job", 1, quality_review=True).extract(
        Document, "Order 00123: 125.75 SAR", "Preserve all numeric values"
    )
    assert result.sections[0].paragraphs == ["125.75 SAR"]
    assert provider.calls == 4
    assert [event[0] for event in ledger] == ["reserve", "settle"] * 4


async def test_schema_repair_spends_only_creation_repair_then_rejection_fails(ledger):
    provider = Provider(["{}", CONTENT, '{"accepted":false,"issues":["omission"]}', "unused"])
    with pytest.raises(ServiceError, match="provider_invalid"):
        await AI(provider, "job", 1, quality_review=True).extract(Document, "source")
    assert provider.calls == 3 and provider.responses == ["unused"]


async def test_maximum_five_calls_and_final_review_has_no_schema_retry(ledger):
    provider = Provider(
        [CONTENT, "{}", '{"accepted":false,"issues":["meaning"]}', CONTENT, "{}", "unused"]
    )
    with pytest.raises(ServiceError, match="provider_invalid"):
        await AI(provider, "job", 1, quality_review=True).extract(Document, "source")
    assert provider.calls == 5 and provider.responses == ["unused"]
    assert [event[0] for event in ledger] == ["reserve", "settle"] * 5


async def test_translation_repair_preserves_language_and_style_contract(ledger):
    class Translation(Provider):
        async def translate(self, schema, source, language, style):
            assert source == "original" and language == "English" and style == "formal"
            return await self.extract_from_text(schema, source, "translation")

        async def extract_from_text(self, schema, source, prompt):
            if self.calls == 2:
                assert "English" in prompt and "formal" in prompt
                assert json.loads(source)["source"] == "original"
            return await super().extract_from_text(schema, source, prompt)

    provider = Translation(
        [
            CONTENT,
            '{"accepted":false,"issues":["language"]}',
            CONTENT,
            '{"accepted":true,"issues":[]}',
        ]
    )
    await AI(provider, "job", 1, quality_review=True).extract(
        Document, "original", language="English", style="formal"
    )
    assert provider.calls == 4


def test_production_runtime_automatically_reviews(monkeypatch):
    from types import SimpleNamespace

    from app.providers import runtime

    provider = object()
    monkeypatch.setattr(runtime, "provider", lambda: provider)
    monkeypatch.setattr(runtime, "storage", lambda: object())
    monkeypatch.setattr(runtime, "config", lambda: SimpleNamespace(document_visual_review=False))
    active = runtime.runtime_for("job", 1, needs_ai=True)
    assert active.ai.provider is provider and active.ai.quality_review is True
    assert runtime.runtime_for("job", 1, needs_ai=False).ai is None
