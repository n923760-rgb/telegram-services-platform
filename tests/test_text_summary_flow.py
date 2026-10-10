import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.core.db import sessions
from app.core.models import Job, Order
from app.core.settings import config
from app.orders.engine import submit
from app.services.base import ServiceError
from app.services.text_summary.schema import Inputs, render, selection_schema
from app.services.text_summary.test_service import PLAN, SOURCE, values
from app.wallet.ledger import balance
from app.workers.runner import execute_job
from tests.test_foundation import job_for
from tests.test_real_services import setup


@pytest.mark.parametrize("language", ["ar", "en"])
@pytest.mark.parametrize("length,repair", [("short", False), ("standard", True)])
async def test_source_points_and_report_capture_once(
    tmp_path, monkeypatch, language, length, repair
):
    inputs = values(language=language, length=length)
    if language == "en":
        inputs["text"] = (
            "I did not agree to order 00123\nAmount 125.50 on 2026-10-10\nContact a@example.invalid\nBackground"
        )
    responses = [json.dumps(PLAN)]
    if repair:
        responses.insert(0, json.dumps({"source_ids": [1, 1]}))
    _, provider, delivery, ctx, price = await setup(
        "text_summary", responses, tmp_path, monkeypatch
    )
    oid = await submit(1, "text_summary", inputs, price, "summary")
    jid = await job_for(oid)
    await execute_job(ctx, str(jid))
    await execute_job(ctx, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000 - price, 0)
        assert (await db.get(Job, jid)).cost_sar == Decimal(".004") * len(responses)
    parsed = Inputs.parse(inputs)
    expected, report = render(parsed, selection_schema(parsed).model_validate(PLAN))
    assert provider.calls == len(responses) and len(delivery.results) == 1
    assert delivery.results[0].text == expected
    assert dict(delivery.files)["summary-source.txt"].decode() == report
    assert not list(tmp_path.glob("[0-9]*/*/*"))


async def test_invalid_summary_after_one_repair_releases_credit(tmp_path, monkeypatch):
    invalid = json.dumps({"source_ids": [1, 1]})
    _, provider, delivery, ctx, price = await setup(
        "text_summary", [invalid, invalid, "unused"], tmp_path, monkeypatch
    )
    oid = await submit(
        1,
        "text_summary",
        values(),
        price,
        "invalid",
    )
    await execute_job(ctx, str(await job_for(oid)))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "failed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
    assert provider.calls == 2 and not delivery.results and not delivery.files
    assert len(provider.responses) == 1


async def test_cached_summary_delivery_does_not_call_provider_again(tmp_path, monkeypatch):
    _, provider, delivery, ctx, price = await setup(
        "text_summary", [json.dumps(PLAN)], tmp_path, monkeypatch
    )
    oid = await submit(
        1,
        "text_summary",
        values(),
        price,
        "cached",
    )
    jid = await job_for(oid)
    send = delivery.send

    async def unavailable(*args):
        raise ConnectionError("synthetic delivery failure")

    monkeypatch.setattr(delivery, "send", unavailable)
    await execute_job(ctx, str(jid))
    async with sessions.begin() as db:
        assert (await db.get(Order, oid)).status == "delivering"
        (await db.get(Job, jid)).next_run_at = datetime.now(UTC) - timedelta(seconds=1)
    monkeypatch.setattr(delivery, "send", send)
    await execute_job(ctx, str(jid))
    assert (
        provider.calls == 1
        and delivery.results[0].text
        == render(
            Inputs.parse(values()), selection_schema(Inputs.parse(values())).model_validate(PLAN)
        )[0]
    )
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        assert (await balance(db, 1)).reserved == 0


async def test_file_save_failure_releases_credit(tmp_path, monkeypatch):
    store, provider, delivery, ctx, price = await setup(
        "text_summary", [json.dumps(PLAN)], tmp_path, monkeypatch
    )

    def fail(*args, **kwargs):
        raise ServiceError("storage_quota")

    monkeypatch.setattr(store, "save", fail)
    oid = await submit(
        1,
        "text_summary",
        values(),
        price,
        "save-fail",
    )
    await execute_job(ctx, str(await job_for(oid)))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "failed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
    assert provider.calls == 1 and not delivery.files


@pytest.mark.parametrize(
    "text,disabled", [(" ", False), ("one paragraph", False), ("a\n" * 81, False), (SOURCE, True)]
)
async def test_rejected_input_or_disabled_ai_reserves_no_credit(
    tmp_path, monkeypatch, text, disabled
):
    _, provider, _, _, price = await setup("text_summary", [], tmp_path, monkeypatch)
    if disabled:
        monkeypatch.setattr(config(), "ai_enabled", False)
    with pytest.raises(ServiceError):
        await submit(
            1,
            "text_summary",
            values(text=text),
            price,
            "rejected",
        )
    async with sessions() as db:
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
    assert provider.calls == 0


@pytest.mark.parametrize(
    "response",
    [
        {"source_ids": [5]},
        {"source_ids": [1], "text": "Invented result"},
        {"source_ids": [1, 2, 3, 4]},
    ],
)
async def test_unknown_generated_or_full_source_selection_releases(tmp_path, monkeypatch, response):
    invalid = json.dumps(response)
    _, provider, delivery, ctx, price = await setup(
        "text_summary", [invalid, invalid], tmp_path, monkeypatch
    )
    oid = await submit(1, "text_summary", values(), price, "source-fail")
    await execute_job(ctx, str(await job_for(oid)))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "failed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
    assert provider.calls == 2 and not delivery.results and not delivery.files
