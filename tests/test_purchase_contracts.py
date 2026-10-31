import asyncio
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError

from app.core.db import sessions
from app.core.models import Ledger, Order, Publication, Service, StarCheckout
from app.core.settings import config
from app.files.retention import cleanup
from app.orders import contracts
from app.orders.engine import register, submit
from app.payments.stars import terms_hash
from app.publications import fulfillment, prepared_page
from app.publications.offering import CONTRACT, PRICE_HALALA
from app.services.base import Result, ServiceError
from app.services.registry import registry
from app.wallet.ledger import apply, balance
from app.workers.runner import execute_job
from tests.profile_page_fixtures import plan, profile
from tests.test_foundation import Delivery, fund, job_for
from tests.test_miniapp_confirmation_flow import confirm
from tests.test_miniapp_confirmation_flow import confirm_shared as confirm_shared
from tests.test_miniapp_confirmation_flow import prepare as mini_prepare
from tests.test_miniapp_confirmation_flow import shared as shared
from tests.test_miniapp_drafts_flow import OWNER
from tests.test_stars import pay
from tests.test_stars import stars as stars

ORIGIN = "https://profiles.example.invalid"


@pytest.fixture
async def policy(monkeypatch):
    # Explicit synthetic eligibility only. No production service is registered.
    monkeypatch.setattr(registry.types["echo"], "purchase_contract", deepcopy(CONTRACT))
    async with sessions.begin() as db:
        row = await db.get(Service, "echo")
        row.price_halala, row.price_stars = PRICE_HALALA, 20


async def quote(*, stars=False):
    async with sessions() as db:
        row = await db.get(Service, "echo")
        return contracts.make_quote(row, registry.types["echo"], stars=stars)


async def purchase(value, *, key="contract", **kwargs):
    return await submit(
        1, "echo", {"text": "source"}, 2900, key, "1", purchase_quote=value, **kwargs
    )


async def reserve_count():
    async with sessions() as db:
        return await db.scalar(
            select(func.count()).select_from(Ledger).where(Ledger.kind == "reserve")
        )


async def test_concurrent_exact_purchase_keeps_original_six_month_terms_once(policy, monkeypatch):
    await fund(1, 10000)
    value = await quote()
    ids = await asyncio.gather(purchase(value), purchase(value))
    assert ids[0] == ids[1] and await reserve_count() == 1
    async with sessions() as db:
        order = await db.get(Order, ids[0])
        assert order.purchase_terms_snapshot == value
        assert order.purchase_terms_hash == contracts.snapshot(value)[1]
        assert (await balance(db, 1)).reserved == 2900

    def no_new_validation(*args, **kwargs):
        raise AssertionError("an existing receipt must not refresh/revalidate a sold offer")

    monkeypatch.setattr(contracts, "validate", no_new_validation)
    monkeypatch.setattr(registry.types["echo"], "purchase_contract", {**CONTRACT, "months": 12})
    assert await purchase(value) == ids[0]
    changed = deepcopy(value)
    changed["contract"]["months"] = 12
    with pytest.raises(ServiceError):
        await purchase(changed)
    assert await reserve_count() == 1


@pytest.mark.parametrize(
    "change", ["missing", "months", "price", "terms", "expiry", "policy", "expired"]
)
async def test_missing_stale_or_changed_offer_never_reserves_credit(policy, monkeypatch, change):
    await fund(1, 10000)
    value = await quote()
    if change == "missing":
        value = None
    elif change == "months":
        value["contract"]["months"] = 12
    elif change == "price":
        value["price_halala"] = 1500
    elif change == "terms":
        value["contract"]["ar"] += " شروط مختلفة."
    elif change == "expiry":
        value["expires_at"] = (datetime.now(UTC) + timedelta(days=365)).isoformat()
    elif change == "policy":
        monkeypatch.setattr(
            registry.types["echo"], "purchase_contract", {**CONTRACT, "version": "changed"}
        )
    else:
        real = contracts.validate
        later = datetime.fromisoformat(value["valid_until"])
        monkeypatch.setattr(
            contracts, "validate", lambda *args, **kwargs: real(*args, **kwargs, now=later)
        )
    with pytest.raises(ServiceError):
        await purchase(value)
    async with sessions() as db:
        assert await db.scalar(select(func.count()).select_from(Order)) == 0
        assert (await balance(db, 1)).reserved == 0
        assert (await balance(db, 1)).available == 10000
    assert await reserve_count() == 0


async def test_sql_terms_cannot_be_replaced_and_legacy_order_cannot_be_retrofitted(
    policy, monkeypatch
):
    await fund(1, 10000)
    value = await quote()
    order_id = await purchase(value)
    for assignment in [
        "purchase_terms_hash='changed'",
        "purchase_terms_snapshot='{}'::json",
        "purchase_terms_hash=NULL,purchase_terms_snapshot=NULL",
    ]:
        with pytest.raises(DBAPIError):
            async with sessions.begin() as db:
                await db.execute(
                    text(f"UPDATE orders SET {assignment} WHERE id=:id"), {"id": order_id}
                )
    monkeypatch.setattr(registry.types["echo"], "purchase_contract", None)
    legacy = await purchase(None, key="legacy")
    with pytest.raises(DBAPIError):
        async with sessions.begin() as db:
            await db.execute(
                text(
                    "UPDATE orders SET purchase_terms_hash=:hash,purchase_terms_snapshot=CAST(:snapshot AS json) WHERE id=:id"
                ),
                {"hash": "a" * 64, "snapshot": "{}", "id": legacy},
            )


async def complete_profile(monkeypatch, order_id):
    identity = uuid4()

    async def extract(schema, source, prompt):
        return schema.model_validate(plan())

    ai = SimpleNamespace(extract=AsyncMock(side_effect=extract))
    result = await fulfillment.generate(
        ai, profile(), "هوية مناسبة للنشاط", publication_id=identity, origin=ORIGIN
    )
    run = AsyncMock(return_value=Result(text="Synthetic private draft", completion=result))
    monkeypatch.setattr(registry, "get", lambda *args: SimpleNamespace(run=run))
    await execute_job({"delivery": Delivery()}, str(await job_for(order_id)))
    return identity, ai


async def test_confirmed_purchase_evidence_survives_retention_and_is_real_private_entitlement(
    policy, monkeypatch, tmp_path
):
    await fund(1, 10000)
    value = await quote()
    order_id = await purchase(value)
    identity, ai = await complete_profile(monkeypatch, order_id)
    monkeypatch.setattr(config(), "storage_root", tmp_path)
    async with sessions.begin() as db:
        row = await db.get(Order, order_id)
        assert row.status == "completed" and row.files_deleted
        row.updated_at = datetime.now(UTC) - timedelta(days=3)
    await cleanup()
    async with sessions() as db:
        row = await db.get(Order, order_id)
        assert row.inputs == {} and row.result is None
        assert row.purchase_terms_snapshot == value
    assert await fulfillment.transfer_purchased(1, order_id, origin=ORIGIN)
    assert not await fulfillment.transfer_purchased(1, order_id, origin=ORIGIN)
    review = await prepared_page.review(1, identity, origin=ORIGIN)
    assert review["expires_at"] == datetime.fromisoformat(value["expires_at"])
    assert review["state"] == "draft" and review["consent_count"] == 0
    assert await prepared_page.public_bundle(identity, origin=ORIGIN) is None
    assert ai.extract.await_count == 1


async def test_arbitrary_completed_order_with_no_purchase_evidence_has_no_hosting_right(
    policy, monkeypatch
):
    monkeypatch.setattr(registry.types["echo"], "purchase_contract", None)
    await fund(1, 10000)
    order_id = await purchase(None)
    await complete_profile(monkeypatch, order_id)
    with pytest.raises(ServiceError, match="not_allowed"):
        await fulfillment.transfer_purchased(1, order_id, origin=ORIGIN)
    async with sessions() as db:
        assert await db.scalar(select(func.count()).select_from(Publication)) == 0


async def test_stars_and_hosting_agreements_are_separate_and_no_sar_is_captured(policy, stars):
    await register(1)
    value = await quote(stars=True)
    order_id = await purchase(
        value,
        expected_stars=20,
        terms_version=config().stars_terms_version,
        expected_terms_hash=terms_hash(),
    )
    await pay(order_id)
    async with sessions() as db:
        order = await db.get(Order, order_id)
        assert order.purchase_terms_snapshot == value
        assert order.purchase_terms_hash != order.terms_hash
        assert order.terms_snapshot["en"] == config().stars_terms_en
        assert await db.scalar(select(func.count()).select_from(Ledger)) == 0


@pytest.mark.parametrize("change", ["missing", "months", "stars"])
async def test_invalid_hosting_terms_create_no_stars_invoice_or_order(policy, stars, change):
    await register(1)
    value = await quote(stars=True)
    if change == "missing":
        value = None
    elif change == "months":
        value["contract"]["months"] = 12
    else:
        value["price_stars"] = 40
    with pytest.raises(ServiceError):
        await purchase(
            value,
            expected_stars=20,
            terms_version=config().stars_terms_version,
            expected_terms_hash=terms_hash(),
        )
    async with sessions() as db:
        for model in (Order, StarCheckout, Ledger):
            assert await db.scalar(select(func.count()).select_from(model)) == 0


async def fund_shared(shared):
    async with sessions.begin() as db:
        await apply(db, OWNER, "credit", 9000, "fixture-hosting-topup")


async def test_miniapp_shows_exact_offer_and_bot_http_race_record_one_agreement(
    policy, confirm_shared
):
    await fund_shared(confirm_shared)
    view = await mini_prepare(confirm_shared)
    data = await confirm_shared[3].get_data()
    value = data["purchase_quote"]
    assert CONTRACT["ar"] in view["review"]["ar"] and "29.00" in view["review"]["ar"]
    assert CONTRACT["en"] in view["review"]["en"]
    token = view["confirmation"]["token"]
    assert (await confirm(token, accepted=False)).status_code == 400
    response, _ = await asyncio.gather(confirm(token), confirm_shared[2]("confirm:" + data["key"]))
    assert response.status_code == 200
    assert response.json()["receipt"]["purchase_terms"] == value
    async with sessions() as db:
        orders = list((await db.scalars(select(Order))).all())
        assert len(orders) == 1 and orders[0].purchase_terms_snapshot == value
        assert (await balance(db, OWNER)).reserved == 2900
    assert await reserve_count() == 1


@pytest.mark.parametrize("channel", ["chat", "miniapp"])
async def test_policy_change_after_display_rejects_in_both_channels(
    policy, confirm_shared, monkeypatch, channel
):
    await fund_shared(confirm_shared)
    view = await mini_prepare(confirm_shared)
    data = await confirm_shared[3].get_data()
    monkeypatch.setattr(registry.types["echo"], "purchase_contract", {**CONTRACT, "months": 12})
    if channel == "miniapp":
        assert (await confirm(view["confirmation"]["token"])).status_code == 409
    else:
        await confirm_shared[2]("confirm:" + data["key"])
    assert await reserve_count() == 0
    async with sessions() as db:
        assert await db.scalar(select(func.count()).select_from(Order)) == 0
