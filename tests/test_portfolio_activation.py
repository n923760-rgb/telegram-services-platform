from copy import deepcopy
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import func, select

from app.core.db import sessions
from app.core.models import Ledger, Service, ServiceActivationChange, ServiceActivationTask
from app.core.settings import config
from app.ops import activation, readiness, service_portfolio
from app.services.base import WORKER_REQUIREMENTS, ServiceError
from app.services.registry import registry
from app.wallet.ledger import balance


@pytest.fixture
async def ready(monkeypatch):
    monkeypatch.setattr(registry.types["echo"], "admin_only", True)
    monkeypatch.setattr(config(), "admin_ids", [7])
    monkeypatch.setattr(config(), "ai_enabled", True)
    provider = SimpleNamespace(upper_bound=lambda *args: Decimal("1"))
    monkeypatch.setattr(readiness, "provider", lambda: provider)
    capabilities = dict.fromkeys(WORKER_REQUIREMENTS, True)
    probe = AsyncMock(return_value=capabilities)
    monkeypatch.setattr(service_portfolio, "probe_worker", probe)
    async with sessions.begin() as db:
        for slug in service_portfolio.customer_slugs():
            row = await db.get(Service, slug)
            row.enabled, row.price_halala, row.price_stars = False, 777, 37
    return capabilities, probe


async def test_read_only_inventory_does_not_expose_orders_or_change_prices(ready):
    from app.orders.engine import submit
    from tests.csv_review_fixtures import inputs
    from tests.test_foundation import fund

    await fund()
    async with sessions.begin() as db:
        (await db.get(Service, "csv_review")).enabled = True
    oid = await submit(1, "csv_review", inputs(), 777, "inventory")
    report, _ = await service_portfolio.inspect()
    assert report["status"] == "ready" and report["customer_services"] == 18
    assert "echo" not in str(report) and "local_ocr" not in str(report)
    assert str(oid) not in str(report) and "orders" not in report
    assert (
        next(row for row in report["services"] if row["slug"] == "csv_review")["active_orders"] == 1
    )
    async with sessions() as db:
        assert await db.scalar(select(func.count()).select_from(ServiceActivationChange)) == 0
        assert await db.scalar(select(func.count()).select_from(Ledger)) == 2
        assert (await balance(db, 1)).reserved == 777
        assert (await db.get(Service, "meeting_minutes")).price_halala == 777


async def test_all_public_services_enable_with_individual_audit_and_convergent_retry(ready):
    report = await service_portfolio.enable_all()
    assert report["status"] == "enabled" and len(report["newly_enabled"]) == 18
    repeated = await service_portfolio.enable_all()
    assert repeated["status"] == "enabled" and repeated["newly_enabled"] == []
    async with sessions() as db:
        audits = list(await db.scalars(select(ServiceActivationChange)))
        assert len(audits) == 18 and all(row.actor_id == 7 and row.new_enabled for row in audits)
        for slug in service_portfolio.customer_slugs():
            row = await db.get(Service, slug)
            assert (row.enabled, row.price_halala, row.price_stars) == (True, 777, 37)
        assert (await db.get(Service, "echo")).enabled
        assert not (await db.get(Service, "local_ocr")).enabled
        assert await db.scalar(select(func.count()).select_from(Ledger)) == 0


@pytest.mark.parametrize(
    "defect",
    ["ai_off", "ai_paused", "native", "version", "schema", "stars_price", "pending", "preview"],
)
async def test_any_preflight_blocker_prevents_all_activation(ready, monkeypatch, defect):
    from uuid import uuid4

    from app.core.models import Setting

    caps, _ = ready
    if defect == "ai_off":
        monkeypatch.setattr(config(), "ai_enabled", False)
    elif defect == "native":
        caps["office_export"] = False
    elif defect == "preview":
        monkeypatch.setattr(config(), "document_visual_review", True)
        caps["pdf_previews"] = False
    async with sessions.begin() as db:
        row = await db.get(Service, "meeting_minutes")
        if defect == "ai_paused":
            db.add(Setting(key="PROVIDER_PAUSED", value={"value": True}))
        elif defect == "version":
            row.version = "old"
        elif defect == "schema":
            schema = deepcopy(row.input_schema)
            schema["fields"][0]["max_length"] = 99
            row.input_schema = schema
        elif defect == "stars_price":
            monkeypatch.setattr(config(), "stars_enabled", True)
            row.price_stars = None
        elif defect == "pending":
            key = uuid4()
            db.add(
                ServiceActivationChange(
                    id=key,
                    actor_id=7,
                    service_slug=row.slug,
                    old_enabled=True,
                    new_enabled=False,
                    snapshot_hash="0" * 64,
                    snapshot={"orders": [], "charges": []},
                )
            )
            await db.flush()
            db.add(ServiceActivationTask(change_id=key))
    report = await service_portfolio.enable_all()
    assert report["status"] == "blocked" and report["newly_enabled"] == []
    assert any(row["blockers"] for row in report["services"])
    async with sessions() as db:
        rows = list(
            await db.scalars(
                select(Service).where(Service.slug.in_(service_portfolio.customer_slugs()))
            )
        )
        assert all(not row.enabled for row in rows)
        assert await db.scalar(select(func.count()).select_from(ServiceActivationChange)) == (
            1 if defect == "pending" else 0
        )


async def test_optional_native_ocr_is_disclosed_without_blocking_ai_fallback(ready):
    caps, _ = ready
    caps["native_ocr"] = False
    report, _ = await service_portfolio.inspect()
    row = next(row for row in report["services"] if row["slug"] == "image_to_text")
    assert report["status"] == "ready"
    assert row["warnings"] == ["worker_optional_missing:native_ocr"] and not row["blockers"]


async def test_inventory_separates_paused_optional_modes_from_direct_services(ready):
    from app.core.models import Setting

    async with sessions.begin() as db:
        db.add(Setting(key="PROVIDER_PAUSED", value={"value": True}))
    report, _ = await service_portfolio.inspect()
    for row in report["services"]:
        if row["ai_policy"] == "required":
            assert "provider_config" in row["blockers"]
        elif row["ai_policy"] == "conditional":
            assert "ai_options_unavailable" in row["warnings"]
            assert "provider_config" not in row["blockers"]
        else:
            assert not row["warnings"] and "provider_config" not in row["blockers"]
    async with sessions() as db:
        assert await db.scalar(select(func.count()).select_from(ServiceActivationChange)) == 0
        assert await db.scalar(select(func.count()).select_from(Ledger)) == 0


async def test_unauthorized_actor_is_rejected_before_probes_or_mutation(ready):
    _, probe = ready
    with pytest.raises(ServiceError, match="not_allowed"):
        await service_portfolio.enable_all(9)
    probe.assert_not_awaited()


async def test_changed_snapshot_stops_remaining_services_and_reports_partial_progress(
    ready, monkeypatch
):
    original = activation.change_activation
    slugs = service_portfolio.customer_slugs()

    async def concurrent_change(slug, *args, **kwargs):
        if slug == slugs[1]:
            async with sessions.begin() as db:
                (await db.get(Service, slug)).price_stars = 38
        return await original(slug, *args, **kwargs)

    monkeypatch.setattr(activation, "change_activation", concurrent_change)
    report = await service_portfolio.enable_all()
    assert report["status"] == "partial" and report["newly_enabled"] == slugs[:1]
    assert report["error"] == "admin_activation_changed"
    async with sessions() as db:
        assert (await db.get(Service, slugs[0])).enabled
        assert not (await db.get(Service, slugs[1])).enabled
        assert await db.scalar(select(func.count()).select_from(ServiceActivationChange)) == 1


async def test_mixed_paths_do_not_use_fabricated_customer_inputs(ready, monkeypatch):
    def forbidden(*args):
        raise AssertionError("do not fabricate customer inputs")

    monkeypatch.setattr(registry.types["text_to_office"], "needs_ai", forbidden)
    report, _ = await service_portfolio.inspect()
    assert report["status"] == "ready"
