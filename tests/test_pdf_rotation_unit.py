"""Page rotation retains every source page; it never reorders, rewrites or rasterizes."""

from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject

from app.builders.pdf_tools import PdfToolError, build
from app.core.i18n import tr
from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.pdf_tools.service import PdfTools
from app.services.pdf_tools.test_service import records, source
from tests.pdf_image_fixtures import mixed_pdf


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize("angle", ["90", "180", "270"])
@pytest.mark.parametrize("selection,indices", [("2", {1}), ("3,1", {0, 2}), ("١-٣", {0, 1, 2})])
def test_only_selected_pages_rotate_and_source_order_and_content_stay_exact(
    angle, selection, indices
):
    data = source(("00123", "00124", "00125"))
    before = PdfReader(BytesIO(data))
    output = build([data], operation="rotate", pages=selection, rotation=angle)
    assert records(output) == ["00123", "00124", "00125"]
    after = PdfReader(BytesIO(output))
    for index, (original, rotated) in enumerate(zip(before.pages, after.pages, strict=True)):
        assert rotated.rotation == (int(angle) if index in indices else 0)
        assert rotated.extract_text() == original.extract_text()
        assert rotated.get_contents().get_data() == original.get_contents().get_data()
        assert rotated.mediabox == original.mediabox


@pytest.mark.parametrize("angle", ["90", "180", "270"])
def test_rotation_is_additive_and_preserves_images_boxes_and_unselected_rotation(angle):
    original = PdfReader(BytesIO(mixed_pdf()))
    writer = PdfWriter()
    page = writer.add_page(original.pages[0])
    page.rotate(270)
    page.cropbox = RectangleObject((10, 20, 500, 700))
    writer.add_page(PdfReader(BytesIO(source(("00124",)))).pages[0]).rotate(180)
    buffer = BytesIO()
    writer.write(buffer)
    data = buffer.getvalue()
    before = PdfReader(BytesIO(data))
    after = PdfReader(BytesIO(build([data], operation="rotate", pages="1", rotation=angle)))
    assert len(after.pages) == 2
    assert after.pages[0].rotation == (270 + int(angle)) % 360
    assert after.pages[1].rotation == 180
    for first, second in zip(before.pages, after.pages, strict=True):
        assert first.get_contents().get_data() == second.get_contents().get_data()
        assert first.mediabox == second.mediabox and first.cropbox == second.cropbox
        assert first.extract_text() == second.extract_text()
        assert [image.data for image in first.images] == [image.data for image in second.images]
    assert len(after.pages[0].images) == 1


@pytest.mark.parametrize(
    "updates",
    [
        {"rotation": None},
        {"rotation": "0"},
        {"rotation": "45"},
        {"rotation": "360"},
        {"rotation": 90},
        {"rotation": True},
        {"pages": None},
        {"pages": "1,1"},
        {"pages": "0"},
        {"files": ["one", "two"]},
        {"operation": "extract"},
        {"operation": "merge", "files": ["one", "two"], "pages": None},
    ],
)
def test_invalid_rotation_contract_fails_before_reservation(updates):
    inputs = {"operation": "rotate", "files": ["one"], "pages": "1", "rotation": "90"} | updates
    with pytest.raises(ServiceError, match="input_invalid"):
        PdfTools.needs_ai(inputs)


@pytest.mark.parametrize(
    "data,key",
    [
        (b"broken", "file_invalid"),
        (source(encrypted=True), "file_invalid"),
        (source(form=True), "pdf_tools_form"),
    ],
)
def test_existing_input_safety_guards_also_apply_to_rotation(data, key):
    with pytest.raises(PdfToolError, match=key):
        build([data], operation="rotate", pages="1", rotation="90")


def test_missing_page_and_invalid_angle_create_no_partial_output():
    with pytest.raises(PdfToolError, match="pdf_page_selection"):
        build([source()], operation="rotate", pages="1,3", rotation="90")
    with pytest.raises(PdfToolError, match="input_invalid"):
        build([source()], operation="rotate", pages="1", rotation="45")


@pytest.mark.parametrize("angle", ["90", "180", "270"])
async def test_service_requires_explicit_angle_and_never_calls_ai(tmp_path, angle):
    storage = OwnedStorage(LocalStorage(tmp_path), 1)
    file = storage.save("input.pdf", source(), "application/pdf")
    service = PdfTools()
    ai = SimpleNamespace(extract=AsyncMock(side_effect=AssertionError("no AI")))
    service.runtime = SimpleNamespace(storage=storage, ai=ai)
    inputs = {"operation": "rotate", "files": [file.key], "pages": "2", "rotation": angle}
    service.input_schema.validate_inputs(inputs)
    assert not service.needs_ai(inputs)
    result = await service.run(inputs)
    after = PdfReader(BytesIO(storage.read(result.artifacts[0].key)))
    assert [page.rotation for page in after.pages] == [0, int(angle)]
    assert result.preview == tr("pdf_tools_rotation_preview")
    assert result.preview_localizations["en"] == tr("pdf_tools_rotation_preview", "en")
    assert result.artifacts[0].filename == "result.pdf"
    ai.extract.assert_not_called()
    with pytest.raises(ServiceError, match="input_invalid"):
        service.input_schema.validate_inputs(
            {key: value for key, value in inputs.items() if key != "rotation"}
        )
