import re
from typing import Literal

from pydantic import Field, HttpUrl, StrictInt, TypeAdapter, ValidationError, model_validator

from app.builders.schema import StrictModel
from app.core.i18n import tr
from app.services.base import ServiceError
from app.services.documents import DocumentInputs


class Inputs(StrictModel):
    mode: Literal["direct", "smart"] = "smart"
    language: Literal["ar", "en"]
    name: str = Field(min_length=1, max_length=48)
    subtitle: str | None = Field(default=None, max_length=60)
    profile: str = Field(default="", max_length=1000)
    links: str = Field(default="", max_length=2400)
    phone: str = Field(default="", max_length=32)

    @model_validator(mode="after")
    def valid_card(self):
        if self.profile:
            DocumentInputs.printable_text(self.profile)
        for value in (self.name, self.subtitle or ""):
            if value:
                DocumentInputs.printable_text(value)
            if any(c in value for c in "\n\r\u2028\u2029") or (value and not value.strip()):
                raise ValueError("single line required")
        self.entries()
        return self

    def entries(self):
        rows = self.links.splitlines()
        if len(rows) > 6:
            raise ValueError("at most six links required")
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
        if self.phone:
            url = whatsapp_url(self.phone)
            if url not in [target for _, target in result]:
                result.append((tr("card_whatsapp", self.language), url))
        if not 1 <= len(result) <= 6:
            raise ValueError("one to six total buttons required")
        return result

    @classmethod
    def parse(cls, inputs):
        try:
            return cls.model_validate(inputs)
        except (ValidationError, ValueError):
            raise ServiceError("input_invalid") from None


def whatsapp_url(value):
    """Normalize explicit international numbers or documented Saudi 05 mobiles."""
    value = value.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789"))
    if not re.fullmatch(r"[+0-9 ()-]+", value):
        raise ValueError("invalid phone characters")
    number = re.sub(r"[ ()-]", "", value)
    if re.fullmatch(r"05[0-9]{8}", number):
        number = "966" + number[1:]
    elif number.startswith("+"):
        number = number[1:]
    elif number.startswith("00"):
        number = number[2:]
    elif not re.fullmatch(r"9665[0-9]{8}", number):
        raise ValueError("include country code")
    if not re.fullmatch(r"[1-9][0-9]{7,14}", number):
        raise ValueError("invalid international phone length")
    if number.startswith("966") and not re.fullmatch(r"9665[0-9]{8}", number):
        raise ValueError("Saudi mobile must use 05 followed by eight digits")
    return "https://wa.me/" + number


class Presentation(StrictModel):
    palette: Literal["navy", "emerald", "graphite"]
    tagline: str = Field(default="", max_length=60)
    order: list[StrictInt] = Field(min_length=1, max_length=6)


def presentation_schema(values):
    count = len(values.entries())

    class GroundedPresentation(Presentation):
        @model_validator(mode="after")
        def preserve_source(self):
            if sorted(self.order) != list(range(count)):
                raise ValueError("every original link must appear exactly once")
            if self.tagline and (
                self.tagline not in values.profile
                or any(c in self.tagline for c in "\n\r\u2028\u2029")
            ):
                raise ValueError("tagline must be an exact single-line source excerpt")
            return self

    return GroundedPresentation
