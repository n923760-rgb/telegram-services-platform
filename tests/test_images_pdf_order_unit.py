from io import BytesIO
from itertools import permutations
from types import SimpleNamespace

import pytest
from PIL import Image, ImageOps
from pypdf import PdfReader

from app.providers.documents.images_pdf import NativeImagePdf
from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.images_to_pdf.schema import Inputs
from app.services.images_to_pdf.service import ImagesToPdf
from tests.images_pdf_fixtures import picture


@pytest.fixture(autouse=True)
def database():
    yield


def source(count=3, **extra):
    return {"images": [f"image-{n}" for n in range(1, count + 1)], "orientation": "auto", **extra}


@pytest.mark.parametrize("count", range(1, 6))
def test_all_bounded_permutations_preserve_input_keys(count):
    for order in permutations(range(1, count + 1)):
        data = source(count, page_order=", ".join(map(str, order)))
        values = Inputs.parse(data)
        ImagesToPdf.input_schema.validate_inputs(data)
        assert values.source_order() == list(order)
        assert values.images == data["images"]
        assert not ImagesToPdf.needs_ai(data)


@pytest.mark.parametrize("order", ["3,1,2", "٣، ١، ٢", "۳ ۱ ۲", " 3 1 2 ", "3, ١ ۲", "3\t1\t2"])
def test_supported_digits_and_separators(order):
    assert Inputs.parse(source(page_order=order)).source_order() == [3, 1, 2]


@pytest.mark.parametrize("count", range(1, 6))
def test_omitted_and_null_order_keep_received_order(count):
    expected = list(range(1, count + 1))
    assert Inputs.parse(source(count)).source_order() == expected
    assert Inputs.parse(source(count, page_order=None)).source_order() == expected


@pytest.mark.parametrize(
    "order",
    [
        "",
        " ",
        "1,1,2",
        "1,2",
        "1,2,3,4",
        "0,1,2",
        "1,2,4",
        "-1,2,3",
        "1.0,2,3",
        "1-3",
        "1;2;3",
        ",1,2,3",
        "1,2,3,",
        "1,,2,3",
        "1\n2\n3",
        "1\r2 3",
        "1\u20282 3",
        "1\u20292 3",
        "1\x002 3",
        "1,2,٣٣",
        "1 2 " + " " * 32 + "3",
        True,
        123,
        [3, 1, 2],
        {"order": "3,1,2"},
        "1 2 3\n",
    ],
)
def test_invalid_order_is_rejected_before_admission(order):
    with pytest.raises(ServiceError, match="input_invalid"):
        ImagesToPdf.needs_ai(source(page_order=order))


@pytest.mark.parametrize("orientation", ["auto", "portrait", "landscape"])
async def test_native_pdf_uses_selected_order_and_retains_decoded_pixels(tmp_path, orientation):
    storage = OwnedStorage(LocalStorage(tmp_path), 1)
    originals = [
        picture(120, 240, orientation=6),
        picture(240, 120, color="blue"),
        picture(color="green"),
    ]
    keys = [
        storage.save(f"{index}.png", data, "image/png").key for index, data in enumerate(originals)
    ]
    service = ImagesToPdf()
    service.runtime = SimpleNamespace(storage=storage, image_pdf=NativeImagePdf(), ai=None)
    result = await service.run(
        {"images": keys, "orientation": orientation, "page_order": "٣، ١، ٢"}
    )
    assert result.artifacts[0].filename == "images.pdf" and len(result.artifacts) == 1
    for language in ("ar", "en"):
        assert "3, 1, 2" in result.preview_localizations[language]
    pages = PdfReader(BytesIO(storage.read(result.artifacts[0].key))).pages
    assert len(pages) == 3
    for page, number in zip(pages, [3, 1, 2], strict=True):
        embedded = page.images[0].image
        with Image.open(BytesIO(originals[number - 1])) as original:
            expected = ImageOps.exif_transpose(original).convert("RGB")
            assert embedded.size == expected.size and embedded.tobytes() == expected.tobytes()
        assert not embedded.getexif()
        landscape = orientation == "landscape" or (
            orientation == "auto" and expected.width > expected.height
        )
        assert (page.mediabox.width > page.mediabox.height) == landscape


def test_optional_order_is_between_upload_and_orientation_with_explicit_skip():
    images, order, orientation = ImagesToPdf.input_schema.conversation()
    assert images.name == "images" and images.multiple and images.preserve_image
    assert order.name == "page_order" and not order.required and order.single_line
    assert order.skip_key == "images_pdf_received_order" and order.max_length == 32
    assert orientation.name == "orientation" and orientation.required
