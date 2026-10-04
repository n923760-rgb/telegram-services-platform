from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.image_to_text.schema import Extracted
from app.services.image_to_text.service import ImageToText


async def test_image_service_unreadable(tmp_path):
    store = OwnedStorage(LocalStorage(tmp_path), 1)
    image = store.save("image.jpg", b"test", "image/jpeg")
    service = ImageToText()
    service.runtime = SimpleNamespace(
        storage=store,
        ai=SimpleNamespace(
            extract=AsyncMock(return_value=Extracted(readable=False, confidence=0, text=""))
        ),
    )
    with pytest.raises(ServiceError, match="image_unclear"):
        await service.run({"images": [image.key]})
