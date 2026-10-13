from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.services.pdf_to_word.schema import source_plan_schema


def plan(text, *, title="Document", heading="", bullets=None):
    return {
        "document": {
            "title": title,
            "sections": [{"heading": heading, "paragraphs": [text], "bullets": bullets or []}],
        }
    }


@pytest.mark.parametrize(
    "source",
    [
        "Order 00123, total 125.50 SAR, date 15/10/2026, discount 10%.",
        "رقم ٠٠١٢٣ مبلغ ١٢٥٫٥٠ تاريخ ١٥/١٠/٢٠٢٦ نسبة ١٠٪",
        "Count 0, delta −2, delta +3, repeated 00123 and 00123.",
        "Contact info@example.com or https://example.com/path?id=00123",
        "Contact INFO@EXAMPLE.COM twice INFO@EXAMPLE.COM",
        "No numeric or contact values in this text.",
    ],
)
def test_preserves_exact_source_tokens(source):
    assert source_plan_schema(source).model_validate(plan(source)).document is not None


@pytest.mark.parametrize(
    ("source", "changed"),
    [
        ("Order 00123", "Order 123"),
        ("Total 125.50", "Total 125.5"),
        ("Date 15/10/2026", "Date 2026-10-15"),
        ("Amount −2", "Amount 2"),
        ("Amount +2", "Amount 2"),
        ("Discount 10%", "Discount 10"),
        ("Value ٠٠١٢٣", "Value 00123"),
        ("Value ١٢٥٫٥٠", "Value ١٢٥.٥٠"),
        ("No numbers", "No numbers 1"),
        ("Invoice 00123", "Invoice"),
        ("Repeated 00123 00123", "Repeated 00123"),
        ("Invoice 00123", "Invoice 00123 00123"),
        ("Contact info@example.com", "Contact other@example.com"),
        ("Contact INFO@example.com", "Contact info@example.com"),
        ("Contact info@example.com info@example.com", "Contact info@example.com"),
        ("Link https://example.com/path", "Link https://example.com/other"),
        ("Contact info@example.com", "Contact"),
    ],
)
def test_rejects_changed_missing_added_or_repeated_tokens(source, changed):
    with pytest.raises(ValidationError):
        source_plan_schema(source).model_validate(plan(changed))


def test_checks_title_headings_and_bullets_without_counting_metadata_or_joining_tokens():
    schema = source_plan_schema("Invoice 00123 Total 125.50 contact info@example.com")
    good = plan("Total 125.50", title="Invoice 00123", bullets=["contact info@example.com"])
    schema.model_validate(good)
    for bad in (
        plan(
            "Total 125.50",
            title="Invoice 00123",
            heading="Page 1",
            bullets=["contact info@example.com"],
        ),
        plan("Total 125.50", title="Invoice 00123", bullets=["contact other@example.com"]),
        plan(
            "Invoice 00123 Total 125.50",
            title="Invoice 00123",
            bullets=["contact info@example.com"],
        ),
    ):
        with pytest.raises(ValidationError):
            schema.model_validate(bad)
    with pytest.raises(ValidationError):
        source_plan_schema("1234").model_validate(plan("34", title="12"))


def test_source_schemas_are_request_local_and_do_not_disclose_source_in_json_schema():
    first = source_plan_schema("private@example.com 00123")
    second = source_plan_schema("other@example.com 00999")
    first.model_validate(plan("private@example.com 00123"))
    second.model_validate(plan("other@example.com 00999"))
    with pytest.raises(ValidationError):
        second.model_validate(plan("private@example.com 00123"))
    assert "private@example.com" not in str(first.model_json_schema())
    assert "00123" not in str(first.model_json_schema())


def test_absent_document_or_missing_information_stays_rejectable_by_service():
    schema = source_plan_schema("Invoice 00123")
    assert schema.model_validate({}).document is None
    assert schema.model_validate({"missing_information": True}).missing_information


def test_forbids_control_characters_that_builder_would_strip():
    with pytest.raises(ValidationError):
        source_plan_schema("12 34").model_validate(plan("12\x0034"))


def test_does_not_claim_semantic_or_prose_coverage_validation():
    # Identical tokens cannot prove negation, owners or associations. AI content
    # review and real-provider acceptance remain separate requirements.
    source = "Alice owes 125.50, Bob owes 0; do not pay."
    candidate = plan("Bob owes 125.50, Alice owes 0; pay.")
    source_plan_schema(source).model_validate(deepcopy(candidate))
