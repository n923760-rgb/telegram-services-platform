"""Upgrade existing service snapshots, not just a freshly seeded test database."""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.db import sessions
from app.core.models import Order, Service
from app.orders.engine import submit
from app.services.base import InputField, InputSchema
from app.services.registry import _input_contract, registry
from app.wallet.ledger import balance
from app.workers.main import shutdown, startup
from app.workers.runner import execute_job
from tests.test_foundation import Delivery, fund, job_for


async def test_legacy_service_snapshots_upgrade_without_cancelling_unchanged_order():
    await fund()
    oid = await submit(1, "echo", {"text": "unchanged"}, 100, "legacy-echo")
    expected = {}
    async with sessions.begin() as db:
        for slug, cls in registry.types.items():
            row = await db.get(Service, slug)
            # Exact old serialization: the two new InputField keys were absent.
            old = _input_contract(cls.input_schema.model_dump())
            row.input_schema = old
            row.enabled, row.price_halala = True, 777
            expected[slug] = (row.version, old)
    async with sessions.begin() as db:
        await registry.sync(db)
    # A subsequent startup is idempotent after snapshots have been rewritten.
    async with sessions.begin() as db:
        await registry.sync(db)
        for slug, cls in registry.types.items():
            row = await db.get(Service, slug)
            assert row.version == expected[slug][0]
            assert row.input_schema == cls.input_schema.model_dump()
            assert row.enabled and row.price_halala == 777
    await execute_job({"delivery": Delivery()}, str(await job_for(oid)))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (900, 0)


@pytest.mark.parametrize(
    "change", [{"single_line": True}, {"skip_key": "document_no_title"}, {"unknown": False}]
)
async def test_registry_still_rejects_real_or_unknown_same_version_changes(change):
    async with sessions.begin() as db:
        row = await db.get(Service, "echo")
        changed = deepcopy(row.input_schema)
        changed["fields"][0].update(change)
        row.input_schema = changed
    with pytest.raises(ValueError, match="Bump the plugin version"):
        async with sessions.begin() as db:
            await registry.sync(db)


def test_contract_default_normalization_is_recursive_and_does_not_mutate():
    schema = InputSchema(
        fields=[
            InputField(
                name="form",
                kind="form",
                prompt_key="input_text",
                fields=[InputField(name="text", prompt_key="input_text")],
            )
        ]
    ).model_dump()
    original = deepcopy(schema)
    legacy = _input_contract(schema)
    assert schema == original
    assert "single_line" not in legacy["fields"][0]["fields"][0]
    assert "skip_key" not in legacy["fields"][0]
    assert _input_contract(legacy) == legacy


async def test_worker_shutdown_after_failed_startup_preserves_original_error(monkeypatch):
    async def fail_sync(db):
        raise ValueError("original startup failure")

    monkeypatch.setattr(registry, "sync", fail_sync)
    ctx = {}
    with pytest.raises(ValueError, match="original startup failure"):
        await startup(ctx)
    await shutdown(ctx)
    close = AsyncMock()
    await shutdown({"bot": SimpleNamespace(session=SimpleNamespace(close=close))})
    close.assert_awaited_once()
