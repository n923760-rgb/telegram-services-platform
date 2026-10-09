import asyncio
import csv
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.providers.documents import runner, tesseract
from app.providers.documents.base import DocumentError
from app.providers.documents.tsv import parse
from app.services.base import ServiceError
from tests.ocr_fixtures import printed, processor


def tsv(words):
    output = StringIO()
    writer = csv.writer(output, delimiter="\t", quoting=csv.QUOTE_NONE, quotechar=None)
    writer.writerow(["level", "page_num", "block_num", "par_num", "line_num", "conf", "text"])
    for word, confidence, line in words:
        writer.writerow([5, 1, 1, 1, line, confidence, word])
    return output.getvalue().encode()


@pytest.mark.parametrize(
    "language,text",
    [
        ("en", "Invoice 00123\nTotal 125.50\nDate 2026-10-09"),
        ("ar", "مرحبا بكم\nخدمة قراءة النصوص"),
        ("mixed", "مرحبا بكم\nInvoice 00123"),
    ],
)
async def test_actual_native_ocr_reads_printed_fixture_without_translation(language, text):
    result = await processor().recognize([printed(text)], language)
    assert result.text.replace("\u200f", "") == text
    assert 0.7 <= result.confidence <= 1


async def test_actual_native_multi_image_keeps_order_and_rejects_no_text():
    result = await processor().recognize([printed("Invoice 00123"), printed("Invoice 00999")], "en")
    assert result.text == "Invoice 00123\n\nInvoice 00999"
    # A contrast-bearing shape passes image validation but contains no printed text.
    from io import BytesIO

    from PIL import Image, ImageDraw

    shape = Image.new("RGB", (400, 200), "white")
    ImageDraw.Draw(shape).rectangle((20, 20, 90, 180), fill="black")
    buffer = BytesIO()
    shape.save(buffer, "PNG")
    with pytest.raises(DocumentError, match="ocr_unclear"):
        await processor().recognize([buffer.getvalue()], "en")


@pytest.mark.parametrize("data", [b"broken", b"x" * (10 * 1024 * 1024 + 1)])
async def test_invalid_image_rejected_without_launch(monkeypatch, data):
    async def no_launch(*args, **kwargs):
        raise AssertionError("invalid image reached native engine")

    monkeypatch.setattr(tesseract.asyncio, "create_subprocess_exec", no_launch)
    with pytest.raises(ServiceError, match="file_invalid"):
        await processor().recognize([data], "en")


@pytest.mark.parametrize(
    "data",
    [
        b"broken",
        b"\xff",
        tsv([]),
        tsv([("Invoice", "nan", 1)]),
        tsv([("Invoice", -1, 1)]),
        tsv([("Invoice", 101, 1)]),
        tsv([("Invoice", 69, 1)]),
        tsv([("00123", 84.99, 1), ("Invoice", 99, 1)]),
        tsv([("مرحبا", 99, 0)]),
    ],
)
def test_tsv_rejects_malformed_empty_low_confidence_and_uncertain_numbers(data):
    with pytest.raises(DocumentError, match="ocr_unclear"):
        parse(data)


def test_tsv_keeps_numbers_without_normalization_and_line_order():
    result = parse(tsv([("00123", 99, 1), ("١٢٥٫٥٠", 99, 1), ("2026-10-09", 99, 2)]))
    assert result.text == "00123 ١٢٥٫٥٠\n2026-10-09"


def test_tsv_preserves_recognized_quotes_as_content():
    assert parse(tsv([('"Approved"', 99, 1)])).text == '"Approved"'


@pytest.mark.parametrize("data", [b"x" * (2 * 1024 * 1024 + 1), tsv([("x" * 50001, 99, 1)])])
def test_tsv_output_size_limits(data):
    with pytest.raises(DocumentError, match="local_ocr_limit"):
        parse(data)


async def test_subprocess_wall_timeout_kills_group_and_cleans_temporary_files(monkeypatch):
    directories, waits, killed = [], [], []
    process = SimpleNamespace(pid=123456, returncode=None)

    async def wait():
        waits.append(1)
        if len(waits) == 1:
            raise TimeoutError
        process.returncode = -9

    process.wait = wait

    async def launch(*args, **kwargs):
        directories.append(Path(args[4]).parent)
        assert kwargs["start_new_session"] and kwargs["stderr"] == asyncio.subprocess.DEVNULL
        assert args[-1] == "eng"
        return process

    monkeypatch.setattr(tesseract.asyncio, "create_subprocess_exec", launch)
    monkeypatch.setattr(tesseract.os, "killpg", lambda pid, sig: killed.append(pid))
    with pytest.raises(DocumentError, match="local_ocr_timeout"):
        await tesseract.TesseractDocuments()._recognize(b"fixture", "eng")
    assert killed == [process.pid] and len(waits) == 2
    assert not directories[0].exists()


async def test_cancellation_reaps_child_before_cleanup_and_releases_slot(monkeypatch):
    entered, cancelled, paths = asyncio.Event(), [], []
    process = SimpleNamespace(pid=123456, returncode=None)

    async def wait():
        if not cancelled:
            entered.set()
            await asyncio.Future()

    process.wait = wait

    async def launch(*args, **kwargs):
        paths.append(Path(args[4]).parent)
        return process

    def kill(pid, sig):
        cancelled.append(pid)
        process.returncode = -9

    monkeypatch.setattr(tesseract.asyncio, "create_subprocess_exec", launch)
    monkeypatch.setattr(tesseract.os, "killpg", kill)
    task = asyncio.create_task(processor().recognize([printed()], "en"))
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert cancelled == [process.pid] and not paths[0].exists()
    assert not tesseract.slot().locked()


async def test_multiple_provider_instances_share_one_native_slot(monkeypatch):
    active, maximum = 0, 0

    async def recognize(self, data, language):
        nonlocal active, maximum
        active += 1
        maximum = max(active, maximum)
        await asyncio.sleep(0.01)
        active -= 1
        return parse(tsv([("Invoice", 99, 1)]))

    monkeypatch.setattr(tesseract.TesseractDocuments, "_recognize", recognize)
    await asyncio.gather(*(processor().recognize([printed()], "en") for _ in range(3)))
    assert maximum == 1


async def test_queue_timeout_is_transient_without_native_launch(monkeypatch):
    class Busy:
        async def acquire(self):
            raise TimeoutError

        def release(self):
            raise AssertionError("unacquired slot released")

    monkeypatch.setattr(tesseract, "slot", lambda: Busy())
    with pytest.raises(DocumentError) as error:
        await processor().recognize([printed()], "en")
    assert error.value.key == "local_ocr_busy" and error.value.transient


def test_private_child_sets_resource_limits_and_fixed_non_shell_command(monkeypatch):
    limits, execution = [], []
    monkeypatch.setattr(runner.sys, "argv", ["runner", "/tmp/input.jpg", "/tmp/output", "ara+eng"])
    monkeypatch.setattr(
        runner.resource, "setrlimit", lambda limit, values: limits.append((limit, values))
    )
    monkeypatch.setattr(
        runner.os, "execve", lambda path, args, env: execution.append((path, args, env))
    )
    runner.main()
    assert (runner.resource.RLIMIT_AS, (512 * 1024 * 1024,) * 2) in limits
    assert (runner.resource.RLIMIT_CPU, (20, 20)) in limits
    assert (runner.resource.RLIMIT_FSIZE, (2 * 1024 * 1024,) * 2) in limits
    assert execution[0][0] == "/usr/bin/tesseract"
    assert execution[0][2]["OMP_THREAD_LIMIT"] == "1"
    assert "ara+eng" in execution[0][1]
