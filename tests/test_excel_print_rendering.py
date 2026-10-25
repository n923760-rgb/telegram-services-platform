"""Actual Calc PDF glyph sizes, independent of stored XLSX font/style assertions."""

import os
import signal
import subprocess

import pdfplumber
import pytest

from app.builders import excel
from tests.excel_print_fixtures import wide_table


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize("arabic", [False, True])
def test_wide_print_does_not_reduce_body_to_tiny_text(tmp_path, arabic):
    source = tmp_path / "source.xlsx"
    source.write_bytes(excel.build(wide_table(arabic=arabic)))
    profile = tmp_path / "profile"
    (profile / "user").mkdir(parents=True)
    (profile / "user/registrymodifications.xcu").write_text(
        '<oor:items xmlns:oor="http://openoffice.org/2001/registry">'
        '<item oor:path="/org.openoffice.Office.Common/Security/Scripting">'
        '<prop oor:name="MacroSecurityLevel" oor:op="fuse"><value>3</value></prop>'
        "</item></oor:items>"
    )
    binary = os.getenv("LOCAL_EXCEL_PDF_TEST_BINARY", "/usr/bin/libreoffice")
    process = subprocess.Popen(
        [
            binary,
            "--headless",
            "--nologo",
            "--nodefault",
            "--norestore",
            "--nolockcheck",
            "--unaccept=all",
            "-env:UserInstallation=" + profile.as_uri(),
            "--convert-to",
            "pdf:calc_pdf_Export",
            "--outdir",
            str(tmp_path),
            str(source),
        ],
        env={
            "PATH": "/usr/bin:/bin",
            "HOME": str(tmp_path),
            "TMPDIR": str(tmp_path),
            "LANG": "C.UTF-8",
            "OMP_THREAD_LIMIT": "1",
        },
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        assert process.wait(timeout=90) == 0
    finally:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
    with pdfplumber.open(tmp_path / "source.pdf") as pdf:
        assert 2 <= len(pdf.pages) <= 6
        text = "\n".join(page.extract_text() for page in pdf.pages)
        for column in range(5):
            for row in range(2):
                token = f"FIELD{column}ROW{row}"
                assert text.count(token) == 1
                words = [
                    word
                    for page in pdf.pages
                    for word in page.extract_words(extra_attrs=["size"])
                    if word["text"] == token
                ]
                assert len(words) == 1 and words[0]["size"] >= 10.5
        assert text.count("00123") == text.count("00124") == 1
        title_chars = [c for c in pdf.pages[0].chars if c["size"] > 17]
        assert title_chars and all(
            0 <= c["x0"] < c["x1"] <= pdf.pages[0].width for c in title_chars
        )
        for page in pdf.pages:
            # Calc emits clipped copies of the merged title outside subsequent
            # horizontal panes. Check table glyphs here; title is checked above.
            assert all(
                0 <= c["x0"] < c["x1"] <= page.width and 0 <= c["top"] < c["bottom"] <= page.height
                for c in page.chars
                if c["size"] < 17
            )
            # Native row headings retain the same record positions on each pane.
            assert {"4", "5"} <= {word["text"] for word in page.extract_words()}
