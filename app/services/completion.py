"""Bounded data-only handoff from a trusted plugin, never a publication consent."""

import hashlib
import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Completion(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    kind: str = Field(pattern=r"^[a-z][a-z0-9_]{0,63}$")
    payload: dict[str, Any]

    @field_validator("payload", mode="before")
    @classmethod
    def bounded_json(cls, value):
        nodes = 0

        def visit(item, depth=0):
            nonlocal nodes
            nodes += 1
            if nodes > 4096 or depth > 8:
                raise ValueError("completion payload too complex")
            if type(item) is dict:
                for key, child in item.items():
                    if type(key) is not str or "\x00" in key:
                        raise ValueError("invalid completion key")
                    visit(child, depth + 1)
            elif type(item) is list:
                for child in item:
                    visit(child, depth + 1)
            elif type(item) is str:
                if "\x00" in item:
                    raise ValueError("invalid completion text")
            elif item is not None and type(item) not in {int, float, bool}:
                raise ValueError("completion requires plain JSON")

        if type(value) is not dict:
            raise ValueError("completion requires an object")
        visit(value)
        try:
            encoded = json.dumps(
                value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")
            ).encode("utf-8")
        except (ValueError, UnicodeError, OverflowError):
            raise ValueError("invalid completion JSON") from None
        if len(encoded) > 32768:
            raise ValueError("completion payload too large")
        return json.loads(encoded)  # Detach mutable plugin-owned objects.

    def digest(self):
        # Revalidate even an already constructed/mutated model at the trust boundary.
        checked = type(self).model_validate(self.model_dump())
        return hashlib.sha256(
            json.dumps(
                checked.model_dump(), sort_keys=True, ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()
