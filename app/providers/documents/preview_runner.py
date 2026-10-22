"""Fixed PDF first-page rasterization. Process limits are not a sandbox."""

import json
import math
import os
import resource
import sys
from pathlib import Path


def main():
    source, output = map(Path, sys.argv[1:])
    os.environ.clear()
    os.environ.update({"LANG": "C.UTF-8", "OMP_NUM_THREADS": "1"})
    for kind, value in (
        (resource.RLIMIT_AS, 512 * 1024 * 1024),
        (resource.RLIMIT_CPU, 15),
        (resource.RLIMIT_FSIZE, 3 * 1024 * 1024),
        (resource.RLIMIT_CORE, 0),
    ):
        resource.setrlimit(kind, (value, value))
    import pypdfium2 as pdfium

    with pdfium.PdfDocument(source) as pdf:
        if not 1 <= len(pdf) <= 50:
            raise ValueError("page limit")
        page = pdf[0]
        try:
            width, height = page.get_size()
            if not all(math.isfinite(v) and 0 < v <= 20000 for v in (width, height)):
                raise ValueError("page dimensions")
            scale = min(959 / width, 1439 / height)
            bitmap = page.render(scale=scale)
            try:
                bitmap.to_pil().convert("RGB").save(output, format="PNG")
            finally:
                bitmap.close()
        finally:
            page.close()
        output.with_name("pages.json").write_text(json.dumps(len(pdf)))


if __name__ == "__main__":
    main()
