"""Direct modes use the same order/ledger/delivery safeguards without a provider."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from io import BytesIO

import pytest
from docx import Document
from sqlalchemy import func, select

from app.core.db import sessions
from app.core.models import CostHold, CostUsage, Job, Order, Service, Setting
from app.core.settings import config
from app.ops.admin import set_service
from app.orders.engine import submit
from app.providers.storage import LocalStorage
from app.services.base import ServiceError
from app.services.registry import registry
from app.wallet.ledger import balance
from app.workers.runner import execute_job
from tests.test_foundation import fund, job_for
from tests.test_real_services import Delivery


def no_provider(*args, **kwargs):
    raise AssertionError("Direct mode must not construct a provider")


async def prepare(tmp_path, monkeypatch, slug):
    from app.providers import runtime

    monkeypatch.setattr(config(), "ai_enabled", False)
    monkeypatch.setattr(config(), "storage_root", tmp_path)
    monkeypatch.setattr(runtime, "provider", no_provider)
    await fund()
    await set_service(slug, enabled=True)
    async with sessions.begin() as db:
        db.add(Setting(key="PROVIDER_PAUSED", value={"value": True}))
        return (await db.get(Service, slug)).price_halala


def direct_inputs(slug):
    return {
        "text": "  محتوى 00123\n\nEnglish <tag> & data 456  ",
        "mode": "direct",
        "title": "عنوان العميل",
        **({"target": "word"} if slug == "text_to_office" else {}),
    }


@pytest.mark.parametrize("slug", ["text_to_office", "text_to_pdf"])
async def test_direct_order_no_provider_no_cost_exactly_once_capture(tmp_path, monkeypatch, slug):
    price = await prepare(tmp_path, monkeypatch, slug)
    inputs = direct_inputs(slug)
    oid = await submit(1, slug, inputs, price, "direct", expected_version="2")
    assert await submit(1, slug, inputs, price, "direct", expected_version="2") == oid
    async with sessions() as db:
        assert (await balance(db, 1)).reserved == price
    delivery = Delivery(LocalStorage(tmp_path))
    jid = await job_for(oid)
    await execute_job({"delivery": delivery}, str(jid))
    await execute_job({"delivery": delivery}, str(jid))
    async with sessions() as db:
        order = await db.get(Order, oid)
        assert order.status == "completed" and order.inputs == inputs
        assert (await db.get(Job, jid)).cost_sar == Decimal("0")
        assert await db.scalar(select(func.count(CostUsage.id))) == 0
        assert await db.scalar(select(func.count(CostHold.id))) == 0
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000 - price, 0)
    assert len(delivery.files) == 1
    assert not list(tmp_path.glob("[0-9]*/*/*"))
    if slug == "text_to_office":
        doc = Document(BytesIO(delivery.files[0][1]))
        assert "\n".join(p.text for p in doc.paragraphs[1:]) == inputs["text"]


@pytest.mark.parametrize("slug", ["text_to_office", "text_to_pdf"])
async def test_smart_mode_still_blocked_before_reserve_without_ai(tmp_path, monkeypatch, slug):
    price = await prepare(tmp_path, monkeypatch, slug)
    inputs = {
        "text": "المحتوى",
        "mode": "smart",
        **({"target": "word"} if slug == "text_to_office" else {}),
    }
    with pytest.raises(ServiceError, match="provider_config"):
        await submit(1, slug, inputs, price, "smart-disabled")
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)


async def test_excel_still_requires_provider(tmp_path, monkeypatch):
    price = await prepare(tmp_path, monkeypatch, "text_to_office")
    with pytest.raises(ServiceError, match="provider_config"):
        await submit(1, "text_to_office", {"text": "بيانات", "target": "excel"}, price, "excel")


@pytest.mark.parametrize("failure", ["build", "delivery"])
@pytest.mark.parametrize("slug", ["text_to_office", "text_to_pdf"])
async def test_direct_terminal_failure_releases_credit(tmp_path, monkeypatch, slug, failure):
    from app.builders import pdf, word

    price = await prepare(tmp_path, monkeypatch, slug)
    oid = await submit(1, slug, direct_inputs(slug), price, "failure")
    delivery = Delivery(LocalStorage(tmp_path))

    def fail_build(*args):
        raise ServiceError("service_failed")

    async def fail_send(*args):
        raise ServiceError("service_failed")

    if failure == "build":
        monkeypatch.setattr(word if slug == "text_to_office" else pdf, "build", fail_build)
    else:
        monkeypatch.setattr(delivery, "send", fail_send)
    await execute_job({"delivery": delivery}, str(await job_for(oid)))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "failed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
    assert not list(tmp_path.glob("[0-9]*/*/*"))


@pytest.mark.parametrize("slug", ["text_to_office", "text_to_pdf"])
async def test_direct_delivery_retry_reuses_prepared_file(tmp_path, monkeypatch, slug):
    from app.builders import pdf, word

    price = await prepare(tmp_path, monkeypatch, slug)
    oid = await submit(1, slug, direct_inputs(slug), price, "retry")
    jid = await job_for(oid)
    delivery = Delivery(LocalStorage(tmp_path))
    original_send = delivery.send

    async def retry_send(*args):
        raise OSError("temporary transport failure")

    monkeypatch.setattr(delivery, "send", retry_send)
    await execute_job({"delivery": delivery}, str(jid))
    async with sessions.begin() as db:
        assert (await db.get(Order, oid)).result["artifacts"]
        assert (await balance(db, 1)).reserved == price
        (await db.get(Job, jid)).next_run_at = datetime.now(UTC) - timedelta(seconds=1)
    monkeypatch.setattr(delivery, "send", original_send)
    monkeypatch.setattr(word if slug == "text_to_office" else pdf, "build", no_provider)
    await execute_job({"delivery": delivery}, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        assert (await balance(db, 1)).reserved == 0
    assert len(delivery.files) == 1


@pytest.mark.parametrize("slug", ["text_to_office", "text_to_pdf"])
async def test_invalid_document_inputs_rejected_before_reserve(tmp_path, monkeypatch, slug):
    price = await prepare(tmp_path, monkeypatch, slug)
    inputs = {**direct_inputs(slug), "text": "invalid\x00"}
    with pytest.raises(ServiceError, match="input_invalid"):
        await submit(1, slug, inputs, price, "invalid-text")
    with pytest.raises(ServiceError, match="invalid_request"):
        await submit(1, slug, {**direct_inputs(slug), "__continuation": {}}, price, "forged")
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0
        assert (await balance(db, 1)).reserved == 0


async def test_registry_version_upgrade_preserves_admin_settings_and_releases_old_jobs():
    await fund()
    async with sessions.begin() as db:
        row = await db.get(Service, "text_to_pdf")
        row.enabled, row.price_halala = True, 700
    oid = await submit(
        1, "text_to_pdf", {"text": "Text", "mode": "direct", "title": "Title"}, 700, "old-job"
    )
    async with sessions.begin() as db:
        row = await db.get(Service, "text_to_pdf")
        row.version, row.input_schema = (
            "1",
            {"fields": [{"name": "text", "prompt_key": "pdf_text"}]},
        )
        (await db.get(Order, oid)).service_version = "1"
        await registry.sync(db)
        await db.refresh(row)  # Core upserts do not refresh the ORM identity map.
        assert row.version == "2" and row.enabled and row.price_halala == 700
    await execute_job(
        {"delivery": Delivery(LocalStorage(config().storage_root))}, str(await job_for(oid))
    )
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "cancelled"
        assert (await db.get(Order, oid)).error_key == "service_changed"
        assert (await balance(db, 1)).reserved == 0
