from datetime import UTC, datetime
from decimal import Decimal
from io import BytesIO

import pytest
from pypdf import PdfReader
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
from tests.images_pdf_fixtures import picture
from tests.test_foundation import fund, job_for
from tests.test_real_services import Delivery


async def prepare(tmp_path, monkeypatch):
    from app.providers import runtime

    def no_provider():
        raise AssertionError("Images to PDF must not construct an AI provider")

    monkeypatch.setattr(runtime, "provider", no_provider)
    monkeypatch.setattr(config(), "ai_enabled", False)
    monkeypatch.setattr(config(), "storage_root", tmp_path)
    await fund()
    async with sessions() as db:
        assert not (await db.get(Service, "images_to_pdf")).enabled
    await set_service("images_to_pdf", enabled=True)
    async with sessions() as db:
        price = (await db.get(Service, "images_to_pdf")).price_halala
    storage = LocalStorage(tmp_path)
    return storage, Delivery(storage), price


async def test_ordered_pages_single_capture_zero_ai_and_all_files_removed(tmp_path, monkeypatch):
    storage, delivery, price = await prepare(tmp_path, monkeypatch)
    first = storage.save(1, "one.png", picture(), "image/png")
    second = storage.save(1, "two.png", picture(240, 120, color="blue"), "image/png")
    oid = await submit(
        1,
        "images_to_pdf",
        {"images": [first.key, second.key], "orientation": "auto"},
        price,
        "images-native",
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
    assert [name for name, _ in delivery.files] == ["images.pdf"]
    pages = PdfReader(BytesIO(delivery.files[0][1])).pages
    assert len(pages) == 2
    assert pages[0].images[0].image.getpixel((0, 0)) == (255, 0, 0)
    assert pages[1].images[0].image.getpixel((0, 0)) == (0, 0, 255)
    assert not list(tmp_path.glob("[0-9]*/*/*"))


@pytest.mark.parametrize("failure", ["invalid", "missing", "foreign", "save"])
async def test_failed_generation_releases_credit_without_delivery(tmp_path, monkeypatch, failure):
    storage, delivery, price = await prepare(tmp_path, monkeypatch)
    owner = 2 if failure == "foreign" else 1
    data = b"bad image" if failure == "invalid" else picture()
    file = storage.save(owner, "source.png", data, "image/png")
    if failure == "missing":
        storage.delete(file.key, owner)
    if failure == "save":
        original = LocalStorage.save

        def save(self, user_id, filename, data, mime):
            if filename.endswith(".pdf"):
                raise ServiceError("storage_quota")
            return original(self, user_id, filename, data, mime)

        monkeypatch.setattr(LocalStorage, "save", save)
    oid = await submit(
        1, "images_to_pdf", {"images": [file.key], "orientation": "auto"}, price, "images-fail"
    )
    await execute_job({"delivery": delivery}, str(await job_for(oid)))
    await deliver_failures({"delivery": delivery})
    await deliver_failures({"delivery": delivery})
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "failed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
    assert not delivery.files and len(delivery.errors) == 1
    assert not list((tmp_path / "1").glob("*/*"))
    if failure == "foreign":
        assert storage.read(file.key, 2) == data


async def test_delivery_retry_reuses_pdf_without_generation_or_early_capture(tmp_path, monkeypatch):
    from app.services.images_to_pdf import service

    storage, delivery, price = await prepare(tmp_path, monkeypatch)
    file = storage.save(1, "source.png", picture(), "image/png")
    oid = await submit(
        1, "images_to_pdf", {"images": [file.key], "orientation": "auto"}, price, "images-retry"
    )
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
        raise AssertionError("retry must use prepared PDF")

    monkeypatch.setattr(service, "build", no_build)
    monkeypatch.setattr(delivery, "send", original)
    await execute_job({"delivery": delivery}, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        assert (await balance(db, 1)).reserved == 0
    assert len(delivery.files) == 1
    assert not list(tmp_path.glob("[0-9]*/*/*"))


async def test_duplicate_image_keys_never_reserve_credit(tmp_path, monkeypatch):
    _, _, price = await prepare(tmp_path, monkeypatch)
    with pytest.raises(ServiceError, match="input_invalid"):
        await submit(
            1,
            "images_to_pdf",
            {"images": ["same", "same"], "orientation": "auto"},
            price,
            "images-invalid",
        )
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0
        assert (await balance(db, 1)).reserved == 0
