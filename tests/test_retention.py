import os
from datetime import UTC, datetime, timedelta

import pytest

from app.core.db import sessions
from app.core.models import Order, Service
from app.core.settings import config
from app.orders.engine import submit
from app.providers.storage import LocalStorage
from tests.test_foundation import fund


async def _prepare(tmp_path, monkeypatch, slug="image_to_text"):
    monkeypatch.setattr(config(), "storage_root", tmp_path)
    monkeypatch.setattr(config(), "ai_enabled", True)
    await fund()
    async with sessions.begin() as db:
        (await db.get(Service, slug)).enabled = True
    return LocalStorage(tmp_path)


async def _price(slug):
    async with sessions() as db:
        return (await db.get(Service, slug)).price_halala


def _age(path, hours=48):
    old = (datetime.now(UTC) - timedelta(hours=hours)).timestamp()
    os.utime(path, (old, old))


async def test_failed_deletion_preserves_references_for_retry(tmp_path, monkeypatch):
    from app.files.retention import cleanup, cleanup_terminal_files
    from app.orders.engine import fail_locked

    store = await _prepare(tmp_path, monkeypatch)
    file = store.save(1, "input.jpg", b"fixture", "image/jpeg")
    artifact = store.save(
        1,
        "result.docx",
        b"artifact",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    oid = await submit(
        1,
        "image_to_text",
        {"images": [file.key], "language": "none"},
        await _price("image_to_text"),
        "retry-refs",
    )
    async with sessions.begin() as db:
        order = await db.get(Order, oid)
        await fail_locked(db, order, "cancelled", cancelled=True)
        order.result = {
            "text": "",
            "artifacts": [{"key": artifact.key, "filename": "result.docx", "mime": "artifact"}],
        }

    original_delete = LocalStorage.delete

    def broken_delete(self, key, user_id):
        raise OSError("simulated storage failure")

    monkeypatch.setattr(LocalStorage, "delete", broken_delete)
    await cleanup_terminal_files()
    async with sessions() as db:
        order = await db.get(Order, oid)
        assert not order.files_deleted
        assert order.inputs["images"] == [file.key]
        assert order.result["artifacts"][0]["key"] == artifact.key

    # Age the files and the order past the TTL, then run the full cleanup: the
    # pending-deletion order must keep its input and result references and its files.
    _age(store.path(file.key))
    _age(store.path(artifact.key))
    async with sessions.begin() as db:
        (await db.get(Order, oid)).updated_at = datetime.now(UTC) - timedelta(hours=48)
    await cleanup()
    async with sessions() as db:
        order = await db.get(Order, oid)
        assert not order.files_deleted
        assert order.inputs["images"] == [file.key]
        assert order.result["artifacts"][0]["key"] == artifact.key
    assert store.path(file.key).is_file()
    assert store.path(artifact.key).is_file()

    monkeypatch.setattr(LocalStorage, "delete", original_delete)
    await cleanup_terminal_files()
    async with sessions.begin() as db:
        order = await db.get(Order, oid)
        assert order.files_deleted
        # Re-age after durable deletion: the files_deleted update reapplies the
        # onupdate default to updated_at, so age it again for the purge sweep.
        order.updated_at = datetime.now(UTC) - timedelta(hours=48)
    assert not store.path(file.key).is_file()
    assert not store.path(artifact.key).is_file()

    # Only after durable deletion succeeded does the next sweep purge the stale references.
    await cleanup()
    async with sessions() as db:
        order = await db.get(Order, oid)
        assert order.inputs == {} and order.result is None


async def test_aged_active_input_survives_expiry(tmp_path, monkeypatch):
    from app.files.retention import cleanup

    store = await _prepare(tmp_path, monkeypatch)
    file = store.save(1, "input.jpg", b"fixture", "image/jpeg")
    oid = await submit(
        1,
        "image_to_text",
        {"images": [file.key], "language": "none"},
        await _price("image_to_text"),
        "active-input",
    )
    _age(store.path(file.key))
    await cleanup()
    async with sessions() as db:
        order = await db.get(Order, oid)
        assert order.status == "queued"
        assert order.inputs["images"] == [file.key]
    assert store.path(file.key).is_file()


async def test_aged_prepared_artifact_survives_expiry(tmp_path, monkeypatch):
    from app.files.retention import cleanup

    store = await _prepare(tmp_path, monkeypatch, "text_to_office")
    artifact = store.save(
        1,
        "result.docx",
        b"artifact",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    oid = await submit(
        1,
        "text_to_office",
        {"text": "نص", "target": "word", "mode": "smart"},
        await _price("text_to_office"),
        "artifact",
    )
    async with sessions.begin() as db:
        order = await db.get(Order, oid)
        order.status = "delivering"
        order.result = {
            "text": "نص",
            "artifacts": [{"key": artifact.key, "filename": "result.docx", "mime": "artifact"}],
        }
    _age(store.path(artifact.key))
    await cleanup()
    async with sessions() as db:
        order = await db.get(Order, oid)
        assert order.result["artifacts"][0]["key"] == artifact.key
    assert store.path(artifact.key).is_file()


async def test_abandoned_upload_expires(tmp_path, monkeypatch):
    from app.files.retention import cleanup

    store = await _prepare(tmp_path, monkeypatch)
    orphan = store.save(1, "orphan.jpg", b"abandoned", "image/jpeg")
    _age(store.path(orphan.key))
    await cleanup()
    assert not store.path(orphan.key).is_file()


async def test_successful_terminal_purge_clears_references(tmp_path, monkeypatch):
    from app.files.retention import cleanup, cleanup_terminal_files
    from app.orders.engine import fail_locked

    store = await _prepare(tmp_path, monkeypatch)
    file = store.save(1, "input.jpg", b"fixture", "image/jpeg")
    oid = await submit(
        1,
        "image_to_text",
        {"images": [file.key], "language": "none"},
        await _price("image_to_text"),
        "purge",
    )
    async with sessions.begin() as db:
        await fail_locked(db, await db.get(Order, oid), "cancelled", cancelled=True)
    await cleanup_terminal_files()
    async with sessions.begin() as db:
        order = await db.get(Order, oid)
        assert order.files_deleted
        order.updated_at = datetime.now(UTC) - timedelta(hours=48)
    await cleanup()
    async with sessions() as db:
        order = await db.get(Order, oid)
        assert order.inputs == {} and order.result is None


async def test_malformed_input_schema_fails_closed(tmp_path, monkeypatch):
    from app.files.retention import cleanup

    store = await _prepare(tmp_path, monkeypatch)
    file = store.save(1, "input.jpg", b"fixture", "image/jpeg")
    oid = await submit(
        1,
        "image_to_text",
        {"images": [file.key], "language": "none"},
        await _price("image_to_text"),
        "malformed-schema",
    )
    async with sessions.begin() as db:
        (await db.get(Order, oid)).input_schema_snapshot = {}
    _age(store.path(file.key))
    with pytest.raises(ValueError):
        await cleanup()
    async with sessions() as db:
        order = await db.get(Order, oid)
        assert not order.files_deleted
        assert order.inputs["images"] == [file.key]
    assert store.path(file.key).is_file()


async def test_malformed_artifact_result_fails_closed(tmp_path, monkeypatch):
    from app.files.retention import cleanup

    store = await _prepare(tmp_path, monkeypatch, "text_to_office")
    artifact = store.save(
        1,
        "result.docx",
        b"artifact",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    oid = await submit(
        1,
        "text_to_office",
        {"text": "نص", "target": "word", "mode": "smart"},
        await _price("text_to_office"),
        "malformed-result",
    )
    async with sessions.begin() as db:
        order = await db.get(Order, oid)
        order.status = "delivering"
        order.result = {"text": "", "artifacts": [artifact.key]}
    _age(store.path(artifact.key))
    with pytest.raises(ValueError):
        await cleanup()
    async with sessions() as db:
        order = await db.get(Order, oid)
        assert not order.files_deleted
        assert order.result["artifacts"] == [artifact.key]
    assert store.path(artifact.key).is_file()
