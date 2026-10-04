from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

from docx import Document

from app.providers.storage import LocalStorage, OwnedStorage
from app.services.text_to_office.schema import WordPlan
from app.services.text_to_office.service import TextToOffice


async def test_word_service_builds_editable_file(tmp_path):
    plan = WordPlan.model_validate(
        {"document": {"title": "عنوان", "sections": [{"paragraphs": ["نص"]}]}}
    )
    service = TextToOffice()
    store = OwnedStorage(LocalStorage(tmp_path), 1)
    service.runtime = SimpleNamespace(
        storage=store, ai=SimpleNamespace(extract=AsyncMock(return_value=plan))
    )
    result = await service.run({"text": "نص", "target": "word"})
    assert not result.needs_confirmation
    assert "نص" in [
        p.text for p in Document(BytesIO(store.read(result.artifacts[0].key))).paragraphs
    ]
