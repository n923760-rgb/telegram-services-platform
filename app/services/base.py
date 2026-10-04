import re
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class InputField(BaseModel):
    name: str
    kind: Literal["text", "image", "file", "audio", "form"] = "text"  # text/image/file/audio/form
    prompt_key: str
    required: bool = True
    choices: list[str] = []
    choice_keys: list[str] = []
    max_length: int = Field(default=12000, ge=1, le=12000)
    multiple: bool = False
    max_items: int = Field(default=5, ge=1, le=5)
    when: dict[str, list[str]] = {}
    fields: list["InputField"] = []

    @model_validator(mode="after")
    def valid(self):
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,40}", self.name):
            raise ValueError("invalid field name")
        if len(set(self.choices)) != len(self.choices):
            raise ValueError("duplicate choices")
        if self.multiple and self.kind not in {"image", "file", "audio"}:
            raise ValueError("multiple is only supported for uploads")
        if len(self.choices) != len(self.choice_keys):
            raise ValueError("choices require i18n keys")
        if self.kind == "form" and not self.fields:
            raise ValueError("form requires nested fields")
        return self


class InputSchema(BaseModel):
    fields: list[InputField]

    def conversation(self):
        result = []

        def flatten(fields, prefix="", inherited_when=None, required=True):
            for field in fields:
                name = prefix + field.name
                if field.kind == "form":
                    flatten(
                        field.fields,
                        name + ".",
                        {**(inherited_when or {}), **field.when},
                        required and field.required,
                    )
                else:
                    result.append(
                        field.model_copy(
                            update={
                                "name": name,
                                "when": {**(inherited_when or {}), **field.when},
                                "required": required and field.required,
                            }
                        )
                    )

        flatten(self.fields)
        return result

    @model_validator(mode="after")
    def valid_schema(self):
        fields = self.conversation()
        names = [field.name for field in fields]
        if not fields or len(names) != len(set(names)):
            raise ValueError("empty or duplicate fields")
        for index, field in enumerate(fields):
            if any(key not in names[:index] for key in field.when):
                raise ValueError("conditions must reference preceding fields")
        return self

    def validate_inputs(self, inputs):
        def known_fields(fields, values):
            if not isinstance(values, dict) or set(values) - {field.name for field in fields}:
                raise ServiceError("input_invalid")
            for field in fields:
                if field.kind == "form" and field.name in values:
                    known_fields(field.fields, values[field.name])

        if any(key.startswith("__") for key in inputs):
            raise ServiceError("invalid_request")
        known_fields(self.fields, inputs)
        for field in self.conversation():
            value = get_input(inputs, field.name)
            if not active_field(field, inputs):
                if value is not None:
                    raise ServiceError("invalid_request")
                continue
            if value is None:
                if field.required:
                    raise ServiceError("input_invalid")
                continue
            values = value if field.multiple else [value]
            if field.multiple and (
                not isinstance(values, list) or not 1 <= len(values) <= field.max_items
            ):
                raise ServiceError("input_invalid")
            for item in values:
                if not isinstance(item, str) or not item.strip() or len(item) > field.max_length:
                    raise ServiceError("input_invalid")
                if field.choices and item not in field.choices:
                    raise ServiceError("input_invalid")


def get_input(inputs, name):
    value = inputs
    for part in name.split("."):
        value = value.get(part) if isinstance(value, dict) else None
    return value


def set_input(inputs, name, value):
    cursor = inputs
    parts = name.split(".")
    for part in parts[:-1]:
        cursor = cursor.setdefault(part, {})
    cursor[parts[-1]] = value


def active_field(field, inputs):
    return all(get_input(inputs, name) in values for name, values in field.when.items())


class Artifact(BaseModel):
    key: str
    filename: str
    mime: str


class Result(BaseModel):
    text: str = ""
    artifacts: list[Artifact] = []
    preview: str = ""
    needs_confirmation: bool = False
    continuation: dict = {}
    cost_sar: Decimal = Decimal("0")

    @model_validator(mode="after")
    def valid_result(self):
        if not self.text and not self.artifacts and not self.needs_confirmation:
            raise ValueError("empty result")
        if self.needs_confirmation and not self.continuation:
            raise ValueError("missing continuation")
        if len(self.text) > 50000 or len(self.preview) > 3000:
            raise ValueError("oversized result")
        return self


class ServiceError(Exception):
    def __init__(self, key="service_failed", transient=False):
        self.key, self.transient = key, transient
        super().__init__(key)


class BaseService:
    version = "1"
    slug: str
    name_ar: str
    name_en: str
    description_ar: str
    price_sar: Decimal
    input_schema: InputSchema
    enabled_by_default = True
    requires_ai = False
    runtime: Any = None

    async def run(self, inputs: dict) -> Result:
        raise NotImplementedError
