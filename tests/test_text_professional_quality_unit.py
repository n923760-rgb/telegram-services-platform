"""Exercise task-specific quality decisions; scripted verdicts are not model evaluation."""

import json
from types import SimpleNamespace

import pytest

from app.providers.ai.gateway import AI
from app.providers.ai.review import QualityReview
from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.text_editing.service import TextEditing
from app.services.text_translation.service import TextTranslation
from tests.test_ai_quality_review import ledger as ledger
from tests.test_file_layers import Provider


@pytest.fixture(autouse=True)
def database():
    yield


CASES = [
    (
        TextTranslation,
        {"text": "يرجى إرسال الطلب 00123 إن أمكن.", "language": "en", "style": "business"},
        "Yo, send order 00123 if you can!",
        "Please send order 00123 if possible.",
    ),
    (
        TextTranslation,
        {"text": "Please send order 00123 if possible.", "language": "ar", "style": "formal"},
        "يا صاحبي أرسل الطلب 00123 إذا تقدر!",
        "يرجى إرسال الطلب 00123 إن أمكن.",
    ),
    (
        TextEditing,
        {"text": "Please sends order 00123.", "mode": "proofread"},
        "Please sends order 00123.",
        "Please send order 00123.",
    ),
    (
        TextEditing,
        {"text": "اريد إرسال الطلب 00123.", "mode": "proofread"},
        "اريد إرسال الطلب 00123.",
        "أريد إرسال الطلب 00123.",
    ),
    (
        TextEditing,
        {"text": "Can you send order 00123 if possible?", "mode": "rewrite", "tone": "business"},
        "Yo, send order 00123 if you can!",
        "Please send order 00123 if possible.",
    ),
    (
        TextEditing,
        {"text": "لو تقدر ترسل الطلب 00123 اليوم", "mode": "rewrite", "tone": "formal"},
        "يا صاحبي أرسل الطلب 00123 اليوم إذا تقدر!",
        "يرجى إرسال الطلب 00123 اليوم إن أمكن.",
    ),
]


def plan(text):
    return json.dumps({"segments": [{"id": 1, "text": text}]}, ensure_ascii=False)


@pytest.mark.parametrize("service_type,inputs,bad,good", CASES)
@pytest.mark.parametrize("accepted", [False, True])
async def test_quality_repair_is_bounded_and_artifacts_wait_for_accepted_review(
    tmp_path, ledger, service_type, inputs, bad, good, accepted
):
    reject = '{"accepted":false,"issues":["quality"]}'
    final = '{"accepted":true,"issues":[]}' if accepted else reject
    requests = []

    class Recording(Provider):
        async def extract_from_text(self, schema, source, prompt):
            requests.append((source, prompt))
            return await super().extract_from_text(schema, source, prompt)

    provider = Recording([plan(bad), reject, plan(good), final, "unused"])
    service = service_type()
    storage = OwnedStorage(LocalStorage(tmp_path), 1)
    service.runtime = SimpleNamespace(
        ai=AI(provider, "job", 1, quality_review=True), storage=storage
    )
    if accepted:
        result = await service.run(inputs)
        assert result.text == good
        assert storage.read(result.artifacts[0].key).decode() == good
        if service_type is TextEditing:
            assert inputs["text"] in storage.read(result.artifacts[1].key).decode()
    else:
        with pytest.raises(ServiceError, match="provider_invalid"):
            await service.run(inputs)
        assert storage.storage.usage(1)[1] == 0
    assert provider.calls == 4 and provider.responses == ["unused"]
    assert [event[0] for event in ledger] == ["reserve", "settle"] * 4
    original_source = requests[0][0]
    for review_index in (1, 3):
        review = json.loads(requests[review_index][0])
        assert review["source"] == original_source
        assert review["task"] == requests[0][1]
    correction = json.loads(requests[2][0])
    assert correction["source"] == original_source
    assert "quality" in requests[2][1]


@pytest.mark.parametrize(
    "service_type,inputs",
    [
        (TextEditing, {"text": "Please send order 00123.", "mode": "proofread"}),
        (
            TextTranslation,
            {"text": "Please send order 00123.", "language": "en", "style": "formal"},
        ),
    ],
)
async def test_already_correct_text_can_pass_without_forced_rewriting(
    tmp_path, ledger, service_type, inputs
):
    provider = Provider([plan(inputs["text"]), '{"accepted":true,"issues":[]}'])
    service = service_type()
    service.runtime = SimpleNamespace(
        ai=AI(provider, "job", 1, quality_review=True),
        storage=OwnedStorage(LocalStorage(tmp_path), 1),
    )
    result = await service.run(inputs)
    assert result.text == inputs["text"] and provider.calls == 2


def test_fixed_quality_category_remains_bounded_and_combines_with_fidelity_findings():
    findings = [
        "meaning",
        "omission",
        "unsupported_content",
        "numbers",
        "language",
        "instructions",
        "quality",
    ]
    assert QualityReview.model_validate({"accepted": False, "issues": findings}).issues == findings
