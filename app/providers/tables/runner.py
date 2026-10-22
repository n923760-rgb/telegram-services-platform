"""Private bounded table-extraction child. Resource limits are not a sandbox."""

import json
import os
import resource
import sys
from pathlib import Path


def extract(source, method):
    from io import BytesIO

    from pypdf import PdfReader

    from app.files.pdf_content import has_image_content
    from app.files.pdf_text import extract_page_text
    from app.providers.tables.base import Extraction
    from app.services.base import ServiceError

    data = source.read_bytes()
    if not data or len(data) > 10 * 1024 * 1024:
        raise ServiceError("pdf_tables_limit")
    try:
        reader = PdfReader(BytesIO(data), strict=True)
        count = reader.trailer["/Root"]["/Pages"].get("/Count", 0)
        if reader.is_encrypted:
            raise ServiceError("file_invalid")
        if not isinstance(count, int) or not 1 <= count <= 5 or not 1 <= len(reader.pages) <= 5:
            raise ServiceError("pdf_tables_limit")
        text_size = 0
        for page in reader.pages:
            if has_image_content(page, reader):
                raise ServiceError("pdf_image_content")
            text = extract_page_text(page, limit=50000 - text_size)
            text_size += len(text)
            if not text:
                raise ServiceError("pdf_tables_missing")
    except ServiceError as error:
        if error.key == "pdf_text_too_long":
            raise ServiceError("pdf_tables_limit") from None
        raise
    except Exception:
        raise ServiceError("file_invalid") from None
    # Lazy import: no native SDK/model is loaded in the Telegram/API/job process.
    import camelot

    tables = []
    for number in range(1, len(reader.pages) + 1):
        found = camelot.read_pdf(
            str(source), pages=str(number), flavor=method, suppress_stdout=True
        )
        if not found:
            raise ServiceError("pdf_tables_missing")
        for table in found:
            tables.append(
                {
                    "page": number,
                    "rows": table.df.values.tolist(),
                    "accuracy": round(float(table.accuracy), 6),
                    "whitespace": round(float(table.whitespace), 6),
                }
            )
            if len(tables) > 5:
                raise ServiceError("pdf_tables_limit")
    try:
        return Extraction.model_validate({"pages": len(reader.pages), "tables": tables}).model_dump(
            mode="json"
        )
    except ValueError:
        raise ServiceError("pdf_tables_quality") from None


def main():
    source, target, method = sys.argv[1:]
    if method not in {"lattice", "stream"}:
        raise ValueError("invalid internal method")
    os.environ.clear()
    os.environ.update(
        {
            "PATH": "/usr/bin:/bin",
            "LANG": "C.UTF-8",
            "OPENBLAS_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "OMP_THREAD_LIMIT": "1",
            "MKL_NUM_THREADS": "1",
        }
    )
    for limit, value in (
        (resource.RLIMIT_AS, 1024 * 1024 * 1024),
        (resource.RLIMIT_CPU, 35),
        (resource.RLIMIT_FSIZE, 512 * 1024),
        (resource.RLIMIT_CORE, 0),
    ):
        resource.setrlimit(limit, (value, value))
    from app.services.base import ServiceError

    try:
        result = extract(Path(source), method)
    except ServiceError as error:
        result = {"error": error.key}
    except Exception:
        result = {"error": "pdf_tables_quality"}
    Path(target).write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
