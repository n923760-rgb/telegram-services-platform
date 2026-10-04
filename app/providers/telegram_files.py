from io import BytesIO

from app.services.base import ServiceError


class LimitedBuffer(BytesIO):
    def __init__(self, limit):
        super().__init__()
        self.limit = limit

    def write(self, data):
        if self.tell() + len(data) > self.limit:
            raise ServiceError("file_invalid")
        return super().write(data)


class TelegramFiles:
    def __init__(self, bot, limit):
        self.bot, self.limit = bot, limit

    async def download(self, file_id):
        buffer = LimitedBuffer(self.limit)
        await self.bot.download(file_id, destination=buffer)
        return buffer.getvalue()
