import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.core.db import sessions
from app.core.models import Order, OrderCompletion, Publication, PublicationRevision, Setting, User
from app.ops.admin import refund
from app.orders.engine import submit
from app.publications import fulfillment as flow
from app.publications import prepared_page, repository
from app.services.base import Result, ServiceError
from app.services.registry import registry
from app.wallet.ledger import balance
from app.workers.runner import execute_job
from tests.profile_page_fixtures import plan, profile
from tests.test_foundation import Delivery, fund, job_for
from tests.test_stars import pay, prepare
from tests.test_stars import stars as stars

ORIGIN = "https://profiles.example.invalid"


async def finish(monkeypatch, order_id, *, invalid_digest=False):
    identity = uuid4()

    async def extract(schema, source, prompt):
        return schema.model_validate(plan())

    ai = SimpleNamespace(extract=AsyncMock(side_effect=extract))
    completion = await flow.generate(
        ai, profile(), "هوية تناسب مهنة العميل", publication_id=identity, origin=ORIGIN
    )
    if invalid_digest:
        completion.payload["digests"]["qr.png"] = "0" * 64
    run = AsyncMock(return_value=Result(text="Private draft prepared", completion=completion))
    monkeypatch.setattr(registry, "get", lambda *args: SimpleNamespace(run=run))
    await execute_job({"delivery": Delivery()}, str(await job_for(order_id)))
    async with sessions() as db:
        order = await db.get(Order, order_id)
        assert order.status == "completed"
        right = flow.HostingEntitlement(
            owner_id=order.user_id,
            order_id=order_id,
            publication_id=identity,
            service_slug=order.service_slug,
            service_version=order.service_version,
            payment_mode=order.payment_mode,
            price_halala=order.price_halala,
            price_stars=order.price_stars,
            purchase_terms_hash=order.terms_hash,
            hosting_terms_hash="a" * 64,
            expires_at=datetime.now(UTC) + timedelta(days=30),
        )
    # Synthetic trusted resolver only. No production hosting purchase is issued.
    resolver = AsyncMock(return_value=right)
    return identity, ai, resolver, right, run


async def ready(monkeypatch, **kwargs):
    await fund()
    order_id = await submit(1, "echo", {"text": "source"}, 100, "profile-projection")
    return order_id, *(await finish(monkeypatch, order_id, **kwargs))


async def assert_pending(order_id):
    async with sessions() as db:
        assert await db.scalar(select(func.count()).select_from(Publication)) == 0
        assert await db.scalar(select(func.count()).select_from(PublicationRevision)) == 0
        row = await db.get(OrderCompletion, order_id)
        assert row.state == "pending" and row.payload is not None


async def test_generated_handoff_creates_private_owner_page_without_new_ai_or_consent(monkeypatch):
    order_id, identity, ai, resolver, right, run = await ready(monkeypatch)
    async with sessions.begin() as db:
        order = await db.get(Order, order_id)
        assert order.files_deleted
        order.inputs, order.result = {}, None
    assert await flow.transfer(1, order_id, origin=ORIGIN, resolve_entitlement=resolver)
    review = await prepared_page.review(1, identity, origin=ORIGIN)
    assert review["revision"] == 1 and review["active_revision"] is None
    assert review["state"] == "draft" and review["consent_count"] == 0
    assert review["expires_at"] == right.expires_at
    assert review["content"]["profile"] == profile()
    assert await prepared_page.public_bundle(identity, origin=ORIGIN) is None
    assert not await flow.transfer(1, order_id, origin=ORIGIN, resolve_entitlement=resolver)
    assert ai.extract.await_count == run.await_count == resolver.await_count == 1
    async with sessions() as db:
        assert (await balance(db, 1)).available == 900
        row = await db.get(OrderCompletion, order_id)
        assert row.state == "applied" and row.payload is None
    await repository.delete_content(1, identity)
    assert not await flow.transfer(1, order_id, origin=ORIGIN, resolve_entitlement=resolver)
    async with sessions() as db:
        assert (await db.get(Publication, identity)).state == "deleted"


@pytest.mark.parametrize(
    "change",
    [
        "owner",
        "order",
        "page",
        "service",
        "version",
        "mode",
        "price",
        "stars",
        "purchase_terms",
        "expired",
        "too_long",
        "missing",
    ],
)
async def test_arbitrary_completed_order_never_implies_hosting_right(monkeypatch, change):
    order_id, identity, ai, resolver, right, run = await ready(monkeypatch)
    field, value = {
        "owner": ("owner_id", 2),
        "order": ("order_id", uuid4()),
        "page": ("publication_id", uuid4()),
        "service": ("service_slug", "different"),
        "version": ("service_version", "999"),
        "mode": ("payment_mode", "stars"),
        "price": ("price_halala", 1500),
        "stars": ("price_stars", 20),
        "purchase_terms": ("purchase_terms_hash", "b" * 64),
        "expired": ("expires_at", datetime.now(UTC) - timedelta(seconds=1)),
        "too_long": ("expires_at", datetime.now(UTC) + timedelta(days=367)),
        "missing": ("owner_id", 1),
    }[change]
    resolver.return_value = None if change == "missing" else right.model_copy(update={field: value})
    with pytest.raises(ValueError if change in {"missing", "too_long"} else ServiceError):
        await flow.transfer(1, order_id, origin=ORIGIN, resolve_entitlement=resolver)
    await assert_pending(order_id)
    assert ai.extract.await_count == run.await_count == 1


async def test_failed_projection_rolls_back_resolver_allocation_revision_and_receipt(monkeypatch):
    order_id, identity, ai, _, right, run = await ready(monkeypatch)

    async def resolve(db, order):
        db.add(Setting(key="fixture_hosting_allocation", value={"order": str(order.id)}))
        return right

    original = repository.revise_in_transaction

    async def broken(*args, **kwargs):
        await original(*args, **kwargs)
        raise RuntimeError("synthetic failure after revision flush")

    monkeypatch.setattr(repository, "revise_in_transaction", broken)
    with pytest.raises(RuntimeError):
        await flow.transfer(1, order_id, origin=ORIGIN, resolve_entitlement=resolve)
    await assert_pending(order_id)
    async with sessions() as db:
        assert await db.get(Setting, "fixture_hosting_allocation") is None
    monkeypatch.setattr(repository, "revise_in_transaction", original)
    assert await flow.transfer(1, order_id, origin=ORIGIN, resolve_entitlement=resolve)
    assert ai.extract.await_count == run.await_count == 1


async def test_concurrent_transfers_allocate_one_private_draft(monkeypatch):
    order_id, identity, ai, resolver, right, run = await ready(monkeypatch)
    # Test DB serialization independently of the separate two-slot native render cap.
    real_render = prepared_page.render_async
    async with asyncio.timeout(30):
        await real_render(
            (await repository_content(order_id)), publication_id=identity, origin=ORIGIN
        )
        monkeypatch.setattr(prepared_page, "render_async", AsyncMock())
        outcomes = await asyncio.gather(
            *[
                flow.transfer(1, order_id, origin=ORIGIN, resolve_entitlement=resolver)
                for _ in range(3)
            ]
        )
    assert outcomes.count(True) == 1 and outcomes.count(False) == 2
    assert resolver.await_count == ai.extract.await_count == 1
    async with sessions() as db:
        assert await db.scalar(select(func.count()).select_from(PublicationRevision)) == 1


async def repository_content(order_id):
    async with sessions() as db:
        return (await db.get(OrderCompletion, order_id)).payload


async def test_native_export_drift_rejects_before_any_right_or_page_write(monkeypatch):
    order_id, identity, ai, resolver, right, run = await ready(monkeypatch, invalid_digest=True)
    with pytest.raises(prepared_page.PreparedPageError):
        await flow.transfer(1, order_id, origin=ORIGIN, resolve_entitlement=resolver)
    resolver.assert_not_awaited()
    await assert_pending(order_id)


@pytest.mark.parametrize("change", ["ban", "refund", "owner"])
async def test_owner_and_settlement_are_rechecked_after_native_preflight(monkeypatch, change):
    order_id, identity, ai, resolver, right, run = await ready(monkeypatch)
    if change == "owner":
        with pytest.raises(ServiceError):
            await flow.transfer(2, order_id, origin=ORIGIN, resolve_entitlement=resolver)
    else:
        original = prepared_page.render_async

        async def render(*args, **kwargs):
            result = await original(*args, **kwargs)
            if change == "refund":
                await refund(order_id)
            else:
                async with sessions.begin() as db:
                    (await db.get(User, 1)).banned = True
            return result

        monkeypatch.setattr(prepared_page, "render_async", render)
        with pytest.raises(ServiceError):
            await flow.transfer(1, order_id, origin=ORIGIN, resolve_entitlement=resolver)
    resolver.assert_not_awaited()
    await assert_pending(order_id)


async def test_stars_refund_request_during_preflight_blocks_projection(monkeypatch, stars):
    order_id = await prepare()
    await pay(order_id)
    identity, ai, resolver, right, run = await finish(monkeypatch, order_id)
    original = prepared_page.render_async

    async def render(*args, **kwargs):
        files = await original(*args, **kwargs)
        await refund(order_id)
        return files

    monkeypatch.setattr(prepared_page, "render_async", render)
    with pytest.raises(ServiceError, match="payment_invalid"):
        await flow.transfer(1, order_id, origin=ORIGIN, resolve_entitlement=resolver)
    resolver.assert_not_awaited()
    await assert_pending(order_id)
