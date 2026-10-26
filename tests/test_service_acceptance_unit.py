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
    assert len(values) == 31 and len({case.slug for case in values}) == 18
    assert {c.inputs["language"] for c in values if c.slug == "cv_formatting"} == {
        "ar",
        "en",
        "bilingual",
    }
    assert {c.inputs.get("mode", "smart") for c in values if c.slug == "text_to_pdf"} == {
        "direct",
        "smart",
    }
    automatic = {"word_smart", "text_pdf_smart", "word_pdf_smart"}
    assert all("mode" not in c.inputs for c in values if c.name in automatic)


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


def test_selected_case_subset_is_explicit_complete_and_canonical():
    templates = cases(acceptance.ASSETS)
    assert acceptance.selected_cases(templates) is templates
    assert [c.name for c in acceptance.selected_cases(templates, ["cv_en", "cv_ar"])] == [
        "cv_ar",
        "cv_en",
    ]
    for invalid in ([], ["cv_en", "cv_en"], ["missing"], ["cv_en", "missing"]):
        with pytest.raises(ServiceError, match="acceptance_case_invalid"):
            acceptance.selected_cases(templates, invalid)


@pytest.mark.parametrize(
    "bad",
    ['{"private-source":"secret"', '{"private-source":"secret"}', '{"accepted":false,"issues":[]}'],
)
async def test_diagnostics_preserve_contract_and_bounded_repair_without_content(monkeypatch, bad):
    import json

    from app.providers.ai import gateway
    from app.providers.ai.base import AIResponse, Usage
    from app.providers.ai.review import QualityReview

    class Provider:
        calls = 0
        schemas = []

        def upper_bound(self, schema, *args):
            self.schemas.append(schema)
            return Decimal(".01")

        async def extract_from_text(self, *args):
            self.calls += 1
            return AIResponse(
                bad if self.calls == 1 else '{"accepted":true,"issues":[]}',
                Usage(1, 2, Decimal(".001")),
            )

    async def reserve(*args):
        return 1

    async def settle(*args, **kwargs):
        pass

    monkeypatch.setattr(gateway, "reserve_call", reserve)
    monkeypatch.setattr(gateway, "settle_call", settle)
    provider = Provider()
    events = []
    ai = acceptance.DiagnosticAI(provider, 1, 1, diagnostics=events)
    result = await ai._extract(QualityReview, "private-source")
    assert type(result) is QualityReview and result.accepted
    assert provider.calls == 2
    assert provider.schemas == [QualityReview.model_json_schema()] * 2
    assert events[0]["stage"] == "review" and events[0]["outcome"] == "invalid"
    assert events[1] == {
        "call": 2,
        "stage": "review",
        "outcome": "valid",
        "accepted": True,
        "issues": [],
    }
    assert "secret" not in json.dumps(events) and "private-source" not in json.dumps(events)


async def test_diagnostics_distinguish_generation_and_semantic_rejection(monkeypatch):
    from app.builders.schema import StrictModel
    from app.providers.ai import gateway
    from app.providers.ai.base import AIResponse, Usage

    class Candidate(StrictModel):
        value: str

    replies = iter(
        [
            '{"value":"private-source"}',
            '{"accepted":false,"issues":["omission"]}',
            '{"value":"private-source"}',
            '{"accepted":true,"issues":[]}',
        ]
    )

    class Provider:
        calls = 0

        def upper_bound(self, *args):
            return Decimal(".01")

        async def extract_from_text(self, *args):
            self.calls += 1
            return AIResponse(next(replies), Usage(1, 2, Decimal(".001")))

    async def reserve(*args):
        return 1

    async def settle(*args, **kwargs):
        pass

    monkeypatch.setattr(gateway, "reserve_call", reserve)
    monkeypatch.setattr(gateway, "settle_call", settle)
    provider, events = Provider(), []
    ai = acceptance.DiagnosticAI(provider, 1, 1, quality_review=True, diagnostics=events)
    assert (await ai.extract(Candidate, "private-source")).value == "private-source"
    assert [(e["stage"], e["outcome"]) for e in events] == [
        ("generation", "valid"),
        ("review", "valid"),
        ("generation", "valid"),
        ("review", "valid"),
    ]
    assert events[1]["issues"] == ["omission"] and events[1]["accepted"] is False
    assert provider.calls == 4 and "private-source" not in str(events)


def test_targeted_plan_and_invalid_selection_do_not_execute(monkeypatch, capsys):
    import json
    import sys

    monkeypatch.setattr(acceptance, "execute", lambda *args: pytest.fail("execution forbidden"))
    monkeypatch.setattr(sys, "argv", ["service_acceptance", "--case", "cv_en"])
    assert acceptance.main() == 0
    assert json.loads(capsys.readouterr().out)["cases"] == ["cv_en"]
    monkeypatch.setattr(sys, "argv", ["service_acceptance", "--execute", "--case", "unknown"])
    assert acceptance.main() == 1
    assert json.loads(capsys.readouterr().out)["error"] == "acceptance_case_invalid"


async def test_cv_constraint_diagnostics_are_specific_and_content_free(monkeypatch):
    import json

    from app.providers.ai import gateway
    from app.providers.ai.base import AIResponse, Usage
    from app.services.cv_formatting.schema import Inputs, revision_schema
    from tests.cv_fixtures import inputs, revision

    source = inputs("en")
    payload = revision(source)
    payload["bodies"][0]["segments"][0]["text"] += " 99999"

    class Provider:
        calls = 0

        def upper_bound(self, *args):
            return Decimal(".01")

        async def extract_from_text(self, *args):
            self.calls += 1
            return AIResponse(json.dumps(payload), Usage(1, 2, Decimal(".001")))

    async def reserve(*args):
        return 1

    async def settle(*args, **kwargs):
        pass

    monkeypatch.setattr(gateway, "reserve_call", reserve)
    monkeypatch.setattr(gateway, "settle_call", settle)
    provider, events = Provider(), []
    ai = acceptance.DiagnosticAI(provider, 1, 1, quality_review=True, diagnostics=events)
    with pytest.raises(ServiceError, match="provider_invalid"):
        await ai.extract(revision_schema(Inputs.parse(source)), Inputs.parse(source).source())
    assert provider.calls == 2
    assert [e["categories"] for e in events] == [["cv_source_tokens"], ["cv_source_tokens"]]
    assert all(e["stage"] == "generation" and e["outcome"] == "invalid" for e in events)
    for value in ("99999", "sample@example.invalid", "0500123456", "Sam Example"):
        assert value not in json.dumps(events)


@pytest.mark.parametrize(
    "declaration",
    [
        None,
        [],
        {"secret field": "raw data"},
        {"private_code": "private data"},
        {"value_error": "override_label"},
    ],
)
async def test_diagnostic_category_metadata_cannot_copy_raw_errors(monkeypatch, declaration):
    from typing import ClassVar

    from pydantic import model_validator
    from pydantic_core import PydanticCustomError

    from app.builders.schema import StrictModel
    from app.providers.ai import gateway
    from app.providers.ai.base import AIResponse, Usage

    class Candidate(StrictModel):
        diagnostic_categories: ClassVar = declaration
        value: str

        @model_validator(mode="after")
        def reject(self):
            code = (
                "value_error"
                if declaration == {"value_error": "override_label"}
                else "private_code"
            )
            raise PydanticCustomError(code, "private error text", {"secret": self.value})

    class Provider:
        calls = 0

        def upper_bound(self, *args):
            return Decimal(".01")

        async def extract_from_text(self, *args):
            self.calls += 1
            return AIResponse('{"value":"private value"}', Usage(1, 2, Decimal(".001")))

    async def reserve(*args):
        return 1

    async def settle(*args, **kwargs):
        pass

    monkeypatch.setattr(gateway, "reserve_call", reserve)
    monkeypatch.setattr(gateway, "settle_call", settle)
    events = []
    ai = acceptance.DiagnosticAI(Provider(), 1, 1, diagnostics=events)
    with pytest.raises(ServiceError, match="provider_invalid"):
        await ai._extract(Candidate, "private source", attempts=1)
    assert events == [
        {
            "call": 1,
            "stage": "generation",
            "outcome": "invalid",
            "categories": [
                "constraint" if declaration == {"value_error": "override_label"} else "schema_type"
            ],
        }
    ]


NATIVE_CASES = [
    "csv",
    "tables_direct",
    "images_pdf",
    "pdf_extract",
    "pdf_rotate",
    "pdf_merge",
    "word_pdf_direct",
]


def test_native_selection_accepts_requested_provider_free_cases_only():
    chosen = acceptance.native_cases(cases(acceptance.ASSETS), NATIVE_CASES)
    assert {case.name for case in chosen} == set(NATIVE_CASES)


@pytest.mark.parametrize(
    "names",
    [None, [], ["unknown"], ["csv", "csv"], ["csv", "summary"], ["tables_labels"], ["cv_en"]],
)
def test_native_selection_rejects_default_invalid_and_ai_cases(names):
    with pytest.raises(ServiceError):
        acceptance.native_cases(cases(acceptance.ASSETS), names)


async def test_native_provider_never_reaches_parent_network_call(monkeypatch):
    from unittest.mock import AsyncMock

    network = AsyncMock(side_effect=AssertionError("must not call provider"))
    monkeypatch.setattr(acceptance.AcceptanceProvider, "call", network)
    adapter = acceptance.NativeAcceptanceProvider()
    with pytest.raises(ServiceError, match="acceptance_native_provider_forbidden"):
        await adapter.call("unexpected")
    network.assert_not_awaited()
    assert adapter.calls == 0


async def test_native_ai_selection_rejects_before_database_or_output_creation(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(acceptance, "isolated", lambda **kwargs: tmp_path)
    with pytest.raises(ServiceError, match="acceptance_native_requires_no_ai"):
        await acceptance.execute(["summary"], native_only=True)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("native_only", [False, True])
@pytest.mark.parametrize("ai_enabled", [False, True])
def test_isolation_requires_ai_state_matching_execution_mode(
    tmp_path, monkeypatch, native_only, ai_enabled
):
    cfg = valid_cfg(tmp_path)
    cfg.ai_enabled = ai_enabled
    monkeypatch.setattr(acceptance, "config", lambda: cfg)
    if ai_enabled == native_only:
        with pytest.raises(ServiceError, match="acceptance_isolation_required"):
            acceptance.isolated(native_only=native_only)
    else:
        assert acceptance.isolated(native_only=native_only) == cfg.storage_root


@pytest.mark.parametrize(
    "field,value", [("app_env", "production"), ("admin_ids", [1]), ("stars_enabled", True)]
)
def test_native_mode_retains_isolation_guards(tmp_path, monkeypatch, field, value):
    cfg = valid_cfg(tmp_path)
    cfg.ai_enabled = False
    setattr(cfg, field, value)
    monkeypatch.setattr(acceptance, "config", lambda: cfg)
    with pytest.raises(ServiceError, match="acceptance_isolation_required"):
        acceptance.isolated(native_only=True)
