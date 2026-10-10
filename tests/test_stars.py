"""Real PostgreSQL monetary lifecycle; Telegram calls are injected test doubles."""

import asyncio
from datetime import UTC, datetime, timedelta
from io import BytesIO
from types import SimpleNamespace as NS
from uuid import uuid4

import httpx
import pytest
from aiogram import Bot
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import SendInvoice
from aiogram.types import CallbackQuery, Chat, Message, SuccessfulPayment, Update
from aiogram.types import User as TelegramUser
from openpyxl import load_workbook
from pydantic import SecretStr, ValidationError
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError

from app.api.main import app
from app.bot.main import create_dispatcher
from app.bot.payments import handle_receipt, invoice
from app.core.db import sessions
from app.core.i18n import CATALOGS
from app.core.models import Job, Ledger, Order, Service, StarCharge, StarCheckout, StarEvent, User
from app.core.settings import Config, config
from app.ops.admin import refund, set_service
from app.orders.engine import fail_locked, register, submit
from app.orders.locking import lock_order
from app.payments.recovery import confirm_refund, locked_charge, reconcile, refunds
from app.payments.stars import (
    cancel_invoice,
    expire_invoices,
    payload,
    pre_checkout,
    receive,
    terms_hash,
)
from app.providers.storage import LocalStorage
from app.services.base import ServiceError
from app.wallet.ledger import balance
from app.workers.runner import execute_job
from tests.csv_review_fixtures import inputs as csv_inputs
from tests.test_bot_flow import Session
from tests.test_foundation import Delivery, fund, job_for
from tests.test_real_services import Delivery as FileDelivery


@pytest.fixture
def stars(monkeypatch):
    for key, value in {
        "stars_enabled": True,
        "telegram_mode": "webhook",
        "telegram_webhook_secret": SecretStr("fixture-secret"),
        "stars_terms_version": "fixture-v1",
        "stars_terms_ar": "شروط اختبار فقط وليست شروط بيع حقيقية.",
        "stars_terms_en": "Fixture terms only; not actual commercial terms.",
    }.items():
        monkeypatch.setattr(config(), key, value)


async def prepare(slug="echo", inputs=None, key="order", user_id=1):
    await register(user_id)
    await set_service(slug, stars=20, enabled=True)
    async with sessions() as db:
        service = await db.get(Service, slug)
    return await submit(
        user_id,
        slug,
        inputs or {"text": "اختبار 00123"},
        service.price_halala,
        key,
        service.version,
        expected_stars=20,
        terms_version=config().stars_terms_version,
        expected_terms_hash=terms_hash(),
    )


async def pay(oid, charge="charge", user_id=1):
    await pre_checkout(user_id, payload(oid), "XTR", 20, str(oid))
    return await receive(user_id, payload(oid), "XTR", 20, charge)


class Provider:
    def __init__(self, outcome=True, transactions=()):
        self.outcome, self.rows, self.calls, self.offsets = outcome, transactions, [], []

    async def refund(self, user_id, charge_id):
        self.calls.append((user_id, charge_id))
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return self.outcome

    async def transactions(self, offset, limit):
        self.offsets.append((offset, limit))
        return self.rows


async def test_unpaid_idempotency_no_job_no_credit_and_terms_snapshot(stars):
    oid = await prepare()
    assert await prepare() == oid
    async with sessions() as db:
        order = await db.get(Order, oid)
        assert order.status == "awaiting_payment" and order.price_stars == 20
        assert order.terms_snapshot["ar"] == config().stars_terms_ar
        assert order.terms_hash == terms_hash()
        assert await db.scalar(select(func.count(Job.id))) == 0
        assert await db.scalar(select(func.count(Ledger.id))) == 0
        assert await db.get(StarCheckout, oid)


async def test_worker_fails_closed_for_accidental_unpaid_job(stars):
    oid = await prepare()
    async with sessions.begin() as db:
        job = Job(order_id=oid, status="pending")
        db.add(job)
        await db.flush()
        jid = job.id
    delivery = Delivery()
    await execute_job({"delivery": delivery}, str(jid))
    assert not delivery.results
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "cancelled"
        assert await db.scalar(select(func.count(Ledger.id))) == 0


@pytest.mark.parametrize(
    "field,value",
    [
        ("expected_stars", 21),
        ("expected_stars", True),
        ("expected_stars", 0),
        ("terms_version", "changed"),
        ("expected_terms_hash", "bad"),
    ],
)
async def test_stale_or_invalid_purchase_contract_rejected(stars, field, value):
    await register(1)
    await set_service("echo", stars=20)
    args = dict(
        expected_stars=20,
        terms_version=config().stars_terms_version,
        expected_terms_hash=terms_hash(),
    )
    args[field] = value
    with pytest.raises(ServiceError):
        await submit(1, "echo", {"text": "x"}, 100, "stale", **args)
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0


async def test_independent_prices_survive_registry_sync(stars):
    from app.services.registry import registry

    await set_service("echo", stars=20, price=999)
    async with sessions.begin() as db:
        await registry.sync(db)
        service = await db.get(Service, "echo")
        assert service.price_stars == 20 and service.price_halala == 999
    await register(1)
    oid = await submit(
        1,
        "echo",
        {"text": "x"},
        100,
        "sar-independent",
        expected_stars=20,
        terms_version=config().stars_terms_version,
        expected_terms_hash=terms_hash(),
    )
    assert oid


@pytest.mark.parametrize(
    "variation",
    [
        "owner",
        "currency",
        "amount",
        "expired",
        "disabled",
        "version",
        "price",
        "terms",
        "banned",
        "second_query",
    ],
)
async def test_precheckout_rejects_invalid_binding_without_job(stars, monkeypatch, variation):
    oid = await prepare()
    user_id, currency, amount, query = 1, "XTR", 20, "query"
    if variation == "owner":
        user_id = 2
    if variation == "currency":
        currency = "SAR"
    if variation == "amount":
        amount = 21
    if variation == "terms":
        monkeypatch.setattr(config(), "stars_terms_en", "Changed fixture terms.")
    async with sessions.begin() as db:
        if variation == "expired":
            (await db.get(StarCheckout, oid)).expires_at = datetime.now(UTC) - timedelta(seconds=1)
        if variation == "disabled":
            (await db.get(Service, "echo")).enabled = False
        if variation == "version":
            (await db.get(Service, "echo")).version = "other"
        if variation == "price":
            (await db.get(Service, "echo")).price_stars = 21
        if variation == "banned":
            (await db.get(User, 1)).banned = True
        if variation == "second_query":
            (await db.get(StarCheckout, oid)).query_id = "first"
    with pytest.raises(ServiceError):
        await pre_checkout(user_id, payload(oid), currency, amount, query)
    assert await job_for(oid) is None


async def test_precheckout_not_payment_receipt_concurrency_single_job(stars):
    oid = await prepare()
    assert await pre_checkout(1, payload(oid), "XTR", 20, "query") == oid
    assert await pre_checkout(1, payload(oid), "XTR", 20, "query") == oid
    assert await job_for(oid) is None
    results = await asyncio.gather(
        *[receive(1, payload(oid), "XTR", 20, "charge") for _ in range(6)]
    )
    assert all(result == (oid, "paid") for result in results)
    async with sessions() as db:
        assert await db.scalar(select(func.count(Job.id))) == 1
        assert await db.scalar(select(func.count(StarCharge.charge_id))) == 1
        assert await db.scalar(select(func.count(StarEvent.id))) == 1
    with pytest.raises(ServiceError):
        await receive(1, payload(oid), "XTR", 21, "charge")


async def test_success_preserves_historic_credit_and_admin_refund_not_fake(stars):
    await fund()
    oid = await prepare()
    await pay(oid)
    delivery = Delivery()
    await execute_job({"delivery": delivery}, str(await job_for(oid)))
    await execute_job({"delivery": delivery}, str(await job_for(oid)))
    assert len(delivery.results) == 1
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        assert (await balance(db, 1)).available == 1000
        assert (await balance(db, 1)).reserved == 0
        assert await db.scalar(select(func.count(Ledger.id))) == 1
    await refund(oid)
    await refund(oid)
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        assert (await db.get(StarCharge, "charge")).state == "refund_pending"
    provider = Provider()
    await refunds({"stars": provider})
    await refunds({"stars": provider})
    assert len(provider.calls) == 1
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "refunded"
        assert (await balance(db, 1)).available == 1000


@pytest.mark.parametrize(
    "variation", ["late", "banned", "wrong_owner", "wrong_amount", "unknown", "no_precheckout"]
)
async def test_unexpected_money_durable_refundable_never_authorizes_job(stars, variation):
    oid = await prepare()
    if variation != "no_precheckout":
        await pre_checkout(1, payload(oid), "XTR", 20, "query")
    uid, amount, value = 1, 20, payload(oid)
    if variation == "late":
        await cancel_invoice(oid, 1)
    if variation == "banned":
        async with sessions.begin() as db:
            (await db.get(User, 1)).banned = True
    if variation == "wrong_owner":
        uid = 2
    if variation == "wrong_amount":
        amount = 21
    if variation == "unknown":
        value = payload(uuid4())
    _, state = await receive(uid, value, "XTR", amount, "unexpected")
    assert state == "refund_pending" and await job_for(oid) is None
    async with sessions() as db:
        charge = await db.get(StarCharge, "unexpected")
        assert not charge.accepted and charge.user_id == uid and charge.amount == amount


async def test_gate_disabled_after_precheckout_still_records_known_money(stars, monkeypatch):
    oid = await prepare()
    await pre_checkout(1, payload(oid), "XTR", 20, "query")
    monkeypatch.setattr(config(), "stars_enabled", False)
    assert await receive(1, payload(oid), "XTR", 20, "charge") == (oid, "paid")
    assert await job_for(oid)


async def test_duplicate_distinct_charge_refund_does_not_cancel_paid_order(stars):
    oid = await prepare()
    await pay(oid)
    assert await receive(1, payload(oid), "XTR", 20, "extra") == (oid, "refund_pending")
    await refunds({"stars": Provider()})
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "queued"
        assert (await db.get(StarCharge, "charge")).state == "paid"
        assert (await db.get(StarCharge, "extra")).state == "refunded"


@pytest.mark.parametrize("action", ["failure", "disable", "expiry"])
async def test_failure_disable_and_invoice_expiry(stars, action):
    oid = await prepare()
    if action == "expiry":
        async with sessions.begin() as db:
            (await db.get(StarCheckout, oid)).expires_at = datetime.now(UTC) - timedelta(seconds=1)
        await expire_invoices()
    else:
        await pay(oid)
        if action == "disable":
            await set_service("echo", enabled=False)
        else:
            async with sessions.begin() as db:
                await fail_locked(db, await lock_order(db, oid))
    async with sessions() as db:
        assert (await db.get(Order, oid)).status in {"failed", "cancelled"}
        assert await db.scalar(select(func.count(Ledger.id))) == 0
        if action != "expiry":
            assert (await db.get(StarCharge, "charge")).state == "refund_pending"


@pytest.mark.parametrize("outcome", [False, TimeoutError("synthetic"), asyncio.CancelledError()])
async def test_refund_uncertainty_never_blindly_retried(stars, outcome):
    oid = await prepare()
    await pay(oid)
    async with sessions.begin() as db:
        await fail_locked(db, await lock_order(db, oid))
    provider = Provider(outcome)
    if isinstance(outcome, asyncio.CancelledError):
        with pytest.raises(asyncio.CancelledError):
            await refunds({"stars": provider})
        async with sessions.begin() as db:
            (await db.get(StarCharge, "charge")).lease_until = datetime.now(UTC) - timedelta(
                seconds=1
            )
    else:
        await refunds({"stars": provider})
    await refunds({"stars": provider})
    await refunds({"stars": provider})
    assert len(provider.calls) == 1
    async with sessions() as db:
        assert (await db.get(StarCharge, "charge")).state == "refund_uncertain"
    proof = NS(
        id="charge",
        amount=-20,
        nanostar_amount=0,
        source=None,
        receiver=NS(type="user", user=NS(id=1)),
    )
    assert await reconcile({"stars": Provider(transactions=[proof])}) == (1, True)
    async with sessions() as db:
        assert (await db.get(StarCharge, "charge")).state == "refunded"


async def test_concurrent_refund_claim_calls_provider_once(stars):
    oid = await prepare()
    await pay(oid)
    async with sessions.begin() as db:
        await fail_locked(db, await lock_order(db, oid))
    provider = Provider()
    await asyncio.gather(*[refunds({"stars": provider}) for _ in range(5)])
    assert len(provider.calls) == 1


async def test_each_refund_claim_has_a_fresh_lease(stars, monkeypatch):
    import app.payments.recovery as recovery

    origin = datetime.now(UTC)

    class Clock:
        elapsed = 0

        @classmethod
        def now(cls, zone):
            return origin + timedelta(seconds=cls.elapsed)

    monkeypatch.setattr(recovery, "datetime", Clock)
    for name in ("first", "second"):
        await receive(1, payload(uuid4()), "XTR", 20, name)

    class SlowBatch(Provider):
        async def refund(self, user_id, charge_id):
            async with sessions() as db:
                charge = await db.get(StarCharge, charge_id)
                assert charge.lease_until > Clock.now(UTC)
            Clock.elapsed += 600
            return await super().refund(user_id, charge_id)

    provider = SlowBatch()
    await refunds({"stars": provider})
    assert len(provider.calls) == 2
    async with sessions() as db:
        assert list((await db.scalars(select(StarCharge.state))).all()) == ["refunded", "refunded"]


async def test_external_refund_stops_queued_job(stars):
    oid = await prepare()
    await pay(oid)
    async with sessions.begin() as db:
        await confirm_refund(db, await locked_charge(db, "charge"))
    delivery = Delivery()
    await execute_job({"delivery": delivery}, str(await job_for(oid)))
    assert not delivery.results
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "cancelled"


@pytest.mark.parametrize(
    "mutation",
    [
        "UPDATE star_charges SET amount=21",
        "DELETE FROM star_charges",
        "UPDATE star_events SET kind='refunded'",
        "DELETE FROM star_events",
        "UPDATE orders SET price_stars=21",
    ],
)
async def test_payment_receipts_and_events_immutable(stars, mutation):
    oid = await prepare()
    await pay(oid)
    with pytest.raises(DBAPIError):
        async with sessions.begin() as db:
            await db.execute(text(mutation))


async def test_bounded_reconciliation_never_absence_proof_and_ignores_unrelated_history(stars):
    unrelated = NS(
        id="historic",
        amount=20,
        nanostar_amount=0,
        source=NS(
            type="user",
            transaction_type="invoice_payment",
            invoice_payload="other-product",
            user=NS(id=1),
        ),
        receiver=None,
    )
    provider = Provider(transactions=[unrelated] * 100)
    assert await reconcile({"stars": provider}, offset=200, pages=2) == (200, False)
    assert provider.offsets == [(200, 100), (300, 100)]
    async with sessions() as db:
        assert await db.scalar(select(func.count(StarCharge.charge_id))) == 0


@pytest.mark.parametrize("language", ["ar", "en"])
async def test_native_csv_paid_flow_no_ledger_or_ai(stars, tmp_path, monkeypatch, language):
    monkeypatch.setattr(config(), "storage_root", tmp_path)
    oid = await prepare("csv_review", csv_inputs(language))
    await pay(oid)
    delivery = FileDelivery(LocalStorage(tmp_path))
    await execute_job({"delivery": delivery}, str(await job_for(oid)))
    book = load_workbook(BytesIO(delivery.files[0][1]))
    assert book["Data"]["A4"].value == "00123"
    async with sessions() as db:
        assert (await db.get(Order, oid)).status == "completed"
        assert await db.scalar(select(func.count(Ledger.id))) == 0
    assert not list(tmp_path.glob("[0-9]*/*/*"))


async def test_invoice_recovery_owner_expiry_and_private_xtr_contract(stars):
    oid = await prepare()

    class BotDouble:
        async def send_invoice(self, **kwargs):
            self.kwargs = kwargs

    bot = BotDouble()
    await invoice(bot, oid, 1, "ar")
    assert bot.kwargs["chat_id"] == 1 and bot.kwargs["currency"] == "XTR"
    assert bot.kwargs["provider_token"] == "" and bot.kwargs["start_parameter"]
    assert bot.kwargs["prices"][0].amount == 20
    assert len(bot.kwargs["payload"].encode()) <= 128
    with pytest.raises(ServiceError):
        await invoice(bot, oid, 2, "en")
    await cancel_invoice(oid, 1)
    with pytest.raises(ServiceError):
        await invoice(bot, oid, 1, "en")


async def test_webhook_money_bypasses_dispatcher_and_notification_failure(stars, monkeypatch):
    oid = await prepare()
    await pre_checkout(1, payload(oid), "XTR", 20, "query")

    class BrokenDispatcher:
        async def feed_update(self, *args):
            raise AssertionError("FSM/Redis must not gate receipts")

    class BrokenBot:
        async def send_message(self, *args):
            raise OSError("synthetic notification failure")

    bot = Bot("123456:TEST_TOKEN_ONLY")
    monkeypatch.setattr(app.state, "bot", bot, raising=False)
    monkeypatch.setattr(app.state, "dispatcher", BrokenDispatcher(), raising=False)
    event = Message(
        message_id=1,
        date=datetime.now(UTC),
        chat=Chat(id=1, type="private"),
        from_user=TelegramUser(id=1, is_bot=False, first_name="Fixture"),
        successful_payment=SuccessfulPayment(
            currency="XTR",
            total_amount=20,
            invoice_payload=payload(oid),
            telegram_payment_charge_id="charge",
            provider_payment_charge_id="",
        ),
    )
    await handle_receipt(event, BrokenBot())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        update = {"update_id": 1, "message": event.model_dump(mode="json", exclude_none=True)}
        assert (await client.post("/webhooks/telegram", json=update)).status_code == 403

        # Avoid any actual Telegram notification in this authenticated webhook test.
        async def no_notify(*args):
            raise OSError("synthetic")

        monkeypatch.setattr(bot, "send_message", no_notify)
        assert (
            await client.post(
                "/webhooks/telegram",
                json=update,
                headers={"X-Telegram-Bot-Api-Secret-Token": "fixture-secret"},
            )
        ).status_code == 200
    assert await job_for(oid)
    await bot.session.close()


@pytest.mark.parametrize(
    "bad",
    [
        {"telegram_mode": "polling"},
        {"stars_terms_version": " "},
        {"stars_terms_version": " " + "v" * 80},
        {"stars_terms_ar": ""},
        {"stars_terms_en": "😀" * 2000},
        {"telegram_webhook_secret": ""},
    ],
)
def test_activation_requires_webhook_secret_and_bounded_real_terms(bad):
    args = dict(
        stars_enabled=True,
        telegram_mode="webhook",
        telegram_webhook_secret="fixture",
        stars_terms_version="v1",
        stars_terms_ar="شروط اختبار وليست شراء حقيقي.",
        stars_terms_en="Fixture purchase terms only.",
    )
    args.update(bad)
    with pytest.raises(ValidationError):
        Config(_env_file=None, **args)


def test_stars_catalogs_have_matching_keys():
    keys = {key for key in CATALOGS["ar"] if key.startswith(("stars_", "payment_"))}
    assert keys and keys <= CATALOGS["en"].keys()


async def test_receipt_transaction_retries_are_not_multiplied(stars, monkeypatch):
    import app.payments.stars as adapter

    class Aborted(Exception):
        sqlstate = "40001"

    failure = DBAPIError("fixture transaction", {}, Aborted())
    attempts = []

    class Transaction:
        async def __aenter__(self):
            attempts.append(1)
            raise failure

        async def __aexit__(self, *args):
            return False

    monkeypatch.setattr(adapter.sessions, "begin", Transaction)
    with pytest.raises(DBAPIError):
        await receive(1, payload(uuid4()), "XTR", 20, "bounded")
    assert len(attempts) == 3


@pytest.mark.parametrize("language", ["ar", "en"])
async def test_real_dispatcher_terms_invoice_recovery_and_admin_denial(stars, language):
    await register(1)
    await set_service("echo", stars=20)
    async with sessions.begin() as db:
        (await db.get(User, 1)).language = language

    class InvoiceSession(Session):
        def __init__(self):
            super().__init__()
            self.invoices = []

        async def make_request(self, bot, method, timeout=None):
            if isinstance(method, SendInvoice):
                self.invoices.append(method)
                return self.messages[-1]
            return await super().make_request(bot, method, timeout)

    transport = InvoiceSession()
    bot = Bot("123456:TEST_TOKEN_ONLY", session=transport)
    dp = create_dispatcher(MemoryStorage(), guard=False)
    user = TelegramUser(id=1, is_bot=False, first_name="Fixture")
    sequence = 0

    async def message(value):
        nonlocal sequence
        sequence += 1
        await dp.feed_update(
            bot,
            Update(
                update_id=sequence,
                message=Message(
                    message_id=sequence,
                    date=datetime.now(UTC),
                    chat=Chat(id=1, type="private"),
                    from_user=user,
                    text=value,
                ),
            ),
        )

    async def callback(value):
        nonlocal sequence
        sequence += 1
        await dp.feed_update(
            bot,
            Update(
                update_id=sequence,
                callback_query=CallbackQuery(
                    id=str(sequence),
                    from_user=user,
                    chat_instance="fixture",
                    message=transport.messages[-1],
                    data=value,
                ),
            ),
        )

    await message("/services")
    async with sessions() as db:
        service = await db.get(Service, "echo")
        expected_name = service.name_ar if language == "ar" else service.name_en
    assert transport.messages[-1].reply_markup.inline_keyboard[0][0].text == expected_name
    await callback("service:echo")
    await message("00123")
    assert getattr(config(), f"stars_terms_{language}") in transport.messages[-1].text
    confirm = transport.messages[-1].reply_markup.inline_keyboard[0][0].callback_data
    await callback(confirm)
    async with sessions() as db:
        order = await db.scalar(select(Order))
        assert order.status == "awaiting_payment"
    assert len(transport.invoices) == 1 and await job_for(order.id) is None
    await message("/orders")
    await callback(f"order:{order.id}")
    await callback(f"pay:{order.id}")
    assert len(transport.invoices) == 2
    await message("/setstars echo 999")
    async with sessions() as db:
        assert (await db.get(Service, "echo")).price_stars == 20
    await message("/paysupport")
    assert transport.messages[-1].text == CATALOGS[language]["support_prompt"]
    await dp.storage.close()
    await bot.session.close()


async def test_receipt_db_failure_returns_retryable_http500(stars, monkeypatch):
    import app.bot.payments as adapter

    async def broken(*args):
        raise OSError("synthetic DB unavailability")

    monkeypatch.setattr(adapter, "receive", broken)
    bot = Bot("123456:TEST_TOKEN_ONLY")
    monkeypatch.setattr(app.state, "bot", bot, raising=False)
    monkeypatch.setattr(app.state, "dispatcher", NS(), raising=False)
    event = Message(
        message_id=1,
        date=datetime.now(UTC),
        chat=Chat(id=1, type="private"),
        from_user=TelegramUser(id=1, is_bot=False, first_name="Fixture"),
        successful_payment=SuccessfulPayment(
            currency="XTR",
            total_amount=20,
            invoice_payload=payload(uuid4()),
            telegram_payment_charge_id="charge",
            provider_payment_charge_id="",
        ),
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test"
    ) as client:
        assert (
            await client.post(
                "/webhooks/telegram",
                json={"update_id": 1, "message": event.model_dump(mode="json", exclude_none=True)},
                headers={"X-Telegram-Bot-Api-Secret-Token": "fixture-secret"},
            )
        ).status_code == 500
    await bot.session.close()


@pytest.mark.parametrize("wrong", ["user", "amount", "fractional"])
async def test_reconciliation_requires_exact_refund_proof(stars, wrong):
    oid = await prepare()
    await pay(oid)
    proof = NS(
        id="charge",
        amount=-21 if wrong == "amount" else -20,
        nanostar_amount=1 if wrong == "fractional" else 0,
        source=None,
        receiver=NS(type="user", user=NS(id=2 if wrong == "user" else 1)),
    )
    await reconcile({"stars": Provider(transactions=[proof])})
    async with sessions() as db:
        assert (await db.get(StarCharge, "charge")).state == "paid"
        assert (await db.get(Order, oid)).status == "queued"
