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
from tests.test_foundation import fund, job_for
from tests.test_real_services import Delivery


async def setup(tmp_path, monkeypatch, data=None):
    await fund()
    monkeypatch.setattr(config(), "storage_root", tmp_path)
    async with sessions.begin() as db:
        service = await db.get(Service, "document_image_enhancement")
        assert not service.enabled
        service.enabled = True
        price = service.price_halala
    store = LocalStorage(tmp_path)
    source = store.save(1, "source.png", picture() if data is None else data, "image/png")
    oid = await submit(
        1, "document_image_enhancement", {"image": source.key, "mode": "contrast"}, price, "enhance"
    )
    return oid, await job_for(oid), store, price


async def test_local_enhancement_delivers_three_files_and_captures_once(tmp_path, monkeypatch):
    from app.providers import runtime

    monkeypatch.setattr(runtime, "provider", lambda: pytest.fail("Must not construct AI"))
    oid, jid, store, price = await setup(tmp_path, monkeypatch)
    delivery = Delivery(store)
    await execute_job({"delivery": delivery}, str(jid))
    await execute_job({"delivery": delivery}, str(jid))
    assert delivery.files[0] == ("received.png", picture())
    assert len(delivery.files) == 3
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000 - price, 0)
        assert await db.scalar(select(func.count(CostUsage.id))) == 0
    assert not list(tmp_path.glob("[0-9]*/*/*"))


async def test_invalid_image_failure_releases_and_cleans(tmp_path, monkeypatch):
    oid, jid, store, _ = await setup(tmp_path, monkeypatch, b"bad image")
    await execute_job({"delivery": Delivery(store)}, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "failed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
    assert not list(tmp_path.glob("[0-9]*/*/*"))


async def test_send_retry_uses_cached_enhanced_files(tmp_path, monkeypatch):
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
    monkeypatch.setattr(document_image, "build", lambda *args: pytest.fail("No second enhancement"))
    # Service imports the builder callable directly; also replace that binding.
    from app.services.document_image_enhancement import service

    monkeypatch.setattr(service, "build", document_image.build)
    delivery.send = send
    await execute_job({"delivery": delivery}, str(jid))
    assert len(delivery.files) == 3
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
