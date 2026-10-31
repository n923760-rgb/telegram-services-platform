import math
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.services.base import Result
from app.services.completion import Completion


@pytest.fixture(autouse=True)
def database():
    pass


def test_literal_detached_payload_and_digest_roundtrip():
    source = {"name": "مدى", "links": ["https://example.invalid/?id=00123"], "flag": False}
    value = Completion(kind="example_v1", payload=source)
    source["links"].clear()
    result = Result(text="ready", completion=value)
    restored = Result.model_validate_json(result.model_dump_json())
    assert restored.completion.digest() == value.digest()
    assert restored.completion.payload["links"] == ["https://example.invalid/?id=00123"]
    assert Completion(kind="other_v1", payload=value.payload).digest() != value.digest()
    reordered = Completion(kind="example_v1", payload=dict(reversed(list(value.payload.items()))))
    assert reordered.digest() == value.digest()


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {1: "x"},
        {"x": math.nan},
        {"x": math.inf},
        {"x": datetime.now(UTC)},
        {"x": b"bytes"},
        {"x": {"set"}},
        {"x": "\ud800"},
        {"x": "\x00"},
        {"\x00": 1},
        {"x": "أ" * 16385},
        {"x": [None] * 4096},
    ],
)
def test_reject_non_json_unsafe_and_oversized_payloads(payload):
    with pytest.raises(ValidationError):
        Completion(kind="example_v1", payload=payload)


def test_depth_and_mutation_revalidated_at_digest_boundary():
    payload = {"value": 1}
    for _ in range(8):
        payload = {"nested": payload}
    with pytest.raises(ValidationError):
        Completion(kind="example_v1", payload=payload)
    value = Completion(kind="example_v1", payload={})
    value.payload["bad"] = math.nan
    with pytest.raises(ValidationError):
        value.digest()


@pytest.mark.parametrize("kind", ["", "bad-kind", "../path", "UPPER", "a" * 65, 1])
def test_kind_is_a_bounded_internal_discriminator(kind):
    with pytest.raises(ValidationError):
        Completion(kind=kind, payload={})


def test_completion_cannot_supply_owner_expiry_or_publication_consent():
    with pytest.raises(ValidationError):
        Completion(kind="example_v1", payload={}, owner_id=1, expires_at="later", publish=True)
    assert Result.model_validate({"text": "old cached result"}).completion is None
    with pytest.raises(ValidationError):
        Result(completion=Completion(kind="example_v1", payload={}))
