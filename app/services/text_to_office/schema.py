from typing import Literal

from pydantic import Field, model_validator

from app.builders.schema import StrictModel, Table
from app.builders.word_schema import WordDocument
from app.services.documents import DocumentInputs


class Inputs(DocumentInputs):
    target: Literal["word", "excel"]

    @classmethod
    def parse(cls, inputs):
        values = dict(inputs)
        # A documented first-line directive, never a phrase search inside customer prose.
        if values.get("target") == "word" and "mode" not in values:
            text = values.get("text")
            if isinstance(text, str):
                first, _, body = text.replace("\r\n", "\n").replace("\r", "\n").partition("\n")
                if first.strip().removesuffix(":").strip().casefold() in {
                    "بدون تعديل النص",
                    "keep text unchanged",
                }:
                    values.update(text=body, mode="direct")
        return super().parse(values)

    @model_validator(mode="after")
    def supported_mode(self):
        if self.target == "excel" and self.mode != "smart":
            raise ValueError("direct Excel is not supported")
        return self


class WordPlan(StrictModel):
    ambiguous: bool = False
    missing_information: bool = False
    question: str = Field(default="", max_length=1000)
    document: WordDocument | None = None

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
