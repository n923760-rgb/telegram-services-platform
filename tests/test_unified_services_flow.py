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
from tests.ocr_fixtures import printed
from tests.test_foundation import fund, job_for
from tests.test_navigation import flow as flow
from tests.test_real_services import setup


@pytest.mark.parametrize("review", [False, True])
@pytest.mark.parametrize("fallback", [False, True])
async def test_unified_order_single_charge_cost_audit_and_cached_delivery(
    tmp_path, monkeypatch, fallback, review
):
    original = "Original 00123 125.50"
    response = json.dumps({"readable": True, "confidence": 0.99, "text": original})
    store, provider, delivery, ctx, price = await setup(
        "image_to_text", [response] if fallback else [], tmp_path, monkeypatch
    )
    if review:
        provider.responses.append('{"accepted":true,"issues":[]}')
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
        value.ai.quality_review = review
        return value

    ctx["runtime_factory"] = runtime
    image = store.save(1, "source.jpg", printed(), "image/jpeg")
    request = {"images": [image.key]}
    oid = await submit(1, "image_to_text", request, price, "unified")
    jid = await job_for(oid)
    await execute_job(ctx, str(jid))
    await execute_job(ctx, str(jid))
    assert await submit(1, "image_to_text", request, price, "unified") == oid
    assert provider.calls == int(fallback) + int(review) and len(delivery.results) == 1
    assert delivery.results[0].text == original
    documents.recognize.assert_awaited_once()
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 1
        assert (await db.get(Order, oid)).status == "completed"
        assert await db.scalar(select(func.count(CostUsage.id))) == int(fallback) + int(review)
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


async def test_native_review_rejection_releases_credit_without_unreviewed_delivery(
    tmp_path, monkeypatch
):
    candidate = json.dumps({"readable": True, "confidence": 0.99, "text": "Wrong 0123"})
    store, provider, delivery, ctx, price = await setup(
        "image_to_text",
        [
            '{"accepted":false,"issues":["numbers"]}',
            candidate,
            '{"accepted":false,"issues":["numbers"]}',
        ],
        tmp_path,
        monkeypatch,
    )
    factory = ctx["runtime_factory"]

    def runtime(jid, uid):
        value = factory(jid, uid)
        value.ai.quality_review = True
        value.documents = SimpleNamespace(
            recognize=AsyncMock(return_value=Recognition("Wrong 0123", 0.99))
        )
        return value

    ctx["runtime_factory"] = runtime
    file = store.save(1, "source.png", printed(), "image/png")
    oid = await submit(1, "image_to_text", {"images": [file.key]}, price, "reject-review")
    await execute_job(ctx, str(await job_for(oid)))
    assert provider.calls == 3 and not delivery.results
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "failed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
        assert await db.scalar(select(func.count(CostUsage.id))) == 3
