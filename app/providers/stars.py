"""Only the adapter knows Telegram's Stars API."""

from abc import ABC, abstractmethod


class StarsPayments(ABC):
    @abstractmethod
    async def refund(self, user_id, charge_id) -> bool: ...

    @abstractmethod
    async def transactions(self, offset, limit): ...


class TelegramStars(StarsPayments):
    def __init__(self, bot):
        self.bot = bot

    async def refund(self, user_id, charge_id):
        return await self.bot.refund_star_payment(
            user_id=user_id, telegram_payment_charge_id=charge_id, request_timeout=10
        )

    async def transactions(self, offset, limit):
        result = await self.bot.get_star_transactions(
            offset=offset, limit=limit, request_timeout=15
        )
        return result.transactions
