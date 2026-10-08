from typing import Literal

from pydantic import Field, model_validator

from app.builders.schema import Document, StrictModel, Table
from app.services.documents import DocumentInputs


class Inputs(DocumentInputs):
    target: Literal["word", "excel"]

    @model_validator(mode="after")
    def supported_mode(self):
        if self.target == "excel" and self.mode != "smart":
            raise ValueError("direct Excel is not supported")
        return self


class WordPlan(StrictModel):
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


class ExcelPlan(StrictModel):
    ambiguous: bool = False
    missing_information: bool = False
    question: str = Field(default="", max_length=1000)
    table: Table | None = None

    @model_validator(mode="after")
    def valid(self):
        if not self.missing_information and self.table is None:
            raise ValueError("missing table")
        if self.ambiguous and not self.question:
            raise ValueError("missing clarification")
        return self
