import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.document_image_enhancement.schema import Assessment
from app.services.document_image_enhancement.service import DocumentImageEnhancement
from tests.document_image_fixtures import shaded


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize("failure", [RuntimeError("save failed"), asyncio.CancelledError()])
async def test_cleanup_continues_after_delete_failure_and_preserves_original(failure):
    class Storage:
        saves = 0
        deleted = []

        def read(self, key):
            return shaded()

        def save(self, *args):
            self.saves += 1
            if self.saves == 3:
                raise failure
            return SimpleNamespace(key=str(self.saves))

        def delete(self, key):
            self.deleted.append(key)
            if key == "1":
                raise OSError("delete unavailable")

    storage = Storage()
    service = DocumentImageEnhancement()
    service.runtime = SimpleNamespace(
        storage=storage,
        ai=SimpleNamespace(extract=AsyncMock(return_value=Assessment(choice="contrast"))),
    )
    with pytest.raises(type(failure)) as caught:
        await service.run({"image": "source"})
    assert caught.value is failure
    assert storage.deleted == ["1", "2"]
