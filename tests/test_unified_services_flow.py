import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import func, select

from app.core.db import sessions
from app.core.i18n import tr
from app.core.models import CostUsage, Order, Service
from app.ops.admin import set_service
from app.orders.engine import submit
from app.providers.documents.base import DocumentError, Recognition
from app.services.base import ServiceError
from app.wallet.ledger import balance
from app.workers.runner import execute_job
from tests.test_foundation import fund, job_for
from tests.test_navigation import flow as flow
from tests.test_real_services import setup


@pytest.mark.parametrize("fallback", [False, True])
async def test_unified_order_single_charge_cost_audit_and_cached_delivery(
    tmp_path, monkeypatch, fallback
):
    original = "Original 00123 125.50"
    response = json.dumps({"readable": True, "confidence": 0.99, "text": original})
    store, provider, delivery, ctx, price = await setup(
        "image_to_text", [response], tmp_path, monkeypatch
    )
    factory = ctx["runtime_factory"]
    documents = SimpleNamespace(
        recognize=AsyncMock(
            return_value=Recognition(original, 0.99),
            side_effect=DocumentError("ocr_unclear") if fallback else None,
        )
    )

    def runtime(jid, uid):
        value = factory(jid, uid)
        value.documents = documents
        return value

    ctx["runtime_factory"] = runtime
    image = store.save(1, "source.jpg", b"synthetic", "image/jpeg")
    request = {"images": [image.key]}
    oid = await submit(1, "image_to_text", request, price, "unified")
    jid = await job_for(oid)
    await execute_job(ctx, str(jid))
    await execute_job(ctx, str(jid))
    assert await submit(1, "image_to_text", request, price, "unified") == oid
    assert provider.calls == int(fallback) and len(delivery.results) == 1
    assert delivery.results[0].text == original
    documents.recognize.assert_awaited_once()
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 1
        assert (await db.get(Order, oid)).status == "completed"
        assert await db.scalar(select(func.count(CostUsage.id))) == int(fallback)
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000 - price, 0)


async def test_retired_service_cannot_be_sold_or_enabled_but_settings_remain():
    await fund()
    async with sessions.begin() as db:
        row = await db.get(Service, "local_ocr")
        row.enabled, row.price_halala = True, 777
    with pytest.raises(ServiceError, match="unavailable"):
        await set_service("local_ocr", enabled=True)
    with pytest.raises(ServiceError, match="unavailable"):
        await submit(1, "local_ocr", {"images": ["one"], "language": "en"}, 777, "retired")
    async with sessions() as db:
        assert (await db.get(Service, "local_ocr")).price_halala == 777
        assert await db.scalar(select(func.count(Order.id))) == 0
        assert (await balance(db, 1)).reserved == 0


async def test_legacy_selection_opens_canonical_draft_with_current_price(flow):
    transport, message, callback, state = flow
    await fund()
    async with sessions.begin() as db:
        row = await db.get(Service, "image_to_text")
        row.enabled, row.price_halala = True, 777
        (await db.get(Service, "local_ocr")).enabled = True
    await message("/start")
    await callback("service:local_ocr")
    data = await state.get_data()
    assert data["slug"] == "image_to_text" and data["price"] == 777
    assert [field["name"] for field in data["schema"]["fields"]] == ["images"]
    assert tr("ocr_name") in transport.messages[-1].text
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0
        assert (await balance(db, 1)).reserved == 0


async def test_legacy_selection_does_not_bypass_disabled_canonical_service(flow):
    transport, message, callback, state = flow
    await message("/start")
    async with sessions.begin() as db:
        (await db.get(Service, "local_ocr")).enabled = True
    await callback("service:local_ocr")
    assert transport.messages[-1].text == tr("unavailable")
    assert await state.get_state() is None
