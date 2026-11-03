"""PDF uses source references without relaxing literal checks or repair bounds."""

import json
from io import BytesIO
from types import SimpleNamespace

import pdfplumber
import pytest

from app.providers.ai.gateway import AI
from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.text_to_pdf.service import TextToPdf
from tests.test_ai_quality_review import ledger as ledger
from tests.test_file_layers import Provider


@pytest.fixture(autouse=True)
def database():
    yield


SOURCE = "Order 00123\nAmount 125.50 SAR\nSend to demo@example.invalid"


def runtime(tmp_path, provider):
    service = TextToPdf()
    store = OwnedStorage(LocalStorage(tmp_path), 1)
    service.runtime = SimpleNamespace(storage=store, ai=AI(provider, "job", 1, quality_review=True))
    return service, store


class ReferenceProvider(Provider):
    def __init__(self, invalid=False):
        super().__init__([])
        self.invalid = invalid
        self.original = None

    async def extract_from_text(self, schema, source, prompt):
        if "protected_values" in json.loads(source):
            data = json.loads(source)
            self.original = data
            assert data["source"].count("[[value-") == 3
            assert set(data["protected_values"].values()) == {
                "00123",
                "125.50",
                "demo@example.invalid",
            }
            assert "protected_values reference dictionary" in prompt
            text = data["source"]
            plan = {"document": {"title": "Order", "sections": [{"paragraphs": text.splitlines()}]}}
            if self.invalid:
                plan["document"]["title"] = "Order 00123"
            self.responses.append(json.dumps(plan))
        elif "validation_categories" in json.loads(source):
            assert self.invalid
            assert json.loads(source)["validation_categories"] == ["document_source_tokens"]
            self.responses.append(
                json.dumps(
                    {
                        "document": {
                            "title": "Order 00123",
                            "sections": [{"paragraphs": [self.original["source"]]}],
                        }
                    }
                )
            )
        else:
            data = json.loads(source)
            assert SOURCE.splitlines()[0] in json.dumps(data["candidate"])
            self.responses.append('{"accepted":true,"issues":[]}')
        return await super().extract_from_text(schema, source, prompt)


async def test_references_are_resolved_before_review_and_pdf_rendering(tmp_path, ledger):
    provider = ReferenceProvider()
    service, store = runtime(tmp_path, provider)
    result = await service.run({"text": SOURCE})
    assert provider.calls == 2
    with pdfplumber.open(BytesIO(store.read(result.artifacts[0].key))) as pdf:
        text = "\n".join(p.extract_text() or "" for p in pdf.pages)
    for value in ("00123", "125.50", "demo@example.invalid"):
        assert text.count(value) == 1
    assert "[[value-" not in text
    assert [e[0] for e in ledger] == ["reserve", "settle"] * 2


async def test_duplicate_resolved_values_still_fail_after_single_repair(tmp_path, ledger):
    provider = ReferenceProvider(invalid=True)
    service, store = runtime(tmp_path, provider)
    with pytest.raises(ServiceError, match="provider_invalid"):
        await service.run({"text": SOURCE})
    assert provider.calls == 2 and store.storage.usage(1)[1] == 0
    assert [e[0] for e in ledger] == ["reserve", "settle"] * 2
