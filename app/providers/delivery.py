from abc import ABC, abstractmethod

from aiogram import Bot
from aiogram.types import BufferedInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select

from app.core.db import sessions
from app.core.i18n import tr
from app.core.models import Order, StarCharge
from app.core.users import get_language
from app.services.base import Result


class Delivery(ABC):
    @abstractmethod
    async def send(self, user_id: int, order_id, result: Result): ...

    async def error(self, user_id: int, order_id, key: str):
        raise NotImplementedError


class TelegramDelivery(Delivery):
    def __init__(self, bot: Bot, storage=None):
        self.bot, self.storage = bot, storage

    async def _lang(self, user_id):
        return await get_language(user_id)

    async def send(self, user_id, order_id, result):
        lang = await self._lang(user_id)
        await self.bot.send_message(user_id, tr("result_header", lang, order_id=order_id))
        if result.preview:
            await self.bot.send_message(
                user_id, tr("structure_preview", lang, preview=result.preview)
            )
        part = ""
        units = 0
        for character in result.text:
            size = 2 if ord(character) > 0xFFFF else 1
            if units + size > 3500:
                await self.bot.send_message(user_id, part)
                part = ""
                units = 0
            part += character
            units += size
        if part:
            await self.bot.send_message(user_id, part)
        for artifact in result.artifacts:
            await self.bot.send_document(
                user_id,
                BufferedInputFile(
                    self.storage.read(artifact.key, user_id), filename=artifact.filename
                ),
            )
        return "telegram:accepted"

    async def error(self, user_id, order_id, key):
        lang = await self._lang(user_id)
        async with sessions() as db:
            order = await db.get(Order, order_id)
            stars = order is not None and order.user_id == user_id and order.payment_mode == "stars"
            charge = (
                await db.scalar(
                    select(StarCharge).where(
                        StarCharge.order_id == order_id, StarCharge.accepted.is_(True)
                    )
                )
                if stars
                else None
            )
        reason = tr("stars_failure_reason", lang) if stars else tr(key, lang)
        if charge and charge.state != "refunded":
            reason += "\n" + tr("stars_refund_pending", lang)
        await self.bot.send_message(
            user_id, tr("order_failed", lang, order_id=order_id, reason=reason)
        )

    async def confirmation(self, user_id, order_id, preview):
        lang = await self._lang(user_id)
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=tr("approve_structure", lang), callback_data=f"approve:{order_id}"
                    ),
                    InlineKeyboardButton(
                        text=tr("cancel_order", lang), callback_data=f"reject:{order_id}"
                    ),
                ]
            ]
        )
        await self.bot.send_message(
            user_id,
            tr("confirmation_waiting", lang, order_id=order_id, preview=preview),
            reply_markup=markup,
        )
