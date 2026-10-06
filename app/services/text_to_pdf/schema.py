from pydantic import Field, model_validator

from app.builders.schema import Document, StrictModel


class Inputs(StrictModel):
    text: str = Field(min_length=1, max_length=12000)


class PdfPlan(StrictModel):
    ambiguous: bool = False
    missing_information: bool = False
    question: str = Field(default="", max_length=1000)
    document: Document | None = None

    @model_validator(mode="after")
    def valid(self):
        if not self.missing_information and self.document is None:
            raise ValueError("missing document")
        if self.ambiguous and not self.question:
            raise ValueError("missing clarification")
        return self
