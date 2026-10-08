"""Shared explicit document modes; never infer intent from customer prose."""

from typing import Annotated, Literal

from pydantic import Field, StringConstraints, ValidationError, field_validator, model_validator

from app.builders.schema import Document, Section, StrictModel
from app.services.base import ServiceError


class DocumentInputs(StrictModel):
    text: Annotated[str, StringConstraints(strip_whitespace=False)] = Field(
        min_length=1, max_length=12000
    )
    # Legacy programmatic callers retain smart behavior; Telegram requires an explicit choice.
    mode: Literal["direct", "smart"] = "smart"
    title: str | None = Field(default=None, min_length=1, max_length=200)

    @field_validator("text")
    @classmethod
    def printable_text(cls, value):
        if not value.strip() or any(
            (ord(char) < 32 and char not in "\t\r\n")
            or 0xD800 <= ord(char) <= 0xDFFF
            or ord(char) in {0xFFFE, 0xFFFF}
            for char in value
        ):
            raise ValueError("invalid document text")
        return value.replace("\r\n", "\n").replace("\r", "\n")

    @field_validator("title", mode="before")
    @classmethod
    def printable_title(cls, value):
        if isinstance(value, str) and any(c in value for c in "\r\n\u2028\u2029"):
            raise ValueError("title must be a single line")
        return cls.printable_text(value) if isinstance(value, str) else value

    @model_validator(mode="after")
    def explicit_title(self):
        if self.mode == "smart" and self.title is not None:
            raise ValueError("title belongs to direct mode")
        if self.mode == "direct" and self.text.count("\n") >= 10000:
            raise ValueError("too many document lines")
        return self

    def document(self):
        lines = self.text.split("\n")
        return Document(
            # Keep the strict AI document contract; builders hide this metadata-only fallback.
            title=self.title or "Document",
            sections=[Section(paragraphs=lines[i : i + 100]) for i in range(0, len(lines), 100)],
        )

    @classmethod
    def parse(cls, inputs):
        try:
            return cls.model_validate({k: v for k, v in inputs.items() if not k.startswith("__")})
        except ValidationError:
            raise ServiceError("input_invalid") from None
