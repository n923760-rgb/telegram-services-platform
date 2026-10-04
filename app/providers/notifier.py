from abc import ABC, abstractmethod

from app.core.i18n import tr
from app.core.settings import config


class AdminChannel(ABC):
    @abstractmethod
    async def send(self, key, **values): ...


class TelegramAdminChannel(AdminChannel):
    def __init__(self, bot):
        self.bot = bot

    async def send(self, key, **values):
        for admin_id in config().admin_ids:
            await self.bot.send_message(admin_id, tr(key, **values))
