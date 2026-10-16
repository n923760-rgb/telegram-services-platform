import json
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select

from app.core.db import sessions
from app.core.models import CostUsage, Job, Ledger, Order
from app.orders.engine import confirm_structure, submit
from app.providers.ai.gateway import AI
from app.providers.storage import OwnedStorage
from app.wallet.ledger import balance
from app.workers.runner import deliver_confirmations, deliver_failures, execute_job
from tests.test_foundation import job_for
from tests.test_real_services import setup

SOURCE = "طلب 00123 بقيمة 125.50، للتواصل a@example.com"


def plan(bad=False, ambiguous=False):
    return {
        "ambiguous": ambiguous,
        "question": "اعتماد الهيكل؟" if ambiguous else "",
        "document": {
            "title": "مذكرة",
            "sections": [{"paragraphs": [SOURCE.replace("00123", "123") if bad else SOURCE]}],
        },
    }


async def prepare(slug, responses, tmp_path, monkeypatch):
    store, provider, delivery, ctx, price = await setup(slug, responses, tmp_path, monkeypatch)
    ctx["runtime_factory"] = lambda jid, uid: SimpleNamespace(
        ai=AI(provider, jid, uid, quality_review=True), storage=OwnedStorage(store, uid)
    )
    inputs = {"text": SOURCE, "mode": "smart"}
    if slug == "text_to_office":
        inputs["target"] = "word"
    else:
        inputs["mode"] = "smart"
    # Match the actual public intake before exercising the database lifecycle.
    from app.services.registry import registry

    registry.types[slug].input_schema.validate_inputs(inputs)
    return provider, delivery, ctx, price, inputs


@pytest.mark.parametrize("slug", ["text_to_office", "text_to_pdf"])
@pytest.mark.parametrize("outcome", ["repair", "reject", "confirm"])
async def test_fidelity_repair_rejection_and_confirmation_keep_accounting_once(
    tmp_path, monkeypatch, slug, outcome
):
    responses = [json.dumps(plan(bad=True)), json.dumps(plan()), '{"accepted":true,"issues":[]}']
    if outcome == "reject":
        responses = [json.dumps(plan(bad=True))] * 2
    elif outcome == "confirm":
        responses = [json.dumps(plan(ambiguous=True)), '{"accepted":true,"issues":[]}']
    provider, delivery, ctx, price, inputs = await prepare(slug, responses, tmp_path, monkeypatch)
    oid = await submit(1, slug, inputs, price, "source-document")
    jid = await job_for(oid)
    await execute_job(ctx, str(jid))
    if outcome == "confirm":
        await deliver_confirmations(ctx)
        async with sessions() as db:
            assert (await db.get(Order, oid)).status == "waiting_confirmation"
            assert (await balance(db, 1)).reserved == price
        await confirm_structure(oid, 1, True)
        await execute_job(ctx, str(jid))
    await execute_job(ctx, str(jid))
    await deliver_failures(ctx)
    await deliver_failures(ctx)
    async with sessions() as db:
        order = await db.get(Order, oid)
        assert order.status == ("failed" if outcome == "reject" else "completed")
        if outcome == "reject":
            assert order.error_key == "provider_invalid"
        assert (await db.get(Job, jid)).cost_sar == Decimal(".004") * len(responses)
        assert await db.scalar(select(func.count(CostUsage.id))) == len(responses)
        kind = "release" if outcome == "reject" else "capture"
        assert await db.scalar(select(func.count(Ledger.id)).where(Ledger.kind == kind)) == 1
        funds = await balance(db, 1)
        assert funds.reserved == 0
        assert funds.available == (1000 if outcome == "reject" else 1000 - price)
    assert provider.calls == len(responses)
    assert len(delivery.files) == (0 if outcome == "reject" else 1)
    assert len(delivery.errors) == (1 if outcome == "reject" else 0)
    assert not list(tmp_path.glob("[0-9]*/*/*"))
