"""Page-level PDF operations; never OCR, rewrite text or rasterize source pages."""

from io import BytesIO

from pypdf import PdfReader, PdfWriter

from app.builders.quality import validate
from app.files.pdf_selection import page_selection


class PdfToolError(ValueError):
    def __init__(self, key="file_invalid"):
        self.key = key
        super().__init__(key)


def build(files: list[bytes], *, operation: str, pages: str | None = None) -> bytes:
    if (
        operation not in {"merge", "extract"}
        or not 1 <= len(files) <= 5
        or (operation == "merge" and (len(files) < 2 or pages is not None))
        or (operation == "extract" and (len(files) != 1 or pages is None))
    ):
        raise PdfToolError("input_invalid")
    if any(not data or len(data) > 10 * 1024 * 1024 for data in files):
        raise PdfToolError()
    if sum(map(len, files)) > 20 * 1024 * 1024:
        raise PdfToolError("pdf_tools_limit")
    try:
        readers = []
        total = 0
        for data in files:
            if not data.startswith(b"%PDF-"):
                raise PdfToolError()
            reader = PdfReader(BytesIO(data), strict=True)
            if reader.is_encrypted:
                raise PdfToolError()
            count = reader.trailer["/Root"]["/Pages"].get("/Count", 0)
            if not isinstance(count, int) or not 1 <= count <= 200:
                raise PdfToolError("pdf_tools_limit")
            total += len(reader.pages)
            if not 1 <= len(reader.pages) <= 200 or total > 200:
                raise PdfToolError("pdf_tools_limit")
            # Page-copying is not a form/signature editor. Reject rather than
            # silently dropping field values or implying preserved signatures.
            root = reader.trailer["/Root"]
            if root.get("/AcroForm") or root.get("/Perms"):
                raise PdfToolError("pdf_tools_form")
            readers.append(reader)
        writer = PdfWriter()
        if operation == "merge":
            for reader in readers:
                for page in reader.pages:
                    writer.add_page(page)
        else:
            try:
                selected = page_selection(pages)
            except ValueError:
                raise PdfToolError("pdf_page_selection") from None
            if max(selected) > len(readers[0].pages):
                raise PdfToolError("pdf_page_selection")
            for number in selected:
                writer.add_page(readers[0].pages[number - 1])
        buffer = BytesIO()
        writer.write(buffer)
        return validate(buffer.getvalue(), "pdf")
    except PdfToolError:
        raise
    except Exception:
        raise PdfToolError() from None
