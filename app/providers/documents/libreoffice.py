import asyncio
import os
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from pypdf import PdfReader

from app.builders.quality import validate
from app.builders.word import build
from app.builders.word_schema import WordDocument
from app.providers.documents.base import DocumentError
from app.providers.documents.execution import run_child, slot
from app.providers.documents.rendering import DocumentRenderer, WordFiles

MAX_BYTES = 10 * 1024 * 1024


class LibreOfficeDocuments(DocumentRenderer):
    """Render builder-owned DOCX only. All profile/output files are request-local."""

    # Use the supported launcher: it handles native cold-profile initialization/restarts.
    def __init__(self, *, binary: Path = Path("/usr/bin/libreoffice")):
        self.binary = binary

    async def word_pdf(self, document: WordDocument, *, include_title=True) -> WordFiles:
        if not isinstance(document, WordDocument):
            raise DocumentError("input_invalid")
        if os.name != "posix" or not self.binary.is_file():
            raise DocumentError("document_render_unavailable")
        semaphore = slot()
        try:
            await asyncio.wait_for(semaphore.acquire(), timeout=5)
        except TimeoutError:
            raise DocumentError("document_render_busy", transient=True) from None
        try:
            docx = await asyncio.to_thread(
                build,
                document,
                include_title=include_title,
                professional_template=True,
                format_dates=True,
            )
            pdf = await self._convert(docx)
            return WordFiles(docx, pdf)
        finally:
            semaphore.release()

    async def _convert(self, docx):
        with TemporaryDirectory(prefix="document-render-") as directory:
            root = Path(directory)
            source, output, profile = root / "source.docx", root / "output", root / "profile"
            output.mkdir()
            (profile / "user").mkdir(parents=True)
            (profile / "user/registrymodifications.xcu").write_text(
                '<oor:items xmlns:oor="http://openoffice.org/2001/registry">'
                '<item oor:path="/org.openoffice.Office.Common/Security/Scripting">'
                '<prop oor:name="MacroSecurityLevel" oor:op="fuse"><value>3</value></prop>'
                "</item></oor:items>"
            )
            source.write_bytes(docx)
            await run_child(
                "app.providers.documents.render_runner",
                [str(self.binary), str(source), str(output), str(profile)],
                timeout=90,
                unavailable_key="document_render_unavailable",
                timeout_key="document_render_timeout",
            )
            result = output / "source.pdf"
            if not result.is_file():
                raise DocumentError("document_render_invalid")
            if result.stat().st_size > MAX_BYTES:
                raise DocumentError("document_render_limit")
            try:
                pdf = validate(result.read_bytes(), "pdf")
                if len(PdfReader(BytesIO(pdf), strict=True).pages) > 50:
                    raise DocumentError("document_render_limit")
                return pdf
            except ValueError:
                raise DocumentError("document_render_invalid") from None
