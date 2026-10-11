from io import BytesIO
from types import SimpleNamespace

import pytest
from PIL import Image, ImageDraw
from pydantic import ValidationError

from app.files import telegram
from app.providers.storage import LocalStorage
from app.services.base import InputField, ServiceError


@pytest.mark.parametrize("format", ["PNG", "JPEG", "WEBP"])
@pytest.mark.parametrize("preserve", [True, False])
async def test_received_image_preservation_is_opt_in_and_format_detected(
    monkeypatch, tmp_path, format, preserve
):
    picture = Image.new("RGB", (1600, 800), "white")
    ImageDraw.Draw(picture).text((20, 20), "Numeric 00123 125.50", fill="black")
    stream = BytesIO()
    picture.save(stream, format)
    payload = stream.getvalue()

    class Bot:
        async def download(self, file_id, destination=None):
            destination.write(payload)
            return destination

    store = LocalStorage(tmp_path)
    monkeypatch.setattr(telegram, "storage", lambda: store)
    message = SimpleNamespace(
        bot=Bot(),
        photo=[],
        # File advertisement is not trusted to choose the actual stored format.
        document=SimpleNamespace(file_id="image", file_size=len(payload), mime_type="image/png"),
    )
    key = await telegram.receive(message, "image", 1, preserve_image=preserve)
    received = store.read(key, 1)
    with Image.open(BytesIO(received)) as image:
        assert image.size == ((1600, 800) if preserve else (1024, 512))
        assert image.format == (format if preserve else "JPEG")
    if preserve:
        assert received == payload
        assert key.endswith({"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp"}[format])
    with pytest.raises(ServiceError, match="not_allowed"):
        store.read(key, 2)


async def test_preserved_upload_still_rejects_corrupt_content(monkeypatch, tmp_path):
    class Bot:
        async def download(self, file_id, destination=None):
            destination.write(b"not an image")
            return destination

    store = LocalStorage(tmp_path)
    monkeypatch.setattr(telegram, "storage", lambda: store)
    message = SimpleNamespace(
        bot=Bot(),
        photo=[],
        document=SimpleNamespace(file_id="image", file_size=12, mime_type="image/png"),
    )
    with pytest.raises(ServiceError, match="file_invalid"):
        await telegram.receive(message, "image", 1, preserve_image=True)
    assert store.usage(1) == (0, 0)


def test_preservation_only_valid_for_image_fields():
    with pytest.raises(ValidationError):
        InputField(name="text", prompt_key="input_text", preserve_image=True)
