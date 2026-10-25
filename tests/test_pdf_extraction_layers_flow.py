from unittest.mock import AsyncMock

import pytest
from sqlalchemy import func, select

from app.core.db import sessions
from app.core.models import CostHold, CostUsage, Job, Ledger, Order, Service, Setting
from app.ops.circuit import evaluate
from app.orders.engine import submit
from app.wallet.ledger import balance
from app.workers.runner import deliver_failures, execute_job
from tests.pdf_extraction_layer_fixtures import layered_table_pdf, layered_text_pdf
from tests.test_foundation import job_for
from tests.test_pdf_tables_flow import prepare
from tests.test_real_services import setup


@pytest.mark.parametrize("target", ["word", "direct", "source", "labels"])
@pytest.mark.parametrize("kind", ["off", "empty"])
async def test_layer_rejection_releases_once_without_provider_output_or_circuit_trip(
    tmp_path, monkeypatch, target, kind
):
    if target == "word":
        slug, key = "pdf_to_word", "pdf_word_layers"
        store, provider, delivery, ctx, price = await setup(slug, [], tmp_path, monkeypatch)
        data = layered_text_pdf(kind, later=True)
    else:
        slug, key = "pdf_tables_excel", "pdf_tables_layers"
        store, provider, delivery, ctx, price = await prepare(tmp_path, monkeypatch, [])
        data = layered_table_pdf(kind)
    file = store.save(1, "source.pdf", data, "application/pdf")
    inputs = {"pdf": file.key} | ({} if target == "word" else {"mode": target, "language": "en"})
    oid = await submit(1, slug, inputs, price, "layers")
    jid = await job_for(oid)
    await execute_job(ctx, str(jid))
    await execute_job(ctx, str(jid))
    await deliver_failures(ctx)
    await deliver_failures(ctx)
    async with sessions.begin() as db:
        assert (await db.get(Order, oid)).status == "failed"
        assert (await db.get(Job, jid)).cost_sar == 0
        assert await db.scalar(select(func.count(CostUsage.id))) == 0
        assert await db.scalar(select(func.count(CostHold.id))) == 0
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
        assert sorted(await db.scalars(select(Ledger.kind).where(Ledger.order_id == oid))) == [
            "release",
            "reserve",
        ]
        db.add(Setting(key="CIRCUIT_MIN_SAMPLES", value={"value": 1}))
        db.add(Setting(key="FAILURE_ALERT_COUNT", value={"value": 1}))
    notifier = AsyncMock()
    assert not await evaluate(slug, notifier)
    notifier.alert.assert_not_awaited()
    assert provider.calls == 0 and not delivery.files
    assert delivery.errors == [(1, oid, key)]
    async with sessions() as db:
        assert (await db.get(Service, slug)).enabled
    assert not list(tmp_path.glob("[0-9]*/*/*"))
