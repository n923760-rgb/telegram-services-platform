from decimal import Decimal
from io import BytesIO
from types import SimpleNamespace

import pytest
from PIL import Image
from pypdf import PdfReader

from app.ops import service_acceptance as acceptance
from app.ops.acceptance_cases import Case, cases, picture, source_pdf
from app.services.base import ServiceError


@pytest.fixture(autouse=True)
def database():
    yield


def test_exact_portfolio_and_modes_use_valid_synthetic_inputs():
    values = cases(acceptance.ASSETS)
    assert len(values) == 28 and len({case.slug for case in values}) == 16
    assert {c.inputs["language"] for c in values if c.slug == "cv_formatting"} == {
        "ar",
        "en",
        "bilingual",
    }
    assert {c.inputs["mode"] for c in values if c.slug == "text_to_pdf"} == {"direct", "smart"}


def valid_cfg(tmp_path):
    return SimpleNamespace(
        app_env="test",
        database_url=SimpleNamespace(
            get_secret_value=lambda: (
                "postgresql+asyncpg://fixture@localhost/svc_abcdef123456_acceptance_test"
            )
        ),
        storage_root=tmp_path / "acceptance-abcdef123456",
        admin_ids=[acceptance.OWNER],
        stars_enabled=False,
        ai_enabled=True,
        max_daily_cost_sar=Decimal("5"),
        max_cost_per_user_per_day=Decimal("5"),
        max_job_cost_sar=Decimal(".75"),
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("app_env", "production"),
        ("stars_enabled", True),
        ("ai_enabled", False),
        ("admin_ids", [1]),
        ("max_daily_cost_sar", Decimal("6")),
        ("max_cost_per_user_per_day", Decimal("0")),
        ("max_job_cost_sar", Decimal("1")),
    ],
)
def test_execution_guard_rejects_wrong_environment_and_budgets(tmp_path, monkeypatch, field, value):
    cfg = valid_cfg(tmp_path)
    setattr(cfg, field, value)
    monkeypatch.setattr(acceptance, "config", lambda: cfg)
    with pytest.raises(ServiceError):
        acceptance.isolated()


def test_production_database_rejected_before_connecting(tmp_path, monkeypatch):
    cfg = valid_cfg(tmp_path)
    cfg.database_url = SimpleNamespace(
        get_secret_value=lambda: "postgresql+asyncpg://fixture@localhost/services"
    )
    monkeypatch.setattr(acceptance, "config", lambda: cfg)
    with pytest.raises(ServiceError, match="acceptance_isolation_required"):
        acceptance.isolated()


def test_exact_isolated_names_allowed_without_mutation(tmp_path, monkeypatch):
    cfg = valid_cfg(tmp_path)
    monkeypatch.setattr(acceptance, "config", lambda: cfg)
    assert acceptance.isolated() == cfg.storage_root
    assert not cfg.storage_root.exists()


def test_real_synthetic_assets_and_readback_guards():
    data = source_pdf()
    case = Case("pdf", "pdf_tools", {}, ("00123",))
    result = acceptance.inspect_output("result.pdf", data, case)
    assert result["pages"] == 1 and len(result["sha256"]) == 64
    assert "00123" in PdfReader(BytesIO(data)).pages[0].extract_text()
    with Image.open(BytesIO(picture(shaded=True, mixed=True))) as image:
        assert image.size == (1400, 700)
    with pytest.raises(ServiceError, match="acceptance_source_token_missing"):
        acceptance.inspect_output("result.txt", b"00124", case)
    with pytest.raises(ServiceError, match="acceptance_output_invalid"):
        acceptance.inspect_output("result.exe", b"00123", case)


def test_provider_whole_run_bound_is_never_refunded(monkeypatch):
    monkeypatch.setattr(acceptance.OpenAICompatible, "upper_bound", lambda *a: Decimal("2"))
    adapter = acceptance.AcceptanceProvider()
    assert adapter.upper_bound({}, "", "", []) == Decimal("2")
    assert adapter.upper_bound({}, "", "", []) == Decimal("2")
    with pytest.raises(ServiceError, match="acceptance_cost_cap"):
        adapter.upper_bound({}, "", "", [])
    assert adapter.bounds == Decimal("4")
    adapter.calls = acceptance.CALLS
    with pytest.raises(ServiceError):
        adapter.upper_bound({}, "", "", [])
