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


@pytest.mark.parametrize("old_version", ["3", "4"])
async def test_office_upgrade_preserves_admin_settings_and_releases_old_job(
    monkeypatch,
    old_version,
):
    from app.core.settings import config

    monkeypatch.setattr(config(), "ai_enabled", True)
    await fund()
    async with sessions.begin() as db:
        row = await db.get(Service, "text_to_office")
        old = deepcopy(row.input_schema)
        old["fields"].extend(
            [
                InputField(
                    name="mode",
                    prompt_key="document_mode" if old_version == "3" else "word_mode",
                    choices=["direct", "smart"] if old_version == "3" else ["smart", "direct"],
                    choice_keys=["document_direct", "document_smart"]
                    if old_version == "3"
                    else ["word_professional", "word_literal"],
                    when={"target": ["word"]},
                ).model_dump(),
                InputField(
                    name="title",
                    prompt_key="document_title",
                    max_length=200,
                    required=False,
                    skip_key="document_no_title",
                    single_line=True,
                    when={"target": ["word"], "mode": ["direct"]},
                ).model_dump(),
            ]
        )
        row.enabled, row.price_halala = True, 777
    oid = await submit(
        1,
        "text_to_office",
        {"target": "word", "text": "unchanged"},
        777,
        "old-office",
    )
    # Reproduce persisted pre-upgrade snapshots after creating a real reservation/job.
    async with sessions.begin() as db:
        row = await db.get(Service, "text_to_office")
        row.version, row.input_schema = old_version, old
        order = await db.get(Order, oid)
        order.service_version, order.input_schema_snapshot = old_version, old
    async with sessions.begin() as db:
        await registry.sync(db)
    async with sessions.begin() as db:
        await registry.sync(db)
        row = await db.get(Service, "text_to_office")
        assert row.version == "5" and row.enabled and row.price_halala == 777
        assert row.input_schema == registry.types["text_to_office"].input_schema.model_dump()
        assert (await db.get(Service, "text_to_pdf")).version == "3"
    await execute_job({"delivery": Delivery()}, str(await job_for(oid)))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "cancelled"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)


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


async def test_worker_delivery_and_refunds_share_selected_test_api(monkeypatch):
    from app.core.settings import config

    monkeypatch.setattr(config(), "telegram_api_environment", "test")
    ctx = {"redis": SimpleNamespace()}
    await startup(ctx)
    try:
        token = config().bot_token.get_secret_value()
        assert ctx["stars"].bot is ctx["bot"]
        assert ctx["delivery"].bot is ctx["bot"]
        assert ctx["bot"].session.api.api_url(token, "refundStarPayment") == (
            f"https://api.telegram.org/bot{token}/test/refundStarPayment"
        )
    finally:
        await shutdown(ctx)
