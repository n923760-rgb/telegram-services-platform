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
        {"image": ""},
        {"image": "key", "mode": "contrast", "prompt": "change numbers"},
        {"image": ["key"]},
    ],
)
def test_invalid_contract_rejected_before_reservation(inputs):
    with pytest.raises(ServiceError, match="input_invalid"):
        DocumentImageEnhancement.needs_ai(inputs)


async def test_plugin_returns_received_bytes_unchanged_without_ai(tmp_path):
    storage = OwnedStorage(LocalStorage(tmp_path), 1)
    data = picture()
    source = storage.save("source.png", data, "image/png")
    service = DocumentImageEnhancement()
    ai = SimpleNamespace(extract=AsyncMock(side_effect=AssertionError("no AI")))
    service.runtime = SimpleNamespace(storage=storage, ai=ai)
    inputs = {"image": source.key}
    assert not service.needs_ai(inputs)
    result = await service.run(inputs)
    assert [a.filename for a in result.artifacts] == [
        "enhanced.png",
        "comparison.png",
        "received.png",
    ]
    assert storage.read(result.artifacts[2].key) == data
    assert result.preview_localizations.keys() == {"ar", "en"}
    assert not ai.extract.called


async def test_later_save_failure_removes_partial_outputs_and_keeps_input(tmp_path):
    storage = OwnedStorage(LocalStorage(tmp_path, quota_files=3), 1)
    source = storage.save("source.png", picture(), "image/png")
    service = DocumentImageEnhancement()
    service.runtime = SimpleNamespace(storage=storage, ai=None)
    with pytest.raises(ServiceError, match="storage_quota"):
        await service.run({"image": source.key})
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
        await service.run({"image": foreign.key})


def test_automatic_enhancement_reduces_uneven_light_and_retains_stamp_color():
    from tests.document_image_fixtures import check_quality, shaded

    _, _, enhanced, _ = build(shaded())
    check_quality(enhanced)


def test_processed_resolution_retained_with_bounded_comparison():
    source = Image.new("RGB", (2400, 1200), "white")
    Draw(source).rectangle((10, 10, 40, 40), fill="black")
    payload = BytesIO()
    source.save(payload, "PNG")
    _, _, enhanced, comparison = build(payload.getvalue())
    with Image.open(BytesIO(enhanced)) as after, Image.open(BytesIO(comparison)) as pair:
        assert after.size == (2048, 1024)
        assert pair.size == (2048, 512)
        assert not after.info


def test_exif_orientation_applied_without_metadata_in_processed_image():
    source = Image.new("RGB", (600, 300), "white")
    Draw(source).rectangle((30, 30, 60, 60), fill="black")
    exif = Image.Exif()
    exif[274] = 6
    exif[270] = "Synthetic metadata"
    payload = BytesIO()
    source.save(payload, "JPEG", exif=exif)
    _, _, enhanced, _ = build(payload.getvalue())
    with Image.open(BytesIO(enhanced)) as after:
        assert after.size == (300, 600)
        assert not after.getexif() and not after.info


def test_detected_noise_is_reduced_without_binarizing_image():
    import numpy as np

    rng = np.random.default_rng(17)
    source = np.clip(190 + rng.normal(0, 6, (300, 480)), 0, 255).astype(np.uint8)
    payload = BytesIO()
    Image.fromarray(source).convert("RGB").save(payload, "PNG")
    _, _, enhanced, _ = build(payload.getvalue())
    with Image.open(BytesIO(enhanced)) as after:
        pixels = np.array(after.convert("L"))
        assert pixels.std() < source.std() * 0.9
        assert len(np.unique(pixels)) > 20
