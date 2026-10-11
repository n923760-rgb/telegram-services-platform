import json
from decimal import Decimal

from pydantic import ValidationError

from app.core.i18n import tr, translations
from app.services.base import BaseService, InputField, InputSchema, Result, ServiceError
from app.services.document_results import word_pdf_result
from app.services.meeting_minutes.prompt import CLASSIFY
from app.services.meeting_minutes.schema import Inputs, classification_schema, document


class MeetingMinutes(BaseService):
    slug = "meeting_minutes"
    category = "professional"
    name_ar = tr("minutes_name")
    name_en = tr("minutes_name", "en")
    description_ar = tr("minutes_description")
    price_sar = Decimal("5.00")
    requires_ai = True
    enabled_by_default = False
    input_schema = InputSchema(
        fields=[
            InputField(name="title", prompt_key="minutes_title", max_length=200, single_line=True),
            InputField(
                name="language",
                prompt_key="minutes_language",
                choices=["ar", "en"],
                choice_keys=["arabic", "english"],
            ),
            InputField(name="notes", prompt_key="minutes_notes"),
        ]
    )

    @classmethod
    def needs_ai(cls, inputs):
        Inputs.parse(inputs)
        return "__continuation" not in inputs

    async def run(self, inputs):
        values = Inputs.parse(inputs)
        notes = values.lines()
        schema = classification_schema(notes)
        continuation = inputs.get("__continuation")
        if "__continuation" in inputs:
            try:
                plan = schema.model_validate(continuation)
            except ValidationError:
                raise ServiceError("provider_invalid") from None
            return await word_pdf_result(
                self.runtime,
                document(values, plan),
                filename="minutes",
                preview=tr("minutes_preview"),
                preview_localizations=translations("minutes_preview"),
            )
        if self.runtime.ai is None:
            raise ServiceError("provider_config")
        source = json.dumps(
            {"notes": [{"id": index, "text": text} for index, text in enumerate(notes, 1)]},
            ensure_ascii=False,
        )
        plan = await self.runtime.ai.extract(schema, source, CLASSIFY)
        # Review before export; source IDs are the only AI-produced document values.
        reviews = {}
        for lang in ("ar", "en"):
            preview = [tr("minutes_review_intro", lang)]
            for category in ("discussion", "decision", "action", "review"):
                ids = sorted(item.note_id for item in plan.assignments if item.category == category)
                if ids:
                    preview.append(tr("minutes_" + category, lang) + f" ({len(ids)})")
                    preview.append(tr("minutes_source_ids", lang, ids=", ".join(map(str, ids))))
                    preview.extend(f"[{number}] {notes[number - 1][:180]}" for number in ids[:2])
            reviews[lang] = "\n".join(preview)
        return Result(
            preview=reviews[values.language],
            preview_localizations=reviews,
            needs_confirmation=True,
            continuation=plan.model_dump(mode="json"),
        )


SERVICE = MeetingMinutes
