from io import BytesIO
from types import SimpleNamespace

import pytest
from pypdf import PdfReader

from app.builders.qr_codes import build
from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.services.qr_codes.schema import Inputs
from app.services.qr_codes.service import QrCodes
from tests.qr_codes_fixtures import decode_all, inputs


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize("language", ["ar", "en"])
async def test_single_native_pdf_decodes_literal_payload_without_ai(tmp_path, language):
    service = QrCodes()
    service.runtime = SimpleNamespace(storage=OwnedStorage(LocalStorage(tmp_path), 1), ai=None)
    values = inputs(language=language, entries="موقعي|https://example.invalid/?id=00123&x=%20")
    assert service.needs_ai(values) is False
    result = await service.run(values)
    assert result.artifacts[0].filename == "qr-codes.pdf"
    content = service.runtime.storage.read(result.artifacts[0].key)
    assert len(PdfReader(BytesIO(content)).pages) == 1
    assert decode_all(content, 1) == [values["entries"].partition("|")[2]]


def test_batch_pagination_duplicates_unicode_and_spaces_are_literal():
    payloads = [
        "00123",
        " مرحبًا ١٢٣ ",
        "A|B",
        "https://example.invalid/?id=00001",
        "00123",
        "x" * 240,
        "Long label",
    ]
    values = Inputs.parse(
        inputs(entries="\n".join(f"عنوان {i}|{v}" for i, v in enumerate(payloads)))
    )
    content = build(values)
    assert len(PdfReader(BytesIO(content)).pages) == 2
    assert decode_all(content, 7) == payloads


def test_maximum_batch_all_symbols_read_back_in_source_order():
    payloads = [f"https://example.invalid/product/{i:05d}" for i in range(24)]
    values = Inputs.parse(inputs(entries="\n".join(f"{i}|{v}" for i, v in enumerate(payloads))))
    content = build(values)
    assert len(PdfReader(BytesIO(content)).pages) == 4
    assert decode_all(content, 24) == payloads


@pytest.mark.parametrize(
    "changes",
    [
        {"entries": ""},
        {"entries": "Missing separator"},
        {"entries": "|data"},
        {"entries": "Label|"},
        {"entries": "Label|data\n"},
        {"entries": "\n".join("L|v" for _ in range(25))},
        {"entries": "L|" + "ع" * 121},
        {"entries": "L|" + "a" * 241},
        {"entries": "a" * 41 + "|v"},
        {"entries": "L|a\x00b"},
        {"entries": "L|a\rb"},
        {"entries": "L|a\u202eb"},
        {"language": "xx"},
        {"extra": "ignored"},
    ],
)
def test_invalid_input_rejected_before_reservation(changes):
    with pytest.raises(ServiceError, match="input_invalid"):
        QrCodes.needs_ai(inputs(**changes))
