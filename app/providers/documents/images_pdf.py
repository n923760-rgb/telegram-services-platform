import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from tempfile import TemporaryDirectory

from app.providers.documents.base import DocumentError
from app.providers.documents.execution import run_child, slot


class ImagePdfRenderer(ABC):
    @abstractmethod
    async def render(self, images: list[bytes], orientation: str) -> bytes: ...


class NativeImagePdf(ImagePdfRenderer):
    async def render(self, images, orientation):
        if (
            orientation not in {"auto", "portrait", "landscape"}
            or not 1 <= len(images) <= 5
            or any(
                not isinstance(data, bytes) or not 0 < len(data) <= 10 * 1024 * 1024
                for data in images
            )
            or sum(map(len, images)) > 20 * 1024 * 1024
        ):
            raise DocumentError("input_invalid")
        capacity = slot()
        try:
            await asyncio.wait_for(capacity.acquire(), timeout=5)
        except TimeoutError:
            raise DocumentError("document_render_busy", transient=True) from None
        try:
            with TemporaryDirectory(prefix="images-pdf-") as directory:
                root = Path(directory)
                for index, data in enumerate(images):
                    (root / f"{index}.image").write_bytes(data)
                target = root / "result.pdf"
                await run_child(
                    "app.providers.documents.images_pdf_runner",
                    [str(root), orientation, str(len(images))],
                    timeout=30,
                    unavailable_key="input_invalid",
                    timeout_key="document_render_timeout",
                )
                if not target.is_file() or not 0 < target.stat().st_size <= 10 * 1024 * 1024:
                    raise DocumentError("input_invalid")
                return target.read_bytes()
        finally:
            capacity.release()
