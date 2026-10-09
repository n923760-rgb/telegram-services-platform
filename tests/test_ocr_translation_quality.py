import json

import pytest
from pydantic import ValidationError

from app.services.image_to_text.schema import Translation, translation_schema

SOURCE = "الطلب 00123 بمبلغ 125.50 ريال بتاريخ 2026-10-08. النسبة 12.5%؛ الصفر 0."
GOOD = "Order 00123, amount 125.50 SAR, date 2026-10-08. Rate 12.5%; zero 0."


def test_translation_schema_accepts_exact_numbers_without_leaking_source_in_schema():
    schema = translation_schema(SOURCE)
    assert schema.model_validate_json(json.dumps({"text": GOOD})).text == GOOD
    assert issubclass(schema, Translation)
    assert all(
        token not in json.dumps(schema.model_json_schema())
        for token in ("00123", "125.50", "2026-10-08")
    )


@pytest.mark.parametrize(
    "text",
    [
        GOOD.replace("00123", "123"),
        GOOD.replace("125.50", "250.50"),
        GOOD.replace("2026-10-08", "08-10-2026"),
        GOOD.replace("12.5%", "12.5"),
        GOOD.replace("125.50", "125.5"),
        GOOD.replace("0.", ""),
        GOOD + " Total 125.50.",
        GOOD.replace("00123", "٠٠١٢٣"),
    ],
)
def test_translation_rejects_changed_missing_added_or_reformatted_numeric_tokens(text):
    with pytest.raises(ValidationError):
        translation_schema(SOURCE).model_validate({"text": text})


@pytest.mark.parametrize(
    "token",
    [
        "+966501234567",
        "-125.50",
        "−125.50",
        "٢٠٢٦/١٠/٠٨",
        "١٢٥٫٥٠",
        "١٬٢٥٠٫٥٠",
        "١٢٫٥٪",
        "1/2",
        "1:2",
        "REF-00123",
    ],
)
def test_translation_preserves_multilingual_signs_separators_and_embedded_ids(token):
    schema = translation_schema(f"قيمة {token}")
    assert schema.model_validate({"text": f"Value {token}"}).text == f"Value {token}"
    with pytest.raises(ValidationError):
        schema.model_validate({"text": "Value missing"})


def test_translation_preserves_duplicate_counts_and_allows_sentence_reordering():
    schema = translation_schema("الطلب 00123 ثم الطلب 00123 بمبلغ 125.50")
    assert schema.model_validate({"text": "Amount 125.50 for order 00123 and order 00123."})
    with pytest.raises(ValidationError):
        schema.model_validate({"text": "Amount 125.50 for order 00123."})


def test_translation_without_source_numbers_rejects_invented_numbers():
    schema = translation_schema("مرحبا أحمد")
    assert schema.model_validate({"text": "Hello Ahmad"})
    with pytest.raises(ValidationError):
        schema.model_validate({"text": "Hello Ahmad, order 123"})


def test_translation_source_contracts_are_request_local():
    first, second = translation_schema("رقم 00123"), translation_schema("رقم 00124")
    assert first.model_validate({"text": "ID 00123"})
    assert second.model_validate({"text": "ID 00124"})
    with pytest.raises(ValidationError):
        first.model_validate({"text": "ID 00124"})
