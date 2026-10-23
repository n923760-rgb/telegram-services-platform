from typing import ClassVar, Literal

from pydantic import Field, model_validator
from pydantic_core import PydanticCustomError

from app.builders.schema import StrictModel, Table
from app.builders.word_schema import WordDocument
from app.services.document_fidelity import DOCUMENT_DIAGNOSTICS
from app.services.documents import DocumentInputs


class Inputs(DocumentInputs):
    target: Literal["word", "excel"]

    @model_validator(mode="after")
    def supported_mode(self):
        if self.target == "excel" and self.mode != "smart":
            raise ValueError("direct Excel is not supported")
        if self.target == "excel" and (
            len(self.lines()) > 200 or any(len(line) > 4000 for line in self.lines())
        ):
            raise ValueError("Excel source line limit")
        return self

    def lines(self):
        return [line for line in self.text.split("\n") if line.strip()]


class WordPlan(StrictModel):
    diagnostic_categories: ClassVar = DOCUMENT_DIAGNOSTICS
    ambiguous: bool = False
    missing_information: bool = Field(
        default=False,
        description="True only when essential source facts are absent. Short notes and an omitted title are valid source content, not missing information.",
    )
    question: str = Field(
        default="", max_length=1000, description="Required and nonblank when ambiguous is true."
    )
    document: WordDocument | None = Field(
        default=None,
        description="Provide a complete document unless missing_information is true. Never omit the body merely because the source is short.",
    )

    @model_validator(mode="after")
    def valid(self):
        if not self.missing_information and self.document is None:
            raise PydanticCustomError("document_missing_body", "missing document")
        if self.ambiguous and not self.question:
            raise PydanticCustomError("document_missing_question", "missing clarification")
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
