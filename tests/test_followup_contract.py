from uuid import uuid4

import pytest

from app.bot.followups import parse_callback
from app.services.base import ServiceError
from app.services.image_to_text.service import ImageToText
from app.services.local_ocr.service import LocalOcr
from app.services.text_translation.service import TextTranslation


@pytest.mark.parametrize(
    "data",
    [
        "follow:bad:0",
        "follow:" + "a" * 32 + ":3",
        "follow:" + "a" * 32 + ":-1",
        "follow:" + "a" * 32 + ":00",
        "follow:" + "A" * 32 + ":0",
        "follow:" + "a" * 32 + ":0:extra",
        "follow:" + "a" * 32 + ":٠",
        "",
    ],
)
def test_callbacks_reject_malformed_or_unbounded_references(data):
    with pytest.raises(ServiceError):
        parse_callback(data)


def test_callback_contains_only_order_reference_and_bounded_action_index():
    oid = uuid4()
    assert parse_callback(f"follow:{oid.hex}:0") == (oid, 0)


def test_ocr_intake_extracts_without_translation_choices():
    assert ImageToText.version == "3"
    assert [field.name for field in ImageToText.input_schema.conversation()] == ["images"]
    assert [field.name for field in LocalOcr.input_schema.conversation()] == ["images", "language"]
    assert ImageToText.text_followups == LocalOcr.text_followups
    assert not TextTranslation.text_followups


@pytest.mark.parametrize("text", ["x" * 12001, "line\n" * 81, "\x01bad", " "])
def test_translation_prefill_rejects_its_own_source_limits(text):
    with pytest.raises(ServiceError):
        TextTranslation.validate_followup_text("text", text)


def test_prefill_accepts_exact_limit_and_never_prefills_choice_fields():
    TextTranslation.validate_followup_text("text", "x" * 12000)
    TextTranslation.validate_followup_text("text", "line\n" * 80)
    with pytest.raises(ServiceError):
        TextTranslation.validate_followup_text("language", "en")
