from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.builders.word_schema import WordDocument


@dataclass(frozen=True)
class WordFiles:
    docx: bytes
    pdf: bytes


class DocumentRenderer(ABC):
    @abstractmethod
    async def word_pdf(self, document: WordDocument, *, include_title: bool = True) -> WordFiles:
        """Render typed source data to Word/PDF. Never accept uploaded Office bytes."""
