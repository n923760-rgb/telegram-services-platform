from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

import numpy as np
import pytest
from PIL import Image, ImageFilter

from app.builders.document_image import build
from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.document_image_enhancement.schema import Assessment
from app.services.document_image_enhancement.service import DocumentImageEnhancement
from tests.ocr_fixtures import printed


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize("choice", ["contrast", "sharpen"])
async def test_selected_candidate_and_original_are_delivered_without_engine_question(
    tmp_path, choice
):
    store = OwnedStorage(LocalStorage(tmp_path), 1)
    source = printed()
    file = store.save("source.png", source, "image/png")
    ai = SimpleNamespace(extract=AsyncMock(return_value=Assessment(choice=choice)))
    service = DocumentImageEnhancement()
    service.runtime = SimpleNamespace(storage=store, ai=ai)
    result = await service.run({"image": file.key})
    assert store.read(result.artifacts[0].key) == build(source, choice)[2]
    assert store.read(result.artifacts[2].key) == source
    evidence = ai.extract.await_args.kwargs["images"]
    assert len(evidence) == 3
    for data in evidence:
        with Image.open(BytesIO(data)) as picture:
            assert picture.format == "JPEG" and max(picture.size) <= 2048
    assert [f.name for f in service.input_schema.conversation()] == ["image"]
    assert service.needs_ai({"image": file.key})


async def test_no_improvement_never_saves_or_delivers_processed_artifacts(tmp_path):
    store = OwnedStorage(LocalStorage(tmp_path), 1)
    file = store.save("source.png", printed(), "image/png")
    service = DocumentImageEnhancement()
    service.runtime = SimpleNamespace(
        storage=store, ai=SimpleNamespace(extract=AsyncMock(return_value=Assessment(choice="none")))
    )
    with pytest.raises(ServiceError, match="enhancement_not_improved"):
        await service.run({"image": file.key})
    assert len(list(tmp_path.glob("1/*/*"))) == 1


async def test_missing_reviewer_does_not_deliver_unreviewed_image(tmp_path):
    store = OwnedStorage(LocalStorage(tmp_path), 1)
    file = store.save("source.png", printed(), "image/png")
    service = DocumentImageEnhancement()
    service.runtime = SimpleNamespace(storage=store, ai=None)
    with pytest.raises(ServiceError, match="provider_config"):
        await service.run({"image": file.key})


def test_sharpen_is_bounded_and_reduces_error_against_known_blurred_source():
    original = Image.open(BytesIO(printed())).convert("RGB")
    blurred = original.filter(ImageFilter.GaussianBlur(1.2))
    payload = BytesIO()
    blurred.save(payload, "PNG")
    enhanced = Image.open(BytesIO(build(payload.getvalue(), "sharpen")[2]))
    ref, before, after = [np.array(p).astype(float) for p in (original, blurred, enhanced)]
    assert np.max(np.abs(after - before)) <= 13
    assert np.mean((after - ref) ** 2) < np.mean((before - ref) ** 2) * 0.85
    assert enhanced.size == original.size
