from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class Usage:
    input_tokens: int
    output_tokens: int
    cost_sar: Decimal
    provider: str = "unknown"
    model: str = "unknown"
    rates: dict = field(default_factory=dict)


@dataclass(frozen=True)
class AIResponse:
    content: str
    usage: Usage


class AIProvider(ABC):
    @abstractmethod
    def upper_bound(self, schema: dict, text: str, prompt: str, images: list[bytes]) -> Decimal: ...
    @abstractmethod
    async def extract_from_text(self, schema: dict, text: str, prompt: str) -> AIResponse: ...
    @abstractmethod
    async def extract_from_image(
        self, schema: dict, text: str, prompt: str, images: list[bytes]
    ) -> AIResponse: ...
    @abstractmethod
    async def translate(self, schema: dict, text: str, language: str, style: str) -> AIResponse: ...
    async def transcribe(self, audio: bytes) -> AIResponse:
        from app.services.base import ServiceError

        raise ServiceError("unsupported")

    async def balance_sar(self) -> Decimal | None:
        return None  # Never assume a provider's prepaid balance.
