"""Acceptance must reject incomplete packages, reordered pages and lost source pixels."""

from dataclasses import replace
from io import BytesIO
from types import SimpleNamespace

import pytest
from PIL import Image

from app.builders.images_pdf import build as image_pdf
from app.builders.pdf_tools import build as pdf_tools
from app.ops.acceptance_cases import OWNER, Case, cases, source_pdf
from app.ops.service_acceptance import (
    ASSETS,
    Delivery,
    inspect_output,
    materialize,
    pixel_signature,
)
from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import Artifact, Result, ServiceError
from tests.images_pdf_fixtures import picture


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize(
    "names",
    [
        ("revision.txt", "changes.txt"),
        ("revision.txt",),
        ("changes.txt",),
        ("revision.txt", "changes.txt", "extra.txt"),
    ],
)
@pytest.mark.parametrize("with_chat", [False, True])
async def test_exact_package_contract_rejects_missing_chat_files_and_extras_before_writing(
    tmp_path, names, with_chat
):
    case = Case(
        "editing",
        "text_editing",
        {},
        expected_files=("revision.txt", "changes.txt", "response.txt"),
    )
    result = Result(
        text="Synthetic" if with_chat else "",
        artifacts=[Artifact(key=name, filename=name, mime="text/plain") for name in names],
    )
    delivery = Delivery(tmp_path / "out", SimpleNamespace(read=lambda *args: b"Synthetic"), case)
    if names == ("revision.txt", "changes.txt") and with_chat:
        await delivery.send(OWNER, "synthetic", result)
        assert delivery.sent == 1 and {file["name"] for file in delivery.files} == set(
            case.expected_files
        )
    else:
        with pytest.raises(ServiceError, match="acceptance_output_invalid"):
            await delivery.send(OWNER, "synthetic", result)
        assert delivery.sent == 0 and not delivery.files and not (tmp_path / "out").exists()


@pytest.mark.parametrize("name", ["cv_ar", "word_pdf_smart", "minutes_ar"])
async def test_word_pdf_pair_cannot_pass_with_only_one_valid_document(tmp_path, name):
    from docx import Document

    case = next(case for case in cases(ASSETS) if case.name == name)
    document = Document()
    document.add_paragraph("Synthetic " + " ".join(case.tokens))
    data = BytesIO()
    document.save(data)
    filename = next(name for name in case.expected_files if name.endswith(".docx"))
    result = Result(
        artifacts=[
            Artifact(
                key="synthetic",
                filename=filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        ]
    )
    delivery = Delivery(tmp_path / "out", SimpleNamespace(read=lambda *args: data.getvalue()), case)
    with pytest.raises(ServiceError, match="acceptance_output_invalid"):
        await delivery.send(OWNER, "synthetic", result)
    assert delivery.sent == 0 and not (tmp_path / "out").exists()


def test_all_31_cases_declare_exact_deliverables_for_all_18_services():
    plan = {case.name: case for case in cases(ASSETS)}
    assert all(case.expected_files for case in plan.values())
    assert len(plan) == 31 and len({case.slug for case in plan.values()}) == 18


@pytest.mark.parametrize("order", ["correct", "reverse", "duplicate", "blank"])
def test_merge_checks_each_distinct_source_page_not_just_total_page_count(order):
    case = next(case for case in cases(ASSETS) if case.name == "pdf_merge")
    first, second = source_pdf(), source_pdf(second=True)
    files = {"correct": [first, second], "reverse": [second, first], "duplicate": [first, first]}
    if order == "blank":
        from pypdf import PdfWriter

        writer = PdfWriter()
        for _ in range(2):
            writer.add_blank_page(width=600, height=800)
        output = BytesIO()
        writer.write(output)
        data = output.getvalue()
    else:
        data = pdf_tools(files[order], operation="merge")
    if order == "correct":
        assert inspect_output("result.pdf", data, case)["pages"] == 2
    else:
        with pytest.raises(ServiceError, match="acceptance_source_token_missing"):
            inspect_output("result.pdf", data, case)


@pytest.mark.parametrize(
    "change", ["none", "reverse", "duplicate", "pixel", "dimensions", "text_only"]
)
def test_image_pdf_requires_exact_received_rgb_pixels_in_selected_order(change):
    sources = [picture(color="red"), picture(color="blue")]
    signatures = []
    for source in sources:
        with Image.open(BytesIO(source)) as image:
            signatures.append(pixel_signature(image))
    case = Case(
        "images", "images_to_pdf", {}, exact_pdf_pages=2, pdf_image_hashes=tuple(signatures)
    )
    images = sources[:]
    if change == "reverse":
        images.reverse()
    if change == "duplicate":
        images[1] = images[0]
    if change in {"pixel", "dimensions"}:
        with Image.open(BytesIO(images[0])) as original:
            altered = (
                original.copy()
                if change == "pixel"
                else original.resize((original.width + 1, original.height))
            )
            if change == "pixel":
                altered.putpixel((0, 0), (1, 2, 3))
            output = BytesIO()
            altered.save(output, "PNG")
            altered.close()
            images[0] = output.getvalue()
    data = (
        image_pdf(images)
        if change != "text_only"
        else pdf_tools([source_pdf(), source_pdf()], operation="merge")
    )
    if change == "none":
        assert inspect_output("images.pdf", data, case)["pages"] == 2
    else:
        with pytest.raises(ServiceError, match="acceptance_output_invalid"):
            inspect_output("images.pdf", data, case)


def test_materialize_binds_pixel_contract_to_sources_without_altering_input_bytes(tmp_path):
    owned = OwnedStorage(LocalStorage(tmp_path), OWNER)
    case = next(case for case in cases(ASSETS) if case.name == "images_pdf")
    data = {"image": picture(color="red"), "mixed": picture(color="blue")}
    materialized = materialize(case, owned, data)
    assert materialized.expected_files == case.expected_files
    assert len(materialized.pdf_image_hashes) == 2
    assert [owned.read(key) for key in materialized.inputs["images"]] == [
        data["image"],
        data["mixed"],
    ]
    result = image_pdf([data["mixed"], data["image"]])
    assert inspect_output("images.pdf", result, materialized)["pages"] == 2
    with pytest.raises(ServiceError, match="acceptance_output_invalid"):
        inspect_output("images.pdf", image_pdf([data["image"], data["mixed"]]), materialized)
    with pytest.raises(ServiceError, match="acceptance_output_invalid"):
        inspect_output("images.pdf", result, replace(materialized, pdf_image_hashes=()))
