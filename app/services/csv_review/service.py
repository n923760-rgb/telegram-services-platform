import asyncio
from decimal import Decimal

from app.builders.csv_review import build
from app.core.i18n import tr, translations
from app.services.base import BaseService, InputField, InputSchema, Result
from app.services.csv_review.schema import Inputs


class CsvReview(BaseService):
    slug = "csv_review"
    name_ar = tr("csv_review_name")
    name_en = tr("csv_review_name", "en")
    description_ar = tr("csv_review_description")
    price_sar = Decimal("3.00")
    requires_ai = False
    enabled_by_default = False
    input_schema = InputSchema(
        fields=[
            InputField(
                name="language",
                prompt_key="csv_review_language",
                choices=["ar", "en"],
                choice_keys=["arabic", "english"],
            ),
            InputField(
                name="delimiter",
                prompt_key="csv_review_delimiter",
                choices=["comma", "semicolon", "tab"],
                choice_keys=["csv_review_comma", "csv_review_semicolon", "csv_review_tab"],
            ),
            InputField(
                name="whitespace",
                prompt_key="csv_review_whitespace",
                choices=["preserve", "trim"],
                choice_keys=["csv_review_preserve", "csv_review_trim"],
            ),
            InputField(name="text", prompt_key="csv_review_text"),
        ]
    )

    @classmethod
    def needs_ai(cls, inputs):
        Inputs.parse(inputs)
        return False

    async def run(self, inputs):
        values = Inputs.parse(inputs)
        headers, rows = values.records()
        content, counts = await asyncio.to_thread(
            build, headers, rows, trim=values.whitespace == "trim", language=values.language
        )
        artifact = self.runtime.storage.save(
            "review.xlsx",
            content,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        return Result(
            preview=tr("csv_review_preview", values.language, **counts),
            preview_localizations=translations("csv_review_preview", **counts),
            artifacts=[artifact],
        )


SERVICE = CsvReview
