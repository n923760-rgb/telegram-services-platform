"""Invalid root input payloads must return a service error."""

import pytest

from app.services.base import InputField, InputSchema, ServiceError


@pytest.fixture(autouse=True)
def database():
    # These pure validation tests must not use the database fixture.
    yield


@pytest.fixture
def schema():
    return InputSchema(fields=[InputField(name="text", prompt_key="text_input")])


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        ["text"],
        42,
        {1: "bad"},
        {"text": "ok", 2: "extra"},
    ],
)
def test_invalid_root_payload_is_rejected(schema, payload):
    with pytest.raises(ServiceError) as error:
        schema.validate_inputs(payload)

    assert error.value.key == "input_invalid"


def test_valid_root_payload_is_accepted(schema):
    schema.validate_inputs({"text": "Valid customer input"})
