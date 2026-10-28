import json
from io import BytesIO

import pytest
from pypdf import PdfReader
from sqlalchemy import func, select

from app.core.db import sessions
from app.core.models import CostUsage, Ledger, Order
from app.orders.engine import submit
from app.providers.storage import LocalStorage
from app.services.interactive_card.test_service import design_plan, inputs
from app.wallet.ledger import apply, balance
from app.workers.runner import execute_job
from tests.test_direct_documents import prepare
from tests.test_foundation import job_for
from tests.test_real_services import Delivery, setup


@pytest.mark.parametrize("failure", [False, True])
async def test_card_capture_once_or_release_without_ai(tmp_path, monkeypatch, failure):
    from app.services.interactive_card import service

    price = await prepare(tmp_path, monkeypatch, "interactive_card")
    async with sessions.begin() as db:
        await apply(db, 1, "credit", 2000, "card-test-extra")
    if failure:

        def broken(*args):
            raise ValueError("synthetic render failure")

        monkeypatch.setattr(service, "build", broken)
    delivery = Delivery(LocalStorage(tmp_path))
    oid = await submit(1, "interactive_card", inputs(), price, "card-order")
    jid = str(await job_for(oid))
    await execute_job({"delivery": delivery}, jid)
    await execute_job({"delivery": delivery}, jid)
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == ("failed" if failure else "completed")
        funds = await balance(db, 1)
        assert funds.reserved == 0 and funds.available == (3000 if failure else 3000 - price)
        assert await db.scalar(select(func.count(CostUsage.id))) == 0
        assert await db.scalar(select(func.count(Ledger.id)).where(Ledger.kind == "capture")) == (
            0 if failure else 1
        )
    if not failure:
        assert len(delivery.files) == 1
        assert len(PdfReader(BytesIO(delivery.files[0][1])).pages) == 1


@pytest.mark.parametrize("invalid", [None, "order", "contrast"])
async def test_smart_card_gateway_capture_or_release_and_no_regeneration(
    tmp_path, monkeypatch, invalid
):
    plan = design_plan(accent="#047857", tagline="Design studio", columns=2, header="outline")
    if invalid == "order":
        plan["order"] = [0, 0]
    elif invalid == "contrast":
        plan["accent"] = "#ffffff"
    responses = [json.dumps(plan)] * (2 if invalid else 1)
    _, provider, delivery, ctx, price = await setup(
        "interactive_card", responses, tmp_path, monkeypatch
    )
    async with sessions.begin() as db:
        await apply(db, 1, "credit", 2000, "card-test-extra")
    oid = await submit(
        1, "interactive_card", inputs(mode="smart", profile="Design studio"), price, "smart-card"
    )
    jid = str(await job_for(oid))
    await execute_job(ctx, jid)
    await execute_job(ctx, jid)
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == ("failed" if invalid else "completed")
        funds = await balance(db, 1)
        assert funds.reserved == 0
        assert funds.available == (3000 if invalid else 3000 - price)
        assert await db.scalar(select(func.count(Ledger.id)).where(Ledger.kind == "capture")) == (
            0 if invalid else 1
        )
        assert await db.scalar(select(func.count(CostUsage.id))) == (2 if invalid else 1)
    assert provider.calls == (2 if invalid else 1)
    assert len(delivery.files) == (0 if invalid else 1)
