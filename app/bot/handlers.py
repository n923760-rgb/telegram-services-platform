from uuid import uuid4

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select

from app.bot.ui import buttons, home_keyboard, leave_support, menu
from app.core.db import sessions
from app.core.display import order_reference
from app.core.i18n import tr
from app.core.models import Order, Service
from app.core.settings import config
from app.core.users import set_language
from app.orders.engine import register, submit
from app.services.base import InputSchema, ServiceError, active_field, get_input, set_input
from app.wallet.ledger import WalletError, apply, balance, halalas, sar


def create_router():
    router = Router()

    async def ask(message, state, lang="ar"):
        """Render the next prompt, confirmation or multiple-file prompt.

        A ``pending_prompt`` marker is persisted before the outbound send and cleared only
        after it succeeds, so a transport failure leaves the draft recoverable.
        """
        data = await state.get_data()
        fields = InputSchema.model_validate(data["schema"]).conversation()
        index = data["index"]
        while index < len(fields) and not active_field(fields[index], data["inputs"]):
            index += 1
        if index != data["index"]:
            data["index"] = index
        data["pending_prompt"] = True
        await state.set_data(data)
        if index >= len(fields):
            await state.set_state("confirm")
            await message.answer(
                tr("confirmation_title", lang, name=data.get(f"name_{lang}", data["slug"]))
                + "\n\n"
                + (
                    tr("stars_confirm", lang, amount=data["stars_price"], terms=data["terms"][lang])
                    if data.get("payment_mode") == "stars"
                    else tr("confirm_price", lang, amount=sar(data["price"]))
                ),
                reply_markup=buttons(
                    [
                        (
                            tr(
                                "stars_agree" if data.get("payment_mode") == "stars" else "confirm",
                                lang,
                            ),
                            f"confirm:{data['key']}",
                        ),
                        (tr("cancel", lang), f"cancel:{data['key']}"),
                    ]
                ),
            )
        else:
            await state.set_state("collect")
            field = fields[index]
            heading = tr(
                "intake_step",
                lang,
                name=data.get(f"name_{lang}", data["slug"]),
                step=sum(active_field(f, data["inputs"]) for f in fields[:index]) + 1,
            )
            cancel_item = (tr("cancel", lang), f"cancel:{data['key']}")
            values = get_input(data["inputs"], field.name)
            if field.multiple and isinstance(values, list) and 0 < len(values) < field.max_items:
                await message.answer(
                    heading
                    + "\n\n"
                    + tr("files_received", lang, count=len(values), maximum=field.max_items)
                    + "\n"
                    + tr("more_files", lang),
                    reply_markup=buttons(
                        [(tr("done_files", lang), f"done:{data['key']}:{index}"), cancel_item]
                    ),
                )
            else:
                items = [
                    (tr(k, lang), f"choice:{data['key']}:{index}:{i}")
                    for i, k in enumerate(field.choice_keys)
                ]
                if not field.required:
                    items.append((tr(field.skip_key, lang), f"skip:{data['key']}:{index}"))
                items.append(cancel_item)
                await message.answer(
                    heading + "\n\n" + tr(field.prompt_key, lang),
                    reply_markup=buttons(
                        items, columns=2 if field.choices else 1, separate_last=bool(field.choices)
                    ),
                )
        data["pending_prompt"] = False
        await state.set_data(data)

    async def _resume_if_pending(message, state, lang="ar") -> bool:
        data = await state.get_data()
        if data.get("pending_prompt") and data.get("key") and "schema" in data:
            await message.answer(tr("update_not_applied", lang))
            await ask(message, state, lang)
            return True
        return False

    @router.callback_query(F.data.startswith("service:"))
    async def choose(callback: CallbackQuery, state: FSMContext, lang: str = "ar"):
        await register(callback.from_user.id)
        async with sessions() as db:
            service = await db.get(Service, callback.data.split(":", 1)[1])
        await callback.answer()
        if not service or not service.enabled:
            await callback.message.answer(tr("unavailable", lang))
            return
        if config().stars_enabled and service.price_stars is None:
            await callback.message.answer(tr("unavailable", lang))
            return
        from app.payments.stars import terms_hash

        await state.set_state("collect")
        await state.set_data(
            {
                "slug": service.slug,
                "name_ar": service.name_ar,
                "name_en": service.name_en,
                "schema": service.input_schema,
                "price": service.price_halala,
                "version": service.version,
                "inputs": {},
                "index": 0,
                "key": uuid4().hex,
                "payment_mode": "stars" if config().stars_enabled else "test_credit",
                "stars_price": service.price_stars if config().stars_enabled else None,
                "terms_version": config().stars_terms_version if config().stars_enabled else None,
                "terms_hash": terms_hash() if config().stars_enabled else None,
                "terms": {"ar": config().stars_terms_ar, "en": config().stars_terms_en},
            }
        )
        await ask(callback.message, state, lang)

    @router.callback_query(F.data.startswith("lang:"))
    async def language_choose(callback: CallbackQuery, state: FSMContext, lang: str = "ar"):
        new_lang = callback.data.split(":", 1)[1]
        if new_lang not in {"ar", "en"}:
            await callback.answer(tr("invalid_request", lang), show_alert=True)
            return
        await set_language(callback.from_user.id, new_lang)
        await callback.answer()
        await leave_support(state)
        await callback.message.answer(
            tr("language_set", new_lang), reply_markup=home_keyboard(new_lang)
        )
        if (await state.get_data()).get("key"):
            await ask(callback.message, state, new_lang)

    @router.callback_query(
        StateFilter("collect", "confirm", "support"), F.data.startswith("cancel:")
    )
    async def cancel(callback: CallbackQuery, state: FSMContext, lang: str = "ar"):
        data = await state.get_data()
        if not data.get("key") or callback.data != f"cancel:{data['key']}":
            await callback.answer(tr("stale_button", lang), show_alert=True)
            return
        await state.clear()
        await callback.answer()
        try:
            await callback.message.edit_reply_markup()
        except Exception:
            pass
        await callback.message.answer(tr("draft_cancelled", lang), reply_markup=menu(lang))

    @router.callback_query(StateFilter("collect"), F.data.startswith("skip:"))
    async def skip_field(callback: CallbackQuery, state: FSMContext, lang: str = "ar"):
        data = await state.get_data()
        if await _resume_if_pending(callback.message, state, lang):
            await callback.answer()
            return
        await callback.answer()
        try:
            _, key, index = callback.data.split(":")
            stale = key != data["key"] or int(index) != data["index"]
        except (ValueError, IndexError):
            await callback.message.answer(tr("invalid_request", lang))
            return
        if stale:
            await callback.message.answer(tr("stale_button", lang))
            return
        field = InputSchema.model_validate(data["schema"]).conversation()[data["index"]]
        if field.required or get_input(data["inputs"], field.name) is not None:
            await callback.message.answer(tr("invalid_request", lang))
            return
        data["index"] += 1
        await state.set_data(data)
        await ask(callback.message, state, lang)

    @router.callback_query(StateFilter("collect"), F.data.startswith("choice:"))
    async def choice(callback: CallbackQuery, state: FSMContext, lang: str = "ar"):
        data = await state.get_data()
        if await _resume_if_pending(callback.message, state, lang):
            await callback.answer()
            return
        try:
            _, key, index, selected = callback.data.split(":")
            selected_index = int(selected)
            stale = key != data["key"] or int(index) != data["index"]
        except (ValueError, IndexError):
            await callback.answer(tr("invalid_request", lang), show_alert=True)
            return
        if stale:
            await callback.answer(tr("stale_button", lang), show_alert=True)
            return
        field = InputSchema.model_validate(data["schema"]).conversation()[data["index"]]
        if not 0 <= selected_index < len(field.choices):
            await callback.answer(tr("invalid_request", lang), show_alert=True)
            return
        value = field.choices[selected_index]
        await callback.answer()
        await collect_value(callback.message, state, data, field.name, value, lang)

    async def collect_value(message, state, data, name, value, lang):
        set_input(data["inputs"], name, value)
        data["index"] += 1
        await state.set_data(data)
        await ask(message, state, lang)

    @router.message(Command("addbalance", "balance", "stats"))
    async def admin(message: Message, lang: str = "ar"):
        if message.from_user.id not in config().admin_ids:
            await message.answer(tr("not_allowed", lang))
            return
        args = (message.text or "").split()
        try:
            command = args[0].split("@")[0]
            if command == "/addbalance":
                user_id, amount = int(args[1]), halalas(args[2])
                await register(user_id)
                async with sessions.begin() as db:
                    await apply(
                        db,
                        user_id,
                        "credit",
                        amount,
                        f"admin:{message.chat.id}:{message.message_id}",
                    )
                await message.answer(tr("credited", lang, amount=sar(amount), user_id=user_id))
            elif command == "/balance":
                async with sessions() as db:
                    funds = await balance(db, int(args[1]))
                await message.answer(
                    tr(
                        "balance_details",
                        lang,
                        available=sar(funds.available),
                        reserved=sar(funds.reserved),
                    )
                )
            else:
                async with sessions() as db:
                    count = await db.scalar(select(func.count(Order.id)))
                await message.answer(tr("stats", lang, orders=count))
        except (ValueError, IndexError, WalletError):
            await message.answer(tr("admin_usage", lang))

    @router.callback_query(StateFilter("confirm"), F.data.startswith("confirm:"))
    async def confirm(callback: CallbackQuery, state: FSMContext, lang: str = "ar"):
        data = await state.get_data()
        if await _resume_if_pending(callback.message, state, lang):
            await callback.answer()
            return
        await callback.answer()
        if callback.data != f"confirm:{data['key']}":
            await callback.message.answer(tr("stale_button", lang))
            return
        try:
            order_id = await submit(
                callback.from_user.id,
                data["slug"],
                data["inputs"],
                data["price"],
                data["key"],
                data["version"],
                expected_stars=data.get("stars_price"),
                terms_version=data.get("terms_version"),
                expected_terms_hash=data.get("terms_hash"),
            )
            if data.get("payment_mode") == "stars":
                from app.bot.payments import invoice

                await invoice(callback.bot, order_id, callback.from_user.id, lang)
            await state.clear()
            try:
                await callback.message.edit_reply_markup()
            except Exception:
                pass
            await callback.message.answer(
                tr(
                    "stars_invoice_sent" if data.get("payment_mode") == "stars" else "queued",
                    lang,
                    order_id=order_reference(order_id),
                ),
                reply_markup=menu(lang),
            )
        except (ServiceError, WalletError) as error:
            await callback.message.answer(tr(error.key, lang))
            if error.key == "cost_cap":
                from app.ops.notifier import Notifier
                from app.providers.notifier import TelegramAdminChannel

                await Notifier(state.storage.redis, TelegramAdminChannel(callback.bot)).alert(
                    "daily_cost_cap"
                )

    @router.message(StateFilter("collect"), ~F.text.startswith("/"))
    async def collect(message: Message, state: FSMContext, lang: str = "ar"):
        data = await state.get_data()
        if await _resume_if_pending(message, state, lang):
            return
        field = InputSchema.model_validate(data["schema"]).conversation()[data["index"]]
        if field.choices:
            await message.answer(tr("choose_option", lang))
            return
        if field.kind in {"image", "file", "audio"}:
            from app.files.telegram import receive

            try:
                value = await receive(message, field.kind, message.from_user.id)
            except ServiceError as error:
                await message.answer(tr(error.key, lang))
                return
        else:
            value = message.text or ""
            if not value.strip() or len(value) > field.max_length:
                await message.answer(tr("input_invalid", lang))
                return
            if field.single_line and any(c in value for c in "\r\n\u2028\u2029"):
                await message.answer(tr("input_single_line", lang))
                return
        if field.multiple:
            values = get_input(data["inputs"], field.name) or []
            values.append(value)
            set_input(data["inputs"], field.name, values)
            await state.set_data(data)
            if len(values) < field.max_items:
                await ask(message, state, lang)
                return
            value = values
        await collect_value(message, state, data, field.name, value, lang)

    @router.message(StateFilter("confirm"), ~F.text.startswith("/"))
    async def confirm_prompt(message: Message, state: FSMContext, lang: str = "ar"):
        if await _resume_if_pending(message, state, lang):
            return
        await message.answer(tr("confirm_unchanged", lang))

    @router.message(Command("cancel"))
    async def cancel_command(message: Message, state: FSMContext, lang: str = "ar"):
        data = await state.get_data()
        if not data.get("key"):
            if await state.get_state() == "support":
                await leave_support(state)
                await message.answer(tr("support_cancelled", lang), reply_markup=menu(lang))
                return
            await message.answer(tr("no_active_draft", lang), reply_markup=menu(lang))
            return
        await state.clear()
        await message.answer(tr("draft_cancelled", lang), reply_markup=menu(lang))

    @router.callback_query(F.data == "draft:resume")
    async def resume_callback(callback: CallbackQuery, state: FSMContext, lang: str = "ar"):
        await callback.answer()
        await leave_support(state)
        data = await state.get_data()
        if not data.get("key") or "schema" not in data:
            await callback.message.answer(tr("resume_none", lang), reply_markup=menu(lang))
            return
        await ask(callback.message, state, lang)

    @router.message(Command("resume"))
    async def resume_command(message: Message, state: FSMContext, lang: str = "ar"):
        await leave_support(state)
        data = await state.get_data()
        if not data.get("key") or "schema" not in data:
            await message.answer(tr("resume_none", lang))
            return
        await ask(message, state, lang)

    @router.callback_query(StateFilter("collect"), F.data.startswith("done:"))
    async def done_files(callback: CallbackQuery, state: FSMContext, lang: str = "ar"):
        data = await state.get_data()
        if await _resume_if_pending(callback.message, state, lang):
            await callback.answer()
            return
        try:
            _, key, index = callback.data.split(":")
            stale = key != data["key"] or int(index) != data["index"]
        except (ValueError, IndexError):
            await callback.answer(tr("invalid_request", lang), show_alert=True)
            return
        if stale:
            await callback.answer(tr("stale_button", lang), show_alert=True)
            return
        field = InputSchema.model_validate(data["schema"]).conversation()[data["index"]]
        values = get_input(data["inputs"], field.name) or []
        if not field.multiple or not values:
            await callback.answer()
            await callback.message.answer(tr("input_invalid", lang))
            return
        await callback.answer()
        await collect_value(callback.message, state, data, field.name, values, lang)

    @router.callback_query(F.data.startswith("approve:") | F.data.startswith("reject:"))
    async def structure_confirmation(callback: CallbackQuery, lang: str = "ar"):
        from uuid import UUID

        from app.orders.engine import confirm_structure

        await callback.answer()
        try:
            parts = callback.data.split(":")
            if len(parts) not in {2, 3} or (len(parts) == 3 and parts[2] != "visual"):
                raise ServiceError("invalid_request")
            await confirm_structure(
                UUID(parts[1]),
                callback.from_user.id,
                callback.data.startswith("approve:"),
                expected_prepared=len(parts) == 3,
            )
            try:
                await callback.message.edit_reply_markup()
            except Exception:
                pass
            await callback.message.answer(
                tr("structure_approved", lang)
                if callback.data.startswith("approve:")
                else tr("cancelled", lang),
                reply_markup=menu(lang),
            )
        except (ValueError, ServiceError) as error:
            await callback.message.answer(
                tr(error.key if isinstance(error, ServiceError) else "invalid_request", lang)
            )

    @router.message(StateFilter(None))
    async def idle_message(message: Message, lang: str = "ar"):
        await message.answer(
            tr("unknown_input" if message.text else "unsupported", lang), reply_markup=menu(lang)
        )

    @router.callback_query()
    async def expired_callback(callback: CallbackQuery, lang: str = "ar"):
        await callback.answer(tr("stale_button", lang), show_alert=True)

    return router
