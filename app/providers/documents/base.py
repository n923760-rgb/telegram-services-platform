from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

Language = Literal["ar", "en", "mixed"]


@dataclass(frozen=True)
class Recognition:
    text: str
    confidence: float


class DocumentError(Exception):
    def __init__(self, key, *, transient=False):
        self.key, self.transient = key, transient
        super().__init__(key)


class DocumentProcessor(ABC):
    @abstractmethod
    async def recognize(self, images: list[bytes], language: Language) -> Recognition:
        """Read bounded printed images, in order, without translation or AI fallback."""
