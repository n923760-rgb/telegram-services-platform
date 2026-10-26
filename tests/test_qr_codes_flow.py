from io import BytesIO

import pytest
from pypdf import PdfReader
from sqlalchemy import func, select

from app.core.db import sessions
from app.core.models import CostUsage, Ledger, Order
from app.orders.engine import submit
from app.providers.storage import LocalStorage
from app.wallet.ledger import balance
from app.workers.runner import execute_job
from tests.qr_codes_fixtures import inputs
from tests.test_direct_documents import prepare
from tests.test_foundation import job_for
from tests.test_real_services import Delivery


@pytest.mark.parametrize("failure", [False, True])
async def test_qr_capture_once_or_release_without_ai(tmp_path, monkeypatch, failure):
    from app.services.qr_codes import service

    price = await prepare(tmp_path, monkeypatch, "qr_codes")
    if failure:

        def broken(*args):
            raise ValueError("synthetic render failure")

        monkeypatch.setattr(service, "build", broken)
    delivery = Delivery(LocalStorage(tmp_path))
    oid = await submit(1, "qr_codes", inputs(), price, "qr-order")
    jid = str(await job_for(oid))
    await execute_job({"delivery": delivery}, jid)
    await execute_job({"delivery": delivery}, jid)
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == ("failed" if failure else "completed")
        funds = await balance(db, 1)
        assert funds.reserved == 0 and funds.available == (1000 if failure else 1000 - price)
        assert await db.scalar(select(func.count(CostUsage.id))) == 0
        assert await db.scalar(select(func.count(Ledger.id)).where(Ledger.kind == "capture")) == (
            0 if failure else 1
        )
    if not failure:
        assert len(delivery.files) == 1
        assert len(PdfReader(BytesIO(delivery.files[0][1])).pages) == 1
