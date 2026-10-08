"""Shared Telegram controls; labels are reserved navigation in both UI languages."""

from aiogram.filters import Filter
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

from app.core.i18n import tr

HOME_ITEMS = ("services", "orders", "balance", "support", "language", "help")


class MenuButton(Filter):
    def __init__(self, key):
        self.labels = {tr(key, lang) for lang in ("ar", "en")}

    async def __call__(self, message: Message) -> bool:
        return message.text in self.labels


def buttons(items, columns=1):
    items = [InlineKeyboardButton(text=text, callback_data=data) for text, data in items]
    return InlineKeyboardMarkup(
        inline_keyboard=[items[i : i + columns] for i in range(0, len(items), columns)]
    )


def menu(lang="ar"):
    return buttons([(tr(key, lang), f"menu:{key}") for key in HOME_ITEMS], columns=2)


def home_keyboard(lang="ar"):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=tr(key, lang)) for key in HOME_ITEMS[i : i + 2]]
            for i in range(0, len(HOME_ITEMS), 2)
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder=tr("menu_placeholder", lang),
    )


async def leave_support(state):
    """Leave support without discarding an intake draft kept beneath it."""
    if await state.get_state() != "support":
        return
    data = await state.get_data()
    previous = data.pop("support_return_state", None)
    data.pop("ticket_id", None)
    await state.set_data(data)
    await state.set_state(previous)


async def section_controls(state, lang="ar"):
    items = [(tr("home", lang), "menu:home")]
    if (await state.get_data()).get("key"):
        items.insert(0, (tr("resume_draft", lang), "draft:resume"))
    return items
