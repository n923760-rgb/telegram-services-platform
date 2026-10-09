import json

from app.builders import word
from app.core.db import sessions
from app.core.models import Order
from app.orders.engine import submit
from app.wallet.ledger import balance
from app.workers.runner import deliver_failures, execute_job
from tests.test_document_templates import plan
from tests.test_foundation import job_for
from tests.test_real_services import setup


async def test_structural_quality_failure_releases_credit_without_delivery(tmp_path, monkeypatch):
    _, provider, delivery, ctx, price = await setup(
        "text_to_office", [json.dumps({"document": plan().model_dump()})], tmp_path, monkeypatch
    )
    original = word.validate

    def corrupted_output(data, kind):
        return original(data[:20], kind)

    monkeypatch.setattr(word, "validate", corrupted_output)
    oid = await submit(
        1, "text_to_office", {"text": "الطلبات", "target": "word"}, price, "bad-file"
    )
    await execute_job(ctx, str(await job_for(oid)))
    await deliver_failures(ctx)
    await deliver_failures(ctx)
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "failed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
    assert provider.calls == 1 and not delivery.files and len(delivery.errors) == 1
    assert not list(tmp_path.glob("[0-9]*/*/*"))
