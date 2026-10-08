"""Regression tests for idempotent draft prompt recovery (/resume and pending-prompt marker).

Covers: a failed outbound text question, choice question, multiple-file prompt and confirmation
prompt re-render on the next applicable update (or /resume) without consuming a retried input
twice, and /resume with no active draft.
"""

import pytest
from aiogram import Bot
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import SendMessage
from aiogram.types import User as TelegramUser
from sqlalchemy import func, select

from app.bot.main import create_dispatcher
from app.core.db import sessions
from app.core.i18n import tr
from app.core.models import Order, Service
from app.core.settings import config
from app.wallet.ledger import balance
from tests.test_bounded_fixes import Recorder, button_by_prefix, feeders
from tests.test_foundation import fund


class SimulatedSendFailure(Exception):
    """Stands in for an aiogram transport failure on an outbound prompt."""


class FlakyRecorder(Recorder):
    """Recorder that can fail the next N SendMessage calls before recovering."""

    def __init__(self, fail_next_sends=0):
        super().__init__()
        self.fail_next_sends = fail_next_sends

    async def make_request(self, bot, method, timeout=None):
        if isinstance(method, SendMessage) and self.fail_next_sends > 0:
            self.fail_next_sends -= 1
            raise SimulatedSendFailure("simulated transport failure")
        return await super().make_request(bot, method, timeout=None)


def make_dp():
    transport = FlakyRecorder()
    bot = Bot("123456:TEST_TOKEN_ONLY", session=transport)
    dp = create_dispatcher(MemoryStorage(), guard=False)
    user = TelegramUser(id=1, is_bot=False, first_name="Customer")
    return transport, bot, dp, user


async def enable(slug):
    async with sessions.begin() as db:
        (await db.get(Service, slug)).enabled = True


async def test_failed_text_prompt_recovers_without_duplicate_answer():
    await fund()
    transport, bot, dp, user = make_dp()
    message, callback = feeders(dp, bot, user, transport)
    await message("/start")
    await callback("menu:services")
    transport.fail_next_sends = 1
    with pytest.raises(SimulatedSendFailure):
        await callback("service:echo")  # the input_text question fails to reach the user
    await message("نص العميل")  # re-renders the pending question instead of consuming it
    assert transport.messages[-1].text.endswith(tr("input_text"))
    await message("نص العميل")  # now it is accepted as the answer
    assert button_by_prefix(transport.messages[-1].reply_markup, "confirm:")
    await callback(button_by_prefix(transport.messages[-1].reply_markup, "confirm:"))
    async with sessions() as db:
        order = await db.scalar(select(Order))
        assert order.inputs == {"text": "نص العميل"}  # not duplicated or overwritten
        assert order.status == "queued"
    await dp.storage.close()
    await bot.session.close()


async def test_failed_confirmation_prompt_recovers_and_submits_once():
    await fund()
    transport, bot, dp, user = make_dp()
    message, callback = feeders(dp, bot, user, transport)
    await message("/start")
    await callback("menu:services")
    await callback("service:echo")
    transport.fail_next_sends = 1
    with pytest.raises(SimulatedSendFailure):
        await message("نص العميل")  # the confirmation prompt fails after the input was accepted
    # Nothing is reserved and no order exists before an explicit confirm.
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0
        assert (await balance(db, 1)).reserved == 0
    # A retry with different text only re-renders confirmation; it is not consumed as input.
    await message("نص مختلف")
    assert transport.messages[-2].text == tr("update_not_applied")
    confirm_data = button_by_prefix(transport.messages[-1].reply_markup, "confirm:")
    assert confirm_data
    # Only an explicit confirm submits, once, preserving the original input.
    await callback(confirm_data)
    async with sessions() as db:
        orders = list(await db.scalars(select(Order)))
        assert len(orders) == 1
        assert orders[0].inputs == {"text": "نص العميل"}
        assert orders[0].status == "queued"
        assert (await balance(db, 1)).reserved == 100
    # A repeated/stale confirm after submission must not create a second order.
    await callback(confirm_data, on=transport.messages[-2])
    assert transport.callback_answers[-1].text == tr("stale_button")
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 1
    await dp.storage.close()
    await bot.session.close()


async def test_delivered_confirm_ignores_text_and_keeps_commands():
    await fund()
    transport, bot, dp, user = make_dp()
    message, callback = feeders(dp, bot, user, transport)
    await message("/start")
    await callback("menu:services")
    await callback("service:echo")
    await message("نص العميل")  # confirmation delivered successfully
    assert button_by_prefix(transport.messages[-1].reply_markup, "confirm:")
    # Non-command text in confirm state is ignored: nothing consumed, no order created.
    await message("نص عشوائي")
    assert transport.messages[-1].text == tr("confirm_unchanged")
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0
    # /resume re-renders the delivered confirmation prompt.
    await message("/resume")
    assert button_by_prefix(transport.messages[-1].reply_markup, "confirm:")
    # /cancel still routes in confirm state and clears the draft without an order.
    await message("/cancel")
    assert transport.messages[-1].text == tr("draft_cancelled")
    async with sessions() as db:
        assert await db.scalar(select(func.count(Order.id))) == 0
    await dp.storage.close()
    await bot.session.close()


async def test_failed_choice_prompt_recovers():
    await enable("text_to_office")
    transport, bot, dp, user = make_dp()
    message, callback = feeders(dp, bot, user, transport)
    await message("/start")
    await callback("menu:services")
    await callback("service:text_to_office")
    assert transport.messages[-1].text.endswith(tr("office_text"))
    transport.fail_next_sends = 1
    with pytest.raises(SimulatedSendFailure):
        await message("المحتوى")  # the target choice question fails
    await message("المحتوى")  # re-renders the choice question instead of consuming again
    assert button_by_prefix(transport.messages[-1].reply_markup, "choice:")
    # Selecting Word advances straight to purchase confirmation.
    await callback(button_by_prefix(transport.messages[-1].reply_markup, "choice:"))
    assert button_by_prefix(transport.messages[-1].reply_markup, "confirm:")
    await dp.storage.close()
    await bot.session.close()


async def test_failed_more_files_prompt_recovers(monkeypatch):
    import app.files.telegram as telegram_module

    async def fake_receive(message, kind, user_id):
        return f"1/{'a' * 32}/input.jpg"

    monkeypatch.setattr(telegram_module, "receive", fake_receive)
    await enable("image_to_text")
    transport, bot, dp, user = make_dp()
    message, callback = feeders(dp, bot, user, transport)
    await message("/start")
    await callback("menu:services")
    await callback("service:image_to_text")
    assert transport.messages[-1].text.endswith(tr("ocr_images"))
    transport.fail_next_sends = 1
    with pytest.raises(SimulatedSendFailure):
        await message("fake-image")  # the more_files prompt fails after the first upload is saved
    await message("fake-image-retry")  # re-renders the more_files prompt instead of a second file
    assert transport.messages[-1].text.endswith(tr("more_files"))
    assert button_by_prefix(transport.messages[-1].reply_markup, "done:")
    await callback(button_by_prefix(transport.messages[-1].reply_markup, "done:"))
    assert button_by_prefix(transport.messages[-1].reply_markup, "choice:")
    await dp.storage.close()
    await bot.session.close()


async def test_resume_without_draft_reports_none():
    transport, bot, dp, user = make_dp()
    message, _ = feeders(dp, bot, user, transport)
    await message("/start")
    await message("/resume")
    assert transport.messages[-1].text == tr("resume_none")
    await dp.storage.close()
    await bot.session.close()


async def test_resume_rerenders_current_prompt():
    transport, bot, dp, user = make_dp()
    message, callback = feeders(dp, bot, user, transport)
    await message("/start")
    await callback("menu:services")
    await callback("service:echo")
    await message("/resume")  # idempotent re-render of the current question
    assert transport.messages[-1].text.endswith(tr("input_text"))
    await dp.storage.close()
    await bot.session.close()


async def test_new_image_after_failed_more_files_is_not_applied(monkeypatch):
    """A distinct image B arriving while A's more_files acknowledgement is pending must not be
    consumed: an explicit notice says it was not applied and only A is retained."""
    import app.files.telegram as telegram_module

    await fund()
    monkeypatch.setattr(config(), "ai_enabled", True)
    counter = {"n": 0}

    async def fake_receive(message, kind, user_id):
        counter["n"] += 1
        hexpart = ("a" if counter["n"] == 1 else "b") * 32
        return f"1/{hexpart}/input.jpg"

    monkeypatch.setattr(telegram_module, "receive", fake_receive)
    await enable("image_to_text")
    transport, bot, dp, user = make_dp()
    message, callback = feeders(dp, bot, user, transport)
    await message("/start")
    await callback("menu:services")
    await callback("service:image_to_text")
    assert transport.messages[-1].text.endswith(tr("ocr_images"))
    transport.fail_next_sends = 1
    with pytest.raises(SimulatedSendFailure):
        await message("image-A")  # A saved; the more_files acknowledgement fails
    await message("image-B")  # B arrives while A's acknowledgement is still pending
    assert transport.messages[-2].text == tr("update_not_applied")
    assert transport.messages[-1].text.endswith(tr("more_files"))
    # Complete the draft: only A was accepted, B was never received.
    await callback(button_by_prefix(transport.messages[-1].reply_markup, "done:"))
    await callback(button_by_prefix(transport.messages[-1].reply_markup, "choice:"))
    await callback(button_by_prefix(transport.messages[-1].reply_markup, "confirm:"))
    assert counter["n"] == 1
    async with sessions() as db:
        order = await db.scalar(select(Order))
        assert order is not None
        assert order.inputs["images"] == [f"1/{'a' * 32}/input.jpg"]
    await dp.storage.close()
    await bot.session.close()


async def test_stale_cancel_preserves_draft_and_resume_restores():
    transport, bot, dp, user = make_dp()
    message, callback = feeders(dp, bot, user, transport)
    await message("/start")
    await callback("menu:services")
    await callback("service:echo")
    await message("نص العميل")
    stale_cancel = button_by_prefix(transport.messages[-1].reply_markup, "cancel:")
    # Start a newer draft; the old cancel button is now stale.
    await callback("menu:services")
    await callback("service:echo")
    assert transport.messages[-1].text.endswith(tr("input_text"))
    await callback(stale_cancel)
    assert transport.callback_answers[-1].text == tr("stale_button")
    # The newer draft survived; /resume re-renders its current prompt.
    await message("/resume")
    assert transport.messages[-1].text.endswith(tr("input_text"))
    await dp.storage.close()
    await bot.session.close()
