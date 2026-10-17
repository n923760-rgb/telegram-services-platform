"""Literal email/URL fidelity is enforced locally, independently of provider prose."""

import json

import pytest
from pydantic import ValidationError

from app.services.text_translation.schema import Inputs, render, translation_schema


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize("language", ["ar", "en"])
@pytest.mark.parametrize(
    "token",
    [
        "Source.Name+sales@example.invalid",
        "https://example.invalid/Path?q=value&tag=other#Section",
        "http://example.invalid/path",
        "www.example.invalid/Path",
        "https://example.invalid/طلب",
    ],
)
def test_exact_contact_tokens_and_counts_survive_target_language_and_blank_lines(language, token):
    values = Inputs.parse({"text": f"اكتب {token} {token}\r\n\r\nنهاية\r\n", "language": language})
    first = f"Write {token} {token}" if language == "en" else f"اكتب {token} {token}"
    last = "End" if language == "en" else "نهاية"
    schema = translation_schema(values)
    plan = {"segments": [{"id": 2, "text": last}, {"id": 1, "text": first}]}
    assert render(values, schema.model_validate(plan)) == f"{first}\n\n{last}\n"
    assert token not in json.dumps(schema.model_json_schema(), ensure_ascii=False)
    plan["segments"][1]["text"] = first.replace(f"{token} {token}", token)
    with pytest.raises(ValidationError, match="contact tokens per line"):
        schema.model_validate(plan)


@pytest.mark.parametrize(
    "source,translated",
    [
        ("source@example.invalid", "changed@example.invalid"),
        ("Source@example.invalid", "source@example.invalid"),
        ("https://example.invalid/Path", "https://example.invalid/path"),
        ("https://example.invalid/path", "http://example.invalid/path"),
        ("https://example.invalid/?q=source", "https://example.invalid/?q=changed"),
        ("www.example.invalid/source", "www.example.invalid/changed"),
        ("source@example.invalid", "omitted"),
        ("no contact", "added@example.invalid"),
        ("source@example.invalid", "source@example.invalid source@example.invalid"),
    ],
)
def test_changed_omitted_added_or_duplicated_contacts_fail_even_without_numbers(source, translated):
    schema = translation_schema(Inputs.parse({"text": source, "language": "en"}))
    with pytest.raises(ValidationError, match="contact tokens per line"):
        schema.model_validate({"segments": [{"id": 1, "text": translated}]})


def test_contacts_cannot_move_between_lines_even_when_global_counts_match():
    values = Inputs.parse(
        {"text": "راسل first@example.invalid\nثم second@example.invalid", "language": "en"}
    )
    with pytest.raises(ValidationError, match="contact tokens per line"):
        translation_schema(values).model_validate(
            {
                "segments": [
                    {"id": 1, "text": "second@example.invalid"},
                    {"id": 2, "text": "first@example.invalid"},
                ]
            }
        )


def test_contact_expectations_remain_request_local():
    first = translation_schema(Inputs.parse({"text": "first@example.invalid", "language": "en"}))
    second = translation_schema(Inputs.parse({"text": "second@example.invalid", "language": "en"}))
    payload = {"segments": [{"id": 1, "text": "second@example.invalid"}]}
    assert second.model_validate(payload)
    with pytest.raises(ValidationError, match="contact tokens per line"):
        first.model_validate(payload)
