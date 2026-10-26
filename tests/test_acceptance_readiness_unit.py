"""Selected/unfinished runs must not qualify an untested service or its other modes."""

import json

import pytest

from app.ops.acceptance_cases import cases
from app.ops.service_acceptance import ASSETS, save_report, service_readiness
from app.services.base import ServiceError


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.fixture
def plan():
    return cases(ASSETS)


def result(case, status="PASS"):
    return {"case": case.name, "service": case.slug, "status": status}


def by_slug(report):
    return {row["service"]: row for row in report["services"]}


def test_empty_run_lists_entire_portfolio_as_not_run(plan):
    report = service_readiness(plan, [])
    assert len(report["services"]) == 17
    assert report["launch_status"] == "NOT_ASSESSED"
    assert all(row["automated_status"] == "NOT_RUN" for row in report["services"])
    assert sum(len(row["not_run_cases"]) for row in report["services"]) == len(plan)


def test_selected_mode_does_not_qualify_whole_service(plan):
    case = next(c for c in plan if c.name == "word_direct")
    rows = by_slug(service_readiness(plan, [result(case)]))
    row = rows[case.slug]
    assert row["automated_status"] == "INCOMPLETE"
    assert row["passed_cases"] == [case.name]
    assert row["not_run_cases"] and row["next_action"] == "run_missing_cases"
    assert rows["text_to_pptx"]["automated_status"] == "NOT_RUN"


def test_failure_takes_priority_over_missing_and_passing_modes(plan):
    values = [c for c in plan if c.slug == "text_to_office"]
    report = service_readiness(plan, [result(values[0], "FAIL"), result(values[1])])
    row = by_slug(report)["text_to_office"]
    assert row["automated_status"] == "FAIL"
    assert row["failed_cases"] == [values[0].name]
    assert row["passed_cases"] == [values[1].name]
    assert row["not_run_cases"]
    assert row["next_action"] == "fix_failed_cases"


def test_full_pass_still_requires_manual_quality_review(plan):
    report = service_readiness(plan, [result(c) for c in plan])
    assert report["launch_status"] == "NOT_ASSESSED"
    for row in report["services"]:
        assert row["automated_status"] == "PASS"
        assert row["manual_review_status"] == "NOT_RECORDED"
        assert row["next_action"] == "review_source_fidelity_and_target_viewer"
        assert not row["failed_cases"] and not row["not_run_cases"]
    editing = by_slug(report)["text_editing"]
    assert editing["manual_review_checks"]


@pytest.mark.parametrize("invalid", ["duplicate", "unknown", "wrong_service", "unknown_status"])
def test_invalid_evidence_is_rejected(plan, invalid):
    row = result(plan[0])
    rows = [row]
    if invalid == "duplicate":
        rows.append(dict(row))
    elif invalid == "unknown":
        row["case"] = "not_a_case"
    elif invalid == "wrong_service":
        row["service"] = "text_to_pptx"
    else:
        row["status"] = "SKIPPED"
    with pytest.raises(ServiceError, match="acceptance_report_invalid"):
        service_readiness(plan, rows)


def test_saved_progress_replaces_stale_summary_without_mutating_cases(tmp_path, plan):
    path = tmp_path / "report.json"
    report = {"cases": [], "service_readiness": {"launch_status": "READY"}}
    save_report(path, report)
    assert json.loads(path.read_text())["service_readiness"]["launch_status"] == "NOT_ASSESSED"
    report["cases"].append(result(plan[0]))
    save_report(path, report)
    saved = json.loads(path.read_text())
    assert saved["cases"] == report["cases"]
    assert by_slug(saved["service_readiness"])[plan[0].slug]["passed_cases"] == [plan[0].name]
    assert not path.with_suffix(".tmp").exists()
