"""Bounded first-page images from builder-owned PDF, using the existing native slot."""

import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image

from app.providers.documents.base import DocumentError
from app.providers.documents.execution import run_child, slot


@dataclass(frozen=True)
class PagePreview:
    png: bytes
    pages: int


class PreviewRenderer(ABC):
    @abstractmethod
    async def first_page(self, pdf: bytes) -> PagePreview: ...


class PdfPreviews(PreviewRenderer):
    async def first_page(self, pdf):
        if not isinstance(pdf, bytes) or not pdf or len(pdf) > 10 * 1024 * 1024:
            raise DocumentError("document_preview_invalid")
        semaphore = slot()
        try:
            await asyncio.wait_for(semaphore.acquire(), timeout=5)
        except TimeoutError:
            raise DocumentError("document_render_busy", transient=True) from None
        try:
            with TemporaryDirectory(prefix="document-preview-") as directory:
                root = Path(directory)
                source, target = root / "source.pdf", root / "page.png"
                source.write_bytes(pdf)
                await run_child(
                    "app.providers.documents.preview_runner",
                    [str(source), str(target)],
                    timeout=20,
                    unavailable_key="document_preview_invalid",
                    timeout_key="document_preview_timeout",
                )
                if not target.is_file() or not 0 < target.stat().st_size <= 3 * 1024 * 1024:
                    raise DocumentError("document_preview_invalid")
                try:
                    data = target.read_bytes()
                    with Image.open(BytesIO(data)) as image:
                        if image.format != "PNG" or not (
                            1 <= image.width <= 960 and 1 <= image.height <= 1440
                        ):
                            raise ValueError("invalid preview")
                        image.verify()
                    pages = json.loads((root / "pages.json").read_text())
                    if type(pages) is not int or not 1 <= pages <= 50:
                        raise ValueError("invalid page count")
                    return PagePreview(data, pages)
                except (OSError, ValueError):
                    raise DocumentError("document_preview_invalid") from None
        finally:
            semaphore.release()
