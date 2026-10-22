from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.core.display import message_parts, result_preview
from app.core.i18n import tr
from app.providers.delivery import TelegramDelivery
from app.services.base import Result
from app.services.meeting_minutes.schema import Inputs
from app.services.meeting_minutes.service import MeetingMinutes
from tests.minutes_fixtures import inputs


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize("language", ["ar", "en"])
async def test_every_task_and_complete_metadata_are_reviewed_before_any_export(language):
    owner = "المسؤول الكامل " + "أحمد " * 12
    deadline = "2026-10-12 only after written approval from the full project committee"
    notes = [f"{owner} sends report {i:05d} by {deadline}." for i in range(1, 9)]
    source = inputs(language) | {"notes": "\n".join(notes + [notes[-1]])}
    candidate = {
        "assignments": [
            {"note_id": i, "category": "action", "assignee": owner, "deadline": deadline}
            for i in range(1, 10)
        ]
    }
    ai = AsyncMock()
    ai.extract.side_effect = lambda schema, *_: schema.model_validate(candidate)
    service = MeetingMinutes()
    service.runtime = SimpleNamespace(ai=ai, storage=None, renderer=None)
    result = await service.run(source)
    assert result.needs_confirmation and not result.artifacts and ai.extract.await_count == 1
    assert MeetingMinutes.version == "4"
    assert len(result.preview) <= 3000
    for lang in ("ar", "en"):
        review = result_preview(result.model_dump(), lang)
        assert review == result.review_details_localizations[lang]
        for i, note in enumerate(Inputs.parse(source).lines(), 1):
            assert review.count(f"[{i}] {note}") == 1
        assert (
            review.count(tr("minutes_task_preview", lang, assignee=owner, deadline=deadline)) == 9
        )
        assert tr("minutes_review_complete_end", lang) in review
        assert len(review) > 3000
    assert result.continuation == candidate


@pytest.mark.parametrize("language", ["ar", "en"])
async def test_all_eighty_units_unknowns_and_unicode_survive_message_splitting(language):
    notes = [f"Source {i:05d} " + "🙂" * 120 for i in range(1, 81)]
    ai = AsyncMock()
    ai.extract.side_effect = lambda schema, *_: schema.model_validate(
        {
            "assignments": [
                {
                    "note_id": i,
                    "category": ("discussion", "decision", "action", "review")[(i - 1) % 4],
                }
                for i in range(1, 81)
            ]
        }
    )
    service = MeetingMinutes()
    service.runtime = SimpleNamespace(ai=ai, storage=None, renderer=None)
    result = await service.run(inputs(language) | {"notes": "\n".join(notes)})
    for lang in ("ar", "en"):
        review = result_preview(result.model_dump(), lang)
        assert len(review) <= 50000
        for i, note in enumerate(notes, 1):
            assert review.count(f"[{i}] {note}") == 1
        unknown = tr("minutes_unspecified", lang)
        assert (
            review.count(tr("minutes_task_preview", lang, assignee=unknown, deadline=unknown)) == 20
        )
        parts = list(message_parts(review))
        assert "".join(parts) == review and len(parts) > 1
        assert all(len(part.encode("utf-16-le")) // 2 <= 3500 for part in parts)


@pytest.mark.parametrize("language", ["ar", "en"])
async def test_complete_review_buttons_only_follow_last_part(language):
    details = "🙂" * 7000 + "FINAL OWNER / 2026-10-12"
    result = Result(
        preview="Short sample",
        review_details="Fallback details",
        review_details_localizations={language: details},
        needs_confirmation=True,
        continuation={"approved": True},
    )
    reference = UUID("6c7382cc-ee7f-4206-b528-cdc51a150506")
    bot = AsyncMock()
    delivery = TelegramDelivery(bot)
    delivery._lang = AsyncMock(return_value=language)
    await delivery.confirmation(1, reference, result_preview(result.model_dump(), language))
    calls = bot.send_message.await_args_list
    assert details in "".join(call.args[1] for call in calls)
    assert all(call.kwargs["reply_markup"] is None for call in calls[:-1])
    assert all(len(call.args[1].encode("utf-16-le")) // 2 <= 3500 for call in calls)
    rows = calls[-1].kwargs["reply_markup"].inline_keyboard
    assert rows[0][0].callback_data == f"approve:{reference}"
    assert rows[1][0].callback_data == f"reject:{reference}"


@pytest.mark.parametrize(
    "patch",
    [
        {"review_details": "x" * 50001},
        {"review_details_localizations": {"ar": "x" * 50001}},
        {"review_details_localizations": {"en": "x" * 50001}},
        {"review_details_localizations": {"fr": "text"}},
        {"preview": "x" * 3001},
    ],
)
def test_review_details_have_separate_bounds_without_relaxing_short_previews(patch):
    with pytest.raises(ValidationError):
        Result(needs_confirmation=True, continuation={"choice": True}, **patch)


def test_legacy_completed_and_missing_language_reviews_keep_their_fallback():
    legacy = {"preview": "Old sample", "needs_confirmation": True}
    assert result_preview(legacy, "en") == "Old sample"
    result = Result(
        preview="Short sample",
        review_details="Full fallback",
        review_details_localizations={"ar": "كل التفاصيل"},
        needs_confirmation=True,
        continuation={"choice": True},
    )
    assert result_preview(result.model_dump(), "en") == "Full fallback"
    assert result_preview(result.model_dump(), "ar") == "كل التفاصيل"
    completed = result.model_dump() | {"needs_confirmation": False}
    assert result_preview(completed, "en") == "Short sample"
    assert Result.model_validate_json(result.model_dump_json()).review_details == "Full fallback"
