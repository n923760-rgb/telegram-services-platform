from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.core.db import sessions
from app.core.models import CostHold, CostUsage, Job, Order, Service
from app.core.settings import config
from app.ops.admin import set_service
from app.orders.engine import submit
from app.providers.documents.base import DocumentError
from app.providers.storage import LocalStorage
from app.services.base import ServiceError
from app.wallet.ledger import balance
from app.workers.runner import deliver_failures, execute_job
from tests.ocr_fixtures import printed, processor
from tests.test_foundation import fund, job_for
from tests.test_real_services import Delivery


async def prepare(tmp_path, monkeypatch):
    from app.providers import runtime

    def no_provider():
        raise AssertionError("Local OCR must not construct an AI provider")

    monkeypatch.setattr(runtime, "provider", no_provider)
    monkeypatch.setattr(runtime, "TesseractDocuments", processor)
    monkeypatch.setattr(config(), "ai_enabled", False)
    monkeypatch.setattr(config(), "storage_root", tmp_path)
    await fund()
    async with sessions() as db:
        assert not (await db.get(Service, "local_ocr")).enabled
    await set_service("local_ocr", enabled=True)
    async with sessions() as db:
        price = (await db.get(Service, "local_ocr")).price_halala
    storage = LocalStorage(tmp_path)
    return storage, Delivery(storage), price


async def test_local_ocr_actual_native_capture_once_zero_ai_cost_and_cleanup(tmp_path, monkeypatch):
    storage, delivery, price = await prepare(tmp_path, monkeypatch)
    image = storage.save(1, "input.png", printed(), "image/png")
    oid = await submit(
        1, "local_ocr", {"images": [image.key], "language": "en"}, price, "local-ocr"
    )
    jid = await job_for(oid)
    await execute_job({"delivery": delivery}, str(jid))
    await execute_job({"delivery": delivery}, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        assert (await db.get(Job, jid)).cost_sar == Decimal("0")
        assert await db.scalar(select(func.count(CostUsage.id))) == 0
        assert await db.scalar(select(func.count(CostHold.id))) == 0
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000 - price, 0)
    assert len(delivery.results) == 1
    assert delivery.results[0].text == "Invoice 00123\nTotal 125.50\nDate 2026-10-09"
    assert not list(tmp_path.glob("[0-9]*/*/*"))


@pytest.mark.parametrize("failure", ["corrupt", "foreign", "unclear", "timeout", "unavailable"])
async def test_local_ocr_failure_releases_credit_and_never_delivers(tmp_path, monkeypatch, failure):
    from app.providers.documents.tesseract import TesseractDocuments

    storage, delivery, price = await prepare(tmp_path, monkeypatch)
    image = storage.save(
        2 if failure == "foreign" else 1,
        "input.png",
        b"broken" if failure == "corrupt" else printed(),
        "image/png",
    )
    if failure in {"unclear", "timeout", "unavailable"}:

        async def fail(*args, **kwargs):
            raise DocumentError(
                {
                    "unclear": "ocr_unclear",
                    "timeout": "local_ocr_timeout",
                    "unavailable": "local_ocr_unavailable",
                }[failure]
            )

        monkeypatch.setattr(TesseractDocuments, "recognize", fail)
    oid = await submit(
        1, "local_ocr", {"images": [image.key], "language": "en"}, price, "local-failure"
    )
    await execute_job({"delivery": delivery}, str(await job_for(oid)))
    await deliver_failures({"delivery": delivery})
    await deliver_failures({"delivery": delivery})
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "failed"
        if failure in {"corrupt", "foreign"}:
            assert (await db.get(Order, oid)).error_key == "input_invalid"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
        assert await db.scalar(select(func.count(CostUsage.id))) == 0
    assert not delivery.results and len(delivery.errors) == 1
    if failure == "foreign":
        assert storage.read(image.key, 2) == printed()
    else:
        assert not list(tmp_path.glob("[0-9]*/*/*"))


async def test_local_ocr_delivery_retry_reuses_prepared_text_without_recognition(
    tmp_path, monkeypatch
):
    from app.providers.documents.tesseract import TesseractDocuments

    storage, delivery, price = await prepare(tmp_path, monkeypatch)
    image = storage.save(1, "input.png", printed(), "image/png")
    oid = await submit(
        1, "local_ocr", {"images": [image.key], "language": "en"}, price, "local-retry"
    )
    jid = await job_for(oid)
    original = delivery.send

    async def unavailable(*args):
        raise ConnectionError("synthetic transport failure")

    monkeypatch.setattr(delivery, "send", unavailable)
    await execute_job({"delivery": delivery}, str(jid))
    async with sessions.begin() as db:
        assert (await db.get(Order, oid)).result["text"]
        assert (await balance(db, 1)).reserved == price
        (await db.get(Job, jid)).next_run_at = datetime.now(UTC) - timedelta(seconds=1)

    async def no_recognition(*args, **kwargs):
        raise AssertionError("prepared result must be reused")

    monkeypatch.setattr(TesseractDocuments, "recognize", no_recognition)
    monkeypatch.setattr(delivery, "send", original)
    await execute_job({"delivery": delivery}, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        assert (await balance(db, 1)).reserved == 0
    assert len(delivery.results) == 1


async def test_local_ocr_busy_retry_retains_reservation_then_succeeds(tmp_path, monkeypatch):
    from app.providers.documents.tesseract import TesseractDocuments

    storage, delivery, price = await prepare(tmp_path, monkeypatch)
    image = storage.save(1, "input.png", printed(), "image/png")
    oid = await submit(
        1, "local_ocr", {"images": [image.key], "language": "en"}, price, "local-busy"
    )
    jid = await job_for(oid)
    original = TesseractDocuments.recognize

    async def busy(*args, **kwargs):
        raise DocumentError("local_ocr_busy", transient=True)

    monkeypatch.setattr(TesseractDocuments, "recognize", busy)
    await execute_job({"delivery": delivery}, str(jid))
    async with sessions.begin() as db:
        assert (await balance(db, 1)).reserved == price
        job = await db.get(Job, jid)
        assert job.status == "pending" and job.failure_count == 1
        job.next_run_at = datetime.now(UTC) - timedelta(seconds=1)
    monkeypatch.setattr(TesseractDocuments, "recognize", original)
    await execute_job({"delivery": delivery}, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        assert (await balance(db, 1)).reserved == 0
    assert len(delivery.results) == 1


async def test_invalid_local_ocr_input_fails_before_reserving(tmp_path, monkeypatch):
    _, _, price = await prepare(tmp_path, monkeypatch)
    with pytest.raises(ServiceError, match="input_invalid"):
        await submit(
            1, "local_ocr", {"images": ["one", "one"], "language": "en"}, price, "invalid-local"
        )
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0
        assert (await balance(db, 1)).reserved == 0
