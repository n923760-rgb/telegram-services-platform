import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.core.db import sessions
from app.core.models import Job, Order, Service
from app.core.settings import config
from app.orders.engine import submit
from app.services.base import ServiceError
from app.services.registry import registry
from app.services.text_translation.service import TextTranslation
from app.services.text_translation.test_service import GOOD, PLAN, SOURCE
from app.wallet.ledger import balance
from app.workers.runner import execute_job
from tests.test_foundation import job_for
from tests.test_real_services import setup


@pytest.mark.parametrize("language,repair", [("en", False), ("en", True), ("ar", False)])
async def test_translation_delivers_all_lines_then_captures_once(
    tmp_path, monkeypatch, language, repair
):
    source = SOURCE if language == "en" else GOOD
    plan = (
        PLAN
        if language == "en"
        else {
            "segments": [
                {"id": i, "text": text} for i, text in enumerate(SOURCE.splitlines(), 1) if text
            ]
        }
    )
    if language == "ar":
        plan["segments"][1]["id"] = 2
    responses = [json.dumps(plan)]
    if repair:
        responses.insert(0, json.dumps({"segments": [{"id": 1, "text": "Wrong 123"}]}))
    store, provider, delivery, ctx, price = await setup(
        "text_translation", responses, tmp_path, monkeypatch
    )
    oid = await submit(
        1,
        "text_translation",
        {"text": source, "language": language, "style": "formal"},
        price,
        "translation",
    )
    jid = await job_for(oid)
    await execute_job(ctx, str(jid))
    await execute_job(ctx, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000 - price, 0)
        assert (await db.get(Job, jid)).cost_sar == Decimal(".004") * len(responses)
    expected = GOOD if language == "en" else SOURCE
    assert provider.calls == len(responses) and len(delivery.results) == 1
    assert delivery.results[0].text == expected
    assert dict(delivery.files)["translation.txt"].decode() == expected
    assert not list(tmp_path.glob("[0-9]*/*/*"))


async def test_invalid_translation_after_one_repair_releases_credit(tmp_path, monkeypatch):
    invalid = json.dumps({"segments": [{"id": 1, "text": "Missing source and wrong 123"}]})
    _, provider, delivery, ctx, price = await setup(
        "text_translation", [invalid, invalid, "unused"], tmp_path, monkeypatch
    )
    oid = await submit(
        1,
        "text_translation",
        {"text": SOURCE, "language": "en", "style": "formal"},
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


async def test_cached_translation_delivery_does_not_call_provider_again(tmp_path, monkeypatch):
    _, provider, delivery, ctx, price = await setup(
        "text_translation", [json.dumps(PLAN)], tmp_path, monkeypatch
    )
    oid = await submit(
        1,
        "text_translation",
        {"text": SOURCE, "language": "en", "style": "formal"},
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
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        assert (await balance(db, 1)).reserved == 0


async def test_file_save_failure_releases_credit(tmp_path, monkeypatch):
    store, provider, delivery, ctx, price = await setup(
        "text_translation", [json.dumps(PLAN)], tmp_path, monkeypatch
    )

    def fail(*args, **kwargs):
        raise ServiceError("storage_quota")

    monkeypatch.setattr(store, "save", fail)
    oid = await submit(
        1,
        "text_translation",
        {"text": SOURCE, "language": "en", "style": "formal"},
        price,
        "save-fail",
    )
    await execute_job(ctx, str(await job_for(oid)))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "failed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
    assert provider.calls == 1 and not delivery.files


@pytest.mark.parametrize("disabled", [False, True])
async def test_rejected_input_or_disabled_ai_reserves_no_credit(tmp_path, monkeypatch, disabled):
    _, provider, _, _, price = await setup("text_translation", [], tmp_path, monkeypatch)
    if disabled:
        monkeypatch.setattr(config(), "ai_enabled", False)
    with pytest.raises(ServiceError):
        await submit(
            1,
            "text_translation",
            {"text": SOURCE if disabled else " ", "language": "en", "style": "formal"},
            price,
            "rejected",
        )
    async with sessions() as db:
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
    assert provider.calls == 0


@pytest.mark.parametrize("language", ["ar", "en"])
@pytest.mark.parametrize("repair", [False, True])
async def test_contact_fidelity_uses_existing_repair_and_captures_once(
    tmp_path, monkeypatch, language, repair
):
    contact = "Source+sales@example.invalid https://example.invalid/Path?q=value"
    source = f"راسل {contact}" if language == "en" else f"Contact {contact}"
    output = f"Contact {contact}" if language == "en" else f"راسل {contact}"
    good = json.dumps({"segments": [{"id": 1, "text": output}]})
    bad = json.dumps({"segments": [{"id": 1, "text": output.replace("Source+sales", "changed")}]})
    responses = [bad, good] if repair else [good]
    _, provider, delivery, ctx, price = await setup(
        "text_translation", responses, tmp_path, monkeypatch
    )
    oid = await submit(
        1,
        "text_translation",
        {"text": source, "language": language, "style": "formal"},
        price,
        "contacts",
    )
    jid = await job_for(oid)
    await execute_job(ctx, str(jid))
    await execute_job(ctx, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        assert (await db.get(Job, jid)).cost_sar == Decimal(".004") * len(responses)
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000 - price, 0)
    assert provider.calls == len(responses) and len(delivery.results) == 1
    assert dict(delivery.files)["translation.txt"].decode() == output


@pytest.mark.parametrize(
    "contact",
    ["source@example.invalid", "https://example.invalid/source", "www.example.invalid/source"],
)
async def test_contact_changes_after_one_repair_fail_without_delivery(
    tmp_path, monkeypatch, contact
):
    bad = json.dumps({"segments": [{"id": 1, "text": contact.replace("source", "changed")}]})
    _, provider, delivery, ctx, price = await setup(
        "text_translation", [bad, bad, "unused"], tmp_path, monkeypatch
    )
    oid = await submit(
        1,
        "text_translation",
        {"text": contact, "language": "en", "style": "formal"},
        price,
        "bad-contact",
    )
    jid = await job_for(oid)
    await execute_job(ctx, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "failed"
        assert (await db.get(Job, jid)).cost_sar == Decimal(".008")
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
    assert provider.calls == 2 and len(provider.responses) == 1
    assert not delivery.results and not delivery.files
    assert not list(tmp_path.glob("[0-9]*/*/*"))


@pytest.mark.parametrize("cached", [False, True])
async def test_upgrade_preserves_prepared_v1_translation_and_admin_settings(
    tmp_path, monkeypatch, cached
):
    _, provider, delivery, ctx, price = await setup(
        "text_translation", [json.dumps(PLAN)], tmp_path, monkeypatch
    )
    oid = await submit(
        1,
        "text_translation",
        {"text": SOURCE, "language": "en", "style": "formal"},
        price,
        "upgrade",
    )
    jid = await job_for(oid)
    send = delivery.send
    if cached:

        async def unavailable(*args):
            raise ConnectionError("synthetic delivery failure")

        monkeypatch.setattr(delivery, "send", unavailable)
        await execute_job(ctx, str(jid))
    async with sessions.begin() as db:
        service = await db.get(Service, "text_translation")
        service.version, service.price_halala, service.price_stars = "1", 777, 25
        (await db.get(Order, oid)).service_version = "1"
        (await db.get(Job, jid)).next_run_at = datetime.now(UTC)
    async with sessions.begin() as db:
        await registry.sync(db)
        service = await db.get(Service, "text_translation")
        assert service.version == "2" and service.enabled
        assert (service.price_halala, service.price_stars) == (777, 25)

    async def forbidden(*args):
        raise AssertionError("upgrade must not regenerate historical output")

    monkeypatch.setattr(TextTranslation, "run", forbidden)
    monkeypatch.setattr(delivery, "send", send)
    await execute_job(ctx, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == ("completed" if cached else "cancelled")
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000 - price if cached else 1000, 0)
    assert provider.calls == int(cached)
    assert [name for name, _ in delivery.files] == (["translation.txt"] if cached else [])
