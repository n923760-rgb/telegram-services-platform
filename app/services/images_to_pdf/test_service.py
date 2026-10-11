from io import BytesIO
from types import SimpleNamespace

import pytest
from PIL import Image, ImageOps
from pypdf import PdfReader
from pypdf.generic import ContentStream

from app.builders.images_pdf import build
from app.providers.documents.images_pdf import NativeImagePdf
from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.images_to_pdf.service import ImagesToPdf
from tests.images_pdf_fixtures import picture


@pytest.mark.parametrize("format", ["PNG", "JPEG", "WEBP"])
@pytest.mark.parametrize("upload", ["document", "photo"])
async def test_received_high_resolution_pixels_survive_intake_and_pdf(
    tmp_path, monkeypatch, format, upload
):
    from PIL import ImageDraw

    from app.files import telegram

    # Real admission previously shrank these small strokes to 1024px, even though
    # the PDF builder already preserved whatever reduced pixels it received.
    image = Image.new("RGB", (1800, 1200), "white")
    draw = ImageDraw.Draw(image)
    draw.text((700, 600), "Order 00123 / Total 125.50 / 2026-10-11", fill="black")
    draw.line((50, 80, 1700, 81), fill="blue", width=1)
    source = BytesIO()
    image.save(source, format=format)
    data = source.getvalue()

    class DownloadFixture:
        async def download(self, file_id, destination=None):
            destination.write(data)
            return destination

    store = LocalStorage(tmp_path)
    monkeypatch.setattr(telegram, "storage", lambda: store)
    media = SimpleNamespace(file_id="source", file_size=len(data), mime_type="image/jpeg")
    message = SimpleNamespace(
        bot=DownloadFixture(),
        photo=[media] if upload == "photo" else [],
        document=media if upload == "document" else None,
    )
    service = ImagesToPdf()
    field = service.input_schema.conversation()[0]
    key = await telegram.receive(message, field.kind, 1, preserve_image=field.preserve_image)
    assert store.read(key, 1) == data
    service.runtime = SimpleNamespace(
        storage=OwnedStorage(store, 1), ai=None, image_pdf=NativeImagePdf()
    )
    result = await service.run({"images": [key], "orientation": "auto"})
    pdf = store.read(result.artifacts[0].key, 1)
    embedded = PdfReader(BytesIO(pdf)).pages[0].images[0].image
    with Image.open(BytesIO(data)) as received:
        expected = received.convert("RGB")
        assert embedded.size == expected.size == (1800, 1200)
        assert embedded.tobytes() == expected.tobytes()
    assert not embedded.getexif()


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
    service.runtime = SimpleNamespace(storage=storage, ai=None, image_pdf=NativeImagePdf())
    values = {"images": [first.key, second.key], "orientation": "portrait"}
    service.input_schema.validate_inputs(values)
    assert not service.needs_ai(values)
    result = await service.run(values)
    assert len(PdfReader(BytesIO(storage.read(result.artifacts[0].key))).pages) == 2
    assert result.artifacts[0].filename == "images.pdf"
    foreign = LocalStorage(tmp_path).save(2, "foreign.png", picture(), "image/png")
    with pytest.raises(ServiceError, match="input_invalid"):
        await service.run({"images": [foreign.key], "orientation": "auto"})


@pytest.mark.parametrize("failure", ["timeout", "missing"])
async def test_native_failure_releases_capacity_and_removes_private_sources(monkeypatch, failure):
    from pathlib import Path

    from app.providers.documents import images_pdf
    from app.providers.documents.base import DocumentError

    directories = []

    async def fail_child(module, args, **kwargs):
        root = Path(args[0])
        directories.append(root)
        assert root.joinpath("0.image").read_bytes() == picture()
        if failure == "timeout":
            raise DocumentError("document_render_timeout")

    monkeypatch.setattr(images_pdf, "run_child", fail_child)
    with pytest.raises(DocumentError, match="document_render_timeout|input_invalid"):
        await NativeImagePdf().render([picture()], "auto")
    assert not images_pdf.slot().locked()
    assert len(directories) == 1 and not directories[0].exists()


async def test_native_cancellation_releases_capacity_and_removes_private_sources(monkeypatch):
    import asyncio
    from pathlib import Path

    from app.providers.documents import images_pdf

    started = asyncio.Event()
    directories = []

    async def wait_child(module, args, **kwargs):
        directories.append(Path(args[0]))
        started.set()
        await asyncio.Event().wait()

    monkeypatch.setattr(images_pdf, "run_child", wait_child)
    task = asyncio.create_task(NativeImagePdf().render([picture()], "auto"))
    await asyncio.wait_for(started.wait(), timeout=1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert not images_pdf.slot().locked()
    assert not directories[0].exists()


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
