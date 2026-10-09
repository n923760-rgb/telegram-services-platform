from datetime import UTC, datetime
from decimal import Decimal
from io import BytesIO

import pytest
from openpyxl import load_workbook
from sqlalchemy import func, select

from app.core.db import sessions
from app.core.models import CostHold, CostUsage, Job, Order, Service
from app.core.settings import config
from app.ops.admin import set_service
from app.orders.engine import submit
from app.providers.storage import LocalStorage
from app.services.base import ServiceError
from app.wallet.ledger import balance
from app.workers.runner import deliver_failures, execute_job
from tests.csv_review_fixtures import inputs
from tests.test_foundation import fund, job_for
from tests.test_real_services import Delivery


async def prepare(tmp_path, monkeypatch):
    from app.providers import runtime

    def no_provider():
        raise AssertionError("CSV review must not construct AI")

    monkeypatch.setattr(runtime, "provider", no_provider)
    monkeypatch.setattr(config(), "ai_enabled", False)
    monkeypatch.setattr(config(), "storage_root", tmp_path)
    await fund()
    async with sessions() as db:
        assert not (await db.get(Service, "csv_review")).enabled
    await set_service("csv_review", enabled=True)
    async with sessions() as db:
        price = (await db.get(Service, "csv_review")).price_halala
    return LocalStorage(tmp_path), Delivery(LocalStorage(tmp_path)), price


@pytest.mark.parametrize("language", ["ar", "en"])
async def test_native_single_capture_zero_ai_and_cleanup(tmp_path, monkeypatch, language):
    _, delivery, price = await prepare(tmp_path, monkeypatch)
    oid = await submit(1, "csv_review", inputs(language), price, "csv-success")
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
    assert len(delivery.files) == 1 and delivery.files[0][0] == "review.xlsx"
    book = load_workbook(BytesIO(delivery.files[0][1]))
    assert book["Data"]["A4"].value == "00123" and book["Data"]["C5"].value == "0"
    assert book["Source"]["B4"].value == " أحمد " and book["Review"]["C6"].value == 1
    assert not list(tmp_path.glob("[0-9]*/*/*"))


@pytest.mark.parametrize("failure", ["render", "save"])
async def test_failure_releases_credit_and_sends_one_safe_error(tmp_path, monkeypatch, failure):
    from app.services.csv_review import service

    _, delivery, price = await prepare(tmp_path, monkeypatch)
    if failure == "render":

        def broken(*args, **kwargs):
            raise ValueError("synthetic render failure")

        monkeypatch.setattr(service, "build", broken)
    else:

        def broken(*args, **kwargs):
            raise ServiceError("storage_quota")

        monkeypatch.setattr(LocalStorage, "save", broken)
    oid = await submit(1, "csv_review", inputs(), price, "csv-failure")
    await execute_job({"delivery": delivery}, str(await job_for(oid)))
    await deliver_failures({"delivery": delivery})
    await deliver_failures({"delivery": delivery})
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "failed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
    assert not delivery.files and len(delivery.errors) == 1
    assert not list(tmp_path.glob("[0-9]*/*/*"))


async def test_delivery_retry_reuses_workbook_without_early_capture(tmp_path, monkeypatch):
    from app.services.csv_review import service

    _, delivery, price = await prepare(tmp_path, monkeypatch)
    oid = await submit(1, "csv_review", inputs(), price, "csv-retry")
    jid = await job_for(oid)
    original = delivery.send

    async def offline(*args):
        raise ConnectionError("synthetic delivery failure")

    monkeypatch.setattr(delivery, "send", offline)
    await execute_job({"delivery": delivery}, str(jid))
    async with sessions.begin() as db:
        assert (await db.get(Order, oid)).result
        assert (await balance(db, 1)).reserved == price
        (await db.get(Job, jid)).next_run_at = datetime.now(UTC)

    def no_build(*args, **kwargs):
        raise AssertionError("retry must use prepared XLSX")

    monkeypatch.setattr(service, "build", no_build)
    monkeypatch.setattr(delivery, "send", original)
    await execute_job({"delivery": delivery}, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        assert (await balance(db, 1)).reserved == 0
    assert len(delivery.files) == 1
    assert not list(tmp_path.glob("[0-9]*/*/*"))


async def test_bad_csv_never_creates_order_or_reserves(tmp_path, monkeypatch):
    _, _, price = await prepare(tmp_path, monkeypatch)
    with pytest.raises(ServiceError, match="input_invalid"):
        await submit(1, "csv_review", {**inputs(), "text": "A,B\n1"}, price, "csv-invalid")
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0
        assert (await balance(db, 1)).reserved == 0
