from collections import Counter

from pydantic import Field, ValidationError, field_validator, model_validator

from app.builders.schema import Deck, StrictModel
from app.services.base import ServiceError
from app.services.documents import DocumentInputs
from app.services.text_editing.schema import CONTACT_TOKEN
from app.services.translation import NUMERIC_TOKEN


class Inputs(StrictModel):
    text: str = Field(min_length=1, max_length=12000)

    @field_validator("text")
    @classmethod
    def printable(cls, value):
        return DocumentInputs.printable_text(value)

    @classmethod
    def parse(cls, inputs):
        try:
            return cls.model_validate({k: v for k, v in inputs.items() if not k.startswith("__")})
        except ValidationError:
            raise ServiceError("input_invalid") from None


class DeckPlan(StrictModel):
    ambiguous: bool = False
    missing_information: bool = False
    question: str = Field(default="", max_length=1000)
    deck: Deck | None = None

    @model_validator(mode="after")
    def valid(self):
        if not self.missing_information and self.deck is None:
            raise ValueError("missing deck")
        if self.ambiguous and not self.question:
            raise ValueError("missing clarification")
        return self


def source_plan_schema(source):
    """Prevent new/altered/over-repeated tokens, not omissions or wrong associations."""
    patterns = (NUMERIC_TOKEN, CONTACT_TOKEN)
    expected = tuple(Counter(pattern.findall(source)) for pattern in patterns)

    class SourceDeckPlan(DeckPlan):
        @model_validator(mode="after")
        def source_tokens(self):
            if self.missing_information or self.deck is None:
                return self
            parts = []
            for slide in self.deck.slides:
                parts.extend([slide.title, *slide.bullets])
                if slide.table is not None:
                    parts.extend(slide.table.columns)
                    parts.extend(cell for row in slide.table.rows for cell in row)
            for pattern, tokens in zip(patterns, expected, strict=True):
                actual = Counter(token for part in parts for token in pattern.findall(part))
                if not actual <= tokens:
                    raise ValueError(
                        "do not invent, alter or duplicate numeric/contact source tokens"
                    )
            return self

    return SourceDeckPlan
