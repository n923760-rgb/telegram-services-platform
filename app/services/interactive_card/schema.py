from typing import Literal

from pydantic import Field, HttpUrl, TypeAdapter, ValidationError, model_validator

from app.builders.schema import StrictModel
from app.services.base import ServiceError
from app.services.documents import DocumentInputs


class Inputs(StrictModel):
    language: Literal["ar", "en"]
    name: str = Field(min_length=1, max_length=48)
    subtitle: str | None = Field(default=None, max_length=60)
    links: str = Field(min_length=1, max_length=2400)

    @model_validator(mode="after")
    def valid_card(self):
        for value in (self.name, self.subtitle or ""):
            if value:
                DocumentInputs.printable_text(value)
            if any(c in value for c in "\n\r\u2028\u2029") or (value and not value.strip()):
                raise ValueError("single line required")
        self.entries()
        return self

    def entries(self):
        rows = self.links.splitlines()
        if not 1 <= len(rows) <= 6:
            raise ValueError("one to six links required")
        result = []
        for row in rows:
            label, separator, url = row.partition("|")
            label, url = label.strip(), url.strip()
            DocumentInputs.printable_text(label)
            if not separator or not 1 <= len(label) <= 48 or not 1 <= len(url) <= 300:
                raise ValueError("invalid link")
            if not url.startswith("https://") or "\\" in url:
                raise ValueError("full HTTPS URL required")
            parsed = TypeAdapter(HttpUrl).validate_python(url)
            if parsed.scheme != "https" or parsed.username or parsed.password:
                raise ValueError("HTTPS without credentials required")
            if any(c.isspace() or ord(c) < 32 for c in url) or any(
                v in url.lower() for v in ("%0a", "%0d")
            ):
                raise ValueError("invalid URL")
            result.append((label, url))
        return result

    @classmethod
    def parse(cls, inputs):
        try:
            return cls.model_validate(inputs)
        except (ValidationError, ValueError):
            raise ServiceError("input_invalid") from None
