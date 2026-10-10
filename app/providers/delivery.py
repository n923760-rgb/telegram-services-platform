from abc import ABC, abstractmethod
from uuid import UUID

from aiogram import Bot
from aiogram.types import BufferedInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select

from app.core.db import sessions
from app.core.display import message_parts, order_reference, result_preview
from app.core.i18n import tr
from app.core.models import Order, StarCharge
from app.core.users import get_language
from app.services.base import Result


class Delivery(ABC):
    @abstractmethod
    async def send(self, user_id: int, order_id, result: Result): ...

    async def error(self, user_id: int, order_id, key: str):
        raise NotImplementedError

    async def visual_confirmation(self, user_id, order_id, result: Result):
        raise NotImplementedError


class TelegramDelivery(Delivery):
    def __init__(self, bot: Bot, storage=None):
        self.bot, self.storage = bot, storage

    async def _lang(self, user_id):
        return await get_language(user_id)

    async def send(self, user_id, order_id, result):
        lang = await self._lang(user_id)
        await self.bot.send_message(
            user_id, tr("result_header", lang, order_id=order_reference(order_id))
        )
        preview = result_preview(result.model_dump(), lang)
        if preview:
            for part in message_parts(tr("structure_preview", lang, preview=preview)):
                await self.bot.send_message(user_id, part)
        for part in message_parts(result.text):
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
        try:
            reference = UUID(str(order_id))
        except (ValueError, TypeError, AttributeError):
            reference = None  # Preserve the adapter's legacy arbitrary display-reference contract.
        async with sessions() as db:
            order = await db.get(Order, reference) if reference else None
            stars = order is not None and order.user_id == user_id and order.payment_mode == "stars"
            charge = (
                await db.scalar(
                    select(StarCharge).where(
                        StarCharge.order_id == reference, StarCharge.accepted.is_(True)
                    )
                )
                if stars
                else None
            )
        reason = tr("stars_failure_reason", lang) if stars else tr(key, lang)
        if charge and charge.state != "refunded":
            reason += "\n" + tr("stars_refund_pending", lang)
        await self.bot.send_message(
            user_id, tr("order_failed", lang, order_id=order_reference(order_id), reason=reason)
        )

    async def send_preview_images(self, user_id, result):
        lang = await self._lang(user_id)
        for artifact in result.preview_artifacts:
            await self.bot.send_photo(
                user_id,
                BufferedInputFile(
                    self.storage.read(artifact.key, user_id), filename=artifact.filename
                ),
                caption=tr("document_preview_caption", lang),
            )

    async def visual_confirmation(self, user_id, order_id, result):
        await self.send_preview_images(user_id, result)
        await self.confirmation(
            user_id,
            order_id,
            result_preview(result.model_dump(), await self._lang(user_id)),
            prepared=result.prepared_delivery,
        )

    async def confirmation(self, user_id, order_id, preview, *, prepared=False):
        lang = await self._lang(user_id)
        suffix = ":visual" if prepared else ""
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=tr("approve_delivery" if prepared else "approve_structure", lang),
                        callback_data=f"approve:{order_id}{suffix}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=tr("cancel_order", lang), callback_data=f"reject:{order_id}{suffix}"
                    )
                ],
            ]
        )
        parts = list(
            message_parts(
                tr(
                    "confirmation_waiting",
                    lang,
                    order_id=order_reference(order_id),
                    preview=preview,
                )
            )
        )
        for index, part in enumerate(parts):
            await self.bot.send_message(
                user_id, part, reply_markup=markup if index == len(parts) - 1 else None
            )
