"""Customer navigation and owner-scoped, read-only order history."""

from uuid import UUID
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.bot.ui import MenuButton, buttons, home_keyboard, leave_support, section_controls
from app.core.db import sessions
from app.core.display import message_parts, order_reference, result_preview
from app.core.i18n import tr
from app.core.models import Order, Service, StarCharge
from app.core.settings import config
from app.orders.engine import register
from app.orders.state import ALLOWED
from app.wallet.ledger import balance, sar

PAGE_SIZE = 6


def status_label(status, lang):
    return tr(f"status_{status}" if status in ALLOWED else "status_unknown", lang)


def create_router():
    router = Router()

    async def home(message, state, user_id, lang):
        await register(user_id)
        await leave_support(state)
        await message.answer(tr("welcome", lang), reply_markup=home_keyboard(lang))
        if (await state.get_data()).get("key"):
            await message.answer(
                tr("draft_saved", lang),
                reply_markup=buttons(await section_controls(state, lang)),
            )

    @router.message(CommandStart())
    @router.message(Command("menu"))
    async def home_command(message: Message, state: FSMContext, lang: str = "ar"):
        await home(message, state, message.from_user.id, lang)

    @router.callback_query(F.data == "menu:home")
    async def home_callback(callback: CallbackQuery, state: FSMContext, lang: str = "ar"):
        await callback.answer()
        await home(callback.message, state, callback.from_user.id, lang)

    async def show_services(message, state, lang):
        await leave_support(state)
        async with sessions() as db:
            rows = (
                await db.scalars(
                    select(Service).where(Service.enabled.is_(True)).order_by(Service.slug)
                )
            ).all()
        if config().stars_enabled:
            rows = [service for service in rows if service.price_stars is not None]
        items = [(s.name_ar if lang == "ar" else s.name_en, f"service:{s.slug}") for s in rows]
        items.extend(await section_controls(state, lang))
        await message.answer(
            tr("choose_service" if rows else "no_services", lang), reply_markup=buttons(items)
        )

    @router.message(Command("services"))
    @router.message(MenuButton("services"))
    async def services_command(message: Message, state: FSMContext, lang: str = "ar"):
        await show_services(message, state, lang)

    @router.callback_query(F.data == "menu:services")
    async def services_callback(callback: CallbackQuery, state: FSMContext, lang: str = "ar"):
        await callback.answer()
        await show_services(callback.message, state, lang)

    async def show_balance(message, state, user_id, lang):
        await leave_support(state)
        async with sessions() as db:
            funds = await balance(db, user_id)
        await message.answer(
            tr(
                "stars_balance_details" if config().stars_enabled else "balance_details",
                lang,
                available=sar(funds.available),
                reserved=sar(funds.reserved),
            ),
            reply_markup=buttons(await section_controls(state, lang)),
        )

    @router.message(Command("wallet"))
    @router.message(MenuButton("balance"))
    async def balance_command(message: Message, state: FSMContext, lang: str = "ar"):
        await show_balance(message, state, message.from_user.id, lang)

    @router.callback_query(F.data == "menu:balance")
    async def balance_callback(callback: CallbackQuery, state: FSMContext, lang: str = "ar"):
        await callback.answer()
        await show_balance(callback.message, state, callback.from_user.id, lang)

    async def show_language(message, state, lang):
        await leave_support(state)
        await message.answer(
            tr("choose_language", lang),
            reply_markup=buttons(
                [(tr("arabic", lang), "lang:ar"), (tr("english", lang), "lang:en")]
                + await section_controls(state, lang)
            ),
        )

    @router.message(Command("lang"))
    @router.message(MenuButton("language"))
    async def language_command(message: Message, state: FSMContext, lang: str = "ar"):
        await show_language(message, state, lang)

    @router.callback_query(F.data == "menu:language")
    async def language_callback(callback: CallbackQuery, state: FSMContext, lang: str = "ar"):
        await callback.answer()
        await show_language(callback.message, state, lang)

    async def show_help(message, state, lang):
        await leave_support(state)
        await message.answer(
            tr("help_text", lang), reply_markup=buttons(await section_controls(state, lang))
        )

    @router.message(Command("help"))
    @router.message(MenuButton("help"))
    async def help_command(message: Message, state: FSMContext, lang: str = "ar"):
        await show_help(message, state, lang)

    @router.callback_query(F.data == "menu:help")
    async def help_callback(callback: CallbackQuery, state: FSMContext, lang: str = "ar"):
        await callback.answer()
        await show_help(callback.message, state, lang)

    async def show_orders(message, state, user_id, lang, page=0):
        await leave_support(state)
        async with sessions() as db:
            rows = (
                await db.execute(
                    select(Order, Service)
                    .join(Service, Service.slug == Order.service_slug)
                    .where(Order.user_id == user_id)
                    .order_by(Order.created_at.desc(), Order.id.desc())
                    .offset(page * PAGE_SIZE)
                    .limit(PAGE_SIZE + 1)
                )
            ).all()
        items = [
            (
                f"{(service.name_ar if lang == 'ar' else service.name_en)[:45]} · "
                f"{status_label(order.status, lang)} · {order_reference(order.id)}",
                f"order:{order.id}",
            )
            for order, service in rows[:PAGE_SIZE]
        ]
        if page:
            items.append((tr("previous_page", lang), f"orders:{page - 1}"))
        if len(rows) > PAGE_SIZE:
            items.append((tr("next_page", lang), f"orders:{page + 1}"))
        items.append((tr("refresh", lang), f"orders:{page}"))
        items.extend(await section_controls(state, lang))
        await message.answer(
            tr("orders_title", lang, page=page + 1) if rows else tr("no_orders", lang),
            reply_markup=buttons(items),
        )

    @router.message(Command("orders"))
    @router.message(MenuButton("orders"))
    async def orders_command(message: Message, state: FSMContext, lang: str = "ar"):
        await show_orders(message, state, message.from_user.id, lang)

    @router.callback_query((F.data == "menu:orders") | F.data.startswith("orders:"))
    async def orders_callback(callback: CallbackQuery, state: FSMContext, lang: str = "ar"):
        raw = "0" if callback.data == "menu:orders" else callback.data.split(":", 1)[1]
        if not raw.isascii() or not raw.isdecimal() or len(raw) > 3:
            await callback.answer(tr("invalid_request", lang), show_alert=True)
            return
        await callback.answer()
        await show_orders(callback.message, state, callback.from_user.id, lang, int(raw))

    @router.callback_query(F.data.startswith("order:"))
    async def order_details(callback: CallbackQuery, state: FSMContext, lang: str = "ar"):
        try:
            order_id = UUID(callback.data.split(":", 1)[1])
        except ValueError:
            await callback.answer(tr("invalid_request", lang), show_alert=True)
            return
        async with sessions() as db:
            row = (
                await db.execute(
                    select(Order, Service)
                    .join(Service, Service.slug == Order.service_slug)
                    .where(Order.id == order_id, Order.user_id == callback.from_user.id)
                )
            ).first()
            charge = (
                await db.scalar(
                    select(StarCharge).where(
                        StarCharge.order_id == order_id,
                        StarCharge.user_id == callback.from_user.id,
                        StarCharge.accepted.is_(True),
                    )
                )
                if row and row[0].payment_mode == "stars"
                else None
            )
        if row is None:
            await callback.answer(tr("order_unavailable", lang), show_alert=True)
            return
        await callback.answer()
        await leave_support(state)
        order, service = row
        text = tr(
            "stars_order_details" if order.payment_mode == "stars" else "order_details",
            lang,
            order_id=order.id,
            name=service.name_ar if lang == "ar" else service.name_en,
            status=status_label(order.status, lang),
            amount=order.price_stars if order.payment_mode == "stars" else sar(order.price_halala),
            created=order.created_at.astimezone(ZoneInfo("Asia/Riyadh")).strftime("%Y-%m-%d %H:%M"),
        )
        items = []
        if charge:
            text += "\n" + tr("stars_charge_" + charge.state, lang)
        if order.status == "awaiting_payment":
            items.extend(
                [
                    (tr("stars_pay", lang), f"pay:{order.id}"),
                    (tr("cancel_order", lang), f"paycancel:{order.id}"),
                ]
            )
        if order.status == "waiting_confirmation":
            review_suffix = ":visual" if (order.result or {}).get("prepared_delivery") else ""
            if (order.result or {}).get("preview_artifacts"):
                from app.providers.delivery import TelegramDelivery
                from app.providers.runtime import storage
                from app.services.base import Result

                await TelegramDelivery(callback.bot, storage()).send_preview_images(
                    order.user_id, Result.model_validate(order.result)
                )
            preview = result_preview(order.result or {}, lang)
            text += "\n\n" + tr(
                "confirmation_waiting", lang, order_id=order_reference(order.id), preview=preview
            )
            items.extend(
                [
                    (
                        tr(
                            "approve_delivery"
                            if (order.result or {}).get("prepared_delivery")
                            else "approve_structure",
                            lang,
                        ),
                        f"approve:{order.id}{review_suffix}",
                    ),
                    (tr("cancel_order", lang), f"reject:{order.id}{review_suffix}"),
                ]
            )
        items.extend([(tr("refresh", lang), f"order:{order.id}"), (tr("orders", lang), "orders:0")])
        items.extend(await section_controls(state, lang))
        parts = list(message_parts(text))
        for index, part in enumerate(parts):
            await callback.message.answer(
                part, reply_markup=buttons(items) if index == len(parts) - 1 else None
            )

    return router
