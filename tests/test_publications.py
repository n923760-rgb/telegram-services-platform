"""Real PostgreSQL ownership, consent, replay and concurrent publication behavior."""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError

from app.core.db import sessions
from app.core.models import Order, Publication, PublicationConsent, PublicationRevision, User
from app.publications import repository as pages
from app.services.registry import registry

TERMS = "a" * 64
FIRST = {"name": "محمد", "buttons": [{"url": "https://example.invalid/?id=00123"}]}


async def seed(owner=1, *, status="completed"):
    async with sessions.begin() as db:
        if await db.get(User, owner) is None:
            db.add(User(id=owner))
            await db.flush()
        row = Order(
            user_id=owner,
            service_slug="echo",
            price_halala=100,
            idempotency_key=str(uuid4()),
            status=status,
            input_hash="0" * 64,
            input_schema_snapshot=registry.types["echo"].input_schema.model_dump(),
            inputs={"text": "synthetic publication source"},
        )
        db.add(row)
        await db.flush()
        return row.id


async def draft():
    order = await seed()
    expiry = datetime.now(UTC) + timedelta(days=30)
    public = await pages.create(1, order, expires_at=expiry)
    await pages.revise(1, public, FIRST, expected_revision=0, operation_id=uuid4())
    return public


async def publish(public, *, revision=1, active=None, operation=None):
    op = operation or uuid4()
    await pages.publish(
        1, public, revision=revision, expected_active=active, terms_hash=TERMS, operation_id=op
    )
    return op


async def test_creation_is_owned_completed_bounded_and_replay_never_extends_hosting():
    order = await seed()
    expiry = datetime.now(UTC) + timedelta(days=30)
    await seed(2)
    with pytest.raises(pages.PublicationError, match="unavailable"):
        await pages.create(2, order, expires_at=expiry)
    pending = await seed(status="queued")
    with pytest.raises(pages.PublicationError, match="order_not_completed"):
        await pages.create(1, pending, expires_at=expiry)
    for invalid in (datetime.now(UTC) - timedelta(days=1), datetime.now(UTC) + timedelta(days=367)):
        with pytest.raises(pages.PublicationError, match="invalid_expiry"):
            await pages.create(1, order, expires_at=invalid)
    public = await pages.create(1, order, expires_at=expiry)
    assert await pages.create(1, order, expires_at=expiry) == public
    with pytest.raises(pages.PublicationError, match="intent_changed"):
        await pages.create(1, order, expires_at=expiry + timedelta(days=1))
    await pages.delete_content(1, public)
    assert await pages.create(1, order, expires_at=expiry) == public
    assert await pages.public_content(public) is None


async def test_draft_and_new_revision_stay_private_until_exact_consent():
    public = await draft()
    assert await pages.public_content(public) is None
    op = await publish(public)
    assert await pages.public_content(public) == FIRST
    async with sessions() as db:
        receipt = await db.get(PublicationConsent, op)
        assert receipt.content_hash == pages.content_snapshot(FIRST)[1]
        assert receipt.terms_hash == TERMS and receipt.actor_id == 1
    second = {"name": "New", "url": "https://www.youtube.com/"}
    await pages.revise(1, public, second, expected_revision=1, operation_id=uuid4())
    assert await pages.public_content(public) == FIRST
    with pytest.raises(pages.PublicationError, match="revision_changed"):
        await publish(public, revision=2, active=None)
    await publish(public, revision=2, active=1)
    assert await pages.public_content(public) == second


async def test_owner_boundary_for_every_mutation_and_banned_owner_visibility():
    public = await draft()
    await seed(2)
    for other in (2, 3):
        actions = [
            pages.revise(other, public, FIRST, expected_revision=1, operation_id=uuid4()),
            pages.publish(
                other,
                public,
                revision=1,
                expected_active=None,
                terms_hash=TERMS,
                operation_id=uuid4(),
            ),
            pages.suspend(other, public, expected_active=None),
            pages.delete_content(other, public),
        ]
        for action in actions:
            with pytest.raises(pages.PublicationError, match="unavailable"):
                await action
    await publish(public)
    async with sessions.begin() as db:
        (await db.get(User, 1)).banned = True
    assert await pages.public_content(public) is None
    with pytest.raises(pages.PublicationError, match="unavailable"):
        await pages.revise(1, public, FIRST, expected_revision=1, operation_id=uuid4())


async def test_stale_preview_cannot_publish_after_a_newer_draft():
    public = await draft()
    await pages.revise(1, public, {"name": "second"}, expected_revision=1, operation_id=uuid4())
    with pytest.raises(pages.PublicationError, match="revision_changed"):
        await publish(public)
    assert await pages.public_content(public) is None


async def test_old_operations_do_not_revert_new_revision_or_resurrect_suspended_content():
    order = await seed()
    public = await pages.create(1, order, expires_at=datetime.now(UTC) + timedelta(days=1))
    rev_op = uuid4()
    await pages.revise(1, public, FIRST, expected_revision=0, operation_id=rev_op)
    consent = await publish(public)
    await pages.revise(1, public, {"name": "second"}, expected_revision=1, operation_id=uuid4())
    assert await pages.revise(1, public, FIRST, expected_revision=0, operation_id=rev_op) == 1
    with pytest.raises(pages.PublicationError, match="intent_changed"):
        await pages.revise(1, public, {"name": "changed"}, expected_revision=0, operation_id=rev_op)
    await pages.suspend(1, public, expected_active=1)
    await publish(public, operation=consent)
    assert await pages.public_content(public) is None
    async with sessions() as db:
        row = await db.get(Publication, public)
        assert row.latest_revision == 2 and row.state == "suspended"


async def test_concurrent_edits_from_same_snapshot_accept_exactly_one():
    public = await draft()
    results = await asyncio.gather(
        *[
            pages.revise(1, public, {"name": label}, expected_revision=1, operation_id=uuid4())
            for label in ("first", "second")
        ],
        return_exceptions=True,
    )
    assert results.count(2) == 1
    assert (
        sum(isinstance(x, pages.PublicationError) and str(x) == "revision_changed" for x in results)
        == 1
    )


async def test_concurrent_consent_and_exact_retries_create_one_receipt():
    public = await draft()
    op = uuid4()
    assert await asyncio.gather(publish(public, operation=op), publish(public, operation=op)) == [
        op,
        op,
    ]
    with pytest.raises(pages.PublicationError, match="revision_changed"):
        await publish(public)
    async with sessions() as db:
        assert await db.scalar(select(func.count()).select_from(PublicationConsent)) == 1


async def test_expiry_hides_content_without_cron_and_old_consent_cannot_extend():
    public = await draft()
    consent = await publish(public)
    async with sessions.begin() as db:
        (await db.get(Publication, public)).expires_at = datetime.now(UTC) - timedelta(seconds=1)
    assert await pages.public_content(public) is None
    with pytest.raises(pages.PublicationError, match="unavailable"):
        await pages.revise(1, public, FIRST, expected_revision=1, operation_id=uuid4())
    with pytest.raises(pages.PublicationError, match="intent_changed"):
        await publish(public, operation=consent)
    await pages.expire()
    async with sessions() as db:
        row = await db.get(Publication, public)
        assert row.state == "expired" and row.active_revision is None


async def test_delete_purges_content_but_keeps_minimal_consent_and_never_republishes():
    public = await draft()
    consent = await publish(public)
    await pages.delete_content(1, public)
    await pages.delete_content(1, public)
    await publish(public, operation=consent)
    assert await pages.public_content(public) is None
    with pytest.raises(pages.PublicationError, match="unavailable"):
        await publish(public)
    async with sessions() as db:
        assert await db.scalar(select(func.count()).select_from(PublicationRevision)) == 0
        receipt = await db.get(PublicationConsent, consent)
        assert receipt and receipt.content_hash == pages.content_snapshot(FIRST)[1]
        assert not hasattr(receipt, "content")


async def test_revisions_and_consents_cannot_be_modified_in_place():
    public = await draft()
    await publish(public)
    for statement in (
        "UPDATE publication_revisions SET content='{}'::json",
        "UPDATE publication_consents SET terms_hash=repeat('b',64)",
        "DELETE FROM publication_consents",
    ):
        with pytest.raises(DBAPIError):
            async with sessions.begin() as db:
                await db.execute(text(statement))
    assert await pages.public_content(public) == FIRST


async def test_live_revision_foreign_key_cannot_point_to_another_publication():
    first = await draft()
    second_order = await seed()
    second = await pages.create(1, second_order, expires_at=datetime.now(UTC) + timedelta(days=1))
    with pytest.raises(DBAPIError):
        async with sessions.begin() as db:
            row = await db.get(Publication, second)
            row.latest_revision, row.active_revision, row.state = 1, 1, "published"
    assert await pages.public_content(first) is None
    assert await pages.public_content(second) is None


async def test_same_order_concurrent_create_returns_one_stable_public_id():
    order = await seed()
    expiry = datetime.now(UTC) + timedelta(days=1)
    ids = await asyncio.gather(*[pages.create(1, order, expires_at=expiry) for _ in range(3)])
    assert len(set(ids)) == 1
    async with sessions() as db:
        assert await db.scalar(select(func.count()).select_from(Publication)) == 1


async def test_revision_limit_and_changed_consent_terms_do_not_affect_live_content():
    public = await draft()
    op = await publish(public)
    for revision in range(1, pages.MAX_REVISIONS):
        await pages.revise(
            1, public, {"version": revision + 1}, expected_revision=revision, operation_id=uuid4()
        )
    with pytest.raises(pages.PublicationError, match="revision_limit"):
        await pages.revise(
            1,
            public,
            {"name": "over limit"},
            expected_revision=pages.MAX_REVISIONS,
            operation_id=uuid4(),
        )
    with pytest.raises(pages.PublicationError, match="intent_changed"):
        await pages.publish(
            1, public, revision=1, expected_active=None, terms_hash="b" * 64, operation_id=op
        )
    assert await pages.public_content(public) == FIRST


async def test_order_file_cleanup_does_not_delete_durable_publication(tmp_path, monkeypatch):
    from app.core.settings import config
    from app.files.retention import cleanup_terminal_files

    monkeypatch.setattr(config(), "storage_root", tmp_path)
    public = await draft()
    await publish(public)
    await cleanup_terminal_files()
    async with sessions() as db:
        row = await db.get(Publication, public)
        assert (await db.get(Order, row.order_id)).files_deleted
    assert await pages.public_content(public) == FIRST


async def test_operation_keys_cannot_move_to_a_different_page():
    first = await draft()
    order = await seed()
    second = await pages.create(1, order, expires_at=datetime.now(UTC) + timedelta(days=1))
    op = uuid4()
    await pages.revise(1, first, FIRST, expected_revision=1, operation_id=op)
    with pytest.raises(pages.PublicationError, match="intent_changed"):
        await pages.revise(1, second, FIRST, expected_revision=1, operation_id=op)
    await pages.revise(1, second, FIRST, expected_revision=0, operation_id=uuid4())
    consent = await publish(first, revision=2)
    with pytest.raises(pages.PublicationError, match="intent_changed"):
        await publish(second, revision=2, operation=consent)
    assert await pages.public_content(second) is None
