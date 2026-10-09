"""Telegram payment adapter; callable without conversation/Redis middleware in webhook."""

import asyncio
from contextlib import suppress
from datetime import UTC, datetime
from uuid import UUID

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import LabeledPrice

from app.core.db import sessions
from app.core.i18n import tr
from app.core.models import Order, StarCheckout
from app.core.settings import config
from app.core.users import get_language
from app.payments.recovery import confirm_refund, locked_charge
from app.payments.stars import cancel_invoice, payload, pre_checkout, receive
from app.services.base import ServiceError


async def invoice(bot, order_id, user_id, lang):
    async with sessions() as db:
        order = await db.get(Order, order_id)
        checkout = await db.get(StarCheckout, order_id)
    if (
        not config().stars_enabled
        or not order
        or order.user_id != user_id
        or order.status != "awaiting_payment"
        or not checkout
        or checkout.expires_at <= datetime.now(UTC)
    ):
        raise ServiceError("payment_invalid")
    await bot.send_invoice(
        chat_id=user_id,
        title=tr("stars_invoice_title", lang),
        description=tr("stars_invoice_description", lang),
        payload=payload(order.id),
        currency="XTR",
        prices=[LabeledPrice(label=tr("stars_service", lang), amount=order.price_stars)],
        provider_token="",
        start_parameter=f"order_{order.id.hex}",
    )


async def handle_precheckout(query, bot):
    lang = "ar"
    ok = False
    try:
        async with asyncio.timeout(6):
            with suppress(TimeoutError):
                async with asyncio.timeout(1):
                    lang = await get_language(query.from_user.id)
            await pre_checkout(
                query.from_user.id,
                query.invoice_payload,
                query.currency,
                query.total_amount,
                query.id,
            )
            ok = True
    except Exception:
        pass
    await bot.answer_pre_checkout_query(
        pre_checkout_query_id=query.id,
        ok=ok,
        error_message=None if ok else tr("payment_invalid", lang),
        request_timeout=2,
    )


async def handle_receipt(message, bot):
    payment = message.successful_payment
    order_id, state = await receive(
        message.from_user.id,
        payment.invoice_payload,
        payment.currency,
        payment.total_amount,
        payment.telegram_payment_charge_id,
    )
    # PostgreSQL has the receipt/job before this best-effort notification. A network
    # failure must not undo known money or depend on FSM/Redis availability.
    with suppress(Exception):
        lang = await get_language(message.from_user.id)
        await bot.send_message(
            message.from_user.id,
            tr(
                "stars_paid" if state == "paid" else "stars_receipt_recorded",
                lang,
                order_id=order_id,
            ),
        )


async def handle_refunded(message):
    payment = message.refunded_payment
    if payment.currency != "XTR":
        return
    async with sessions.begin() as db:
        charge = await locked_charge(db, payment.telegram_payment_charge_id)
        if (
            charge
            and charge.user_id == message.from_user.id
            and charge.amount == payment.total_amount
            and charge.payload == payment.invoice_payload
        ):
            await confirm_refund(db, charge)


def create_router():
    router = Router()

    @router.pre_checkout_query()
    async def checkout(query):
        await handle_precheckout(query, query.bot)

    @router.message(F.successful_payment)
    async def paid(message):
        await handle_receipt(message, message.bot)

    @router.message(F.refunded_payment)
    async def refunded(message):
        await handle_refunded(message)

    @router.message(Command("terms"))
    async def terms(message, lang="ar"):
        text = getattr(config(), f"stars_terms_{lang}") or tr("stars_not_live", lang)
        await message.answer(text)

    @router.callback_query(F.data.startswith("pay:") | F.data.startswith("paycancel:"))
    async def payment_action(callback, lang="ar"):
        await callback.answer()
        try:
            action, value = callback.data.split(":", 1)
            order_id = UUID(value)
            if action == "pay":
                await invoice(callback.bot, order_id, callback.from_user.id, lang)
            else:
                await cancel_invoice(order_id, callback.from_user.id)
                await callback.message.answer(tr("draft_cancelled", lang))
        except (ValueError, ServiceError):
            await callback.message.answer(tr("payment_invalid", lang))

    return router
