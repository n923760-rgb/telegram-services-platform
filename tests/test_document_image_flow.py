from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select

from app.core.db import sessions
from app.core.models import CostUsage, Job, Order, Service
from app.core.settings import config
from app.orders.engine import submit
from app.providers.storage import LocalStorage
from app.services.document_image_enhancement.test_service import picture
from app.wallet.ledger import balance
from app.workers.runner import execute_job
from tests.test_file_layers import Provider
from tests.test_foundation import fund, job_for
from tests.test_navigation import flow  # noqa: F401
from tests.test_real_services import Delivery


async def setup(tmp_path, monkeypatch, data=None):
    from app.providers import runtime

    await fund()
    monkeypatch.setattr(config(), "ai_enabled", True)
    monkeypatch.setattr(config(), "storage_root", tmp_path)
    provider = Provider(['{"choice":"contrast"}', '{"accepted":true,"issues":[]}'])
    monkeypatch.setattr(runtime, "provider", lambda: provider)
    async with sessions.begin() as db:
        service = await db.get(Service, "document_image_enhancement")
        assert not service.enabled
        service.enabled = True
        price = service.price_halala
    store = LocalStorage(tmp_path)
    source = store.save(1, "source.png", picture() if data is None else data, "image/png")
    oid = await submit(1, "document_image_enhancement", {"image": source.key}, price, "enhance")
    return oid, await job_for(oid), store, price


async def test_local_enhancement_delivers_three_files_and_captures_once(tmp_path, monkeypatch):
    oid, jid, store, price = await setup(tmp_path, monkeypatch)
    delivery = Delivery(store)
    await execute_job({"delivery": delivery}, str(jid))
    await execute_job({"delivery": delivery}, str(jid))
    assert delivery.files[2] == ("received.png", picture())
    assert len(delivery.files) == 3
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000 - price, 0)
        assert await db.scalar(select(func.count(CostUsage.id))) == 2
    assert not list(tmp_path.glob("[0-9]*/*/*"))


async def test_invalid_image_failure_releases_and_cleans(tmp_path, monkeypatch):
    oid, jid, store, _ = await setup(tmp_path, monkeypatch, b"bad image")
    await execute_job({"delivery": Delivery(store)}, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "failed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
    assert not list(tmp_path.glob("[0-9]*/*/*"))


@pytest.mark.parametrize("old_version", ["1", "3"])
async def test_send_retry_uses_cached_enhanced_files(tmp_path, monkeypatch, old_version):
    from unittest.mock import AsyncMock

    from app.builders import document_image

    oid, jid, store, _ = await setup(tmp_path, monkeypatch)
    delivery = Delivery(store)
    send = delivery.send
    delivery.send = AsyncMock(side_effect=OSError("offline"))
    await execute_job({"delivery": delivery}, str(jid))
    async with sessions.begin() as db:
        job = await db.get(Job, jid)
        job.next_run_at = datetime.now(UTC) - timedelta(seconds=1)
        # A previously prepared v1 result must be replayed, never regenerated.
        order = await db.get(Order, oid)
        order.service_version = old_version
        if old_version == "1":
            # Reproduce the old received/enhanced/comparison artifact ordering.
            cached = dict(order.result)
            cached["artifacts"] = [cached["artifacts"][2], *cached["artifacts"][:2]]
            order.result = cached
    monkeypatch.setattr(document_image, "build", lambda *args: pytest.fail("No second enhancement"))
    # Service imports the builder callable directly; also replace that binding.
    from app.services.document_image_enhancement import service

    monkeypatch.setattr(service, "build", document_image.build)
    delivery.send = send
    await execute_job({"delivery": delivery}, str(jid))
    assert len(delivery.files) == 3
    assert delivery.files[0][0] == ("received.png" if old_version == "1" else "enhanced.png")
    assert ("received.png", picture()) in delivery.files
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"


@pytest.mark.parametrize("old_version", ["1", "2", "3"])
async def test_old_upgrade_keeps_admin_settings_and_releases_incompatible_job(
    tmp_path, monkeypatch, old_version
):
    from copy import deepcopy

    from app.services.base import InputField
    from app.services.registry import registry

    oid, jid, store, _ = await setup(tmp_path, monkeypatch)
    async with sessions.begin() as db:
        row = await db.get(Service, "document_image_enhancement")
        old = deepcopy(row.input_schema)
        if old_version == "1":
            old["fields"][0].pop("preserve_image")
            old["fields"].append(
                InputField(
                    name="mode",
                    prompt_key="document_image_mode",
                    choices=["contrast", "grayscale"],
                    choice_keys=["document_image_contrast", "document_image_grayscale"],
                ).model_dump()
            )
        row.version, row.input_schema, row.price_halala = old_version, old, 777
        order = await db.get(Order, oid)
        order.service_version, order.input_schema_snapshot = old_version, old
        if old_version == "1":
            order.inputs = {**order.inputs, "mode": "contrast"}
    async with sessions.begin() as db:
        await registry.sync(db)
        row = await db.get(Service, "document_image_enhancement")
        assert row.version == "4" and row.enabled and row.price_halala == 777
    await execute_job({"delivery": Delivery(store)}, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "cancelled"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)


async def test_image_upload_reaches_price_confirmation_without_engine_question(flow, monkeypatch):  # noqa: F811
    from app.files import telegram
    from tests.test_bounded_fixes import button_by_prefix

    transport, message, callback, state = flow
    await fund()
    monkeypatch.setattr(config(), "ai_enabled", True)
    async with sessions.begin() as db:
        (await db.get(Service, "document_image_enhancement")).enabled = True

    async def receive(message, kind, owner, *, preserve_image=False):
        assert (kind, owner, preserve_image) == ("image", 1, True)
        return "1/" + "a" * 32 + "/input.png"

    monkeypatch.setattr(telegram, "receive", receive)
    await message("/start")
    await callback("service:document_image_enhancement")
    await message("uploaded image")
    assert await state.get_state() == "confirm"
    assert button_by_prefix(transport.messages[-1].reply_markup, "confirm:")
    async with sessions() as db:
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)


async def test_no_reliable_improvement_releases_without_delivering_image(tmp_path, monkeypatch):
    from app.providers import runtime

    oid, jid, store, price = await setup(tmp_path, monkeypatch)
    provider = Provider(['{"choice":"none"}', '{"accepted":true,"issues":[]}'])
    monkeypatch.setattr(runtime, "provider", lambda: provider)
    delivery = Delivery(store)
    await execute_job({"delivery": delivery}, str(jid))
    assert not delivery.files and provider.calls == 2
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "failed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
    assert not list(tmp_path.glob("[0-9]*/*/*"))
