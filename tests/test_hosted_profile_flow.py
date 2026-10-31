"""Registered pilot through real order/cost/retention/publication contracts.

Provider and delivery are synthetic. No actual network call, charge or public page.
"""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from pydantic import SecretStr
from sqlalchemy import func, select

from app.core.db import sessions
from app.core.models import CostHold, CostUsage, Job, Order, OrderCompletion, Publication, Service
from app.core.settings import config
from app.orders.contracts import make_quote
from app.orders.engine import submit
from app.payments.stars import terms_hash
from app.providers.ai.gateway import AI
from app.providers.storage import LocalStorage, OwnedStorage
from app.publications import fulfillment, prepared_page
from app.services.base import ServiceError
from app.services.hosted_profile.service import HostedProfile
from app.services.hosted_profile.test_service import design_plan, inputs
from app.services.registry import registry
from app.wallet.ledger import apply, balance
from app.workers.runner import execute_job
from tests.test_file_layers import Provider
from tests.test_foundation import fund, job_for
from tests.test_miniapp_confirmation_flow import confirm
from tests.test_miniapp_confirmation_flow import confirm_shared as confirm_shared
from tests.test_miniapp_confirmation_flow import shared as shared
from tests.test_miniapp_drafts_flow import OWNER
from tests.test_real_services import Delivery
from tests.test_stars import pay
from tests.test_stars import stars as stars

ORIGIN = "https://profiles.example.invalid"


@pytest.fixture
async def pilot(monkeypatch, tmp_path):
    cfg = config()
    for key, value in {
        "admin_ids": [11],
        "ai_enabled": True,
        "publications_enabled": True,
        "publication_origin": ORIGIN,
        "storage_root": tmp_path,
        "ai_api_key": SecretStr("synthetic-test-key"),
        "ai_input_usd_per_million": Decimal("1"),
        "ai_output_usd_per_million": Decimal("1"),
    }.items():
        monkeypatch.setattr(cfg, key, value)
    async with sessions.begin() as db:
        service = await db.get(Service, "hosted_profile")
        assert service and not service.enabled and service.price_halala == 2900
        service.enabled = True  # Synthetic administrator qualification only.
    await fund(11, 10000)


async def purchase(values=None, *, owner=11, key="pilot"):
    stars = config().stars_enabled
    async with sessions() as db:
        service = await db.get(Service, "hosted_profile")
        quote = make_quote(service, HostedProfile, stars=stars)
    payment = (
        {
            "expected_stars": service.price_stars,
            "terms_version": config().stars_terms_version,
            "expected_terms_hash": terms_hash(),
        }
        if stars
        else {}
    )
    return await submit(
        owner, "hosted_profile", values or inputs(), 2900, key, "1", purchase_quote=quote, **payment
    )


def runtime(tmp_path, *, responses=None, delivery=None):
    store = LocalStorage(tmp_path)
    provider = Provider(
        responses
        if responses is not None
        else [
            json.dumps(design_plan()),
            '{"accepted":true,"issues":[]}',
        ]
    )
    delivery = delivery or Delivery(store)
    ctx = {
        "delivery": delivery,
        "runtime_factory": lambda jid, uid: SimpleNamespace(
            ai=AI(provider, jid, uid, quality_review=True), storage=OwnedStorage(store, uid)
        ),
    }
    return provider, delivery, ctx


async def assert_costs(calls):
    async with sessions() as db:
        assert await db.scalar(select(func.count()).select_from(CostUsage)) == calls
        assert (
            await db.scalar(
                select(func.count())
                .select_from(CostHold)
                .where(CostHold.status.in_(["open", "uncertain"]))
            )
            == 0
        )


async def test_customer_cannot_buy_pilot_even_when_admin_enabled_it(pilot):
    await fund(12, 10000)
    assert not registry.can_request("hosted_profile")
    with pytest.raises(ServiceError, match="unavailable"):
        await purchase(owner=12)
    async with sessions() as db:
        assert (await balance(db, 12)).available == 10000
        assert await db.scalar(select(func.count()).select_from(Order)) == 0


async def test_shared_admin_intake_collects_free_brief_and_confirms_original_contract(
    pilot, confirm_shared, monkeypatch
):
    monkeypatch.setattr(config(), "admin_ids", [11, OWNER])
    async with sessions.begin() as db:
        await apply(db, OWNER, "credit", 9000, "synthetic-profile-topup")
    call = confirm_shared[0]
    response = await call("open", slug="hosted_profile")
    assert response.status_code == 200
    draft = response.json()["draft"]
    values = inputs()
    for field in HostedProfile.input_schema.fields:
        assert draft["field"]["prompt"]["ar"]
        response = await call(
            "answer", revision=draft["revision"], operation=uuid4().hex, value=values[field.name]
        )
        assert response.status_code == 200
        draft = response.json()["draft"]
    assert draft["ready"] and "29.00" in draft["review"]["ar"]
    assert HostedProfile.purchase_contract["ar"] in draft["review"]["ar"]
    data = await confirm_shared[3].get_data()
    assert data["inputs"] == values
    response = await confirm(draft["confirmation"]["token"])
    assert response.status_code == 200
    assert response.json()["receipt"]["purchase_terms"] == data["purchase_quote"]
    async with sessions() as db:
        assert (await balance(db, OWNER)).reserved == 2900
        assert await db.scalar(select(func.count()).select_from(CostUsage)) == 0


async def test_registered_plugin_purchase_ai_private_transfer_and_explicit_publication(
    pilot, tmp_path
):
    order_id = await purchase()
    provider, delivery, ctx = runtime(tmp_path)
    job = await job_for(order_id)
    await execute_job(ctx, str(job))
    await execute_job(ctx, str(job))
    assert provider.calls == 2 and len(delivery.results) == 1
    assert {name for name, _ in delivery.files} == {
        "profile.html",
        "qr.png",
        "qr.svg",
        "share-card.png",
    }
    async with sessions() as db:
        order = await db.get(Order, order_id)
        assert order.status == "completed" and order.files_deleted
        assert (await balance(db, 11)).available == 7100
        assert (await balance(db, 11)).reserved == 0
        quote = order.purchase_terms_snapshot
        row = await db.get(OrderCompletion, order_id)
        assert row.state == "pending"
        identity = UUID(row.payload["publication_id"])
        assert await db.scalar(select(func.count()).select_from(Publication)) == 0
    await assert_costs(2)
    applied = await asyncio.gather(
        fulfillment.transfer_purchased(11, order_id, origin=ORIGIN),
        fulfillment.transfer_purchased(11, order_id, origin=ORIGIN),
    )
    assert sorted(applied) == [False, True]
    review = await prepared_page.review(11, identity, origin=ORIGIN)
    assert review["state"] == "draft" and review["consent_count"] == 0
    assert review["expires_at"] == datetime.fromisoformat(quote["expires_at"])
    assert await prepared_page.public_bundle(identity, origin=ORIGIN) is None
    await prepared_page.approve(
        11,
        identity,
        origin=ORIGIN,
        revision=review["revision"],
        expected_active=None,
        expected_expires_at=review["expires_at"],
        content_hash=review["content_hash"],
        terms_hash="a" * 64,
        operation_id=uuid4(),
        expected_state="draft",
        expected_consents=0,
    )
    assert await prepared_page.public_bundle(identity, origin=ORIGIN) == review["files"]
    assert provider.calls == 2


async def test_native_stars_pilot_keeps_independent_price_and_requires_paid_charge(
    pilot, stars, tmp_path
):
    async with sessions.begin() as db:
        service = await db.get(Service, "hosted_profile")
        service.price_stars = 20  # Independent synthetic Stars price, no conversion.
    order_id = await purchase()
    async with sessions() as db:
        order = await db.get(Order, order_id)
        assert order.status == "awaiting_payment" and await job_for(order_id) is None
    await pay(order_id, user_id=11)
    provider, _, ctx = runtime(tmp_path)
    await execute_job(ctx, str(await job_for(order_id)))
    assert await fulfillment.transfer_purchased(11, order_id, origin=ORIGIN)
    async with sessions() as db:
        order = await db.get(Order, order_id)
        assert order.status == "completed" and order.price_stars == 20
        assert order.purchase_terms_snapshot["price_stars"] == 20
        assert order.purchase_terms_hash != order.terms_hash
        assert (await balance(db, 11)).available == 10000
        assert (await balance(db, 11)).reserved == 0
    assert provider.calls == 2
    await assert_costs(2)


async def test_delivery_failure_reuses_prepared_ai_and_page_identity(pilot, tmp_path):
    class Uncertain(Delivery):
        async def send(self, *args):
            if not self.results:
                self.results.append(None)
                raise OSError("synthetic delivery interruption")
            await super().send(*args)

    provider, delivery, ctx = runtime(tmp_path, delivery=Uncertain(LocalStorage(tmp_path)))
    order_id = await purchase()
    job = await job_for(order_id)
    await execute_job(ctx, str(job))
    async with sessions.begin() as db:
        order = await db.get(Order, order_id)
        assert order.status == "delivering" and order.result
        before = order.result["completion"]
        row = await db.get(Job, job)
        row.next_run_at = datetime.now(UTC) - timedelta(seconds=1)
    await execute_job(ctx, str(job))
    async with sessions() as db:
        order = await db.get(Order, order_id)
        assert order.status == "completed" and order.result["completion"] == before
        assert (await db.get(OrderCompletion, order_id)).content_hash == delivery.results[
            -1
        ].completion.digest()
    assert provider.calls == 2
    await assert_costs(2)


@pytest.mark.parametrize("failure", ["invalid_source", "provider_invalid", "disabled"])
async def test_failures_release_credit_without_hosting_or_orphaned_handoff(
    pilot, monkeypatch, tmp_path, failure
):
    values = inputs(links="javascript:alert(1)") if failure == "invalid_source" else inputs()
    order_id = await purchase(values)
    if failure == "disabled":
        monkeypatch.setattr(config(), "publications_enabled", False)
    provider, _, ctx = runtime(
        tmp_path, responses=["{}", "{}"] if failure == "provider_invalid" else None
    )
    await execute_job(ctx, str(await job_for(order_id)))
    async with sessions() as db:
        assert (await db.get(Order, order_id)).status == "failed"
        assert (await balance(db, 11)).available == 10000
        assert (await balance(db, 11)).reserved == 0
        assert await db.scalar(select(func.count()).select_from(OrderCompletion)) == 0
        assert await db.scalar(select(func.count()).select_from(Publication)) == 0
    assert provider.calls == (2 if failure == "provider_invalid" else 0)
    await assert_costs(provider.calls)
