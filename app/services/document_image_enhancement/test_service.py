from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from PIL import Image
from PIL.ImageDraw import Draw

from app.builders.document_image import build
from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.document_image_enhancement.service import DocumentImageEnhancement


def picture():
    image = Image.new("RGB", (480, 300), (180, 180, 180))
    Draw(image).text((40, 90), "Invoice 00123 / 125.50", fill=(100, 100, 100))
    stream = BytesIO()
    image.save(stream, "PNG")
    return stream.getvalue()


@pytest.mark.parametrize("mode", ["contrast", "grayscale"])
def test_native_enhancement_is_bounded_and_comparison_ordered(mode):
    data = picture()
    extension, mime, enhanced, comparison = build(data, mode)
    assert (extension, mime) == ("png", "image/png")
    with Image.open(BytesIO(enhanced)) as output, Image.open(BytesIO(comparison)) as pair:
        assert output.size == (480, 300)
        assert pair.size == (960, 300)
        assert pair.crop((480, 0, 960, 300)).tobytes() == output.tobytes()
        assert pair.crop((0, 0, 480, 300)).tobytes() != output.tobytes()
        if mode == "grayscale":
            assert (
                output.getchannel("R").tobytes()
                == output.getchannel("G").tobytes()
                == output.getchannel("B").tobytes()
            )


@pytest.mark.parametrize(
    "inputs",
    [
        {"image": "key", "mode": "ai"},
        {"image": "", "mode": "contrast"},
        {"image": "key", "mode": "contrast", "prompt": "change numbers"},
        {"image": ["key"], "mode": "contrast"},
    ],
)
def test_invalid_contract_rejected_before_reservation(inputs):
    with pytest.raises(ServiceError, match="input_invalid"):
        DocumentImageEnhancement.needs_ai(inputs)


@pytest.mark.parametrize("mode", ["contrast", "grayscale"])
async def test_plugin_returns_received_bytes_unchanged_without_ai(tmp_path, mode):
    storage = OwnedStorage(LocalStorage(tmp_path), 1)
    data = picture()
    source = storage.save("source.png", data, "image/png")
    service = DocumentImageEnhancement()
    ai = SimpleNamespace(extract=AsyncMock(side_effect=AssertionError("no AI")))
    service.runtime = SimpleNamespace(storage=storage, ai=ai)
    inputs = {"image": source.key, "mode": mode}
    assert not service.needs_ai(inputs)
    result = await service.run(inputs)
    assert [a.filename for a in result.artifacts] == [
        "received.png",
        "enhanced.png",
        "comparison.png",
    ]
    assert storage.read(result.artifacts[0].key) == data
    assert result.preview_localizations.keys() == {"ar", "en"}
    assert not ai.extract.called


async def test_later_save_failure_removes_partial_outputs_and_keeps_input(tmp_path):
    storage = OwnedStorage(LocalStorage(tmp_path, quota_files=3), 1)
    source = storage.save("source.png", picture(), "image/png")
    service = DocumentImageEnhancement()
    service.runtime = SimpleNamespace(storage=storage, ai=None)
    with pytest.raises(ServiceError, match="storage_quota"):
        await service.run({"image": source.key, "mode": "contrast"})
    assert len(list(tmp_path.glob("[0-9]*/*/*"))) == 1
    assert storage.read(source.key) == picture()


@pytest.mark.parametrize("data", [b"broken", b"", b"x" * (10 * 1024 * 1024 + 1)])
def test_corrupt_and_oversized_source_rejected(data):
    with pytest.raises(ServiceError):
        build(data, "contrast")


async def test_foreign_owner_file_rejected(tmp_path):
    store = LocalStorage(tmp_path)
    foreign = store.save(2, "source.png", picture(), "image/png")
    service = DocumentImageEnhancement()
    service.runtime = SimpleNamespace(storage=OwnedStorage(store, 1), ai=None)
    with pytest.raises(ServiceError, match="input_invalid"):
        await service.run({"image": foreign.key, "mode": "contrast"})
