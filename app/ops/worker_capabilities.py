"""Fixed local presence/import probes; no customer content, AI calls or quality claims."""

import asyncio
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from app.builders.pdf import _FONT_FILES, _first_font


async def command(*args, capture=False):
    with TemporaryDirectory(prefix="worker-probe-") as directory:
        process = None
        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                cwd=directory,
                env={"PATH": "/usr/local/bin:/usr/bin:/bin", "LANG": "C.UTF-8", "HOME": directory},
                stdout=asyncio.subprocess.PIPE if capture else asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            output, _ = await asyncio.wait_for(process.communicate(), timeout=10)
            return process.returncode == 0, output or b""
        except (OSError, TimeoutError):
            return False, b""
        finally:
            if process is not None and process.returncode is None:
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
                await process.wait()


async def probe_worker():
    # Probe sequentially to avoid several heavy import processes on a small VPS.
    results = {"pdf_font": _first_font(_FONT_FILES["DejaVu"]) is not None}
    binary = Path("/usr/bin/libreoffice")
    results["office_export"] = (
        binary.is_file()
        and (await command(str(binary), "--headless", "--version"))[0]
        and results["pdf_font"]
    )
    for key, imports in (
        ("pdf_tables", "import camelot, cv2, numpy, pypdfium2"),
        ("document_images", "import cv2, numpy; from PIL import Image"),
        ("image_pdf", "import reportlab, pypdf; from PIL import Image"),
        ("pdf_previews", "import pypdfium2"),
    ):
        results[key] = (await command(sys.executable, "-I", "-c", imports))[0]
    binary = Path("/usr/bin/tesseract")
    ok, output = (
        await command(str(binary), "--list-langs", capture=True)
        if binary.is_file()
        else (False, b"")
    )
    results["native_ocr"] = (
        ok and len(output) <= 65536 and {b"ara", b"eng"} <= set(output.splitlines())
    )
    return results
