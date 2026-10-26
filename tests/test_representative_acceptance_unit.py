"""Acceptance must expose actual editing/translation work and multi-page sources."""

from io import BytesIO

import pytest
from docx import Document

from app.builders import word
from app.ops.acceptance_cases import cases
from app.ops.service_acceptance import ASSETS, inspect_output
from app.services.base import ServiceError
from app.services.text_summary.schema import Inputs as SummaryInputs
from app.services.text_to_word_pdf.schema import Inputs as BundleInputs


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.fixture
def plan():
    return {case.name: case for case in cases(ASSETS)}


@pytest.mark.parametrize(
    "name,filename",
    [
        ("editing_proofread", "revision.txt"),
        ("editing_rewrite", "revision.txt"),
        ("translation_ar", "translation.txt"),
        ("translation_en", "translation.txt"),
    ],
)
@pytest.mark.parametrize("whitespace_only", [False, True])
def test_known_error_and_cross_language_fixtures_cannot_pass_with_echo(
    plan, name, filename, whitespace_only
):
    case = plan[name]
    text = case.inputs["text"]
    if whitespace_only:
        text = "\n\n".join(text.split())
    with pytest.raises(ServiceError, match="acceptance_text_unchanged"):
        inspect_output(filename, text.encode(), case)


def test_corrected_english_passes_but_source_number_changes_still_fail(plan):
    case = plan["editing_proofread"]
    corrected = (
        case.inputs["text"]
        .replace(
            "report contain several error and need", "report contains several errors and needs"
        )
        .replace("00123 have", "00123 has")
        .replace("Please sends", "Please send")
    )
    assert inspect_output("revision.txt", corrected.encode(), case)["text_changed"] is True
    with pytest.raises(ServiceError, match="acceptance_source_token_missing"):
        inspect_output("revision.txt", corrected.replace("00123", "123").encode(), case)


def test_guard_does_not_mistake_editing_change_log_or_unchanged_valid_fixture_for_revision(plan):
    case = plan["editing_proofread"]
    assert "text_changed" not in inspect_output("changes.txt", case.inputs["text"].encode(), case)
    direct = plan["word_direct"]
    assert "text_changed" not in inspect_output(
        "response.txt", direct.inputs["text"].encode(), direct
    )


def test_multi_page_source_roundtrips_every_line_in_editable_word(plan):
    case = plan["word_pdf_direct"]
    values = BundleInputs.parse(case.inputs)
    assert 4000 < len(values.text) < 12000
    assert case.pdf_pages == 2
    data = word.build(values.document(), include_title=False)
    assert "\n".join(p.text for p in Document(BytesIO(data)).paragraphs) == values.text
    inspect_output("result.docx", data, case)
    assert len([token for token in case.tokens if token.startswith("SEC-")]) == 12


def test_long_summary_and_real_cross_language_source_keep_existing_plan_bounds(plan):
    assert len(plan) == 30 and len({case.slug for case in plan.values()}) == 17
    summary = SummaryInputs.parse(plan["summary"].inputs)
    assert len(summary.lines()) == 12 and len(summary.text) > 1500 and summary.limit() == 3
    assert "لم تعتمد" in plan["translation_en"].inputs["text"]
    assert "payment has not been approved" in plan["translation_ar"].inputs["text"]
    assert "report contain several error" in plan["editing_proofread"].inputs["text"]
    assert "يا فريق" in plan["editing_rewrite"].inputs["text"]
    assert sum(bool(case.review_checks) for case in plan.values()) == 6
