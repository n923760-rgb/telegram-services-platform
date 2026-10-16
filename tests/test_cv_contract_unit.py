"""Offline CV contract tests, not evidence of successful live model generation."""

import json

import pytest
from pydantic import ValidationError

from app.services.cv_formatting.schema import CV_VALIDATION_CODES, Inputs, revision_schema
from tests.cv_fixtures import inputs, revision


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize("language", ["ar", "en", "bilingual"])
@pytest.mark.parametrize("summary", [False, True])
def test_request_json_schema_exposes_exact_sections_ids_and_counts(language, summary):
    source = inputs() | {"language": language}
    if not summary:
        source.pop("summary")
    values = Inputs.parse(source)
    model = revision_schema(values)
    schema = model.model_json_schema()
    expected_sections = {v["field"] for v in values.segments().values()} - {"contact", "headline"}
    expected_sections.add("summary")
    order = schema["properties"]["section_order"]
    assert set(order["items"]["enum"]) == expected_sections
    assert order["minItems"] == order["maxItems"] == len(expected_sections)
    segments = schema["$defs"]["CvSourceBody"]["properties"]["segments"]
    assert segments["minItems"] == segments["maxItems"] == len(values.segments())
    assert set(schema["$defs"]["CvSourceSegment"]["properties"]["id"]["enum"]) == set(
        values.segments()
    )
    assert schema["properties"]["bodies"]["minItems"] == len(values.targets())
    assert "diagnostic_categories" not in schema["properties"]
    assert model.model_validate(revision(source)).bodies[0].language == values.targets()[0]


def test_request_schema_does_not_leak_ids_between_requests():
    first = revision_schema(Inputs.parse(inputs()))
    other = inputs() | {"projects": "A project"}
    second = revision_schema(Inputs.parse(other))
    first_ids = first.model_json_schema()["$defs"]["CvSourceSegment"]["properties"]["id"]["enum"]
    second_ids = second.model_json_schema()["$defs"]["CvSourceSegment"]["properties"]["id"]["enum"]
    assert "projects:1" not in first_ids and "projects:1" in second_ids
    assert (
        "projects:1"
        not in first.model_json_schema()["$defs"]["CvSourceSegment"]["properties"]["id"]["enum"]
    )


@pytest.mark.parametrize("provided", [False, True])
def test_summary_presence_is_explicit_in_provider_schema(provided):
    source = inputs("en")
    if not provided:
        source.pop("summary")
    model = revision_schema(Inputs.parse(source))
    body = model.model_json_schema()["$defs"]["CvSourceBody"]
    assert body["properties"]["language"]["const"] == "en"
    payload = revision(source)
    if provided:
        assert body["properties"]["summary"]["type"] == "null"
        payload["bodies"][0]["summary"] = {"text": "A profile", "source_ids": ["skills:1"]}
    else:
        assert "summary" in body["required"]
        payload["bodies"][0].pop("summary")
    with pytest.raises(ValidationError):
        model.model_validate(payload)


@pytest.mark.parametrize(
    "code",
    [
        "cv_section_order",
        "cv_target_languages",
        "cv_name_identifiers",
        "cv_name_script",
        "cv_source_ids",
        "cv_single_line",
        "cv_source_tokens",
        "cv_paragraph_role",
        "cv_headline_limit",
        "cv_summary_line",
        "cv_summary_sources",
        "cv_summary_tokens",
    ],
)
def test_semantic_cv_guards_keep_rejecting_with_fixed_codes(code):
    source = inputs() | {"headline": "منسق عمليات"}
    if code == "cv_target_languages":
        source["language"] = "bilingual"
    source.pop("summary")
    payload = revision(source)
    body = payload["bodies"][0]
    if code == "cv_section_order":
        payload["section_order"][0] = payload["section_order"][1]
    elif code == "cv_target_languages":
        body["language"] = "en"
    elif code == "cv_name_identifiers":
        body["full_name"] += " 99999"
    elif code == "cv_name_script":
        body["full_name"] = "اسم مختلف"
    elif code == "cv_source_ids":
        body["segments"][0]["id"] = body["segments"][1]["id"]
    elif code == "cv_single_line":
        body["segments"][0]["text"] += "\nline"
    elif code == "cv_source_tokens":
        body["segments"][0]["text"] += " 99999"
    elif code == "cv_paragraph_role":
        body["segments"][0]["presentation"] = "lead"
    elif code == "cv_headline_limit":
        body["segments"][0]["text"] = "x" * 121
    elif code == "cv_summary_line":
        body["summary"]["text"] += "\nline"
    elif code == "cv_summary_sources":
        body["summary"]["source_ids"] = ["skills:1", "skills:1"]
    elif code == "cv_summary_tokens":
        body["summary"]["text"] += " 99999"
    model = revision_schema(Inputs.parse(source))
    with pytest.raises(ValidationError) as caught:
        model.model_validate(payload)
    assert caught.value.errors()[0]["type"] == code
    assert set(model.diagnostic_categories) == set(CV_VALIDATION_CODES)
    assert "99999" not in json.dumps(model.diagnostic_categories)


def test_injected_output_cannot_bypass_request_enum_or_fidelity():
    from app.services.cv_formatting.schema import document

    source = inputs()
    values = Inputs.parse(source)
    model = revision_schema(values)
    candidate = model.model_validate(revision(source))
    candidate.bodies[0].segments[0].text += " 99999"
    with pytest.raises(ValidationError):
        document(values, candidate)
