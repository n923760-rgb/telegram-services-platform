"""Private admin controls; price replies do not replace customer intake/support state."""

import re
import time
from uuid import uuid4
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import Command, Filter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ForceReply, Message
from sqlalchemy import func, select

from app.bot.navigation import status_label
from app.bot.ui import MenuButton, buttons
from app.core.db import sessions
from app.core.display import message_parts
from app.core.i18n import tr
from app.core.models import Order, Service, StarPriceChange
from app.core.settings import config
from app.ops.prices import change_stars_price
from app.ops.reports import stars_report
from app.services.base import ServiceError
from app.services.registry import registry

PAGE_SIZE = 6
TTL = 300


class PriceReply(Filter):
    async def __call__(self, message: Message, state: FSMContext):
        pending = (await state.get_data()).get("admin_price") or {}
        return bool(
            message.reply_to_message
            and message.reply_to_message.message_id == pending.get("prompt_id")
        )


def allowed(user):
    return user is not None and user.id in config().admin_ids


def price_label(price, lang):
    return (
        tr("admin_price_unset", lang)
        if price is None
        else tr("admin_stars_value", lang, price=price)
    )


def controls(lang):
    return buttons(
        [
            (tr("admin_services", lang), "admin:services:0"),
            (tr("admin_orders", lang), "admin:orders"),
            (tr("admin_stars", lang), "admin:stars"),
            (tr("admin_history", lang), "admin:history"),
            (tr("home", lang), "menu:home"),
        ]
    )


async def show_services(message, lang, page):
    async with sessions() as db:
        rows = list((await db.scalars(select(Service).order_by(Service.slug))).all())
    rows = [row for row in rows if registry.customer_visible(row.slug)]
    page = min(max(page, 0), max((len(rows) - 1) // PAGE_SIZE, 0))
    items, details = [], []
    for row in rows[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]:
        name = row.name_en if lang == "en" else row.name_ar
        label = tr(
            "admin_service_button",
            lang,
            name=name,
            price=price_label(row.price_stars, lang),
            status=tr("admin_enabled" if row.enabled else "admin_disabled", lang),
        )
        details.append(label)
        items.append((name, f"admin:price:{row.slug}"))
    if page:
        items.append((tr("previous_page", lang), f"admin:services:{page - 1}"))
    if (page + 1) * PAGE_SIZE < len(rows):
        items.append((tr("next_page", lang), f"admin:services:{page + 1}"))
    items.append((tr("admin_back", lang), "admin:home"))
    await message.answer(
        tr("admin_services_text", lang) + "\n\n" + "\n\n".join(details), reply_markup=buttons(items)
    )


def create_router():
    router = Router()

    @router.message(Command("admin"))
    @router.message(MenuButton("admin_panel"))
    async def home(message: Message, state: FSMContext, lang: str = "ar"):
        if not allowed(message.from_user):
            await message.answer(tr("not_allowed", lang))
            return
        await state.update_data(admin_price=None)
        await message.answer(tr("admin_panel_intro", lang), reply_markup=controls(lang))

    @router.callback_query(F.data.startswith("admin:"))
    async def action(callback: CallbackQuery, state: FSMContext, lang: str = "ar"):
        if not allowed(callback.from_user):
            await callback.answer(tr("not_allowed", lang), show_alert=True)
            return
        parts = (callback.data or "").split(":")
        try:
            if len(parts) == 3 and parts[1] == "confirm":
                pending = (await state.get_data()).get("admin_price") or {}
                if (
                    pending.get("token") != parts[2]
                    or "new" not in pending
                    or pending.get("expires", 0) < time.time()
                ):
                    raise ServiceError("stale_button")
                await change_stars_price(
                    pending["slug"],
                    pending["new"],
                    expected_price=pending["old"],
                    actor_id=callback.from_user.id,
                    change_id=pending["token"],
                )
                await state.update_data(admin_price=None)
                await callback.answer(tr("admin_done", lang))
                await callback.message.answer(
                    tr("admin_price_saved", lang), reply_markup=controls(lang)
                )
                return
            await state.update_data(admin_price=None)
            if len(parts) == 2 and parts[1] in {"home", "cancel"}:
                text, keyboard = tr("admin_panel_intro", lang), controls(lang)
            elif (
                len(parts) == 3 and parts[1] == "services" and re.fullmatch(r"[0-9]{1,5}", parts[2])
            ):
                await callback.answer()
                await show_services(callback.message, lang, int(parts[2]))
                return
            elif len(parts) == 3 and parts[1] == "price":
                async with sessions() as db:
                    row = await db.get(Service, parts[2])
                if not row or not registry.customer_visible(row.slug):
                    raise ServiceError("unavailable")
                name = row.name_en if lang == "en" else row.name_ar
                prompt = await callback.message.answer(
                    tr(
                        "admin_price_prompt",
                        lang,
                        name=name,
                        price=price_label(row.price_stars, lang),
                    ),
                    reply_markup=ForceReply(
                        selective=True, input_field_placeholder=tr("admin_price_placeholder", lang)
                    ),
                )
                await state.update_data(
                    admin_price={
                        "slug": row.slug,
                        "old": row.price_stars,
                        "name": name,
                        "prompt_id": prompt.message_id,
                        "token": uuid4().hex,
                        "expires": time.time() + TTL,
                    }
                )
                await callback.answer()
                return
            elif len(parts) == 2 and parts[1] == "orders":
                async with sessions() as db:
                    counts = (
                        await db.execute(
                            select(Order.status, func.count(Order.id)).group_by(Order.status)
                        )
                    ).all()
                text = (
                    tr("admin_orders", lang)
                    + "\n"
                    + (
                        "\n".join(
                            f"{status_label(status, lang)}: {count}"
                            for status, count in sorted(counts)
                        )
                        or tr("admin_no_orders", lang)
                    )
                )
                keyboard = controls(lang)
            elif len(parts) == 2 and parts[1] == "stars":
                text, keyboard = await stars_report(lang=lang), controls(lang)
            elif len(parts) == 2 and parts[1] == "history":
                async with sessions() as db:
                    rows = list(
                        (
                            await db.scalars(
                                select(StarPriceChange)
                                .order_by(
                                    StarPriceChange.created_at.desc(), StarPriceChange.id.desc()
                                )
                                .limit(5)
                            )
                        ).all()
                    )
                text = (
                    tr("admin_history_title", lang)
                    + "\n\n"
                    + (
                        "\n\n".join(
                            tr(
                                "admin_history_entry",
                                lang,
                                slug=row.service_slug,
                                actor=row.actor_id,
                                old=price_label(row.old_price, lang),
                                new=price_label(row.new_price, lang),
                                date=row.created_at.astimezone(ZoneInfo("Asia/Riyadh")).strftime(
                                    "%Y-%m-%d %H:%M"
                                ),
                            )
                            for row in rows
                        )
                        or tr("admin_history_empty", lang)
                    )
                )
                keyboard = controls(lang)
            else:
                raise ServiceError("invalid_request")
            await callback.answer()
            for part in message_parts(text):
                await callback.message.answer(part, reply_markup=keyboard)
        except ServiceError as error:
            await callback.answer(tr(error.key, lang), show_alert=True)

    @router.message(PriceReply())
    async def price_reply(message: Message, state: FSMContext, lang: str = "ar"):
        if not allowed(message.from_user):
            await message.answer(tr("not_allowed", lang))
            return
        pending = (await state.get_data()).get("admin_price") or {}
        if pending.get("expires", 0) < time.time():
            await state.update_data(admin_price=None)
            await message.answer(tr("stale_button", lang), reply_markup=controls(lang))
            return
        value = (message.text or "").strip()
        if not re.fullmatch(r"[0-9٠-٩]{1,7}", value) or not 1 <= int(value) <= 1000000:
            await message.answer(tr("admin_price_invalid", lang))
            return
        # Freeze this reply: later replies cannot silently change an existing confirmation.
        if "new" in pending:
            await message.answer(tr("stale_button", lang), reply_markup=controls(lang))
            return
        pending["new"] = int(value)
        await state.update_data(admin_price=pending)
        await message.answer(
            tr(
                "admin_price_review",
                lang,
                name=pending["name"],
                old=price_label(pending["old"], lang),
                new=price_label(pending["new"], lang),
            ),
            reply_markup=buttons(
                [
                    (tr("admin_price_confirm", lang), f"admin:confirm:{pending['token']}"),
                    (tr("cancel", lang), "admin:cancel"),
                ]
            ),
        )

    return router
