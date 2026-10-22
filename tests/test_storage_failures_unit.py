"""Fault injection at the shared upload/result storage boundary; no external services."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.providers.storage import LocalStorage


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize("stage", ["write", "replace"])
@pytest.mark.parametrize("error_type", [OSError, KeyboardInterrupt])
def test_failed_save_removes_partial_bytes_and_allows_retry(
    tmp_path, monkeypatch, stage, error_type
):
    store = LocalStorage(tmp_path, quota_bytes=8, quota_files=1)
    other = store.save(2, "other.txt", b"other", "text/plain")
    original = error_type("injected storage interruption")
    write = Path.write_bytes

    def fail_write(path, data):
        write(path, data[:3])
        raise original

    def fail_replace(path, destination):
        raise original

    with monkeypatch.context() as patch:
        patch.setattr(
            Path,
            "write_bytes" if stage == "write" else "replace",
            fail_write if stage == "write" else fail_replace,
        )
        with pytest.raises(error_type) as raised:
            store.save(1, "result.txt", b"complete", "text/plain")
        assert raised.value is original

    assert store.usage(1) == (0, 0)
    assert not list((tmp_path / "1").glob("*"))
    saved = store.save(1, "result.txt", b"complete", "text/plain")
    assert store.read(saved.key, 1) == b"complete"
    assert store.read(other.key, 2) == b"other"
    assert store.usage(1) == (8, 1)


@pytest.mark.parametrize("cleanup_stage", ["unlink", "rmdir"])
def test_cleanup_failure_preserves_original_error_and_retention_can_recover(
    tmp_path, monkeypatch, cleanup_stage
):
    store = LocalStorage(tmp_path)
    original = OSError("original rename failure")

    def fail_replace(path, destination):
        raise original

    def fail_cleanup(path, *args, **kwargs):
        raise PermissionError("secondary cleanup failure")

    with monkeypatch.context() as patch:
        patch.setattr(Path, "replace", fail_replace)
        patch.setattr(Path, cleanup_stage, fail_cleanup)
        with pytest.raises(OSError) as raised:
            store.save(1, "result.txt", b"complete", "text/plain")
        assert raised.value is original

    assert not list((tmp_path / "1").glob("*/result.txt"))
    if cleanup_stage == "unlink":
        assert store.usage(1) == (8, 1)
        store.expire_before(datetime.now(UTC) + timedelta(seconds=1))
    assert store.usage(1) == (0, 0)
