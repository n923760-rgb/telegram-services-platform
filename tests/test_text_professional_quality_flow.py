"""DB settlement for scripted professional-quality rejection/correction verdicts."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.core.db import sessions
from app.core.models import CostUsage, Job, Ledger, Order
from app.orders.engine import submit
from app.providers.ai.gateway import AI
from app.providers.storage import OwnedStorage
from app.wallet.ledger import balance
from app.workers.runner import execute_job
from tests.test_foundation import job_for
from tests.test_real_services import setup
from tests.test_text_professional_quality_unit import CASES, plan


@pytest.mark.parametrize("service_type,inputs,bad,good", CASES)
@pytest.mark.parametrize("accepted", [False, True])
async def test_quality_decision_settles_once_and_reuses_only_approved_files(
    tmp_path, monkeypatch, service_type, inputs, bad, good, accepted
):
    reject = '{"accepted":false,"issues":["quality"]}'
    final = '{"accepted":true,"issues":[]}' if accepted else reject
    store, provider, delivery, ctx, price = await setup(
        service_type.slug, [plan(bad), reject, plan(good), final, "unused"], tmp_path, monkeypatch
    )
    ctx["runtime_factory"] = lambda jid, uid: SimpleNamespace(
        ai=AI(provider, jid, uid, quality_review=True), storage=OwnedStorage(store, uid)
    )
    oid = await submit(1, service_type.slug, inputs, price, "professional-quality")
    jid = await job_for(oid)
    send = delivery.send
    if accepted:

        async def offline(*args):
            raise ConnectionError("synthetic delivery interruption")

        monkeypatch.setattr(delivery, "send", offline)
    await execute_job(ctx, str(jid))
    if accepted:
        async with sessions.begin() as db:
            assert (await db.get(Order, oid)).status == "delivering"
            assert (await balance(db, 1)).reserved == price
            (await db.get(Job, jid)).next_run_at = datetime.now(UTC) - timedelta(seconds=1)
        monkeypatch.setattr(delivery, "send", send)
    await execute_job(ctx, str(jid))
    await execute_job(ctx, str(jid))
    assert provider.calls == 4 and provider.responses == ["unused"]
    async with sessions() as db:
        order = await db.get(Order, oid)
        assert order.status == ("completed" if accepted else "failed")
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000 - price if accepted else 1000, 0)
        assert (await db.get(Job, jid)).cost_sar == Decimal(".016")
        usage = list(await db.scalars(select(CostUsage).where(CostUsage.job_id == jid)))
        assert len(usage) == 4
        entries = list(await db.scalars(select(Ledger).where(Ledger.order_id == oid)))
        assert sorted(entry.kind for entry in entries) == sorted(
            ["reserve", "capture" if accepted else "release"]
        )
    if accepted:
        assert len(delivery.results) == 1 and delivery.results[0].text == good
        assert (
            dict(delivery.files)[
                "translation.txt" if service_type.slug == "text_translation" else "revision.txt"
            ].decode()
            == good
        )
    else:
        assert not delivery.results and not delivery.files
    assert not list(tmp_path.glob("[0-9]*/*/*"))
