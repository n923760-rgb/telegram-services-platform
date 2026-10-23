"""Real SQL lifecycle: incomplete sources release once without extra provider calls."""

from types import SimpleNamespace

import pytest
from sqlalchemy import func, select

from app.core.db import sessions
from app.core.models import CostHold, CostUsage, Job, Ledger, Order
from app.orders.engine import submit
from app.providers.ai.gateway import AI
from app.providers.storage import OwnedStorage
from app.wallet.ledger import balance
from app.workers.runner import execute_job
from tests.test_foundation import job_for
from tests.test_real_services import setup


@pytest.mark.parametrize(
    "slug,inputs",
    [
        ("text_to_office", {"target": "word", "text": "Short source"}),
        ("text_to_pdf", {"text": "Short source"}),
        ("text_to_pptx", {"text": "Short source", "slide_count": "1"}),
    ],
)
async def test_incomplete_source_has_actionable_failure_one_call_and_one_release(
    tmp_path, monkeypatch, slug, inputs
):
    store, provider, delivery, ctx, price = await setup(
        slug, ['{"missing_information":true}', "unused"], tmp_path, monkeypatch
    )
    ctx["runtime_factory"] = lambda jid, uid: SimpleNamespace(
        ai=AI(provider, jid, uid, quality_review=True), storage=OwnedStorage(store, uid)
    )
    oid = await submit(1, slug, inputs, price, "incomplete-source")
    jid = await job_for(oid)
    for _ in range(2):
        await execute_job(ctx, str(jid))
    assert provider.calls == 1 and provider.responses == ["unused"]
    assert not delivery.results and not delivery.files
    async with sessions() as db:
        order = await db.get(Order, oid)
        assert order.status == "failed" and order.error_key == "needs_information"
        assert (await db.get(Job, jid)).attempts == 1
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
        assert sorted(await db.scalars(select(Ledger.kind).where(Ledger.order_id == oid))) == [
            "release",
            "reserve",
        ]
        assert await db.scalar(select(func.count(CostUsage.id))) == 1
        assert list(await db.scalars(select(CostHold.status))) == ["settled"]
