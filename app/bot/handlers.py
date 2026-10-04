from uuid import uuid4

from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import func, select

from app.core.db import sessions
from app.core.i18n import tr
from app.core.models import Order, Service
from app.core.settings import config
from app.orders.engine import register, submit
from app.services.base import InputSchema, ServiceError, active_field, get_input, set_input
from app.wallet.ledger import WalletError, apply, balance, halalas, sar


def create_router():
    router = Router()

    def buttons(items):
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=text, callback_data=data)] for text, data in items
            ]
        )

    def menu():
        return buttons(
            [
                (tr("services"), "menu:services"),
                (tr("balance"), "menu:balance"),
                (tr("support"), "menu:support"),
            ]
        )

    @router.message(CommandStart())
    async def start(message: Message, state: FSMContext):
        await register(message.from_user.id)
        await state.clear()
        await message.answer(tr("welcome"), reply_markup=menu())

    @router.callback_query(F.data == "menu:services")
    async def services(callback: CallbackQuery, state: FSMContext):
        await state.clear()
        async with sessions() as db:
            rows = (
                await db.scalars(
                    select(Service).where(Service.enabled.is_(True)).order_by(Service.slug)
                )
            ).all()
        await callback.answer()
        await callback.message.answer(
            tr("choose_service"),
            reply_markup=buttons(
                [
                    (f"{s.name_ar} — {sar(s.price_halala)} {tr('sar')}", f"service:{s.slug}")
                    for s in rows
                ]
            ),
        )

    @router.callback_query(F.data == "menu:balance")
    async def my_balance(callback: CallbackQuery):
        async with sessions() as db:
            funds = await balance(db, callback.from_user.id)
        await callback.answer()
        await callback.message.answer(
            tr("balance_details", available=sar(funds.available), reserved=sar(funds.reserved))
        )

    async def ask(message, state):
        data = await state.get_data()
        fields = InputSchema.model_validate(data["schema"]).conversation()
        index = data["index"]
        while index < len(fields) and not active_field(fields[index], data["inputs"]):
            index += 1
        if index != data["index"]:
            data["index"] = index
            await state.set_data(data)
        if index >= len(fields):
            await state.set_state("confirm")
            await message.answer(
                tr("confirm_price", amount=sar(data["price"])),
                reply_markup=buttons(
                    [(tr("confirm"), f"confirm:{data['key']}"), (tr("cancel"), "cancel")]
                ),
            )
            return
        field = fields[index]
        items = [
            (tr(k), f"choice:{data['key']}:{index}:{i}") for i, k in enumerate(field.choice_keys)
        ]
        if not field.required:
            items.append((tr("skip_field"), f"skip:{data['key']}:{index}"))
        markup = buttons(items) if items else None
        await message.answer(tr(field.prompt_key), reply_markup=markup)

    @router.callback_query(F.data.startswith("service:"))
    async def choose(callback: CallbackQuery, state: FSMContext):
        await register(callback.from_user.id)
        async with sessions() as db:
            service = await db.get(Service, callback.data.split(":", 1)[1])
        await callback.answer()
        if not service or not service.enabled:
            await callback.message.answer(tr("unavailable"))
            return
        await state.set_state("collect")
        await state.set_data(
            {
                "slug": service.slug,
                "schema": service.input_schema,
                "price": service.price_halala,
                "version": service.version,
                "inputs": {},
                "index": 0,
                "key": uuid4().hex,
            }
        )
        await ask(callback.message, state)

    @router.callback_query(F.data == "cancel")
    async def cancel(callback: CallbackQuery, state: FSMContext):
        await state.clear()
        await callback.answer()
        await callback.message.answer(tr("cancelled"), reply_markup=menu())

    @router.callback_query(StateFilter("collect"), F.data.startswith("skip:"))
    async def skip_field(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        await callback.answer()
        try:
            _, key, index = callback.data.split(":")
            field = InputSchema.model_validate(data["schema"]).conversation()[data["index"]]
            if (
                key != data["key"]
                or int(index) != data["index"]
                or field.required
                or get_input(data["inputs"], field.name) is not None
            ):
                raise ValueError
        except (ValueError, IndexError):
            await callback.message.answer(tr("invalid_request"))
            return
        data["index"] += 1
        await state.set_data(data)
        await ask(callback.message, state)

    @router.callback_query(StateFilter("collect"), F.data.startswith("choice:"))
    async def choice(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        field = InputSchema.model_validate(data["schema"]).conversation()[data["index"]]
        try:
            _, key, index, selected = callback.data.split(":")
            if key != data["key"] or int(index) != data["index"]:
                raise ValueError
            value = field.choices[int(selected)]
        except (ValueError, IndexError):
            await callback.answer()
            return
        await callback.answer()
        await collect_value(callback.message, state, data, field.name, value)

    async def collect_value(message, state, data, name, value):
        set_input(data["inputs"], name, value)
        data["index"] += 1
        await state.set_data(data)
        await ask(message, state)

    @router.message(Command("addbalance", "balance", "stats"))
    async def admin(message: Message):
        if message.from_user.id not in config().admin_ids:
            await message.answer(tr("not_allowed"))
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
                await message.answer(tr("credited", amount=sar(amount), user_id=user_id))
            elif command == "/balance":
                async with sessions() as db:
                    funds = await balance(db, int(args[1]))
                await message.answer(
                    tr(
                        "balance_details",
                        available=sar(funds.available),
                        reserved=sar(funds.reserved),
                    )
                )
            else:
                async with sessions() as db:
                    count = await db.scalar(select(func.count(Order.id)))
                await message.answer(tr("stats", orders=count))
        except (ValueError, IndexError, WalletError):
            await message.answer(tr("admin_usage"))

    @router.callback_query(StateFilter("confirm"), F.data.startswith("confirm:"))
    async def confirm(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        await callback.answer()
        if callback.data != f"confirm:{data['key']}":
            await callback.message.answer(tr("invalid_request"))
            return
        try:
            order_id = await submit(
                callback.from_user.id,
                data["slug"],
                data["inputs"],
                data["price"],
                data["key"],
                data["version"],
            )
            await state.clear()
            await callback.message.answer(tr("queued", order_id=order_id), reply_markup=menu())
        except (ServiceError, WalletError) as error:
            await callback.message.answer(tr(error.key))
            if error.key == "cost_cap":
                from app.ops.notifier import Notifier
                from app.providers.notifier import TelegramAdminChannel

                await Notifier(state.storage.redis, TelegramAdminChannel(callback.bot)).alert(
                    "daily_cost_cap"
                )

    @router.message(StateFilter("collect"), ~F.text.startswith("/"))
    async def collect(message: Message, state: FSMContext):
        data = await state.get_data()
        field = InputSchema.model_validate(data["schema"]).conversation()[data["index"]]
        if field.choices:
            await message.answer(tr("choose_option"))
            return
        if field.kind in {"image", "file", "audio"}:
            from app.files.telegram import receive

            try:
                value = await receive(message, field.kind, message.from_user.id)
            except ServiceError as error:
                await message.answer(tr(error.key))
                return
        else:
            value = (message.text or "").strip()
            if not value or len(value) > field.max_length:
                await message.answer(tr("input_invalid"))
                return
        if field.multiple:
            values = get_input(data["inputs"], field.name) or []
            values.append(value)
            set_input(data["inputs"], field.name, values)
            await state.set_data(data)
            if len(values) < field.max_items:
                await message.answer(
                    tr("more_files"),
                    reply_markup=buttons(
                        [(tr("done_files"), f"done:{data['key']}:{data['index']}")]
                    ),
                )
                return
            value = values
        await collect_value(message, state, data, field.name, value)

    @router.message(Command("cancel"))
    async def cancel_command(message: Message, state: FSMContext):
        await state.clear()
        await message.answer(tr("cancelled"), reply_markup=menu())

    @router.callback_query(StateFilter("collect"), F.data.startswith("done:"))
    async def done_files(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        await callback.answer()
        _, key, index = callback.data.split(":")
        if key != data["key"] or int(index) != data["index"]:
            await callback.message.answer(tr("invalid_request"))
            return
        field = InputSchema.model_validate(data["schema"]).conversation()[data["index"]]
        values = get_input(data["inputs"], field.name) or []
        if not field.multiple or not values:
            await callback.message.answer(tr("input_invalid"))
            return
        await collect_value(callback.message, state, data, field.name, values)

    @router.callback_query(F.data.startswith("approve:") | F.data.startswith("reject:"))
    async def structure_confirmation(callback: CallbackQuery):
        from uuid import UUID

        from app.orders.engine import confirm_structure

        await callback.answer()
        try:
            await confirm_structure(
                UUID(callback.data.split(":")[1]),
                callback.from_user.id,
                callback.data.startswith("approve:"),
            )
            await callback.message.answer(
                tr("admin_done") if callback.data.startswith("approve:") else tr("cancelled")
            )
        except (ValueError, ServiceError) as error:
            await callback.message.answer(
                tr(error.key if isinstance(error, ServiceError) else "invalid_request")
            )

    @router.callback_query()
    async def expired_callback(callback: CallbackQuery):
        await callback.answer(tr("invalid_request"), show_alert=True)

    return router
