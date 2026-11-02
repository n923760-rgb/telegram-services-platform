import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.core.db import sessions
from app.core.models import Job, Order, Service
from app.core.settings import config
from app.orders.engine import submit
from app.services.base import ServiceError
from app.services.text_editing.test_service import GOOD, PLAN, SOURCE
from app.wallet.ledger import balance
from app.workers.runner import execute_job
from tests.test_foundation import job_for
from tests.test_real_services import setup


@pytest.mark.parametrize("language,repair", [("en", False), ("en", True), ("ar", False)])
@pytest.mark.parametrize("mode", ["proofread", "rewrite"])
async def test_editing_delivers_all_lines_then_captures_once(
    tmp_path, monkeypatch, language, repair, mode
):
    source = (
        SOURCE if language == "en" else "الطلب 00123 بمبلغ 125.50\n\nالتاريخ 2026-10-10 والصفر 0\n"
    )
    plan = (
        PLAN
        if language == "en"
        else {
            "segments": [
                {"id": i, "text": text} for i, text in enumerate(source.splitlines(), 1) if text
            ]
        }
    )
    if language == "ar":
        plan["segments"][1]["id"] = 2
    responses = [json.dumps(plan)]
    if repair:
        responses.insert(0, json.dumps({"segments": [{"id": 1, "text": "Wrong 123"}]}))
    store, provider, delivery, ctx, price = await setup(
        "text_editing", responses, tmp_path, monkeypatch
    )
    oid = await submit(
        1,
        "text_editing",
        {"text": source, "mode": mode, **({"tone": "formal"} if mode == "rewrite" else {})},
        price,
        "editing",
    )
    jid = await job_for(oid)
    await execute_job(ctx, str(jid))
    await execute_job(ctx, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000 - price, 0)
        assert (await db.get(Job, jid)).cost_sar == Decimal(".004") * len(responses)
    expected = GOOD if language == "en" else source
    assert provider.calls == len(responses) and len(delivery.results) == 1
    assert delivery.results[0].text == expected
    assert dict(delivery.files)["revision.txt"].decode() == expected
    assert set(dict(delivery.files)) == {"revision.txt", "changes.txt"}
    assert source in dict(delivery.files)["changes.txt"].decode()
    assert not list(tmp_path.glob("[0-9]*/*/*"))


async def test_invalid_editing_after_one_repair_releases_credit(tmp_path, monkeypatch):
    invalid = json.dumps({"segments": [{"id": 1, "text": "Missing source and wrong 123"}]})
    _, provider, delivery, ctx, price = await setup(
        "text_editing", [invalid, invalid, "unused"], tmp_path, monkeypatch
    )
    oid = await submit(
        1,
        "text_editing",
        {"text": SOURCE, "mode": "rewrite", "tone": "formal"},
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


async def test_cached_editing_delivery_does_not_call_provider_again(tmp_path, monkeypatch):
    _, provider, delivery, ctx, price = await setup(
        "text_editing", [json.dumps(PLAN)], tmp_path, monkeypatch
    )
    oid = await submit(
        1,
        "text_editing",
        {"text": SOURCE, "mode": "rewrite", "tone": "formal"},
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
    assert provider.calls == 1 and delivery.results[0].text == GOOD
    assert set(dict(delivery.files)) == {"revision.txt", "changes.txt"}
    assert SOURCE in dict(delivery.files)["changes.txt"].decode()
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        assert (await balance(db, 1)).reserved == 0


@pytest.mark.parametrize("failed_save", [1, 2])
async def test_file_save_failure_releases_credit(tmp_path, monkeypatch, failed_save):
    store, provider, delivery, ctx, price = await setup(
        "text_editing", [json.dumps(PLAN)], tmp_path, monkeypatch
    )

    original, calls = store.save, 0

    def fail(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == failed_save:
            raise ServiceError("storage_quota")
        return original(*args, **kwargs)

    monkeypatch.setattr(store, "save", fail)
    oid = await submit(
        1,
        "text_editing",
        {"text": SOURCE, "mode": "rewrite", "tone": "formal"},
        price,
        "save-fail",
    )
    await execute_job(ctx, str(await job_for(oid)))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "failed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
    assert provider.calls == 1 and not delivery.files
    assert not list(tmp_path.glob("[0-9]*/*/*"))


@pytest.mark.parametrize("cached", [False, True])
async def test_upgrade_preserves_legacy_single_file_cache_and_admin_price(
    tmp_path, monkeypatch, cached
):
    from app.services.registry import registry
    from app.services.text_editing.service import TextEditing

    store, provider, delivery, ctx, price = await setup(
        "text_editing", [json.dumps(PLAN)], tmp_path, monkeypatch
    )
    oid = await submit(1, "text_editing", {"text": SOURCE, "mode": "proofread"}, price, "upgrade")
    jid = await job_for(oid)
    original = delivery.send
    extra = None
    if cached:

        async def unavailable(*args):
            raise ConnectionError("synthetic delivery failure")

        monkeypatch.setattr(delivery, "send", unavailable)
        await execute_job(ctx, str(jid))
    async with sessions.begin() as db:
        service = await db.get(Service, "text_editing")
        service.version, service.price_halala, service.price_stars = "1", 777, 25
        order = await db.get(Order, oid)
        order.service_version = "1"
        if cached:
            legacy = json.loads(json.dumps(order.result))
            extra = legacy["artifacts"].pop()["key"]
            order.result = legacy
        (await db.get(Job, jid)).next_run_at = datetime.now(UTC)
    if extra:
        store.delete(extra, 1)  # Fixture now represents the historical one-file result.
    async with sessions.begin() as db:
        await registry.sync(db)
        service = await db.get(Service, "text_editing")
        assert service.version == "3" and service.enabled
        assert (service.price_halala, service.price_stars) == (777, 25)

    async def forbidden(*args):
        raise AssertionError("upgrade must not regenerate either file")

    monkeypatch.setattr(TextEditing, "run", forbidden)
    monkeypatch.setattr(delivery, "send", original)
    await execute_job(ctx, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == ("completed" if cached else "cancelled")
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000 - price if cached else 1000, 0)
    assert provider.calls == int(cached)
    assert [name for name, _ in delivery.files] == (["revision.txt"] if cached else [])


@pytest.mark.parametrize("disabled", [False, True])
async def test_rejected_input_or_disabled_ai_reserves_no_credit(tmp_path, monkeypatch, disabled):
    _, provider, _, _, price = await setup("text_editing", [], tmp_path, monkeypatch)
    if disabled:
        monkeypatch.setattr(config(), "ai_enabled", False)
    with pytest.raises(ServiceError):
        await submit(
            1,
            "text_editing",
            {"text": SOURCE if disabled else " ", "mode": "rewrite", "tone": "formal"},
            price,
            "rejected",
        )
    async with sessions() as db:
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
    assert provider.calls == 0


async def test_changed_contact_after_repair_releases_credit(tmp_path, monkeypatch):
    invalid = json.dumps({"segments": [{"id": 1, "text": "Write to changed@example.invalid"}]})
    _, provider, delivery, ctx, price = await setup(
        "text_editing", [invalid, invalid], tmp_path, monkeypatch
    )
    oid = await submit(
        1,
        "text_editing",
        {"text": "write to source@example.invalid", "mode": "proofread"},
        price,
        "contact-fail",
    )
    await execute_job(ctx, str(await job_for(oid)))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "failed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
    assert provider.calls == 2 and not delivery.results and not delivery.files


@pytest.mark.parametrize("repair", [False, True])
async def test_swapped_values_repair_or_release_without_delivering_invalid_output(
    tmp_path, monkeypatch, repair
):
    source = "please sends order 00123 for 125.50 SAR"
    good = "Please send order 00123 for 125.50 SAR"
    swapped = "Please send order 125.50 for 00123 SAR"

    def plan(text):
        return json.dumps({"segments": [{"id": 1, "text": text}]})

    _, provider, delivery, ctx, price = await setup(
        "text_editing",
        [plan(swapped), plan(good if repair else swapped), "unused"],
        tmp_path,
        monkeypatch,
    )
    oid = await submit(
        1, "text_editing", {"text": source, "mode": "proofread"}, price, "swapped-values"
    )
    jid = await job_for(oid)
    await execute_job(ctx, str(jid))
    await execute_job(ctx, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == ("completed" if repair else "failed")
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000 - price if repair else 1000, 0)
    assert provider.calls == 2 and provider.responses == ["unused"]
    if repair:
        assert len(delivery.results) == 1 and delivery.results[0].text == good
        assert dict(delivery.files)["revision.txt"].decode() == good
        assert source in dict(delivery.files)["changes.txt"].decode()
    else:
        assert not delivery.results and not delivery.files
    assert not list(tmp_path.glob("[0-9]*/*/*"))
