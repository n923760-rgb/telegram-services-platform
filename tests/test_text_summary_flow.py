import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.core.db import sessions
from app.core.models import Job, Order
from app.core.settings import config
from app.orders.engine import submit
from app.providers.ai.gateway import AI
from app.providers.storage import OwnedStorage
from app.services.base import ServiceError
from app.services.text_summary.schema import Inputs, render, summary_schema
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
    plan = PLAN
    if language == "en":
        plan = {
            "points": [
                {"text": "Order 00123 was not approved.", "source_ids": [1]},
                {"text": "Contact a@example.invalid", "source_ids": [3]},
            ]
        }
    responses = [json.dumps(plan)]
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
    expected, report = render(parsed, summary_schema(parsed).model_validate(plan))
    assert provider.calls == len(responses) and len(delivery.results) == 1
    assert delivery.results[0].text == expected
    label = "فقرات المصدر: " if language == "ar" else "Source paragraphs: "
    assert label + "[1]" in expected and label + "[3]" in expected
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


@pytest.mark.parametrize("old_version", [None, "1", "2"])
async def test_cached_summary_delivery_does_not_call_provider_again(
    tmp_path, monkeypatch, old_version
):
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
        if old_version:
            order = await db.get(Order, oid)
            order.service_version = old_version
            order.result = {**order.result, "text": "Legacy summary without inline references"}
    monkeypatch.setattr(delivery, "send", send)
    await execute_job(ctx, str(jid))
    assert provider.calls == 1 and delivery.results[0].text == (
        "Legacy summary without inline references"
        if old_version
        else render(
            Inputs.parse(values()), summary_schema(Inputs.parse(values())).model_validate(PLAN)
        )[0]
    )
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        assert (await balance(db, 1)).reserved == 0


@pytest.mark.parametrize("old_version", ["1", "2"])
async def test_upgrade_releases_unprepared_work_and_preserves_admin_prices(
    tmp_path, monkeypatch, old_version
):
    from app.core.models import Service
    from app.services.registry import registry

    _, provider, delivery, ctx, price = await setup("text_summary", [], tmp_path, monkeypatch)
    oid = await submit(1, "text_summary", values(), price, "old-summary")
    jid = await job_for(oid)
    async with sessions.begin() as db:
        (await db.get(Order, oid)).service_version = old_version
        row = await db.get(Service, "text_summary")
        row.version, row.price_halala, row.price_stars = old_version, 777, 42
    async with sessions.begin() as db:
        await registry.sync(db)
        row = await db.get(Service, "text_summary")
        assert (row.version, row.enabled, row.price_halala, row.price_stars) == ("3", True, 777, 42)
    await execute_job(ctx, str(jid))
    await execute_job(ctx, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "cancelled"
        assert (await db.get(Job, jid)).cost_sar == Decimal("0")
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
    assert provider.calls == 0 and not delivery.files


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


@pytest.mark.parametrize("text,disabled", [(" ", False), ("a\n" * 81, False), (SOURCE, True)])
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
        {"points": [{"text": "unknown", "source_ids": [5]}]},
        {"points": [{"text": "Amount 999", "source_ids": [2]}]},
        {"points": [{"text": letter, "source_ids": [1]} for letter in "abcd"]},
    ],
)
async def test_unknown_ungrounded_or_excessive_points_release(tmp_path, monkeypatch, response):
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


DECISIONS = (
    "Launch was planned for 20-10-2026 with a budget of 3500 SAR. "
    "It was postponed to 27-10-2026 because quality tests are incomplete. "
    "A budget increase to 5000 SAR was proposed but rejected.\n"
    "Khalid must finish tests before 24-10-2026. Sara must prepare the guide before 25-10-2026.\n"
    "The next meeting is on 26-10-2026."
)
FINAL = {
    "points": [
        {
            "text": "Launch postponed to 27-10-2026; budget remains 3500 SAR, increase to 5000 SAR rejected.",
            "source_ids": [1],
        },
        {
            "text": "Khalid: tests before 24-10-2026; Sara: guide before 25-10-2026.",
            "source_ids": [2],
        },
        {"text": "Next meeting: 26-10-2026.", "source_ids": [3]},
    ]
}


@pytest.mark.parametrize("defect", ["omission", "meaning", "unsupported_content"])
@pytest.mark.parametrize("corrected", [True, False])
async def test_production_review_repairs_or_refuses_semantic_defects(
    tmp_path, monkeypatch, defect, corrected
):
    from copy import deepcopy
    from types import SimpleNamespace

    bad = deepcopy(FINAL)
    if defect == "omission":
        bad["points"].pop()
    elif defect == "meaning":
        bad["points"][0]["text"] = "Launch on 20-10-2026; increase to 5000 SAR approved."
    else:
        bad["points"][1]["text"] += " Ali is responsible for both tasks."
    inputs = values(text=DECISIONS, length="standard", language="en")
    # All three defects pass source-ID/numeric checks; semantic review is necessary.
    summary_schema(Inputs.parse(inputs)).model_validate(bad)
    reject = json.dumps({"accepted": False, "issues": [defect]})
    responses = [
        json.dumps(bad),
        reject,
        json.dumps(FINAL if corrected else bad),
        '{"accepted":true,"issues":[]}' if corrected else reject,
    ]
    store, provider, delivery, ctx, price = await setup(
        "text_summary", responses, tmp_path, monkeypatch
    )
    ctx["runtime_factory"] = lambda jid, uid: SimpleNamespace(
        ai=AI(provider, jid, uid, quality_review=True), storage=OwnedStorage(store, uid)
    )
    oid = await submit(1, "text_summary", inputs, price, "review-summary")
    jid = await job_for(oid)
    await execute_job(ctx, str(jid))
    await execute_job(ctx, str(jid))
    async with sessions() as db:
        order = await db.get(Order, oid)
        assert order.status == ("completed" if corrected else "failed")
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000 - price if corrected else 1000, 0)
        assert (await db.get(Job, jid)).cost_sar == Decimal(".016")
    assert provider.calls == 4
    if corrected:
        assert "Next meeting: 26-10-2026." in delivery.results[0].text
        assert "approved" not in delivery.results[0].text
        assert dict(delivery.files)["summary-source.txt"].decode().endswith(DECISIONS)
    else:
        assert not delivery.results and not delivery.files
    assert not list(tmp_path.glob("[0-9]*/*/*"))
