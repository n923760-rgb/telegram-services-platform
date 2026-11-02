"""Production gateway with scripted responses, not live provider qualification."""

import json
from types import SimpleNamespace

import pytest

from app.providers.ai.gateway import AI
from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.text_editing.service import TextEditing
from tests.test_ai_quality_review import ledger as ledger
from tests.test_file_layers import Provider


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize("mode", ["proofread", "rewrite"])
@pytest.mark.parametrize("repair", [False, True])
async def test_gateway_repairs_token_swaps_once_or_refuses_before_creating_files(
    tmp_path, ledger, mode, repair
):
    source = "please sends order 00123 for 125.50 SAR to a@example.invalid"
    swapped = "Please send order 125.50 for 00123 SAR to a@example.invalid"
    good = "Please send order 00123 for 125.50 SAR to a@example.invalid"

    def plan(text):
        return json.dumps({"segments": [{"id": 1, "text": text}]})

    responses = [plan(swapped), plan(good if repair else swapped)]
    if repair:
        responses.append('{"accepted":true,"issues":[]}')
    responses.append("unused")
    provider = Provider(responses)
    storage = OwnedStorage(LocalStorage(tmp_path), 1)
    service = TextEditing()
    service.runtime = SimpleNamespace(
        ai=AI(provider, "job", 1, quality_review=True), storage=storage
    )
    if repair:
        result = await service.run({"text": source, "mode": mode, "tone": "formal"})
        assert result.text == good
        assert [a.filename for a in result.artifacts] == ["revision.txt", "changes.txt"]
        assert storage.read(result.artifacts[0].key).decode() == good
        report = storage.read(result.artifacts[1].key).decode()
        assert source in report and good in report
    else:
        with pytest.raises(ServiceError, match="provider_invalid"):
            await service.run({"text": source, "mode": mode, "tone": "formal"})
        assert storage.storage.usage(1)[1] == 0
    count = 3 if repair else 2
    assert provider.calls == count and provider.responses == ["unused"]
    assert [event[0] for event in ledger] == ["reserve", "settle"] * count
