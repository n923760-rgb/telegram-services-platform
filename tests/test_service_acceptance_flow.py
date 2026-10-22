import json
from decimal import Decimal
from unittest.mock import AsyncMock

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import func, select

from app.core.db import sessions
from app.core.models import CostHold, CostUsage, Ledger, Order, Setting, User
from app.core.settings import config
from app.ops import service_acceptance as acceptance
from app.ops.acceptance_cases import OWNER, Case
from app.services.base import ServiceError


def configure(tmp_path, monkeypatch):
    cfg = config()
    for key, value in {
        "app_env": "test",
        "database_url": SecretStr(
            "postgresql+asyncpg://fixture@localhost/svc_abcdef123456_acceptance_test"
        ),
        "storage_root": tmp_path / "acceptance-abcdef123456",
        "admin_ids": [OWNER],
        "ai_enabled": True,
        "stars_enabled": False,
        "max_daily_cost_sar": Decimal("5"),
        "max_cost_per_user_per_day": Decimal("5"),
        "max_job_cost_sar": Decimal(".75"),
        "ai_api_key": SecretStr("test-only-key"),
        "ai_base_url": "https://api.deepseek.com",
        "ai_input_usd_per_million": Decimal(".30"),
        "ai_output_usd_per_million": Decimal("1.20"),
        "document_visual_review": False,
    }.items():
        monkeypatch.setattr(cfg, key, value)
    return cfg.storage_root / "results"


async def test_direct_acceptance_native_outputs_and_single_capture_without_provider(
    tmp_path, monkeypatch
):
    path = configure(tmp_path, monkeypatch)
    call = AsyncMock(side_effect=AssertionError("no network"))
    monkeypatch.setattr(acceptance.AcceptanceProvider, "call", call)
    monkeypatch.setattr(
        acceptance,
        "cases",
        lambda assets: [
            Case("direct", "text_to_pdf", {"text": "Invoice 00123", "mode": "direct"}, ("00123",))
        ],
    )
    assert await acceptance.execute(["direct"]) == 0
    result = json.loads((path / "report.json").read_text())
    assert result["status"] == "PASS" and result["passed"] == 1 and result["provider_calls"] == 0
    assert result["active_orders"] == result["wallet_reserved_halala"] == 0
    assert result["selected_cases"] == ["direct"]
    assert result["calculated_usage_sar"] == "0"
    assert result["cases"][0]["diagnostics"] == []
    assert (path / "direct" / "result.pdf").is_file()
    call.assert_not_awaited()
    async with sessions() as db:
        assert await db.scalar(select(func.count(CostHold.id))) == 0
        assert await db.scalar(select(func.count(Ledger.id)).where(Ledger.kind == "capture")) == 1


async def test_latest_native_acceptance_cases_pass_without_provider_calls(tmp_path, monkeypatch):
    # The global test fixture exposes echo publicly for unrelated lifecycle tests;
    # these real-portfolio cases must use its production admin-only audience.
    monkeypatch.setattr(acceptance.registry.types["echo"], "admin_only", True)
    path = configure(tmp_path, monkeypatch)
    call = AsyncMock(side_effect=AssertionError("no network"))
    monkeypatch.setattr(acceptance.AcceptanceProvider, "call", call)
    assert await acceptance.execute(["csv", "images_pdf", "pdf_rotate", "pdf_merge"]) == 0
    report = json.loads((path / "report.json").read_text())
    assert report["status"] == "PASS" and report["passed"] == 4
    assert report["provider_calls"] == 0 and report["calculated_usage_sar"] == "0"
    assert report["active_orders"] == report["wallet_reserved_halala"] == 0
    cases = {case["case"]: case for case in report["cases"]}
    assert all(case["status"] == "PASS" for case in cases.values())
    assert "Columns" in cases["csv"]["artifacts"][0]["sheets"]
    assert cases["images_pdf"]["artifacts"][0]["pages"] == 2
    assert cases["pdf_rotate"]["artifacts"][0]["rotations"] == [90]
    assert cases["pdf_merge"]["artifacts"][0]["pages"] == 2
    call.assert_not_awaited()
    async with sessions() as db:
        assert await db.scalar(select(func.count(CostHold.id))) == 0
        assert await db.scalar(select(func.count(Ledger.id)).where(Ledger.kind == "capture")) == 4


async def test_long_bilingual_bundle_acceptance_uses_native_export_without_provider(
    tmp_path, monkeypatch
):
    from docx import Document
    from pypdf import PdfReader

    monkeypatch.setattr(acceptance.registry.types["echo"], "admin_only", True)
    path = configure(tmp_path, monkeypatch)
    case = next(c for c in acceptance.cases(acceptance.ASSETS) if c.name == "word_pdf_direct")
    call = AsyncMock(side_effect=AssertionError("no network"))
    monkeypatch.setattr(acceptance.AcceptanceProvider, "call", call)
    assert await acceptance.execute([case.name]) == 0
    report = json.loads((path / "report.json").read_text())
    record = report["cases"][0]
    assert report["provider_calls"] == 0 and report["calculated_usage_sar"] == "0"
    assert report["active_orders"] == report["wallet_reserved_halala"] == 0
    assert record["manual_review_checks"] == list(case.review_checks)
    assert len(PdfReader(path / case.name / "result.pdf").pages) >= 2
    doc = Document(path / case.name / "result.docx")
    assert "\n".join(p.text for p in doc.paragraphs) == case.inputs["text"]
    call.assert_not_awaited()
    async with sessions() as db:
        assert await db.scalar(select(func.count(CostHold.id))) == 0
        assert await db.scalar(select(func.count(Ledger.id)).where(Ledger.kind == "capture")) == 1


@pytest.mark.parametrize(
    "failure", ["missing_sheet", "missing_file", "reordered_images", "reordered_pdf"]
)
async def test_failed_output_contract_never_counts_pass_or_captures_credit(
    tmp_path, monkeypatch, failure
):
    from dataclasses import replace

    monkeypatch.setattr(acceptance.registry.types["echo"], "admin_only", True)
    path = configure(tmp_path, monkeypatch)
    original = acceptance.cases

    def invalid_contract(assets):
        plan = {case.name: case for case in original(assets)}
        if failure == "missing_sheet":
            case = replace(plan["csv"], required_sheets=("Missing",))
        elif failure == "missing_file":
            case = replace(plan["csv"], expected_files=("review.xlsx", "missing.txt"))
        elif failure == "reordered_images":
            case = replace(plan["images_pdf"], pdf_image_sources=("image", "mixed"))
        else:
            case = replace(
                plan["pdf_merge"],
                pdf_page_tokens=tuple(reversed(plan["pdf_merge"].pdf_page_tokens)),
            )
        return [replace(case, name="invalid_contract")]

    monkeypatch.setattr(acceptance, "cases", invalid_contract)
    call = AsyncMock(side_effect=AssertionError("no network"))
    monkeypatch.setattr(acceptance.AcceptanceProvider, "call", call)
    assert await acceptance.execute(["invalid_contract"]) == 1
    report = json.loads((path / "report.json").read_text())
    assert report["status"] == "REVIEW_REQUIRED" and report["passed"] == 0
    assert report["failed"] == 1 and report["provider_calls"] == 0
    assert report["active_orders"] == report["wallet_reserved_halala"] == 0
    assert not report["cases"][0]["artifacts"]
    call.assert_not_awaited()
    async with sessions() as db:
        assert await db.scalar(select(func.count(Ledger.id)).where(Ledger.kind == "capture")) == 0
        assert await db.scalar(select(func.count(Ledger.id)).where(Ledger.kind == "release")) == 1


@pytest.mark.parametrize("failure", ["cap", "transport", "echo", "none"])
async def test_live_adapter_fixtures_keep_failures_costs_and_direct_independent(
    tmp_path, monkeypatch, failure
):
    path = configure(tmp_path, monkeypatch)
    if failure == "cap":
        monkeypatch.setattr(config(), "ai_max_output_tokens", 8)
    templates = [
        Case(
            "translation",
            "text_translation",
            {"text": "Hello 00123", "language": "ar", "style": "formal"},
            ("00123",),
            changed_text_files=("translation.txt",),
            review_checks=("Translate the source into Arabic.",),
        ),
        Case("direct", "text_to_pdf", {"text": "Invoice 00123", "mode": "direct"}, ("00123",)),
    ]
    monkeypatch.setattr(acceptance, "cases", lambda assets: templates)
    calls = []

    def respond(request):
        calls.append(request)
        if failure == "transport":
            raise httpx.ReadTimeout("private body")
        review = "QualityReview" in request.content.decode()
        content = (
            '{"accepted":true,"issues":[]}'
            if review
            else json.dumps(
                {
                    "segments": [
                        {"id": 1, "text": "Hello 00123" if failure == "echo" else "مرحبا 00123"}
                    ]
                }
            )
        )
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": content}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 9 if failure == "cap" else 4},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        cls = acceptance.AcceptanceProvider
        adapter = cls()
        adapter.client = client
        monkeypatch.setattr(acceptance, "AcceptanceProvider", lambda: adapter)
        code = await acceptance.execute()
    report = json.loads((path / "report.json").read_text())
    assert code == (0 if failure == "none" else 1)
    assert report["active_orders"] == report["wallet_reserved_halala"] == 0
    assert report["cases"][1]["status"] == "PASS"
    assert report["provider_calls"] == (2 if failure in {"none", "echo"} else 1)
    assert report["cases"][0]["manual_review_checks"] == ["Translate the source into Arabic."]
    if failure == "echo":
        assert report["cases"][0]["status"] == "FAIL"
        assert not report["cases"][0]["artifacts"]
    if failure == "none":
        assert [e["stage"] for e in report["cases"][0]["diagnostics"]] == ["generation", "review"]
        assert report["cases"][0]["diagnostics"][-1]["accepted"] is True
        assert Decimal(report["calculated_usage_sar"]) > 0
    async with sessions() as db:
        assert await db.scalar(select(func.count(User.id))) == 1
        assert await db.scalar(select(func.count(Order.id))) == 2
        if failure == "echo":
            failed = report["cases"][0]
            assert failed["error"] == "acceptance_text_unchanged"
            assert (
                await db.scalar(select(func.count(Ledger.id)).where(Ledger.kind == "capture")) == 1
            )  # Only the independent direct case succeeds.
            assert (
                await db.scalar(select(func.count(Ledger.id)).where(Ledger.kind == "release")) == 1
            )
        holds = list((await db.scalars(select(CostHold))).all())
        assert all(
            h.status == ("uncertain" if failure == "transport" else "settled") for h in holds
        )
        assert await db.scalar(select(func.count(CostUsage.id))) == (
            0 if failure == "transport" else len(holds)
        )
        if failure == "cap":
            assert (await db.get(Setting, "PROVIDER_PAUSED")).value == {"value": True}
    assert "private body" not in str(report) and "test-only-key" not in str(report)


async def test_existing_test_subject_aborts_before_seed_or_provider(tmp_path, monkeypatch):
    configure(tmp_path, monkeypatch)
    monkeypatch.setattr(
        acceptance, "cases", lambda assets: pytest.fail("fixtures prepared before freshness guard")
    )
    async with sessions.begin() as db:
        db.add(User(id=123))
    with pytest.raises(ServiceError, match="acceptance_fresh_database_required"):
        await acceptance.execute()
    async with sessions() as db:
        assert await db.scalar(select(func.count(Ledger.id))) == 0
