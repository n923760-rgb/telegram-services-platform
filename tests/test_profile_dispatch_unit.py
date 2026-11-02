import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.settings import config
from app.publications import dispatch as flow


@pytest.fixture(autouse=True)
def database():
    pass


@pytest.fixture
def enabled(monkeypatch):
    monkeypatch.setattr(config(), "publications_enabled", True)
    monkeypatch.setattr(config(), "admin_ids", [11])


async def test_disabled_does_not_read_or_apply(monkeypatch):
    monkeypatch.setattr(config(), "publications_enabled", False)
    read = AsyncMock()
    monkeypatch.setattr(flow, "candidates", read)
    assert await flow.dispatch_profiles({}) == {"selected": 0, "applied": 0, "deferred": 0}
    read.assert_not_awaited()


async def test_failure_is_redacted_and_does_not_starve_next_row(enabled, monkeypatch, caplog):
    rows = [(uuid4(), 11, datetime.now(UTC)), (uuid4(), 11, datetime.now(UTC))]
    monkeypatch.setattr(flow, "candidates", AsyncMock(return_value=rows))
    transfer = AsyncMock(side_effect=[ValueError("private-source-secret"), True])
    monkeypatch.setattr(flow, "transfer_purchased", transfer)
    ctx = {}
    assert await flow.dispatch_profiles(ctx) == {"selected": 2, "applied": 1, "deferred": 1}
    assert ctx["profile_dispatch_cursor"] == (rows[-1][2], rows[-1][0])
    assert "private-source-secret" not in caplog.text


async def test_cursor_wraps_and_existing_receipt_is_not_counted_as_new(enabled, monkeypatch):
    row = (uuid4(), 11, datetime.now(UTC))
    scan = AsyncMock(side_effect=[[], [row]])
    monkeypatch.setattr(flow, "candidates", scan)
    monkeypatch.setattr(flow, "transfer_purchased", AsyncMock(return_value=False))
    ctx = {"profile_dispatch_cursor": (row[2], row[0])}
    assert (await flow.dispatch_profiles(ctx))["applied"] == 0
    assert scan.await_count == 2


async def test_interruption_propagates_without_acknowledging_pending_work(enabled, monkeypatch):
    monkeypatch.setattr(
        flow, "candidates", AsyncMock(return_value=[(uuid4(), 11, datetime.now(UTC))])
    )
    monkeypatch.setattr(flow, "transfer_purchased", AsyncMock(side_effect=asyncio.CancelledError))
    with pytest.raises(asyncio.CancelledError):
        await flow.dispatch_profiles({})
