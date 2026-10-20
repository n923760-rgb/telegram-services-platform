from copy import deepcopy

import pytest

from app.core.display import message_parts
from app.core.i18n import tr
from app.services.base import Result
from app.services.text_summary.schema import Inputs, render, summary_schema
from app.services.text_summary.test_service import PLAN, SOURCE, values


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize("language", ["ar", "en"])
@pytest.mark.parametrize("ids", [[3], [3, 1], [4, 2, 1]])
def test_each_point_has_exact_source_ids_in_both_summary_and_report(language, ids):
    inputs = Inputs.parse(values(language=language))
    candidate = {"points": [{"text": "Background", "source_ids": ids}]}
    plan = summary_schema(inputs).model_validate(candidate)
    before = deepcopy(plan.model_dump())
    summary, report = render(inputs, plan)
    references = ", ".join(f"[{number}]" for number in sorted(ids))
    assert (
        f"• [1] Background\n{tr('text_summary_point_sources', language, references=references)}"
        in summary
    )
    assert tr("text_summary_references", language) + f"\n[1] {references}\n" in report
    assert report.startswith(summary + "\n\n") and report.endswith(SOURCE)
    assert plan.model_dump() == before
    assert inputs.text == SOURCE


@pytest.mark.parametrize("language", ["ar", "en"])
def test_point_number_and_source_number_are_separate(language):
    inputs = Inputs.parse(values(language=language))
    summary, report = render(inputs, summary_schema(inputs).model_validate(PLAN))
    assert "• [2] " + PLAN["points"][1]["text"] in summary
    assert tr("text_summary_point_sources", language, references="[3]") in summary
    assert "[1] [1]\n[2] [3]" in report
    assert f"[3] {inputs.lines()[2]}" in report
    # Source-owned leading zeros and contact tokens are untouched in generated point text.
    assert PLAN["points"][0]["text"] in summary
    assert summary.count("a@example.invalid") == 1


@pytest.mark.parametrize("language", ["ar", "en"])
def test_maximum_points_and_references_fit_result_and_message_chunks(language):
    inputs = Inputs.parse(
        values(
            language=language,
            length="standard",
            text="\n".join("Source " + "x" * 130 for _ in range(80)),
        )
    )
    candidate = {
        "points": [
            {"text": chr(65 + i) * 850, "source_ids": list(range(80, 0, -1))} for i in range(7)
        ]
    }
    plan = summary_schema(inputs).model_validate(candidate)
    summary, report = render(inputs, plan)
    Result(text=summary)
    assert report.endswith(inputs.text)
    references = ", ".join(f"[{number}]" for number in range(1, 81))
    assert summary.count(tr("text_summary_point_sources", language, references=references)) == 7
    parts = list(message_parts(summary))
    assert len(parts) > 1
    assert all(len(part.encode("utf-16-le")) // 2 <= 3500 for part in parts)
    joined = "".join(parts)
    assert joined.count("[80]") == 7
    for point in plan.points:
        assert point.text in joined
