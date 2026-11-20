"""Validate privacy-safe AI schema categories and bounded repair context."""

import json
from typing import Literal

import pytest
from pydantic import Field, ValidationError

from app.builders.schema import StrictModel
from app.providers.ai.validation import repair_input, validation_categories


@pytest.fixture(autouse=True)
def database():
    yield


class Candidate(StrictModel):
    title: str = Field(max_length=4)
    entries: list[str] = Field(max_length=1)
    action: Literal["keep"]
    rank: int = Field(ge=1)


def test_known_limits_and_choices_have_actionable_content_free_categories():
    source = "Private source 00123"
    invalid = json.dumps({"title": "Too long", "entries": ["a", "b"], "action": "drop", "rank": 0})
    with pytest.raises(ValidationError) as caught:
        Candidate.model_validate_json(invalid)

    labels = validation_categories(Candidate, caught.value)
    assert labels == ["collection_limit", "invalid_choice", "numeric_limit", "text_limit"]
    assert "Private" not in json.dumps(labels) and "00123" not in json.dumps(labels)

    repair = json.loads(repair_input(Candidate, source, invalid, caught.value))
    assert repair["validation_categories"] == labels
    assert repair["source"] == source and repair["invalid_candidate"] == invalid
    assert "errors" not in repair and "locations" not in repair and "context" not in repair


def test_wrong_field_types_are_static_and_do_not_expose_values():
    invalid = json.dumps(
        {"title": 987654321, "entries": "Sensitive source", "action": "keep", "rank": 1}
    )
    with pytest.raises(ValidationError) as caught:
        Candidate.model_validate_json(invalid)
    labels = validation_categories(Candidate, caught.value)
    assert labels == ["field_type"]
    assert "Sensitive source" not in json.dumps(labels)
