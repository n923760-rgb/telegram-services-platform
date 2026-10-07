from datetime import UTC, datetime, timedelta
from io import BytesIO

import pytest
from docx import Document

from app.core.db import sessions
from app.core.models import Job, Order
from app.orders.engine import submit
from app.services.pdf_to_word.test_service import SOURCE, pdf_bytes
from app.wallet.ledger import balance
from app.workers.runner import deliver_failures, execute_job
from tests.test_foundation import job_for
from tests.test_real_services import setup

PLAN = '{"document":{"title":"Invoice","sections":[{"paragraphs":["' + SOURCE + '"]}]}}'


async def test_pdf_to_word_delivers_editable_docx_then_captures_once(tmp_path, monkeypatch):
    store, provider, delivery, ctx, price = await setup(
        "pdf_to_word", [PLAN], tmp_path, monkeypatch
    )
    source = store.save(1, "source.pdf", pdf_bytes(), "application/pdf")
    oid = await submit(1, "pdf_to_word", {"pdf": source.key}, price, "pdf-word-success")
    jid = await job_for(oid)
    await execute_job(ctx, str(jid))
    await execute_job(ctx, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        funds = await balance(db, 1)
        assert funds.available == 1000 - price and funds.reserved == 0
    assert provider.calls == 1 and len(delivery.files) == 1
    filename, data = delivery.files[0]
    assert filename == "result.docx"
    assert SOURCE in [p.text for p in Document(BytesIO(data)).paragraphs]


@pytest.mark.parametrize(
    ("data", "key"),
    [
        (b"not a pdf", "file_invalid"),
        (pdf_bytes(encrypted=True), "file_invalid"),
        (pdf_bytes(text=""), "pdf_text_unreadable"),
        (pdf_bytes(drawn_page=True), "pdf_text_unreadable"),
        (pdf_bytes(text="x" * 50001), "pdf_text_too_long"),
    ],
    ids=["malformed", "encrypted", "blank", "mixed", "oversized-text"],
)
async def test_pdf_rejection_releases_credit_and_notifies_once(tmp_path, monkeypatch, data, key):
    store, provider, delivery, ctx, price = await setup("pdf_to_word", [], tmp_path, monkeypatch)
    source = store.save(1, "source.pdf", data, "application/pdf")
    oid = await submit(1, "pdf_to_word", {"pdf": source.key}, price, "pdf-word-failure")
    await execute_job(ctx, str(await job_for(oid)))
    await deliver_failures(ctx)
    await deliver_failures(ctx)
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "failed"
        funds = await balance(db, 1)
        assert funds.available == 1000 and funds.reserved == 0
    assert provider.calls == 0
    assert delivery.errors == [(1, oid, key)] and not delivery.files


async def test_invalid_pdf_plan_releases_credit_without_delivering(tmp_path, monkeypatch):
    store, provider, delivery, ctx, price = await setup(
        "pdf_to_word", ["{}"], tmp_path, monkeypatch
    )
    source = store.save(1, "source.pdf", pdf_bytes(), "application/pdf")
    oid = await submit(1, "pdf_to_word", {"pdf": source.key}, price, "pdf-word-invalid-plan")
    await execute_job(ctx, str(await job_for(oid)))
    await deliver_failures(ctx)
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "failed"
        funds = await balance(db, 1)
        assert funds.available == 1000 and funds.reserved == 0
    assert provider.calls == 1 and not delivery.files
    assert delivery.errors == [(1, oid, "needs_information")]


async def test_pdf_delivery_retry_reuses_output_and_captures_after_delivery(tmp_path, monkeypatch):
    store, provider, delivery, ctx, price = await setup(
        "pdf_to_word", [PLAN], tmp_path, monkeypatch
    )
    source = store.save(1, "source.pdf", pdf_bytes(), "application/pdf")
    oid = await submit(1, "pdf_to_word", {"pdf": source.key}, price, "pdf-word-retry")
    jid = await job_for(oid)
    original_send = delivery.send

    async def unavailable(*args):
        raise ConnectionError("test delivery unavailable")

    monkeypatch.setattr(delivery, "send", unavailable)
    await execute_job(ctx, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "delivering"
        funds = await balance(db, 1)
        assert funds.available == 1000 - price and funds.reserved == price
    monkeypatch.setattr(delivery, "send", original_send)
    async with sessions.begin() as db:
        (await db.get(Job, jid)).next_run_at = datetime.now(UTC) - timedelta(seconds=1)
    await execute_job(ctx, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        funds = await balance(db, 1)
        assert funds.available == 1000 - price and funds.reserved == 0
    assert provider.calls == 1 and len(delivery.files) == 1
