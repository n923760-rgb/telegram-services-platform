from pydantic import Field, model_validator

from app.builders.schema import Deck, StrictModel


class Inputs(StrictModel):
    text: str = Field(min_length=1, max_length=12000)


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
