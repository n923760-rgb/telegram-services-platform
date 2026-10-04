from abc import ABC, abstractmethod

from aiogram import Bot
from aiogram.types import BufferedInputFile, InlineKeyboardButton, InlineKeyboardMarkup

from app.core.i18n import tr
from app.services.base import Result


class Delivery(ABC):
    @abstractmethod
    async def send(self, user_id: int, order_id, result: Result): ...

    async def error(self, user_id: int, order_id, key: str):
        raise NotImplementedError


class TelegramDelivery(Delivery):
    def __init__(self, bot: Bot, storage=None):
        self.bot, self.storage = bot, storage

    async def send(self, user_id, order_id, result):
        await self.bot.send_message(user_id, tr("result_header", order_id=order_id))
        if result.preview:
            await self.bot.send_message(user_id, tr("structure_preview", preview=result.preview))
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
        await self.bot.send_message(user_id, tr("order_failed", order_id=order_id, reason=tr(key)))

    async def confirmation(self, user_id, order_id, preview):
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=tr("approve_structure"), callback_data=f"approve:{order_id}"
                    ),
                    InlineKeyboardButton(
                        text=tr("cancel_order"), callback_data=f"reject:{order_id}"
                    ),
                ]
            ]
        )
        await self.bot.send_message(
            user_id,
            tr("confirmation_waiting", order_id=order_id, preview=preview),
            reply_markup=markup,
        )
