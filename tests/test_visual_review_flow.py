from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.db import sessions
from app.core.models import Job, Order, Service
from app.core.settings import config
from app.files.retention import cleanup, cleanup_order_files
from app.orders.engine import confirm_structure, submit
from app.providers.documents.previews import PdfPreviews
from app.providers.documents.rendering import WordFiles
from app.providers.storage import LocalStorage, OwnedStorage
from app.services.base import ServiceError
from app.wallet.ledger import balance
from app.workers.runner import deliver_confirmations, execute_job
from tests.test_document_previews import sample_pdf
from tests.test_foundation import fund, job_for
from tests.test_real_services import Delivery


async def setup(tmp_path, monkeypatch, slug="text_to_word_pdf", inputs=None):
    await fund()
    monkeypatch.setattr(config(), "storage_root", tmp_path)
    async with sessions.begin() as db:
        service = await db.get(Service, slug)
        service.enabled = True
        price = service.price_halala
    store = LocalStorage(tmp_path)
    renderer = SimpleNamespace(word_pdf=AsyncMock(return_value=WordFiles(b"docx", sample_pdf())))
    delivery = Delivery(store)
    delivery.visual_confirmation = AsyncMock()
    ctx = {
        "delivery": delivery,
        "runtime_factory": lambda jid, uid: SimpleNamespace(
            ai=None, storage=OwnedStorage(store, uid), renderer=renderer, previews=PdfPreviews()
        ),
    }
    oid = await submit(1, slug, inputs or {"text": "Invoice 00123"}, price, "visual")
    return oid, await job_for(oid), ctx, renderer, store, price


@pytest.mark.parametrize("approved", [True, False])
async def test_prepared_visual_review_approval_or_cancellation(tmp_path, monkeypatch, approved):
    oid, jid, ctx, renderer, store, price = await setup(tmp_path, monkeypatch)
    await execute_job(ctx, str(jid))
    async with sessions() as db:
        order = await db.get(Order, oid)
        assert order.status == "waiting_confirmation"
        keys = [f["key"] for f in order.result["artifacts"] + order.result["preview_artifacts"]]
        prepared = [store.read(key, 1) for key in keys]
        assert (await balance(db, 1)).reserved == price
    assert not ctx["delivery"].files
    await deliver_confirmations(ctx)
    await deliver_confirmations(ctx)
    assert ctx["delivery"].visual_confirmation.await_count == 1
    with pytest.raises(ServiceError, match="not_allowed"):
        await confirm_structure(oid, 2, approved)
    with pytest.raises(ServiceError, match="stale_button"):
        await confirm_structure(oid, 1, approved, expected_prepared=False)
    await confirm_structure(oid, 1, approved, expected_prepared=True)
    if approved:
        await execute_job(ctx, str(jid))
        await execute_job(ctx, str(jid))
        assert [data for _, data in ctx["delivery"].files] == prepared[:2]
    else:
        await cleanup_order_files(oid)
    assert renderer.word_pdf.await_count == 1
    async with sessions() as db:
        order = await db.get(Order, oid)
        assert order.status == ("completed" if approved else "cancelled")
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000 - price if approved else 1000, 0)
    assert not list(tmp_path.glob("[0-9]*/*/*"))


async def test_expired_visual_review_releases_and_deletes_all_files(tmp_path, monkeypatch):
    oid, jid, ctx, _, _, _ = await setup(tmp_path, monkeypatch)
    await execute_job(ctx, str(jid))
    async with sessions.begin() as db:
        order = await db.get(Order, oid)
        order.updated_at = datetime.now(UTC) - timedelta(minutes=31)
    await cleanup()
    await cleanup()  # The next sweep deletes artifacts after the first cancels the order.
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "cancelled"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
    assert not list(tmp_path.glob("[0-9]*/*/*"))


async def test_delivery_retry_uses_same_prepared_files_without_new_render(tmp_path, monkeypatch):
    oid, jid, ctx, renderer, _, _ = await setup(tmp_path, monkeypatch)
    await execute_job(ctx, str(jid))
    await confirm_structure(oid, 1, True)
    original = ctx["delivery"].send
    ctx["delivery"].send = AsyncMock(side_effect=OSError("offline"))
    await execute_job(ctx, str(jid))
    async with sessions.begin() as db:
        job = await db.get(Job, jid)
        job.next_run_at = datetime.now(UTC) - timedelta(seconds=1)
    ctx["delivery"].send = original
    await execute_job(ctx, str(jid))
    assert renderer.word_pdf.await_count == 1
    assert len(ctx["delivery"].files) == 2
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"


async def test_structural_then_visual_review_notifies_both_without_second_ai(tmp_path, monkeypatch):
    from tests.minutes_fixtures import inputs, plan

    oid, jid, ctx, renderer, _, _ = await setup(tmp_path, monkeypatch, "meeting_minutes", inputs())

    async def extract(schema, source, prompt):
        return schema.model_validate(plan())

    ai = SimpleNamespace(extract=AsyncMock(side_effect=extract))
    runtime_factory = ctx["runtime_factory"]

    def runtime(jid, uid):
        result = runtime_factory(jid, uid)
        result.ai = ai
        return result

    ctx["runtime_factory"] = runtime
    await execute_job(ctx, str(jid))
    await deliver_confirmations(ctx)
    assert len(ctx["delivery"].confirmations) == 1
    assert renderer.word_pdf.await_count == 0
    await confirm_structure(oid, 1, True)
    await execute_job(ctx, str(jid))
    await deliver_confirmations(ctx)
    assert ctx["delivery"].visual_confirmation.await_count == 1
    await confirm_structure(oid, 1, True)
    await execute_job(ctx, str(jid))
    assert ai.extract.await_count == renderer.word_pdf.await_count == 1
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"


async def test_old_notification_cannot_mark_new_review_as_notified(tmp_path, monkeypatch):
    from tests.minutes_fixtures import inputs, plan

    oid, jid, ctx, _, _, _ = await setup(tmp_path, monkeypatch, "meeting_minutes", inputs())

    async def extract(schema, source, prompt):
        return schema.model_validate(plan())

    factory = ctx["runtime_factory"]

    def runtime(jid, uid):
        result = factory(jid, uid)
        result.ai = SimpleNamespace(extract=extract)
        return result

    ctx["runtime_factory"] = runtime

    async def advance(user_id, order_id, preview):
        await confirm_structure(order_id, user_id, True, expected_prepared=False)
        await execute_job(ctx, str(jid))

    ctx["delivery"].confirmation = advance
    await execute_job(ctx, str(jid))
    await deliver_confirmations(ctx)
    async with sessions() as db:
        order = await db.get(Order, oid)
        assert order.result["prepared_delivery"]
        assert not order.confirmation_notified
    await deliver_confirmations(ctx)
    assert ctx["delivery"].visual_confirmation.await_count == 1
