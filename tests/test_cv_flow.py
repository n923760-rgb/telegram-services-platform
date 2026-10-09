from datetime import UTC, datetime
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
from tests.cv_fixtures import inputs
from tests.test_foundation import fund, job_for
from tests.test_real_services import Delivery
from tests.word_pdf_fixtures import renderer


async def prepare(tmp_path, monkeypatch):
    from app.providers import runtime

    def no_provider():
        raise AssertionError("CV formatting must not construct an AI provider")

    monkeypatch.setattr(runtime, "provider", no_provider)
    monkeypatch.setattr(runtime, "LibreOfficeDocuments", renderer)
    monkeypatch.setattr(config(), "ai_enabled", False)
    monkeypatch.setattr(config(), "storage_root", tmp_path)
    await fund()
    async with sessions() as db:
        assert not (await db.get(Service, "cv_formatting")).enabled
    await set_service("cv_formatting", enabled=True)
    async with sessions() as db:
        price = (await db.get(Service, "cv_formatting")).price_halala
    storage = LocalStorage(tmp_path)
    return storage, Delivery(storage), price


@pytest.mark.parametrize("language", ["ar", "en"])
async def test_cv_two_native_files_single_capture_zero_ai_usage_and_cleanup(
    tmp_path, monkeypatch, language
):
    storage, delivery, price = await prepare(tmp_path, monkeypatch)
    source = inputs(language)
    oid = await submit(1, "cv_formatting", source, price, "cv-native")
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
    assert [name for name, _ in delivery.files] == ["cv.docx", "cv.pdf"]
    assert Document(BytesIO(delivery.files[0][1])).paragraphs[0].text == source["full_name"]
    assert "0500123456" in PdfReader(BytesIO(delivery.files[1][1])).pages[0].extract_text()
    assert not list(tmp_path.glob("[0-9]*/*/*"))


@pytest.mark.parametrize(
    "failure", ["document_render_unavailable", "document_render_timeout", "storage_quota"]
)
async def test_cv_failure_releases_without_partial_delivery(tmp_path, monkeypatch, failure):
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
    oid = await submit(1, "cv_formatting", inputs(), price, "cv-failure")
    await execute_job({"delivery": delivery}, str(await job_for(oid)))
    await deliver_failures({"delivery": delivery})
    await deliver_failures({"delivery": delivery})
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "failed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
    assert not delivery.files and len(delivery.errors) == 1
    assert not list(tmp_path.glob("[0-9]*/*/*"))


@pytest.mark.parametrize("partial", [False, True])
async def test_cv_delivery_retry_reuses_prepared_pair_and_does_not_capture_early(
    tmp_path, monkeypatch, partial
):
    from app.providers.documents.libreoffice import LibreOfficeDocuments

    storage, delivery, price = await prepare(tmp_path, monkeypatch)
    oid = await submit(1, "cv_formatting", inputs(), price, "cv-retry")
    jid = await job_for(oid)
    original = delivery.send

    async def offline(user_id, order_id, result):
        if partial:
            artifact = result.artifacts[0]
            delivery.files.append((artifact.filename, storage.read(artifact.key, user_id)))
        raise ConnectionError("synthetic delivery failure")

    monkeypatch.setattr(delivery, "send", offline)
    await execute_job({"delivery": delivery}, str(jid))
    async with sessions.begin() as db:
        assert len((await db.get(Order, oid)).result["artifacts"]) == 2
        assert (await balance(db, 1)).reserved == price
        (await db.get(Job, jid)).next_run_at = datetime.now(UTC)

    async def no_render(*args, **kwargs):
        raise AssertionError("retry must reuse prepared CV files")

    monkeypatch.setattr(LibreOfficeDocuments, "word_pdf", no_render)
    monkeypatch.setattr(delivery, "send", original)
    await execute_job({"delivery": delivery}, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        assert (await balance(db, 1)).reserved == 0
    assert len(delivery.files) == (3 if partial else 2)


@pytest.mark.parametrize(
    "patch", [{"experience": None, "education": None}, {"summary": "x" * 1001}]
)
async def test_invalid_cv_never_reserves_credit(tmp_path, monkeypatch, patch):
    _, _, price = await prepare(tmp_path, monkeypatch)
    with pytest.raises(ServiceError, match="input_invalid"):
        await submit(1, "cv_formatting", inputs() | patch, price, "cv-invalid")
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0
        assert (await balance(db, 1)).reserved == 0
