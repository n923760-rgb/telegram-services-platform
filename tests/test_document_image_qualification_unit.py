"""Qualify visible illumination benefit while keeping a controlled no-output decline."""

from io import BytesIO
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image

from app.builders.document_image import build
from app.ops.acceptance_cases import picture
from app.ops.service_acceptance import DiagnosticAI
from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.document_image_enhancement.service import DocumentImageEnhancement
from tests.test_schema_repair_context_unit import Provider
from tests.test_schema_repair_context_unit import ledger as ledger


@pytest.fixture(autouse=True)
def database():
    yield


def test_existing_acceptance_image_has_measurable_paper_illumination_benefit_without_lost_ink():
    original = picture(shaded=True)
    enhanced = build(original)[2]
    before = np.array(Image.open(BytesIO(original)).convert("L"))
    after = np.array(Image.open(BytesIO(enhanced)).convert("L"))
    assert before.shape == after.shape
    # The bottom paper band contains no printed source text.
    assert np.std(after[400:690]) < np.std(before[400:690]) * 0.6
    # Black printed stroke cores remain dark, not washed into the paper.
    ink = before < 16
    assert ink.sum() > 1000 and np.mean(after[ink] < 40) > 0.99


@pytest.mark.parametrize("choice", ["contrast", "sharpen", "none"])
async def test_reviewed_choices_keep_two_calls_original_bytes_and_no_output_on_decline(
    tmp_path, ledger, choice
):
    source = picture(shaded=True)
    provider = Provider(['{"choice":"' + choice + '"}', '{"accepted":true,"issues":[]}'])
    store = OwnedStorage(LocalStorage(tmp_path), 1)
    artifact = store.save("source.png", source, "image/png")
    service = DocumentImageEnhancement()
    service.runtime = SimpleNamespace(
        storage=store, ai=DiagnosticAI(provider, 1, 1, quality_review=True, diagnostics=[])
    )
    if choice == "none":
        with pytest.raises(ServiceError, match="enhancement_not_improved"):
            await service.run({"image": artifact.key})
        assert store.storage.usage(1)[1] == 1
    else:
        result = await service.run({"image": artifact.key})
        assert [item.filename for item in result.artifacts] == [
            "enhanced.png",
            "comparison.png",
            "received.png",
        ]
        assert store.read(result.artifacts[2].key) == source
        assert store.read(result.artifacts[0].key) == build(source, choice)[2]
    reserve, settle, uncertain = ledger
    assert provider.calls == reserve.await_count == settle.await_count == 2
    uncertain.assert_not_awaited()
    assert all(len(request[2]) == 3 for request in provider.requests)
