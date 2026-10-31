"""Literal customer intake; AI controls composition, never contact destinations."""

from typing import Literal

from pydantic import Field, ValidationError, field_validator, model_validator

from app.builders.schema import StrictModel
from app.core.i18n import tr
from app.publications.design import Action, Profile, Section, https_url, literal_text
from app.services.base import ServiceError
from app.services.interactive_card.schema import link_platform, whatsapp_url


class Inputs(StrictModel):
    language: Literal["ar", "en"]
    name: str = Field(min_length=1, max_length=64)
    role: str = Field(min_length=1, max_length=96)
    intro: str = Field(min_length=1, max_length=480)
    phone: str = Field(default="", max_length=32)
    links: str = Field(default="", max_length=2100)
    sections: str = Field(default="", max_length=5000)
    brief: str = Field(min_length=1, max_length=1600)
    qr: Literal["embedded", "separate"] = "embedded"

    @field_validator("name", "role")
    @classmethod
    def identity(cls, value):
        if not value.strip():
            raise ValueError("identity required")
        return literal_text(value)

    @field_validator("intro", "brief")
    @classmethod
    def readable(cls, value):
        if not value.strip():
            raise ValueError("source required")
        return literal_text(value, multiline=True)

    def profile(self):
        actions = []
        rows = self.links.splitlines()
        if len(rows) > 6:
            raise ValueError("at most six links")
        for row in rows:
            if not row.strip():
                raise ValueError("empty link row")
            label, separator, url = row.partition("|")
            if not separator:
                url = row.strip()
                https_url(url)
                label = tr("card_platform_" + link_platform(url), self.language)
            actions.append(Action(label=label.strip(), url=url.strip()))
        if self.phone:
            target = whatsapp_url(self.phone)
            if target not in [a.url for a in actions]:
                actions.append(Action(label=tr("card_whatsapp", self.language), url=target))
        sections = []
        rows = self.sections.splitlines()
        if len(rows) > 6:
            raise ValueError("at most six sections")
        for row in rows:
            title, separator, body = row.partition("|")
            if not separator or not title.strip() or not body.strip():
                raise ValueError("each section needs title and body")
            sections.append(Section(title=title.strip(), body=body.strip()))
        return Profile(
            language=self.language,
            name=self.name,
            role=self.role,
            intro=self.intro,
            actions=actions,
            sections=sections,
        )

    @model_validator(mode="after")
    def bounded_profile(self):
        self.profile()
        return self

    @classmethod
    def parse(cls, values):
        try:
            return cls.model_validate(values)
        except (ValidationError, ValueError):
            raise ServiceError("input_invalid") from None
