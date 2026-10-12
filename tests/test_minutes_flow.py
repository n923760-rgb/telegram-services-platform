import json
from datetime import UTC, datetime
from decimal import Decimal
from io import BytesIO
from types import SimpleNamespace

import pytest
from docx import Document
from pypdf import PdfReader
from sqlalchemy import func, select

from app.core.db import sessions
from app.core.models import Job, Order, Service
from app.core.settings import config
from app.orders.engine import confirm_structure, submit
from app.services.base import ServiceError
from app.wallet.ledger import balance
from app.workers.runner import deliver_confirmations, deliver_failures, execute_job
from tests.minutes_fixtures import inputs, plan
from tests.test_foundation import job_for
from tests.test_real_services import setup
from tests.word_pdf_fixtures import renderer


async def prepare(tmp_path, monkeypatch, responses):
    store, provider, delivery, ctx, price = await setup(
        "meeting_minutes", responses, tmp_path, monkeypatch
    )
    original = ctx["runtime_factory"]

    def factory(jid, uid):
        runtime = original(jid, uid)
        return SimpleNamespace(ai=runtime.ai, storage=runtime.storage, renderer=renderer())

    ctx["runtime_factory"] = factory
    return store, provider, delivery, ctx, price


async def review(ctx, oid):
    jid = await job_for(oid)
    await execute_job(ctx, str(jid))
    await deliver_confirmations(ctx)
    await deliver_confirmations(ctx)
    return jid


@pytest.mark.parametrize("language", ["ar", "en"])
async def test_confirmed_source_notes_native_pair_single_capture_and_provider_call(
    tmp_path, monkeypatch, language
):
    store, provider, delivery, ctx, price = await prepare(
        tmp_path, monkeypatch, [json.dumps(plan())]
    )
    source = inputs(language)
    oid = await submit(1, "meeting_minutes", source, price, "minutes-native")
    jid = await review(ctx, oid)
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "waiting_confirmation"
        assert (await balance(db, 1)).reserved == price
        assert await db.scalar(select(func.count(Order.id))) == 1
    assert not delivery.files and len(delivery.confirmations) == 1
    with pytest.raises(ServiceError, match="not_allowed"):
        await confirm_structure(oid, 2, True)
    await confirm_structure(oid, 1, True)
    monkeypatch.setattr(config(), "ai_enabled", False)
    await execute_job(ctx, str(jid))
    await execute_job(ctx, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000 - price, 0)
        assert (await db.get(Job, jid)).cost_sar == Decimal(".004")
    assert provider.calls == 1
    assert [name for name, _ in delivery.files] == ["minutes.docx", "minutes.pdf"]
    text = [
        p.text.replace("\u200e", "") for p in Document(BytesIO(delivery.files[0][1])).paragraphs
    ]
    for index, line in enumerate(source["notes"].split("\n"), 1):
        assert text.count(f"[{index}] {line}") == 1
    pdf_text = PdfReader(BytesIO(delivery.files[1][1])).pages[0].extract_text()
    assert "00123" in pdf_text and "125.50" in pdf_text and "00017" in pdf_text
    assert not list(tmp_path.glob("[0-9]*/*/*"))


@pytest.mark.parametrize("repair_success", [False, True])
async def test_incomplete_classification_one_repair_or_release(
    tmp_path, monkeypatch, repair_success
):
    invalid = json.dumps({"assignments": [{"note_id": 1, "category": "action"}]})
    responses = [invalid, json.dumps(plan()) if repair_success else invalid]
    _, provider, delivery, ctx, price = await prepare(tmp_path, monkeypatch, responses)
    oid = await submit(1, "meeting_minutes", inputs(), price, "minutes-repair")
    await review(ctx, oid)
    if repair_success:
        await confirm_structure(oid, 1, True)
        await execute_job(ctx, str(await job_for(oid)))
    else:
        await deliver_failures(ctx)
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == ("completed" if repair_success else "failed")
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (
            1000 - price if repair_success else 1000,
            0,
        )
        assert (await db.get(Job, await job_for(oid))).cost_sar == Decimal(".008")
    assert provider.calls == 2
    assert len(delivery.files) == (2 if repair_success else 0)


async def test_declined_review_releases_without_render_but_keeps_actual_ai_cost(
    tmp_path, monkeypatch
):
    _, provider, delivery, ctx, price = await prepare(tmp_path, monkeypatch, [json.dumps(plan())])
    oid = await submit(1, "meeting_minutes", inputs(), price, "minutes-decline")
    await review(ctx, oid)
    await confirm_structure(oid, 1, False)
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "cancelled"
        assert (await balance(db, 1)).available == 1000
        assert (await balance(db, 1)).reserved == 0
        assert (await db.get(Job, await job_for(oid))).cost_sar == Decimal(".004")
    assert provider.calls == 1 and not delivery.files


async def test_confirmed_render_failure_releases_credit(tmp_path, monkeypatch):
    from app.providers.documents.base import DocumentError
    from app.providers.documents.libreoffice import LibreOfficeDocuments

    _, _, delivery, ctx, price = await prepare(tmp_path, monkeypatch, [json.dumps(plan())])
    oid = await submit(1, "meeting_minutes", inputs(), price, "minutes-render-fail")
    await review(ctx, oid)
    await confirm_structure(oid, 1, True)

    async def fail(*args, **kwargs):
        raise DocumentError("document_render_unavailable")

    monkeypatch.setattr(LibreOfficeDocuments, "word_pdf", fail)
    await execute_job(ctx, str(await job_for(oid)))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "failed"
        assert (await balance(db, 1)).available == 1000
        assert (await balance(db, 1)).reserved == 0
    assert not delivery.files


@pytest.mark.parametrize("old_version", [None, "1", "2"])
async def test_confirmed_delivery_retry_reuses_pair_without_ai_or_export(
    tmp_path, monkeypatch, old_version
):
    from app.providers.documents.libreoffice import LibreOfficeDocuments

    _, provider, delivery, ctx, price = await prepare(tmp_path, monkeypatch, [json.dumps(plan())])
    oid = await submit(1, "meeting_minutes", inputs(), price, "minutes-retry")
    jid = await review(ctx, oid)
    await confirm_structure(oid, 1, True)
    original = delivery.send

    async def offline(*args):
        raise ConnectionError("synthetic delivery failure")

    monkeypatch.setattr(delivery, "send", offline)
    await execute_job(ctx, str(jid))
    async with sessions.begin() as db:
        assert len((await db.get(Order, oid)).result["artifacts"]) == 2
        assert (await balance(db, 1)).reserved == price
        (await db.get(Job, jid)).next_run_at = datetime.now(UTC)
        if old_version:
            (await db.get(Order, oid)).service_version = old_version

    async def no_render(*args, **kwargs):
        raise AssertionError("prepared minutes must be reused")

    monkeypatch.setattr(LibreOfficeDocuments, "word_pdf", no_render)
    monkeypatch.setattr(delivery, "send", original)
    await execute_job(ctx, str(jid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        assert (await balance(db, 1)).reserved == 0
    assert provider.calls == 1 and len(delivery.files) == 2
    assert not list(tmp_path.glob("[0-9]*/*/*"))


@pytest.mark.parametrize("old_version", ["1", "2"])
@pytest.mark.parametrize("approved", [False, True])
async def test_boundary_upgrade_retains_admin_settings_and_cancels_unprepared_old_work(
    tmp_path, monkeypatch, old_version, approved
):
    from app.services.registry import registry

    _, provider, delivery, ctx, price = await prepare(
        tmp_path, monkeypatch, [json.dumps(plan())] if approved else []
    )
    oid = await submit(1, "meeting_minutes", inputs(), price, "minutes-old-boundaries")
    jid = await job_for(oid)
    if approved:
        await review(ctx, oid)
        await confirm_structure(oid, 1, True)
    async with sessions.begin() as db:
        (await db.get(Order, oid)).service_version = old_version
        row = await db.get(Service, "meeting_minutes")
        row.version, row.price_halala, row.price_stars = old_version, 777, 42
    async with sessions.begin() as db:
        await registry.sync(db)
        row = await db.get(Service, "meeting_minutes")
        assert (row.version, row.enabled, row.price_halala, row.price_stars) == ("3", True, 777, 42)
    await execute_job(ctx, str(jid))
    await execute_job(ctx, str(jid))
    await deliver_failures(ctx)
    await deliver_failures(ctx)
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "cancelled"
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000, 0)
        assert (await db.get(Job, jid)).cost_sar == Decimal(".004" if approved else "0")
    assert provider.calls == int(approved) and not delivery.files
    assert len(delivery.errors) == 1 and delivery.errors[0][2] == "service_changed"


@pytest.mark.parametrize("language,name", [("ar", "د. أحمد"), ("en", "Dr. Sam")])
async def test_titled_action_owner_native_export_after_approval_only(
    tmp_path, monkeypatch, language, name
):
    source = inputs(language) | {"notes": f"{name} sends report 00017 on 2026-10-12."}
    candidate = {
        "assignments": [
            {"note_id": 1, "category": "action", "assignee": name, "deadline": "2026-10-12"}
        ]
    }
    _, provider, delivery, ctx, price = await prepare(
        tmp_path, monkeypatch, [json.dumps(candidate)]
    )
    oid = await submit(1, "meeting_minutes", source, price, "minutes-titled-owner")
    jid = await review(ctx, oid)
    assert not delivery.files and name in delivery.confirmations[0][1]
    await confirm_structure(oid, 1, True)
    await execute_job(ctx, str(jid))
    await execute_job(ctx, str(jid))
    doc = Document(BytesIO(dict(delivery.files)["minutes.docx"]))
    assert [cell.text.replace("\u200e", "") for cell in doc.tables[0].rows[1].cells] == [
        "[1]",
        name,
        "2026-10-12",
    ]
    pdf = PdfReader(BytesIO(dict(delivery.files)["minutes.pdf"]))
    assert "00017" in pdf.pages[0].extract_text() and "2026-10-12" in pdf.pages[0].extract_text()
    assert provider.calls == 1 and len(delivery.files) == 2
    async with sessions() as db:
        funds = await balance(db, 1)
        assert (await db.get(Order, oid)).status == "completed"
        assert (funds.available, funds.reserved) == (1000 - price, 0)


async def test_note_limits_before_reservation(tmp_path, monkeypatch):
    _, provider, _, _, price = await prepare(tmp_path, monkeypatch, [])
    with pytest.raises(ServiceError, match="minutes_input_invalid"):
        await submit(
            1, "meeting_minutes", inputs() | {"notes": "line\n" * 81}, price, "minutes-invalid"
        )
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0
        assert (await balance(db, 1)).reserved == 0
    assert provider.calls == 0


@pytest.mark.parametrize("accepted", [True, False])
@pytest.mark.parametrize("defect", ["owner", "deadline"])
async def test_action_metadata_quality_review_repairs_or_refuses_before_export(
    tmp_path, monkeypatch, accepted, defect
):
    from app.providers.ai.gateway import AI
    from app.providers.storage import OwnedStorage
    from app.services.meeting_minutes.schema import Inputs, classification_schema

    source = inputs("en") | {
        "notes": (
            "Sam reported that Sara must submit report 00017 on 2026-10-12, "
            "not the earlier proposed 2026-10-10."
        )
    }
    good = {
        "assignments": [
            {"note_id": 1, "category": "action", "assignee": "Sara", "deadline": "2026-10-12"}
        ]
    }
    bad = {
        "assignments": [
            {
                **good["assignments"][0],
                "assignee": "Sam" if defect == "owner" else "Sara",
                "deadline": "2026-10-10" if defect == "deadline" else "2026-10-12",
            }
        ]
    }
    # Lexical validation alone cannot prove which quoted owner/date is correct.
    classification_schema(Inputs.parse(source).lines()).model_validate(bad)
    reject = '{"accepted":false,"issues":["meaning"]}'
    responses = [
        json.dumps(bad),
        reject,
        json.dumps(good if accepted else bad),
        '{"accepted":true,"issues":[]}' if accepted else reject,
    ]
    store, provider, delivery, ctx, price = await prepare(tmp_path, monkeypatch, responses)
    ctx["runtime_factory"] = lambda jid, uid: SimpleNamespace(
        ai=AI(provider, jid, uid, quality_review=True),
        storage=OwnedStorage(store, uid),
        renderer=renderer(),
    )
    oid = await submit(1, "meeting_minutes", source, price, "action-review")
    jid = await review(ctx, oid)
    assert provider.calls == 4 and not delivery.files
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == (
            "waiting_confirmation" if accepted else "failed"
        )
        assert (await db.get(Job, jid)).cost_sar == Decimal(".016")
    if accepted:
        await confirm_structure(oid, 1, True)
        await execute_job(ctx, str(jid))
        await execute_job(ctx, str(jid))
        document = Document(BytesIO(dict(delivery.files)["minutes.docx"]))
        cells = [cell.text.replace("\u200e", "") for cell in document.tables[0].rows[1].cells]
        assert cells == ["[1]", "Sara", "2026-10-12"]
        assert provider.calls == 4 and len(delivery.files) == 2
    async with sessions() as db:
        funds = await balance(db, 1)
        assert (funds.available, funds.reserved) == (1000 - price if accepted else 1000, 0)
    assert not list(tmp_path.glob("[0-9]*/*/*"))
