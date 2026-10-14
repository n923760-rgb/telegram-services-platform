"""Generic source serialization safety; no DB access or production content."""

import hashlib
import json

import pytest

from app.core.settings import config
from app.orders import engine
from app.services.base import ServiceError


@pytest.mark.parametrize(
    "source",
    [
        {"text": "نص عربي English 00123 😊", "language": "ar"},
        {"text": "  source\n\n00123", "title": None},
        {"images": ["1/" + "a" * 32 + "/source.png"]},
    ],
)
def test_valid_input_hash_is_identical_to_existing_idempotency_contract(source):
    expected = hashlib.sha256(
        json.dumps(source, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()
    assert engine.input_digest(source) == expected
    assert engine.input_digest(dict(reversed(list(source.items())))) == expected


@pytest.mark.parametrize("source", [{"text": "synthetic\ud800"}, {"text": object()}])
async def test_invalid_serialization_fails_safely_before_any_database_access(monkeypatch, source):
    monkeypatch.setattr(config(), "stars_enabled", False)

    def forbidden():
        raise AssertionError("invalid source must not touch a database")

    monkeypatch.setattr(engine, "sessions", forbidden)
    with pytest.raises(ServiceError, match="input_invalid") as error:
        await engine.submit(1, "unused", source, 300, "invalid-encoding")
    assert str(error.value) == "input_invalid"


def test_circular_non_json_source_has_safe_error():
    source = {}
    source["self"] = source
    with pytest.raises(ServiceError, match="input_invalid"):
        engine.input_digest(source)
