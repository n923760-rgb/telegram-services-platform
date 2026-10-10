import asyncio
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from pydantic import ValidationError

from app.providers.documents.base import DocumentError
from app.providers.documents.execution import run_child, slot
from app.providers.tables.base import Extraction, TableExtractor

MAX_BYTES = 10 * 1024 * 1024
MAX_OUTPUT = 512 * 1024
ERRORS = {
    "file_invalid",
    "pdf_image_content",
    "pdf_tables_limit",
    "pdf_tables_missing",
    "pdf_tables_quality",
}


class CamelotTables(TableExtractor):
    async def extract(self, data, method):
        if not data or len(data) > MAX_BYTES or method not in {"lattice", "stream"}:
            raise DocumentError("input_invalid")
        if os.name != "posix":
            raise DocumentError("pdf_tables_unavailable")
        semaphore = slot()
        try:
            await asyncio.wait_for(semaphore.acquire(), timeout=5)
        except TimeoutError:
            raise DocumentError("pdf_tables_busy", transient=True) from None
        try:
            with TemporaryDirectory(prefix="document-tables-") as directory:
                root = Path(directory)
                source, target = root / "input.pdf", root / "output.json"
                source.write_bytes(data)
                await run_child(
                    "app.providers.tables.runner",
                    [str(source), str(target), method],
                    timeout=45,
                    unavailable_key="pdf_tables_unavailable",
                    timeout_key="pdf_tables_timeout",
                )
                if not target.is_file() or target.stat().st_size > MAX_OUTPUT:
                    raise DocumentError("pdf_tables_limit")
                try:
                    result = json.loads(target.read_bytes())
                    if (
                        isinstance(result, dict)
                        and set(result) == {"error"}
                        and isinstance(result["error"], str)
                        and result["error"] in ERRORS
                    ):
                        raise DocumentError(result["error"])
                    return Extraction.model_validate(result)
                except (ValueError, ValidationError):
                    raise DocumentError("pdf_tables_quality") from None
        finally:
            semaphore.release()
