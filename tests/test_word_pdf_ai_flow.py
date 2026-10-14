import json
from datetime import UTC, datetime
from decimal import Decimal
from io import BytesIO
from unittest.mock import AsyncMock

import pytest
from docx import Document
from sqlalchemy import func, select

from app.core.db import sessions
from app.core.models import CostHold, CostUsage, Job, Ledger, Order, Service, Setting
from app.core.settings import config
from app.ops.admin import set_service
from app.orders.engine import confirm_structure, submit
from app.providers.storage import LocalStorage
from app.services.base import ServiceError
from app.services.registry import registry
from app.wallet.ledger import balance
from app.workers.runner import deliver_failures, execute_job
from tests.test_file_layers import Provider
from tests.test_foundation import fund, job_for
from tests.test_real_services import Delivery
from tests.word_pdf_ai_fixtures import inputs, revision
from tests.word_pdf_fixtures import renderer


async def prepare(tmp_path, monkeypatch, responses=None):
    from app.providers import runtime

    provider = Provider(responses or [json.dumps(revision()), '{"accepted":true,"issues":[]}'])
    monkeypatch.setattr(runtime, "provider", lambda: provider)
    monkeypatch.setattr(runtime, "LibreOfficeDocuments", renderer)
    monkeypatch.setattr(config(), "ai_enabled", True)
    monkeypatch.setattr(config(), "storage_root", tmp_path)
    await fund()
    await set_service("text_to_word_pdf", enabled=True)
    async with sessions() as db:
        price = (await db.get(Service, "text_to_word_pdf")).price_halala
    storage = LocalStorage(tmp_path)
    return provider, Delivery(storage), price


async def test_smart_native_pair_reviewed_cost_recorded_and_reused_on_delivery_retry(
    tmp_path, monkeypatch
):
    provider, delivery, price = await prepare(tmp_path, monkeypatch)
    oid = await submit(1, "text_to_word_pdf", inputs(), price, "smart-retry")
    jid = await job_for(oid)
    original = delivery.send
    delivery.send = AsyncMock(side_effect=ConnectionError("synthetic offline"))
    await execute_job({"delivery": delivery}, str(jid))
    async with sessions.begin() as db:
        assert (await balance(db, 1)).reserved == price
        job = await db.get(Job, jid)
        assert job.cost_sar == Decimal(".008")
        job.next_run_at = datetime.now(UTC)
    delivery.send = original
    await execute_job({"delivery": delivery}, str(jid))
    await execute_job({"delivery": delivery}, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        assert (await balance(db, 1)).reserved == 0
        assert await db.scalar(select(func.count(CostUsage.id))) == 2
        assert await db.scalar(select(func.count(Ledger.id)).where(Ledger.kind == "capture")) == 1
    assert provider.calls == 2
    assert [name for name, _ in delivery.files] == ["result.docx", "result.pdf"]
    paragraphs = [p.text for p in Document(BytesIO(delivery.files[0][1])).paragraphs]
    assert "المبلغ 125.50 ريال ولم تتم الموافقة على الصرف." in paragraphs
    assert not list(tmp_path.glob("[0-9]*/*/*"))


@pytest.mark.parametrize("repair", [False, True])
async def test_numeric_failure_has_one_repair_and_one_credit_settlement(
    tmp_path, monkeypatch, repair
):
    bad = revision()
    bad["sections"][0]["segments"][1]["text"] = "المبلغ 999.50 ريال"
    responses = [json.dumps(bad), json.dumps(revision() if repair else bad)]
    if repair:
        responses.append('{"accepted":true,"issues":[]}')
    provider, delivery, price = await prepare(tmp_path, monkeypatch, responses)
    oid = await submit(1, "text_to_word_pdf", inputs(), price, "smart-repair")
    await execute_job({"delivery": delivery}, str(await job_for(oid)))
    await deliver_failures({"delivery": delivery})
    await deliver_failures({"delivery": delivery})
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == ("completed" if repair else "failed")
        assert (await balance(db, 1)).reserved == 0
        assert await db.scalar(select(func.count(CostUsage.id))) == (3 if repair else 2)
        assert (
            await db.scalar(
                select(func.count(Ledger.id)).where(
                    Ledger.kind == ("capture" if repair else "release")
                )
            )
            == 1
        )
    assert provider.calls == (3 if repair else 2)
    assert len(delivery.files) == (2 if repair else 0)


async def test_paused_provider_blocks_smart_but_keeps_direct_available(tmp_path, monkeypatch):
    provider, delivery, price = await prepare(tmp_path, monkeypatch)
    async with sessions.begin() as db:
        db.add(Setting(key="PROVIDER_PAUSED", value={"value": True}))
    with pytest.raises(ServiceError, match="provider_config"):
        await submit(1, "text_to_word_pdf", inputs(), price, "paused-smart")
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0
        assert await db.scalar(select(func.count(CostHold.id))) == 0
    oid = await submit(
        1, "text_to_word_pdf", {"text": "Source 00123", "mode": "direct"}, price, "paused-direct"
    )
    await execute_job({"delivery": delivery}, str(await job_for(oid)))
    assert provider.calls == 0 and len(delivery.files) == 2


async def test_smart_visual_approval_reuses_files_without_new_ai(tmp_path, monkeypatch):
    provider, delivery, price = await prepare(tmp_path, monkeypatch)
    monkeypatch.setattr(config(), "document_visual_review", True)
    delivery.visual_confirmation = AsyncMock()
    oid = await submit(1, "text_to_word_pdf", inputs(), price, "smart-visual")
    jid = await job_for(oid)
    await execute_job({"delivery": delivery}, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "waiting_confirmation"
        assert (await balance(db, 1)).reserved == price
    await confirm_structure(oid, 1, True, expected_prepared=True)
    await execute_job({"delivery": delivery}, str(jid))
    assert provider.calls == 2 and len(delivery.files) == 2
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        assert (await balance(db, 1)).reserved == 0


async def test_smart_source_limit_rejects_before_order_or_hold(tmp_path, monkeypatch):
    provider, _, price = await prepare(tmp_path, monkeypatch)
    with pytest.raises(ServiceError, match="input_invalid"):
        await submit(
            1, "text_to_word_pdf", {"mode": "smart", "text": "x" * 9001}, price, "too-long"
        )
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0
        assert await db.scalar(select(func.count(CostHold.id))) == 0
        assert (await balance(db, 1)).reserved == 0
    assert provider.calls == 0


async def test_upgrade_retains_admin_price_gate_and_releases_old_unprepared_order(
    tmp_path, monkeypatch
):
    provider, delivery, price = await prepare(tmp_path, monkeypatch)
    oid = await submit(1, "text_to_word_pdf", {"text": "Literal"}, price, "old-document")
    async with sessions.begin() as db:
        row = await db.get(Service, "text_to_word_pdf")
        row.version, row.price_halala, row.enabled = "1", 777, True
        (await db.get(Order, oid)).service_version = "1"
    async with sessions.begin() as db:
        await registry.sync(db)
    async with sessions() as db:
        row = await db.get(Service, "text_to_word_pdf")
        assert row.version == "2" and row.price_halala == 777 and row.enabled
    await execute_job({"delivery": delivery}, str(await job_for(oid)))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "cancelled"
        assert (await balance(db, 1)).reserved == 0
    assert provider.calls == 0 and not delivery.files
