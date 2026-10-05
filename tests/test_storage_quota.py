"""Regression tests for per-owner upload storage quota (byte and file bounds).

The quota is enforced in LocalStorage.save under a POSIX lock so concurrent bot/worker uploads
cannot overshoot it, and an advisory pre-check (ensure_quota) runs before the expensive Telegram
download. These tests exercise exhaustion, owner isolation and the pre-check path.
"""

import threading

import pytest

from app.providers.storage import LocalStorage
from app.services.base import ServiceError


def _owner_subdirs(store, user_id):
    owner = store._owner_dir(user_id)
    if not owner.is_dir():
        return set()
    return {path.name for path in owner.iterdir() if path.is_dir()}


def test_byte_quota_exhaustion_rejects_save(tmp_path):
    store = LocalStorage(tmp_path, max_bytes=100, quota_bytes=20, quota_files=100)
    store.save(1, "a.txt", b"1234567890", "text/plain")  # 10 bytes, ok
    with pytest.raises(ServiceError, match="storage_quota"):
        store.save(1, "b.txt", b"12345678901", "text/plain")  # would exceed 20 bytes


def test_file_count_quota_exhaustion_rejects_save(tmp_path):
    store = LocalStorage(tmp_path, max_bytes=100, quota_bytes=1000, quota_files=1)
    store.save(1, "a.txt", b"x", "text/plain")
    with pytest.raises(ServiceError, match="storage_quota"):
        store.save(1, "b.txt", b"y", "text/plain")


def test_rejected_byte_saves_leave_no_empty_directories(tmp_path):
    store = LocalStorage(tmp_path, max_bytes=100, quota_bytes=20, quota_files=10)
    store.save(1, "a.txt", b"1234567890", "text/plain")  # 10 bytes, one file
    original_dirs = _owner_subdirs(store, 1)

    with pytest.raises(ServiceError, match="storage_quota"):
        store.save(1, "b.txt", b"12345678901", "text/plain")  # would exceed 20 bytes
    with pytest.raises(ServiceError, match="storage_quota"):
        store.save(1, "c.txt", b"12345678901", "text/plain")

    assert _owner_subdirs(store, 1) == original_dirs
    # Pre-existing file is preserved and still readable by its owner.
    saved = original_dirs.pop()
    assert store.read(f"1/{saved}/a.txt", 1) == b"1234567890"


def test_rejected_file_count_saves_leave_no_empty_directories(tmp_path):
    store = LocalStorage(tmp_path, max_bytes=100, quota_bytes=1000, quota_files=1)
    store.save(1, "a.txt", b"x", "text/plain")
    original_dirs = _owner_subdirs(store, 1)

    with pytest.raises(ServiceError, match="storage_quota"):
        store.save(1, "b.txt", b"y", "text/plain")
    with pytest.raises(ServiceError, match="storage_quota"):
        store.save(1, "c.txt", b"z", "text/plain")

    assert _owner_subdirs(store, 1) == original_dirs
    # Owner isolation: a different owner can still save without new directories.
    store.save(2, "d.txt", b"w", "text/plain")
    assert _owner_subdirs(store, 1) == original_dirs


def test_quota_is_isolated_per_owner(tmp_path):
    store = LocalStorage(tmp_path, max_bytes=100, quota_bytes=10, quota_files=100)
    store.save(1, "a.txt", b"1234567890", "text/plain")  # owner 1 fills its 10-byte quota
    with pytest.raises(ServiceError, match="storage_quota"):
        store.save(1, "b.txt", b"z", "text/plain")
    # A different owner is unaffected.
    assert store.save(2, "c.txt", b"1234567890", "text/plain").key


def test_quota_precheck_raises_before_write(tmp_path):
    store = LocalStorage(tmp_path, max_bytes=100, quota_bytes=10, quota_files=100)
    store.save(1, "a.txt", b"1234567890", "text/plain")
    with pytest.raises(ServiceError, match="storage_quota"):
        store.ensure_quota(1, incoming_bytes=1)


def test_concurrent_saves_do_not_overshoot_quota(tmp_path):
    store = LocalStorage(tmp_path, max_bytes=100, quota_bytes=40, quota_files=100)
    results = []

    def upload(seed):
        try:
            store.save(1, f"f{seed}.txt", b"1234567890", "text/plain")
            results.append(("ok", seed))
        except ServiceError as error:
            results.append((error.key, seed))

    threads = [threading.Thread(target=upload, args=(i,)) for i in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    # At most 4 files of 10 bytes fit in 40 bytes; the POSIX lock serializes the check+write.
    assert sum(1 for status, _ in results if status == "ok") <= 4
    total, count = store.usage(1)
    assert total <= 40 and count <= 4
