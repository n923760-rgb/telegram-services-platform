from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pptx import Presentation

from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.text_to_pptx.schema import DeckPlan
from app.services.text_to_pptx.service import TextToPptx


async def test_pptx_service_builds_editable_file(tmp_path):
    plan = DeckPlan.model_validate({"deck": {"slides": [{"title": "عنوان", "bullets": ["نقطة"]}]}})
    service = TextToPptx()
    store = OwnedStorage(LocalStorage(tmp_path), 1)
    service.runtime = SimpleNamespace(
        storage=store, ai=SimpleNamespace(extract=AsyncMock(return_value=plan))
    )
    result = await service.run({"text": "نص"})
    assert not result.needs_confirmation
    presentation = Presentation(BytesIO(store.read(result.artifacts[0].key)))
    assert any(
        shape.has_text_frame and "نقطة" in shape.text for shape in presentation.slides[0].shapes
    )


async def test_pptx_service_builds_native_table_with_count_and_preserved_ids(tmp_path):
    from tests.test_pptx_quality import sample_plan

    plan = DeckPlan.model_validate({"deck": sample_plan()})
    service = TextToPptx()
    store = OwnedStorage(LocalStorage(tmp_path), 1)
    service.runtime = SimpleNamespace(
        storage=store, ai=SimpleNamespace(extract=AsyncMock(return_value=plan))
    )
    result = await service.run({"text": "البيانات الأصلية"})
    prs = Presentation(BytesIO(store.read(result.artifacts[0].key)))
    assert len(prs.slides) == 3 and not result.needs_confirmation
    native = next(s.table for s in prs.slides[2].shapes if s.has_table)
    assert native.cell(1, 0).text == "00123" and native.cell(1, 2).text == "125.50"
    assert "الجداول القابلة للتعديل: 1" in result.preview
    service.runtime.ai.extract.assert_awaited_once()


async def test_pptx_service_missing_information_releases(tmp_path):
    plan = DeckPlan.model_validate({"missing_information": True})
    service = TextToPptx()
    service.runtime = SimpleNamespace(
        storage=OwnedStorage(LocalStorage(tmp_path), 1),
        ai=SimpleNamespace(extract=AsyncMock(return_value=plan)),
    )
    with pytest.raises(ServiceError, match="needs_information"):
        await service.run({"text": "غير كافٍ"})


async def test_pptx_service_ambiguous_confirmation_then_resume(tmp_path):
    plan = DeckPlan.model_validate(
        {
            "ambiguous": True,
            "question": "اعتماد هذا الهيكل؟",
            "deck": {"slides": [{"title": "عنوان", "bullets": ["نقطة"]}]},
        }
    )
    service = TextToPptx()
    store = OwnedStorage(LocalStorage(tmp_path), 1)
    service.runtime = SimpleNamespace(
        storage=store, ai=SimpleNamespace(extract=AsyncMock(return_value=plan))
    )
    first = await service.run({"text": "نص"})
    assert first.needs_confirmation and first.continuation
    # Resuming with the continuation must not call the AI provider again.
    second = await service.run({"text": "نص", "__continuation": first.continuation})
    assert not second.needs_confirmation
    assert service.runtime.ai.extract.await_count == 1
    presentation = Presentation(BytesIO(store.read(second.artifacts[0].key)))
    assert any(
        shape.has_text_frame and "نقطة" in shape.text for shape in presentation.slides[0].shapes
    )
