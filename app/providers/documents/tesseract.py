import asyncio
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from app.files.validation import image
from app.providers.documents.base import DocumentError, DocumentProcessor, Language, Recognition
from app.providers.documents.execution import run_child, slot
from app.providers.documents.tsv import MAX_OUTPUT, MAX_TEXT, parse

LANGUAGES = {"ar": "ara", "en": "eng", "mixed": "ara+eng"}


class TesseractDocuments(DocumentProcessor):
    """One native subprocess per worker at a time; all request files are temporary."""

    def __init__(self, *, tessdata_dir: Path | None = None):
        self.tessdata_dir = tessdata_dir

    async def recognize(self, images: list[bytes], language: Language) -> Recognition:
        if language not in LANGUAGES or not 1 <= len(images) <= 5:
            raise DocumentError("input_invalid")
        if sum(map(len, images)) > 20 * 1024 * 1024:
            raise DocumentError("input_invalid")
        semaphore = slot()
        try:
            await asyncio.wait_for(semaphore.acquire(), timeout=5)
        except TimeoutError:
            raise DocumentError("local_ocr_busy", transient=True) from None
        try:
            results = []
            for data in images:
                # Reuse intake limits/EXIF correction; decoding does not block the event loop.
                normalized = await asyncio.to_thread(image, data, 10 * 1024 * 1024)
                results.append(await self._recognize(normalized, LANGUAGES[language]))
                if sum(len(result.text) for result in results) + 2 * (len(results) - 1) > MAX_TEXT:
                    raise DocumentError("local_ocr_limit")
            return Recognition(
                "\n\n".join(result.text for result in results),
                min(result.confidence for result in results),
            )
        finally:
            semaphore.release()

    async def _recognize(self, data, language):
        if os.name != "posix" or not Path("/usr/bin/tesseract").is_file():
            raise DocumentError("local_ocr_unavailable")
        with TemporaryDirectory(prefix="document-ocr-") as directory:
            source, target = Path(directory) / "input.jpg", Path(directory) / "output"
            source.write_bytes(data)
            args = [str(source), str(target), language]
            if self.tessdata_dir is not None:
                args.append(str(self.tessdata_dir))
            await run_child(
                "app.providers.documents.runner",
                args,
                timeout=25,
                unavailable_key="local_ocr_unavailable",
                timeout_key="local_ocr_timeout",
            )
            output = target.with_suffix(".tsv")
            if not output.is_file() or output.stat().st_size > MAX_OUTPUT:
                raise DocumentError("local_ocr_limit")
            return parse(output.read_bytes())
