from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import DBAPIError

from app.core.db import sessions
from app.core.models import CostHold, CostUsage, Ledger, Order, Setting
from app.core.settings import config
from app.ops import order_diagnostics
from app.ops.costs import reserve_call, settle_call, uncertain_call
from app.orders.engine import fail_locked
from app.services.base import ServiceError
from tests.test_operations import running


@pytest.fixture
def owner(monkeypatch):
    monkeypatch.setattr(config(), "admin_ids", [7])


async def test_snapshot_reports_release_overrun_unknown_exposure_without_writes(owner):
    oid, jid = await running()
    unknown = await reserve_call(jid, 1, Decimal(".01"))
    await uncertain_call(unknown)
    settled = await reserve_call(jid, 1, Decimal(".02"))
    with pytest.raises(ServiceError, match="provider_usage"):
        await settle_call(settled, Decimal(".03"), 10, 15532)
    async with sessions.begin() as db:
        order = await db.get(Order, oid)
        order.inputs = {"text": "PRIVATE CUSTOMER TEXT"}
        await fail_locked(db, order, "provider_usage")
    first = await order_diagnostics.inspect(str(oid)[:8].upper())
    second = await order_diagnostics.inspect(str(oid))
    assert first == second
    assert first["wallet"]["test_credit_release_confirmed"] is True
    assert first["provider"]["paused"] is True
    assert first["observations"] == {"unsettled_cost_holds": 1, "recorded_overruns": 1}
    assert first["actions_performed"] == []
    assert "PRIVATE CUSTOMER TEXT" not in str(first) and "user_id" not in str(first)
    unresolved = next(row for row in first["cost_holds"] if row["status"] == "uncertain")
    assert unresolved["hold_id"] == str(unknown) and unresolved["recorded_sar"] is None
    assert unresolved["recorded_overrun"] is None
    async with sessions() as db:
        assert (await db.get(CostHold, unknown)).status == "uncertain"
        assert (await db.get(Setting, "PROVIDER_PAUSED")).value == {"value": True}
        assert await db.scalar(select(func.count()).select_from(Ledger)) == 3
        assert await db.scalar(select(func.count()).select_from(CostUsage)) == 1


async def test_unknown_order_fails_without_private_data(owner):
    with pytest.raises(ServiceError, match="order_not_found"):
        await order_diagnostics.inspect("12345678")


async def test_ambiguous_prefix_requires_full_uuid(owner):
    original, _ = await running()
    ids = [UUID(f"abcdef12-0000-0000-0000-{tail:012d}") for tail in (1, 2)]
    async with sessions.begin() as db:
        source = await db.get(Order, original)
        for number, identifier in enumerate(ids):
            db.add(
                Order(
                    id=identifier,
                    user_id=source.user_id,
                    service_slug=source.service_slug,
                    price_halala=100,
                    status="failed",
                    inputs={"text": "fixture"},
                    input_hash="0" * 64,
                    idempotency_key=f"diagnostic-prefix-{number}",
                )
            )
    with pytest.raises(ServiceError, match="order_ambiguous"):
        await order_diagnostics.inspect("ABCDEF12")
    report = await order_diagnostics.inspect(str(ids[0]))
    assert report["status"] == "observed" and report["job"] is None


async def test_row_limit_returns_no_partial_financial_report(owner, monkeypatch):
    oid, jid = await running()
    await reserve_call(jid, 1, Decimal(".01"))
    monkeypatch.setattr(order_diagnostics, "MAX_ROWS", 0)
    with pytest.raises(ServiceError, match="diagnostic_limit"):
        await order_diagnostics.inspect(str(oid))


async def test_snapshot_transaction_rejects_accidental_write(owner):
    from sqlalchemy import text

    async with sessions.begin() as db:
        await db.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"))
        with pytest.raises(DBAPIError) as error:
            await db.execute(
                text("UPDATE settings SET value = value WHERE key = 'PROVIDER_PAUSED'")
            )
        assert getattr(error.value.orig, "sqlstate", None) == "25006"
        await db.rollback()


@pytest.mark.parametrize("value", [None, {}, {"value": "false"}])
async def test_invalid_pause_state_is_not_reported_as_safe(owner, value):
    oid, _ = await running()
    async with sessions.begin() as db:
        db.add(Setting(key="PROVIDER_PAUSED", value=value))
    with pytest.raises(ServiceError, match="provider_state_invalid"):
        await order_diagnostics.inspect(str(oid))
