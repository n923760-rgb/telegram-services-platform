from uuid import UUID

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.core.db import sessions
from app.core.i18n import tr
from app.core.models import Order, SupportTicket
from app.core.settings import config
from app.ops.admin import ban, refund, set_service
from app.ops.reports import report
from app.services.base import ServiceError
from app.wallet.ledger import WalletError, halalas


def create_router():
    router = Router()

    @router.message(Command("disable", "enable", "setprice", "refund", "ban", "report"))
    async def admin_ops(message: Message):
        if message.from_user.id not in config().admin_ids:
            await message.answer(tr("not_allowed"))
            return
        args = (message.text or "").split()
        command = args[0].split("@")[0]
        try:
            if command == "/report":
                await message.answer(await report())
                return
            if command == "/refund":
                await refund(UUID(args[1]))
            elif command == "/ban":
                await ban(int(args[1]))
            elif command == "/setprice":
                await set_service(args[1], price=halalas(args[2]))
            else:
                await set_service(args[1], enabled=command == "/enable")
            await message.answer(tr("admin_done"))
        except ServiceError as error:
            await message.answer(tr(error.key))
        except (ValueError, IndexError, WalletError):
            await message.answer(tr("admin_usage"))

    @router.callback_query(F.data == "menu:support")
    async def support(callback: CallbackQuery, state: FSMContext):
        await state.clear()
        await state.set_state("support")
        await callback.answer()
        await callback.message.answer(tr("support_prompt"))

    @router.message(StateFilter("support"), ~F.text.startswith("/"))
    async def support_message(message: Message, state: FSMContext):
        if not message.text or len(message.text) > 3000:
            await message.answer(tr("input_invalid"))
            return
        data = await state.get_data()
        stored = data.get("ticket_id")
        ticket_id = None
        if stored:
            try:
                ticket_id = UUID(stored)
            except (ValueError, TypeError, AttributeError):
                ticket_id = None
        async with sessions.begin() as db:
            ticket = await db.get(SupportTicket, ticket_id) if ticket_id else None
            if ticket is None or ticket.user_id != message.from_user.id:
                order_id = await db.scalar(
                    select(Order.id)
                    .where(Order.user_id == message.from_user.id)
                    .order_by(Order.created_at.desc())
                    .limit(1)
                )
                ticket = SupportTicket(user_id=message.from_user.id, order_id=order_id)
                db.add(ticket)
                await db.flush()
                ticket_id = ticket.id
            else:
                order_id = ticket.order_id
        await state.update_data(ticket_id=str(ticket_id))
        delivered = 0
        for admin in config().admin_ids:
            try:
                await message.bot.send_message(
                    admin,
                    tr(
                        "support_context",
                        ticket=ticket_id,
                        order_id=order_id or tr("none"),
                        user_id=message.from_user.id,
                    ),
                )
                await message.bot.copy_message(admin, message.chat.id, message.message_id)
                delivered += 1
            except Exception:
                continue
        if delivered:
            await state.clear()
            await message.answer(tr("support_sent"))
        else:
            await message.answer(tr("support_failed"))

    @router.message(Command("reply"))
    async def reply(message: Message):
        if message.from_user.id not in config().admin_ids:
            await message.answer(tr("not_allowed"))
            return
        try:
            _, ticket_id, content = (message.text or "").split(maxsplit=2)
            if len(content) > 3000:
                raise ValueError
            async with sessions() as db:
                ticket = await db.get(SupportTicket, UUID(ticket_id))
            if not ticket:
                raise ValueError
        except (ValueError, IndexError):
            await message.answer(tr("admin_usage"))
            return
        try:
            await message.bot.send_message(ticket.user_id, tr("support_reply", content=content))
        except Exception:
            await message.answer(tr("support_reply_failed"))
            return
        await message.answer(tr("admin_done"))

    return router
