import re
from collections import Counter
from typing import ClassVar

from pydantic import Field, ValidationError, field_validator, model_validator
from pydantic_core import PydanticCustomError

from app.builders.schema import Deck, Slide, StrictModel
from app.services.base import ServiceError
from app.services.documents import DocumentInputs
from app.services.text_editing.schema import CONTACT_TOKEN
from app.services.translation import NUMERIC_TOKEN


class Inputs(StrictModel):
    text: str = Field(min_length=1, max_length=12000)
    slide_count: int | None = Field(default=None, strict=True, ge=1, le=30)

    @field_validator("slide_count", mode="before")
    @classmethod
    def explicit_count(cls, value):
        if isinstance(value, str):
            if not re.fullmatch(r"\d{1,2}", value.strip()):
                raise ValueError("invalid slide count")
            return int(value.strip())
        return value

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
    diagnostic_categories: ClassVar = {
        "pptx_missing_deck": "pptx_missing_deck",
        "pptx_missing_question": "pptx_missing_question",
        "pptx_source_tokens": "pptx_source_tokens",
        "pptx_slide_count": "pptx_slide_count",
    }
    ambiguous: bool = False
    missing_information: bool = Field(
        default=False,
        description="True only when essential source facts are absent. Short source notes can be arranged into slides without adding facts.",
    )
    question: str = Field(
        default="", max_length=1000, description="Required and nonblank when ambiguous is true."
    )
    deck: Deck | None = Field(
        default=None, description="Provide the complete deck unless missing_information is true."
    )

    @model_validator(mode="after")
    def valid(self):
        if not self.missing_information and self.deck is None:
            raise PydanticCustomError("pptx_missing_deck", "missing deck")
        if self.ambiguous and not self.question:
            raise PydanticCustomError("pptx_missing_question", "missing clarification")
        return self


def source_token_violations(source, deck):
    """Yield content-free locations exceeding the v7 source-token budgets.

    Numeric literals permit one additional contextual use on another slide.
    Each slide still has the original source occurrence budget. Contacts retain
    their original whole-deck budget. This does not establish meaning/coverage.
    """
    for kind, pattern in (("numeric", NUMERIC_TOKEN), ("contact", CONTACT_TOKEN)):
        expected, seen = Counter(pattern.findall(source)), Counter()
        for number, slide in enumerate(deck.slides, 1):
            per_slide, excess = Counter(), Counter()
            parts = [("title", slide.title), *(("bullet", text) for text in slide.bullets)]
            if slide.table is not None:
                parts.extend(("table_header", text) for text in slide.table.columns)
                parts.extend(("table_cell", text) for row in slide.table.rows for text in row)
            for field, text in parts:
                for token in pattern.findall(text):
                    seen[token] += 1
                    per_slide[token] += 1
                    if token not in expected:
                        excess[(field, kind + "_added")] += 1
                    elif (
                        seen[token] > expected[token] + (kind == "numeric")
                        or per_slide[token] > expected[token]
                    ):
                        excess[(field, kind + "_repeated")] += 1
            for (field, category), count in sorted(excess.items()):
                yield {"slide": number, "field": field, "kind": category, "occurrences": count}


def source_plan_schema(source, slide_count=None, *, protected=None):
    """Bound exact source literals and contextual reuse; meaning needs review."""
    if slide_count is not None and (type(slide_count) is not int or not 1 <= slide_count <= 30):
        raise ValueError("invalid slide count")

    class RequestedDeck(Deck):
        slides: list[Slide] = Field(min_length=slide_count or 1, max_length=slide_count or 30)

        @field_validator("slides", mode="before")
        @classmethod
        def exact_count(cls, value):
            if slide_count is not None and isinstance(value, list) and len(value) != slide_count:
                raise PydanticCustomError("pptx_slide_count", "match the requested slide count")
            return value

    class SourceDeckPlan(DeckPlan):
        diagnostic_categories: ClassVar = {
            **DeckPlan.diagnostic_categories,
            "protected_value_reference": "protected_value_reference",
        }
        deck: RequestedDeck | None = Field(
            default=None,
            description="Provide the complete deck with the requested slide count unless missing_information is true.",
        )

        @model_validator(mode="before")
        @classmethod
        def resolve_source_values(cls, value):
            return protected.resolve(value) if protected is not None else value

        @model_validator(mode="after")
        def source_tokens(self):
            if self.missing_information or self.deck is None:
                return self
            if next(source_token_violations(source, self.deck), None) is not None:
                raise PydanticCustomError(
                    "pptx_source_tokens",
                    "preserve numeric/contact source tokens and their bounded reuse",
                )
            return self

    return SourceDeckPlan
