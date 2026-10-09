from io import BytesIO
from types import SimpleNamespace

import pytest
from PIL import Image, ImageOps
from pypdf import PdfReader
from pypdf.generic import ContentStream

from app.builders.images_pdf import build
from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.images_to_pdf.service import ImagesToPdf
from tests.images_pdf_fixtures import picture


@pytest.mark.parametrize("orientation", ["auto", "portrait", "landscape"])
def test_order_pixels_aspect_ratio_and_a4_bounds(orientation):
    sources = [picture(), picture(240, 120, color="blue")]
    reader = PdfReader(BytesIO(build(sources, orientation=orientation)))
    assert len(reader.pages) == 2
    for index, page in enumerate(reader.pages):
        width, height = float(page.mediabox.width), float(page.mediabox.height)
        assert sorted((round(width, 1), round(height, 1))) == [595.3, 841.9]
        expected_landscape = orientation == "landscape" or (orientation == "auto" and index == 1)
        assert (width > height) == expected_landscape
        assert len(page.images) == 1
        embedded = page.images[0].image
        with Image.open(BytesIO(sources[index])) as original:
            assert embedded.size == original.size
            assert embedded.tobytes() == original.convert("RGB").tobytes()
        commands = ContentStream(page.get_contents(), reader).operations
        transforms = [args for args, operation in commands if operation == b"cm"]
        a, _, _, d, x, y = map(float, transforms[-1])
        assert abs(a / d - embedded.width / embedded.height) < 0.0001
        assert x >= 28.34 and y >= 28.34
        assert x + a <= width - 28.34 and y + d <= height - 28.34
        assert abs(x - (width - a) / 2) < 0.001
        assert abs(y - (height - d) / 2) < 0.001


def test_exif_rotation_before_orientation_and_private_metadata_removed():
    source = picture(120, 240, orientation=6)
    page = PdfReader(BytesIO(build([source]))).pages[0]
    assert float(page.mediabox.width) > float(page.mediabox.height)
    embedded = page.images[0].image
    with Image.open(BytesIO(source)) as original:
        expected = ImageOps.exif_transpose(original).convert("RGB")
        assert embedded.size == expected.size
        assert embedded.tobytes() == expected.tobytes()
    assert not embedded.getexif()


def test_transparency_composited_on_white():
    embedded = PdfReader(BytesIO(build([picture(transparent=True)]))).pages[0].images[0].image
    assert embedded.getpixel((0, 0)) == (255, 255, 255)
    assert embedded.getpixel((30, 60)) == (255, 0, 0)


@pytest.mark.parametrize(
    "images,orientation",
    [
        ([], "auto"),
        ([picture()] * 6, "auto"),
        ([b"%PDF- not an image"], "auto"),
        ([picture(31, 100)], "auto"),
        ([picture()], "unknown"),
        ([b"x" * (10 * 1024 * 1024 + 1)], "auto"),
    ],
    ids=["empty", "too-many", "wrong-content", "too-small", "bad-choice", "oversized"],
)
def test_invalid_image_sources(images, orientation):
    with pytest.raises(ValueError):
        build(images, orientation=orientation)


def test_decoded_pixel_and_total_byte_limits_before_load(monkeypatch):
    import app.builders.images_pdf as module

    monkeypatch.setattr(module, "MAX_PIXELS", 100)
    with pytest.raises(ValueError, match="decoded image limit"):
        build([picture()])
    monkeypatch.setattr(module, "MAX_TOTAL_BYTES", 1)
    with pytest.raises(ValueError, match="image input limit"):
        build([picture()])


def test_output_byte_limit(monkeypatch):
    import app.builders.images_pdf as module

    source = picture()
    monkeypatch.setattr(module, "MAX_BYTES", len(source) + 10)
    with pytest.raises(ValueError, match="output limit"):
        build([source])


def test_animated_sources_rejected_before_frames_are_dropped():
    output = BytesIO()
    with (
        Image.new("RGB", (80, 80), "red") as first,
        Image.new("RGB", (80, 80), "blue") as second,
    ):
        first.save(
            output, format="PNG", save_all=True, append_images=[second], duration=100, loop=0
        )
    with pytest.raises(ValueError, match="unsupported image"):
        build([output.getvalue()])


async def test_owned_sources_produce_actual_pdf_and_foreign_source_fails(tmp_path):
    storage = OwnedStorage(LocalStorage(tmp_path), 1)
    first = storage.save("one.png", picture(), "image/png")
    second = storage.save("two.png", picture(240, 120), "image/png")
    service = ImagesToPdf()
    service.runtime = SimpleNamespace(storage=storage, ai=None)
    values = {"images": [first.key, second.key], "orientation": "portrait"}
    service.input_schema.validate_inputs(values)
    assert not service.needs_ai(values)
    result = await service.run(values)
    assert len(PdfReader(BytesIO(storage.read(result.artifacts[0].key))).pages) == 2
    assert result.artifacts[0].filename == "images.pdf"
    foreign = LocalStorage(tmp_path).save(2, "foreign.png", picture(), "image/png")
    with pytest.raises(ServiceError, match="input_invalid"):
        await service.run({"images": [foreign.key], "orientation": "auto"})


@pytest.mark.parametrize(
    "values",
    [
        {"images": [], "orientation": "auto"},
        {"images": ["same", "same"], "orientation": "auto"},
        {"images": ["one"], "orientation": "stretch"},
        {"images": ["one"], "orientation": "auto", "other": "ignored?"},
    ],
)
def test_invalid_inputs_fail_admission(values):
    with pytest.raises(ServiceError, match="input_invalid"):
        ImagesToPdf.needs_ai(values)
