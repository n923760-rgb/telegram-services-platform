"""Native PPTX quality gates preserve repair, capture/release and cached delivery."""

import json
from datetime import UTC, datetime, timedelta
from io import BytesIO

import pytest
from pptx import Presentation

from app.core.db import sessions
from app.core.models import Job, Order, Service
from app.orders.engine import submit
from app.services.registry import registry
from app.wallet.ledger import balance
from app.workers.runner import deliver_failures, execute_job
from tests.test_foundation import job_for
from tests.test_pptx_quality import sample_plan
from tests.test_real_services import setup


@pytest.mark.parametrize("repair", [False, True])
async def test_pptx_native_table_delivery_captures_once_after_bounded_repair(
    tmp_path, monkeypatch, repair
):
    responses = [json.dumps({"deck": sample_plan()})]
    if repair:
        responses.insert(
            0, json.dumps({"deck": {"slides": [{"title": "Dense", "bullets": ["W" * 180] * 6}]}})
        )
    _, provider, delivery, ctx, price = await setup(
        "text_to_pptx", responses, tmp_path, monkeypatch
    )
    oid = await submit(1, "text_to_pptx", {"text": "الطلبات"}, price, "native-pptx")
    jid = await job_for(oid)
    await execute_job(ctx, str(jid))
    await execute_job(ctx, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000 - price, 0)
    assert provider.calls == len(responses) and len(delivery.files) == 1
    prs = Presentation(BytesIO(delivery.files[0][1]))
    native = next(s.table for s in prs.slides[2].shapes if s.has_table)
    assert native.cell(1, 0).text == "00123" and native.cell(1, 2).text == "125.50"
    assert not list(tmp_path.glob("[0-9]*/*/*"))


async def test_pptx_density_invalid_after_one_repair_releases_and_notifies_once(
    tmp_path, monkeypatch
):
    invalid = json.dumps({"deck": {"slides": [{"title": "Dense", "bullets": ["W" * 180] * 6}]}})
    _, provider, delivery, ctx, price = await setup(
        "text_to_pptx", [invalid, invalid], tmp_path, monkeypatch
    )
    oid = await submit(1, "text_to_pptx", {"text": "Content"}, price, "dense-pptx")
    await execute_job(ctx, str(await job_for(oid)))
    await deliver_failures(ctx)
    await deliver_failures(ctx)
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "failed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
    assert provider.calls == 2 and not delivery.files
    assert delivery.errors == [(1, oid, "provider_invalid")]


async def test_pptx_builder_failure_does_not_capture_credit(tmp_path, monkeypatch):
    from app.builders import pptx

    _, provider, delivery, ctx, price = await setup(
        "text_to_pptx", [json.dumps({"deck": sample_plan()})], tmp_path, monkeypatch
    )

    def failed(*args):
        raise ValueError("synthetic render failure")

    monkeypatch.setattr(pptx, "build", failed)
    oid = await submit(1, "text_to_pptx", {"text": "Content"}, price, "render-pptx")
    await execute_job(ctx, str(await job_for(oid)))
    await deliver_failures(ctx)
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "failed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
    assert provider.calls == 1 and not delivery.files and len(delivery.errors) == 1


async def test_pptx_delivery_retry_reuses_native_file_before_single_capture(tmp_path, monkeypatch):
    _, provider, delivery, ctx, price = await setup(
        "text_to_pptx", [json.dumps({"deck": sample_plan()})], tmp_path, monkeypatch
    )
    oid = await submit(1, "text_to_pptx", {"text": "Content"}, price, "retry-pptx")
    jid = await job_for(oid)
    original_send = delivery.send

    async def unavailable(*args):
        raise ConnectionError("synthetic delivery unavailable")

    monkeypatch.setattr(delivery, "send", unavailable)
    await execute_job(ctx, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "delivering"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000 - price, price)
    monkeypatch.setattr(delivery, "send", original_send)
    async with sessions.begin() as db:
        (await db.get(Job, jid)).next_run_at = datetime.now(UTC) - timedelta(seconds=1)
    await execute_job(ctx, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000 - price, 0)
    assert provider.calls == 1 and len(delivery.files) == 1
    assert any(s.has_table for s in Presentation(BytesIO(delivery.files[0][1])).slides[2].shapes)


async def test_pptx_version_upgrade_keeps_admin_settings_and_releases_old_pending_job(
    tmp_path, monkeypatch
):
    _, provider, delivery, ctx, price = await setup("text_to_pptx", [], tmp_path, monkeypatch)
    oid = await submit(1, "text_to_pptx", {"text": "Content"}, price, "old-pptx")
    async with sessions.begin() as db:
        row = await db.get(Service, "text_to_pptx")
        row.version, row.price_halala, row.enabled = "1", 777, True
        (await db.get(Order, oid)).service_version = "1"
    async with sessions.begin() as db:
        await registry.sync(db)
    async with sessions() as db:
        row = await db.get(Service, "text_to_pptx")
        assert row.version == "2" and row.price_halala == 777 and row.enabled
    await execute_job(ctx, str(await job_for(oid)))
    await execute_job(ctx, str(await job_for(oid)))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "cancelled"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
    assert provider.calls == 0 and not delivery.files
