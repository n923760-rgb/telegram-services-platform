from datetime import UTC, datetime, timedelta
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
from app.services.pdf_tools.test_service import records, source
from app.wallet.ledger import balance
from app.workers.runner import deliver_failures, execute_job
from tests.test_foundation import fund, job_for
from tests.test_real_services import Delivery


async def prepare(tmp_path, monkeypatch):
    from app.providers import runtime

    def no_provider():
        raise AssertionError("PDF utilities must not construct an AI provider")

    monkeypatch.setattr(runtime, "provider", no_provider)
    monkeypatch.setattr(config(), "ai_enabled", False)
    monkeypatch.setattr(config(), "storage_root", tmp_path)
    await fund()
    await set_service("pdf_tools", enabled=True)
    async with sessions() as db:
        price = (await db.get(Service, "pdf_tools")).price_halala
    storage = LocalStorage(tmp_path)
    return storage, Delivery(storage), price


@pytest.mark.parametrize("operation", ["merge", "extract", "rotate"])
async def test_pdf_tools_capture_once_no_ai_cost_and_cleanup(tmp_path, monkeypatch, operation):
    storage, delivery, price = await prepare(tmp_path, monkeypatch)
    files = [storage.save(1, "one.pdf", source(), "application/pdf").key]
    if operation == "merge":
        files.append(storage.save(1, "two.pdf", source(("00999",)), "application/pdf").key)
    inputs = {
        "operation": operation,
        "files": files,
        **({"pages": "2,1"} if operation == "extract" else {}),
        **({"pages": "2", "rotation": "90"} if operation == "rotate" else {}),
    }
    oid = await submit(1, "pdf_tools", inputs, price, "pdf-tools")
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
    assert len(delivery.files) == 1
    expected = {
        "merge": ["00123", "00124", "00999"],
        "extract": ["00124", "00123"],
        "rotate": ["00123", "00124"],
    }
    assert records(delivery.files[0][1]) == expected[operation]
    if operation == "rotate":
        assert [page.rotation for page in PdfReader(BytesIO(delivery.files[0][1])).pages] == [0, 90]
    assert not list(tmp_path.glob("[0-9]*/*/*"))


@pytest.mark.parametrize("failure", ["corrupt", "encrypted", "form", "pages", "foreign"])
@pytest.mark.parametrize("operation", ["extract", "rotate"])
async def test_pdf_tools_failures_release_credit_and_never_deliver(
    tmp_path, monkeypatch, failure, operation
):
    storage, delivery, price = await prepare(tmp_path, monkeypatch)
    data = (
        b"broken"
        if failure == "corrupt"
        else source(encrypted=failure == "encrypted", form=failure == "form")
    )
    file = storage.save(2 if failure == "foreign" else 1, "one.pdf", data, "application/pdf")
    inputs = {
        "operation": operation,
        "files": [file.key],
        "pages": "3" if failure == "pages" else "1",
        **({"rotation": "90"} if operation == "rotate" else {}),
    }
    oid = await submit(1, "pdf_tools", inputs, price, "pdf-tools-failure")
    await execute_job({"delivery": delivery}, str(await job_for(oid)))
    await deliver_failures({"delivery": delivery})
    await deliver_failures({"delivery": delivery})
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "failed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
    assert not delivery.files and len(delivery.errors) == 1
    if failure == "foreign":
        assert storage.read(file.key, 2) == data  # no cross-owner deletion
    else:
        assert not list(tmp_path.glob("[0-9]*/*/*"))


@pytest.mark.parametrize(
    "inputs",
    [
        {"operation": "merge", "files": ["one"]},
        {"operation": "rotate", "files": ["one"], "pages": "1"},
        {"operation": "rotate", "files": ["one"], "pages": "1", "rotation": "45"},
        {"operation": "rotate", "files": ["one", "two"], "pages": "1", "rotation": "90"},
    ],
)
async def test_invalid_pdf_tools_input_fails_before_reservation(tmp_path, monkeypatch, inputs):
    _, _, price = await prepare(tmp_path, monkeypatch)
    with pytest.raises(ServiceError, match="input_invalid"):
        await submit(1, "pdf_tools", inputs, price, "invalid-pdf")
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0
        assert (await balance(db, 1)).reserved == 0


@pytest.mark.parametrize("operation", ["extract", "rotate"])
async def test_pdf_tools_delivery_retry_reuses_output_without_rebuilding(
    tmp_path, monkeypatch, operation
):
    from app.services.pdf_tools import service

    storage, delivery, price = await prepare(tmp_path, monkeypatch)
    file = storage.save(1, "one.pdf", source(), "application/pdf")
    oid = await submit(
        1,
        "pdf_tools",
        {
            "operation": operation,
            "files": [file.key],
            "pages": "1",
            **({"rotation": "270"} if operation == "rotate" else {}),
        },
        price,
        "pdf-retry",
    )
    jid = await job_for(oid)
    original = delivery.send

    async def unavailable(*args):
        raise ConnectionError("synthetic transport failure")

    monkeypatch.setattr(delivery, "send", unavailable)
    await execute_job({"delivery": delivery}, str(jid))
    async with sessions.begin() as db:
        assert (await db.get(Order, oid)).result["artifacts"]
        assert (await balance(db, 1)).reserved == price
        (await db.get(Job, jid)).next_run_at = datetime.now(UTC) - timedelta(seconds=1)

    def no_rebuild(*args, **kwargs):
        raise AssertionError("prepared output must be reused")

    monkeypatch.setattr(service, "build", no_rebuild)
    monkeypatch.setattr(delivery, "send", original)
    await execute_job({"delivery": delivery}, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        assert (await balance(db, 1)).reserved == 0
    output = PdfReader(BytesIO(delivery.files[0][1]))
    assert len(output.pages) == (2 if operation == "rotate" else 1)
    assert output.pages[0].rotation == (270 if operation == "rotate" else 0)


@pytest.mark.parametrize("cached", [False, True])
async def test_pdf_tools_v1_upgrade_keeps_prepared_output_and_admin_overrides(
    tmp_path, monkeypatch, cached
):
    from app.services.pdf_tools.service import PdfTools
    from app.services.registry import registry

    storage, delivery, price = await prepare(tmp_path, monkeypatch)
    file = storage.save(1, "input.pdf", source(), "application/pdf")
    oid = await submit(
        1,
        "pdf_tools",
        {"operation": "extract", "files": [file.key], "pages": "2,1"},
        price,
        "upgrade",
    )
    jid = await job_for(oid)
    send = delivery.send
    if cached:

        async def unavailable(*args):
            raise ConnectionError("synthetic transport failure")

        monkeypatch.setattr(delivery, "send", unavailable)
        await execute_job({"delivery": delivery}, str(jid))
    async with sessions.begin() as db:
        service = await db.get(Service, "pdf_tools")
        service.version, service.price_halala, service.price_stars = "1", 777, 25
        (await db.get(Order, oid)).service_version = "1"
        (await db.get(Job, jid)).next_run_at = datetime.now(UTC)
    async with sessions.begin() as db:
        await registry.sync(db)
        service = await db.get(Service, "pdf_tools")
        assert service.version == "2" and service.enabled
        assert (service.price_halala, service.price_stars) == (777, 25)

    async def forbidden(*args):
        raise AssertionError("upgrade must not regenerate old output")

    monkeypatch.setattr(PdfTools, "run", forbidden)
    monkeypatch.setattr(delivery, "send", send)
    await execute_job({"delivery": delivery}, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == ("completed" if cached else "cancelled")
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000 - price if cached else 1000, 0)
    assert len(delivery.files) == int(cached)
    if cached:
        assert records(delivery.files[0][1]) == ["00124", "00123"]
