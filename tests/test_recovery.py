import os
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.core.db import sessions
from app.core.models import CostBudget, CostHold, Job, Order
from app.core.settings import config
from app.files.retention import cleanup
from app.ops.admin import set_service
from app.ops.costs import keys, reserve_call, uncertain_call
from app.orders.engine import submit
from app.wallet.ledger import balance
from app.workers.runner import execute_job
from tests.test_foundation import Delivery, fund, job_for
from tests.test_operations import running


async def test_interrupted_delivery_reuses_result_without_regeneration(monkeypatch):
    await fund()
    oid = await submit(1, "echo", {"text": "x"}, 100, "recovery")
    jid = await job_for(oid)
    async with sessions.begin() as db:
        order = await db.get(Order, oid)
        order.status = "delivering"
        order.result = {"text": "persisted", "artifacts": []}
        job = await db.get(Job, jid)
        job.status = "running"
        job.lease_until = datetime.now(UTC) - timedelta(seconds=1)
    from app.services.registry import registry

    monkeypatch.setattr(
        registry, "get", lambda *a: (_ for _ in ()).throw(AssertionError("must not rerender"))
    )
    delivery = Delivery()
    await execute_job({"delivery": delivery}, str(jid))
    assert delivery.results[0].text == "persisted"
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"


async def test_uncertain_provider_call_retains_exposure():
    _, jid = await running()
    hold = await reserve_call(jid, 1, Decimal(".1"))
    await uncertain_call(hold)
    async with sessions() as db:
        assert (await db.get(CostHold, hold)).status == "uncertain"
        assert (await db.get(CostBudget, keys(1)[0])).reserved == Decimal(".1")


async def test_service_disabled_after_admission_releases(monkeypatch):
    await fund()
    oid = await submit(1, "echo", {"text": "x"}, 100, "disable")
    await set_service("echo", enabled=False)
    await execute_job({"delivery": Delivery()}, str(await job_for(oid)))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "cancelled"
        assert (await balance(db, 1)).reserved == 0
        assert (await balance(db, 1)).available == 1000


async def test_ttl_deletes_abandoned_files_and_user_content(tmp_path, monkeypatch):
    monkeypatch.setattr(config(), "storage_root", tmp_path)
    await fund()
    oid = await submit(1, "echo", {"text": "private"}, 100, "privacy")
    await execute_job({"delivery": Delivery()}, str(await job_for(oid)))
    from app.providers.runtime import storage

    file = storage().save(1, "abandoned.txt", b"private", "text/plain")
    old = datetime.now(UTC) - timedelta(hours=25)
    os.utime(storage().path(file.key), (old.timestamp(), old.timestamp()))
    async with sessions.begin() as db:
        (await db.get(Order, oid)).updated_at = old
    await cleanup()
    async with sessions() as db:
        order = await db.get(Order, oid)
        assert order.inputs == {} and order.result is None
    assert not storage().path(file.key).exists()
    assert await submit(1, "echo", {"text": "private"}, 100, "privacy") == oid


async def test_runtime_initialization_failure_releases_credit():
    await fund()
    oid = await submit(1, "echo", {"text": "x"}, 100, "bad-runtime")

    def broken(*args):
        raise ValueError("configuration unavailable")

    await execute_job({"delivery": Delivery(), "runtime_factory": broken}, str(await job_for(oid)))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "failed"
        assert (await balance(db, 1)).available == 1000


async def test_audit_attempt_number_does_not_consume_retry_budget():
    await fund()
    oid = await submit(1, "echo", {"text": "x"}, 100, "attempts")
    jid = await job_for(oid)
    async with sessions.begin() as db:
        job = await db.get(Job, jid)
        job.attempts = 3
        job.failure_count = 0
    await execute_job({"delivery": Delivery()}, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        assert (await db.get(Job, jid)).attempts == 4


async def test_exhausted_abandoned_attempt_releases_credit():
    await fund()
    oid = await submit(1, "echo", {"text": "x"}, 100, "exhausted")
    jid = await job_for(oid)
    async with sessions.begin() as db:
        job = await db.get(Job, jid)
        job.status = "running"
        job.failure_count = config().max_attempts - 1
        job.lease_until = datetime.now(UTC) - timedelta(seconds=1)
    await execute_job({"delivery": Delivery()}, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "failed"
        assert (await balance(db, 1)).available == 1000


async def test_cached_delivery_survives_incompatible_plugin_update(monkeypatch):
    from app.services.registry import registry

    await fund()
    oid = await submit(1, "echo", {"text": "x"}, 100, "cached-upgrade")
    jid = await job_for(oid)
    async with sessions.begin() as db:
        order = await db.get(Order, oid)
        order.status = "delivering"
        order.result = {"text": "persisted", "artifacts": []}
    monkeypatch.setattr(registry.types["echo"], "version", "2")
    monkeypatch.setattr(config(), "ai_provider", "unconfigured-vendor")
    delivery = Delivery()
    await execute_job({"delivery": delivery}, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
    assert delivery.results[0].text == "persisted"
