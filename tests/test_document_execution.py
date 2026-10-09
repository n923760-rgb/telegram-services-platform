import asyncio
from io import BytesIO
from pathlib import Path

import pytest
from pypdf import PdfWriter

from app.providers.documents import libreoffice, render_runner, tesseract
from app.providers.documents.base import DocumentError, Recognition
from tests.ocr_fixtures import printed
from tests.word_pdf_fixtures import document, renderer


def pdf(pages=1):
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(595, 842)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


@pytest.mark.parametrize(
    "failure,key",
    [
        ("missing", "document_render_invalid"),
        ("corrupt", "document_render_invalid"),
        ("pages", "document_render_limit"),
        ("bytes", "document_render_limit"),
        ("timeout", "document_render_timeout"),
    ],
)
async def test_export_rejects_bad_output_and_cleans_source_profile_and_files(
    monkeypatch, failure, key
):
    directories = []

    async def export(module, args, **kwargs):
        directories.append(Path(args[1]).parent)
        assert Path(args[3], "user/registrymodifications.xcu").is_file()
        if failure == "timeout":
            raise DocumentError("document_render_timeout")
        if failure != "missing":
            Path(args[2], "source.pdf").write_bytes(
                b"broken" if failure == "corrupt" else pdf(51 if failure == "pages" else 1)
            )

    monkeypatch.setattr(libreoffice, "run_child", export)
    if failure == "bytes":
        monkeypatch.setattr(libreoffice, "MAX_BYTES", 20)
    with pytest.raises(DocumentError, match=key):
        await renderer()._convert(b"generated fixture")
    assert not directories[0].exists()


async def test_uploaded_bytes_are_rejected_at_public_render_contract():
    with pytest.raises(DocumentError, match="input_invalid"):
        await renderer().word_pdf(b"uploaded DOCX")


async def test_renderer_and_ocr_share_native_capacity(monkeypatch):
    active, maximum = 0, 0

    async def work():
        nonlocal active, maximum
        active += 1
        maximum = max(maximum, active)
        await asyncio.sleep(0.02)
        active -= 1

    async def convert(self, data):
        await work()
        return pdf()

    async def recognize(self, data, language):
        await work()
        return Recognition("Invoice", 0.99)

    monkeypatch.setattr(libreoffice.LibreOfficeDocuments, "_convert", convert)
    monkeypatch.setattr(tesseract.TesseractDocuments, "_recognize", recognize)
    await asyncio.gather(
        renderer().word_pdf(document()), tesseract.TesseractDocuments().recognize([printed()], "en")
    )
    assert maximum == 1


async def test_renderer_queue_timeout_is_transient(monkeypatch):
    class Busy:
        async def acquire(self):
            raise TimeoutError

        def release(self):
            raise AssertionError("unacquired slot released")

    monkeypatch.setattr(libreoffice, "slot", lambda: Busy())
    with pytest.raises(DocumentError) as error:
        await renderer().word_pdf(document())
    assert error.value.key == "document_render_busy" and error.value.transient


def test_export_launcher_uses_private_profile_limits_no_listener_or_credentials(monkeypatch):
    limits, commands = [], []
    monkeypatch.setattr(
        render_runner.sys,
        "argv",
        [
            "runner",
            "/usr/lib/libreoffice/program/soffice.bin",
            "/tmp/source.docx",
            "/tmp/output",
            "/tmp/profile",
        ],
    )
    monkeypatch.setattr(
        render_runner.resource, "setrlimit", lambda key, values: limits.append((key, values))
    )
    monkeypatch.setattr(
        render_runner.os, "execve", lambda binary, args, env: commands.append((binary, args, env))
    )
    render_runner.main()
    assert (render_runner.resource.RLIMIT_AS, (1024 * 1024 * 1024,) * 2) in limits
    assert (render_runner.resource.RLIMIT_CPU, (60, 60)) in limits
    binary, args, env = commands[0]
    assert "--headless" in args and "--unaccept=all" in args
    assert "-env:UserInstallation=file:///tmp/profile" in args
    assert "pdf:writer_pdf_Export" in args and not any(arg.startswith("--accept=") for arg in args)
    assert "BOT_TOKEN" not in env and "DATABASE_URL" not in env
    assert env["HOME"] == env["TMPDIR"] == "/tmp"
