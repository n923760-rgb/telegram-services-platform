from datetime import UTC, datetime, timedelta
from decimal import Decimal
from io import BytesIO

import pytest
from docx import Document
from pypdf import PdfReader
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
from tests.test_foundation import fund, job_for
from tests.test_real_services import Delivery
from tests.word_pdf_fixtures import TEXT, renderer


async def prepare(tmp_path, monkeypatch):
    from app.providers import runtime

    def no_provider():
        raise AssertionError("Word/PDF formatting must not construct an AI provider")

    monkeypatch.setattr(runtime, "provider", no_provider)
    monkeypatch.setattr(runtime, "LibreOfficeDocuments", renderer)
    monkeypatch.setattr(config(), "ai_enabled", False)
    monkeypatch.setattr(config(), "storage_root", tmp_path)
    await fund()
    async with sessions() as db:
        assert not (await db.get(Service, "text_to_word_pdf")).enabled
    await set_service("text_to_word_pdf", enabled=True)
    async with sessions() as db:
        price = (await db.get(Service, "text_to_word_pdf")).price_halala
    storage = LocalStorage(tmp_path)
    return storage, Delivery(storage), price


async def test_actual_word_and_pdf_delivered_before_single_capture_no_ai_cost_and_cleanup(
    tmp_path, monkeypatch
):
    storage, delivery, price = await prepare(tmp_path, monkeypatch)
    oid = await submit(
        1, "text_to_word_pdf", {"text": TEXT, "title": "تقرير الطلبات"}, price, "word-pdf"
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
    assert [name for name, _ in delivery.files] == ["result.docx", "result.pdf"]
    doc = Document(BytesIO(delivery.files[0][1]))
    assert [p.text.replace("\u200e", "") for p in doc.paragraphs] == [
        "تقرير الطلبات",
        *TEXT.splitlines(),
    ]
    assert PdfReader(BytesIO(delivery.files[1][1])).pages[0].extract_text().count("00123") == 2
    assert not list(tmp_path.glob("[0-9]*/*/*"))


@pytest.mark.parametrize(
    "failure",
    [
        "document_render_timeout",
        "document_render_unavailable",
        "document_render_invalid",
        "document_render_limit",
        "storage_quota",
    ],
)
async def test_word_pdf_failure_releases_credit_with_no_partial_delivery(
    tmp_path, monkeypatch, failure
):
    from app.providers.documents.libreoffice import LibreOfficeDocuments

    storage, delivery, price = await prepare(tmp_path, monkeypatch)
    if failure == "storage_quota":
        original = LocalStorage.save

        def save(self, user_id, filename, data, mime):
            if filename.endswith(".pdf"):
                raise ServiceError("storage_quota")
            return original(self, user_id, filename, data, mime)

        monkeypatch.setattr(LocalStorage, "save", save)
    else:

        async def fail(*args, **kwargs):
            raise DocumentError(failure)

        monkeypatch.setattr(LibreOfficeDocuments, "word_pdf", fail)
    oid = await submit(1, "text_to_word_pdf", {"text": TEXT}, price, "word-pdf-failure")
    await execute_job({"delivery": delivery}, str(await job_for(oid)))
    await deliver_failures({"delivery": delivery})
    await deliver_failures({"delivery": delivery})
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "failed"
        if failure == "document_render_limit":
            assert (await db.get(Order, oid)).error_key == "input_invalid"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
    assert not delivery.files and len(delivery.errors) == 1
    assert not list(tmp_path.glob("[0-9]*/*/*"))


@pytest.mark.parametrize("partial", [False, True])
async def test_word_pdf_delivery_retry_reuses_both_files_without_rerendering(
    tmp_path, monkeypatch, partial
):
    from app.providers.documents.libreoffice import LibreOfficeDocuments

    storage, delivery, price = await prepare(tmp_path, monkeypatch)
    oid = await submit(1, "text_to_word_pdf", {"text": TEXT}, price, "word-pdf-retry")
    jid = await job_for(oid)
    original = delivery.send

    async def offline(user_id, order_id, result):
        if partial:
            file = result.artifacts[0]
            delivery.files.append((file.filename, storage.read(file.key, user_id)))
        raise ConnectionError("synthetic transport failure")

    monkeypatch.setattr(delivery, "send", offline)
    await execute_job({"delivery": delivery}, str(jid))
    async with sessions.begin() as db:
        assert len((await db.get(Order, oid)).result["artifacts"]) == 2
        assert (await balance(db, 1)).reserved == price
        (await db.get(Job, jid)).next_run_at = datetime.now(UTC) - timedelta(seconds=1)

    async def no_render(*args, **kwargs):
        raise AssertionError("prepared files must be reused")

    monkeypatch.setattr(LibreOfficeDocuments, "word_pdf", no_render)
    monkeypatch.setattr(delivery, "send", original)
    await execute_job({"delivery": delivery}, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        assert (await balance(db, 1)).reserved == 0
    # Existing at-least-once policy may resend Word after the first delivery succeeded.
    assert len(delivery.files) == (3 if partial else 2) and len(delivery.results) == 1


async def test_word_pdf_busy_retry_keeps_credit_then_completes(tmp_path, monkeypatch):
    from app.providers.documents.libreoffice import LibreOfficeDocuments

    storage, delivery, price = await prepare(tmp_path, monkeypatch)
    oid = await submit(1, "text_to_word_pdf", {"text": TEXT}, price, "word-pdf-busy")
    jid = await job_for(oid)
    original = LibreOfficeDocuments.word_pdf

    async def busy(*args, **kwargs):
        raise DocumentError("document_render_busy", transient=True)

    monkeypatch.setattr(LibreOfficeDocuments, "word_pdf", busy)
    await execute_job({"delivery": delivery}, str(jid))
    async with sessions.begin() as db:
        job = await db.get(Job, jid)
        assert job.status == "pending" and job.failure_count == 1
        assert (await balance(db, 1)).reserved == price
        job.next_run_at = datetime.now(UTC) - timedelta(seconds=1)
    monkeypatch.setattr(LibreOfficeDocuments, "word_pdf", original)
    await execute_job({"delivery": delivery}, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        assert (await balance(db, 1)).reserved == 0
    assert len(delivery.files) == 2


async def test_invalid_word_pdf_input_never_reserves_credit(tmp_path, monkeypatch):
    _, _, price = await prepare(tmp_path, monkeypatch)
    with pytest.raises(ServiceError, match="input_invalid"):
        await submit(
            1, "text_to_word_pdf", {"text": TEXT, "title": "line\nline"}, price, "invalid-word-pdf"
        )
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0
        assert (await balance(db, 1)).reserved == 0
