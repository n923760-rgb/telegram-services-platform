import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from io import BytesIO

import pytest
from docx import Document

from app.core.db import sessions
from app.core.models import Job, Order, Service
from app.orders.engine import submit
from app.services.registry import registry
from app.wallet.ledger import balance
from app.workers.runner import deliver_failures, execute_job
from tests.test_foundation import job_for
from tests.test_ocr_translation_quality import GOOD, SOURCE
from tests.test_real_services import setup


def extracted(text=SOURCE):
    return json.dumps({"readable": True, "confidence": 0.99, "text": text})


async def create_order(store, price, language="en"):
    image = store.save(1, "input.jpg", b"synthetic test image", "image/jpeg")
    return await submit(
        1,
        "image_to_text",
        {"images": [image.key], "language": language, "style": "formal"},
        price,
        "numeric-translation",
    )


@pytest.mark.parametrize("repair", [False, True])
async def test_ocr_translation_preserves_numbers_then_captures_once(tmp_path, monkeypatch, repair):
    responses = [extracted()]
    if repair:
        responses.append(json.dumps({"text": GOOD.replace("125.50", "250.50")}))
    responses.append(json.dumps({"text": GOOD}))
    store, provider, delivery, ctx, price = await setup(
        "image_to_text", responses, tmp_path, monkeypatch
    )
    oid = await create_order(store, price)
    jid = await job_for(oid)
    await execute_job(ctx, str(jid))
    await execute_job(ctx, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000 - price, 0)
        assert (await db.get(Job, jid)).cost_sar == Decimal(".004") * len(responses)
    assert provider.calls == len(responses) and len(delivery.results) == 1
    assert delivery.results[0].text == GOOD


async def test_ocr_numeric_failure_after_one_repair_releases_and_notifies_once(
    tmp_path, monkeypatch
):
    wrong = json.dumps({"text": GOOD.replace("00123", "123")})
    store, provider, delivery, ctx, price = await setup(
        "image_to_text", [extracted(), wrong, wrong, "unused"], tmp_path, monkeypatch
    )
    oid = await create_order(store, price)
    await execute_job(ctx, str(await job_for(oid)))
    await deliver_failures(ctx)
    await deliver_failures(ctx)
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "failed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
    assert provider.calls == 3 and len(provider.responses) == 1
    assert not delivery.results and not delivery.files
    assert delivery.errors == [(1, oid, "provider_invalid")]
    assert not list(tmp_path.glob("[0-9]*/*/*"))


async def test_ocr_long_translation_cached_delivery_retains_editable_numeric_output(
    tmp_path, monkeypatch
):
    source, translated = (SOURCE + "\n") * 50, (GOOD + "\n") * 50
    store, provider, delivery, ctx, price = await setup(
        "image_to_text",
        [extracted(source), json.dumps({"text": translated})],
        tmp_path,
        monkeypatch,
    )
    oid = await create_order(store, price)
    jid = await job_for(oid)
    send = delivery.send

    async def unavailable(*args):
        raise ConnectionError("synthetic delivery failure")

    monkeypatch.setattr(delivery, "send", unavailable)
    await execute_job(ctx, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "delivering"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000 - price, price)
    monkeypatch.setattr(delivery, "send", send)
    async with sessions.begin() as db:
        (await db.get(Job, jid)).next_run_at = datetime.now(UTC) - timedelta(seconds=1)
    await execute_job(ctx, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000 - price, 0)
    assert provider.calls == 2 and len(delivery.results) == 1
    files = dict(delivery.files)
    assert files["result.txt"].decode() == translated.strip()
    document = Document(BytesIO(files["result.docx"]))
    body = "\n".join(p.text for p in document.paragraphs[1:])
    assert body.count("00123") == 50 and body.count("125.50") == 50
    document.paragraphs[1].runs[0].text = "Updated editable text 00123"
    saved = BytesIO()
    document.save(saved)
    assert Document(BytesIO(saved.getvalue())).paragraphs[1].text == "Updated editable text 00123"


async def test_ocr_without_translation_has_one_call_and_keeps_original_numbers(
    tmp_path, monkeypatch
):
    store, provider, delivery, ctx, price = await setup(
        "image_to_text", [extracted()], tmp_path, monkeypatch
    )
    oid = await create_order(store, price, "none")
    await execute_job(ctx, str(await job_for(oid)))
    assert provider.calls == 1 and delivery.results[0].text == SOURCE


async def test_ocr_version_upgrade_retains_admin_settings_and_releases_old_work(
    tmp_path, monkeypatch
):
    store, provider, delivery, ctx, price = await setup("image_to_text", [], tmp_path, monkeypatch)
    oid = await create_order(store, price)
    async with sessions.begin() as db:
        row = await db.get(Service, "image_to_text")
        row.version, row.price_halala, row.enabled = "1", 777, True
        (await db.get(Order, oid)).service_version = "1"
    async with sessions.begin() as db:
        await registry.sync(db)
    async with sessions() as db:
        row = await db.get(Service, "image_to_text")
        assert row.version == "2" and row.price_halala == 777 and row.enabled
    await execute_job(ctx, str(await job_for(oid)))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "cancelled"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
    assert provider.calls == 0 and not delivery.results
