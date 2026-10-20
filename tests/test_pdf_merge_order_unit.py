from io import BytesIO
from itertools import permutations
from types import SimpleNamespace

import pytest
from pypdf import PdfReader

from app.files.upload_order import ordered_indices
from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.pdf_tools.schema import Inputs
from app.services.pdf_tools.service import PdfTools
from app.services.pdf_tools.test_service import records, source


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize("count", range(2, 6))
def test_all_merge_permutations_and_default_order(count):
    files = [f"file-{number}" for number in range(count)]
    for permutation in permutations(range(1, count + 1)):
        inputs = {
            "operation": "merge",
            "files": files,
            "file_order": ",".join(map(str, permutation)),
        }
        PdfTools.input_schema.validate_inputs(inputs)
        assert Inputs.parse(inputs).source_order() == list(permutation)
        assert not PdfTools.needs_ai(inputs)
    for order in (None,):
        assert Inputs.parse(
            {"operation": "merge", "files": files, "file_order": order}
        ).source_order() == list(range(1, count + 1))


@pytest.mark.parametrize("order", ["٢، ١", "۲ ۱", "2,1", " 2 1 "])
def test_merge_accepts_same_digits_and_separators_as_image_order(order):
    assert Inputs.parse(
        {"operation": "merge", "files": ["first", "second"], "file_order": order}
    ).source_order() == [2, 1]


@pytest.mark.parametrize("order", ["", "1,1", "1", "1,3", "1,,2", "1\n2", True, [2, 1]])
def test_invalid_merge_order_is_rejected_before_admission(order):
    with pytest.raises(ServiceError, match="input_invalid"):
        PdfTools.needs_ai({"operation": "merge", "files": ["one", "two"], "file_order": order})


@pytest.mark.parametrize("operation", ["extract", "rotate"])
def test_order_field_belongs_to_merge_only(operation):
    inputs = {"operation": operation, "files": ["one"], "pages": "1", "file_order": "1"}
    if operation == "rotate":
        inputs["rotation"] = "90"
    with pytest.raises(ServiceError, match="input_invalid"):
        PdfTools.needs_ai(inputs)
    with pytest.raises(ServiceError, match="invalid_request"):
        PdfTools.input_schema.validate_inputs(inputs)


@pytest.mark.parametrize("count", [0, 6, True])
def test_shared_order_helper_has_its_own_count_bound(count):
    with pytest.raises(ValueError):
        ordered_indices(None, count)


@pytest.mark.parametrize(
    "order,sequence", [(None, [1, 2, 3]), ("3,1,2", [3, 1, 2]), ("٣،١،٢", [3, 1, 2])]
)
async def test_merge_reorders_whole_files_without_changing_pages(tmp_path, order, sequence):
    originals = [source(("00101", "00102")), source(("00201",)), source(("00301", "00302"))]
    storage = OwnedStorage(LocalStorage(tmp_path), 1)
    files = [
        storage.save(f"{number}.pdf", data, "application/pdf").key
        for number, data in enumerate(originals)
    ]
    service = PdfTools()
    service.runtime = SimpleNamespace(storage=storage, ai=None)
    inputs = {"operation": "merge", "files": files}
    if order is not None:
        inputs["file_order"] = order
    result = await service.run(inputs)
    assert len(result.artifacts) == 1 and result.artifacts[0].filename == "result.pdf"
    data = storage.read(result.artifacts[0].key)
    expected = [
        page for number in sequence for page in PdfReader(BytesIO(originals[number - 1])).pages
    ]
    actual = PdfReader(BytesIO(data)).pages
    assert len(actual) == len(expected) == 5
    assert records(data) == [
        record for number in sequence for record in records(originals[number - 1])
    ]
    for before, after in zip(expected, actual, strict=True):
        assert before.get_contents().get_data() == after.get_contents().get_data()
        assert before.mediabox == after.mediabox and before.rotation == after.rotation
    for language in ("ar", "en"):
        assert ", ".join(map(str, sequence)) in result.preview_localizations[language]
    assert inputs["files"] == files


def test_generic_optional_field_is_conditional_with_explicit_skip():
    field = next(
        field for field in PdfTools.input_schema.conversation() if field.name == "file_order"
    )
    assert field.when == {"operation": ["merge"]}
    assert not field.required and field.single_line and field.max_length == 32
    assert field.skip_key == "pdf_tools_upload_order"
