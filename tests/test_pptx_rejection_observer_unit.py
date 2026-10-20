"""Isolated diagnostics describe excess token kinds without retaining values."""

import json

import pytest

from app.ops.service_acceptance import DiagnosticAI, pptx_token_diagnostics
from app.services.base import ServiceError
from app.services.protected_values import ProtectedValues
from app.services.text_editing.schema import CONTACT_TOKEN
from app.services.text_to_pptx.schema import source_plan_schema
from tests.test_schema_repair_context_unit import Provider
from tests.test_schema_repair_context_unit import ledger as ledger


@pytest.fixture(autouse=True)
def database():
    yield


SOURCE = "Order 00123\nAmount 125.50 SAR\nContact a12@example.invalid"


def content(*slides, **extra):
    return json.dumps({"deck": {"slides": list(slides)}, **extra})


def test_repetition_is_counted_across_slides_not_mistaken_for_a_new_value():
    data = content(
        {"title": "Order 00123", "bullets": ["Amount 125.50 SAR"]},
        {"title": "Details", "bullets": ["Order 00123"]},
    )
    result = pptx_token_diagnostics(data, SOURCE)
    assert result["counts"] == {
        "numeric_added": 0,
        "numeric_repeated": 1,
        "contact_added": 0,
        "contact_repeated": 0,
    }
    assert result["locations"] == [
        {"slide": 2, "field": "bullet", "kind": "numeric_repeated", "occurrences": 1}
    ]
    assert not result["truncated"]


def test_new_changed_and_repeated_numbers_and_contacts_have_separate_counts():
    data = content(
        {
            "title": "Order 123",
            "bullets": [
                "125.50 SAR, 125.50 SAR",
                "a12@example.invalid a12@example.invalid",
                "new@example.invalid",
            ],
        }
    )
    result = pptx_token_diagnostics(data, SOURCE)
    assert result["counts"] == {
        "numeric_added": 1,
        "numeric_repeated": 2,
        "contact_added": 1,
        "contact_repeated": 1,
    }
    # The original counter also sees numeric parts inside contacts; mirror it exactly.
    assert {row["kind"] for row in result["locations"]} == set(result["counts"])
    serialized = json.dumps(result)
    for literal in ("123", "125.50", "a12@example.invalid", "new@example.invalid"):
        assert literal not in serialized


def test_native_table_fields_and_title_are_observed():
    data = content(
        {
            "title": "Order 00123",
            "table": {
                "columns": ["ID 00123", "Value"],
                "rows": [["00123", "999"]],
            },
        }
    )
    result = pptx_token_diagnostics(data, SOURCE)
    assert result["counts"]["numeric_repeated"] == 2
    assert result["counts"]["numeric_added"] == 1
    assert {row["field"] for row in result["locations"]} == {"table_header", "table_cell"}


def test_references_restore_before_observing_excess_and_metadata_is_excluded():
    protected = ProtectedValues(SOURCE, CONTACT_TOKEN)
    marker = next(key for key, value in protected.values.items() if value == "00123")
    data = content(
        {"title": "Order " + marker, "bullets": ["Order " + marker]},
        ambiguous=True,
        question="private question 999",
    )
    result = pptx_token_diagnostics(data, SOURCE)
    assert result["counts"]["numeric_repeated"] == 1
    assert result["counts"]["numeric_added"] == 0
    assert "[[value-" not in json.dumps(result)


def test_omissions_are_not_reported_as_new_or_repeated_values():
    result = pptx_token_diagnostics(content({"title": "Note", "bullets": ["Pending"]}), SOURCE)
    assert set(result["counts"].values()) == {0}
    assert result["locations"] == []


@pytest.mark.parametrize(
    "data",
    [
        "{",
        "[]",
        "{}",
        "x" * 100001,
        '{"missing_information": true}',
        content({"title": "Bad", "bullets": ["Text"], "unknown": "sensitive"}),
    ],
)
def test_invalid_or_oversized_output_cannot_create_misleading_token_diagnostics(data):
    assert pptx_token_diagnostics(data, SOURCE) is None


def test_diagnostic_locations_are_bounded_while_totals_remain_complete():
    data = content(*[{"title": "999", "bullets": ["888"]} for _ in range(30)])
    result = pptx_token_diagnostics(data, SOURCE)
    assert result["counts"]["numeric_added"] == 60
    assert len(result["locations"]) == 32 and result["truncated"]


@pytest.mark.parametrize("observe", [False, True])
async def test_failed_generation_preserves_two_calls_settlement_and_safe_original_category(
    ledger, observe
):
    source = "Order 00123"
    invalid = content({"title": "Order 00123", "bullets": ["Order 00123"]})
    provider = Provider([invalid, invalid])
    events = []
    ai = DiagnosticAI(provider, 1, 1, diagnostics=events, pptx_source=source if observe else None)
    with pytest.raises(ServiceError, match="provider_invalid"):
        await ai.extract(source_plan_schema(source, 1), source, "Create slides.")
    assert provider.calls == 2
    reserve, settle, uncertain = ledger
    assert reserve.await_count == settle.await_count == 2
    uncertain.assert_not_awaited()
    for event in events:
        assert event["categories"] == ["pptx_source_tokens"]
        assert ("token_diagnostics" in event) is observe
        if observe:
            assert event["token_diagnostics"]["counts"]["numeric_repeated"] == 1
    assert "00123" not in json.dumps(events) and "Order" not in json.dumps(events)
