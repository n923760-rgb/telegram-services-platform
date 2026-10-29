"""Real PostgreSQL proof that reviewed exports bind to consent and stable identity."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.builders import publication_page
from app.core.db import sessions
from app.core.models import Publication, PublicationConsent, User
from app.publications import prepared_page as prepared
from app.publications import repository
from tests.profile_page_fixtures import plan, profile
from tests.test_publications import seed

ORIGIN = "https://profiles.example.invalid"
TERMS = "d" * 64


async def draft():
    order = await seed()
    identity = await repository.create(1, order, expires_at=datetime.now(UTC) + timedelta(days=30))
    await prepared.revise(
        1,
        identity,
        profile(),
        plan(),
        origin=ORIGIN,
        embedded_qr=True,
        expected_revision=0,
        operation_id=uuid4(),
    )
    return identity


async def approve(identity, review, *, operation=None):
    return await prepared.approve(
        1,
        identity,
        origin=ORIGIN,
        revision=review["revision"],
        expected_active=review["active_revision"],
        expected_expires_at=review["expires_at"],
        content_hash=review["content_hash"],
        terms_hash=TERMS,
        operation_id=operation or uuid4(),
    )


async def test_owner_review_stays_private_and_consent_serves_identical_files():
    identity = await draft()
    review = await prepared.review(1, identity, origin=ORIGIN)
    assert review["revision"] == 1 and review["active_revision"] is None
    assert await prepared.public_bundle(identity, origin=ORIGIN) is None
    operation = await approve(identity, review)
    assert await approve(identity, review, operation=operation) == operation
    assert await prepared.public_bundle(identity, origin=ORIGIN) == review["files"]
    async with sessions() as db:
        receipt = await db.get(PublicationConsent, operation)
        assert receipt.content_hash == review["content_hash"]
        assert receipt.expires_at == review["expires_at"] and receipt.terms_hash == TERMS
        assert await db.scalar(select(func.count()).select_from(PublicationConsent)) == 1


async def test_changed_draft_keeps_live_version_and_same_whole_page_qr_until_new_consent():
    identity = await draft()
    first = await prepared.review(1, identity, origin=ORIGIN)
    await approve(identity, first)
    await prepared.revise(
        1,
        identity,
        profile(name="هوية جديدة"),
        plan(),
        origin=ORIGIN,
        embedded_qr=False,
        expected_revision=1,
        operation_id=uuid4(),
    )
    assert await prepared.public_bundle(identity, origin=ORIGIN) == first["files"]
    with pytest.raises(repository.PublicationError, match="revision_changed"):
        await approve(identity, first)
    second = await prepared.review(1, identity, origin=ORIGIN)
    assert second["content_hash"] != first["content_hash"]
    await approve(identity, second)
    assert await prepared.public_bundle(identity, origin=ORIGIN) == second["files"]
    assert second["files"]["qr.png"] == first["files"]["qr.png"]
    assert second["files"]["qr.svg"] == first["files"]["qr.svg"]


async def test_failed_generation_cannot_replace_live_content():
    identity = await draft()
    review = await prepared.review(1, identity, origin=ORIGIN)
    await approve(identity, review)
    with pytest.raises(prepared.PreparedPageError):
        await prepared.revise(
            1,
            identity,
            profile(),
            plan(action_order=[0, 0, 0]),
            origin=ORIGIN,
            embedded_qr=True,
            expected_revision=1,
            operation_id=uuid4(),
        )
    assert await prepared.public_bundle(identity, origin=ORIGIN) == review["files"]
    assert (await repository.review(1, identity))["revision"] == 1


async def test_renderer_drift_creates_no_consent_and_exposes_no_changed_public_bytes(monkeypatch):
    identity = await draft()
    review = await prepared.review(1, identity, origin=ORIGIN)
    original = publication_page.bundle

    def changed(*args, **kwargs):
        files = original(*args, **kwargs)
        files["profile.html"] += b"changed"
        return files

    monkeypatch.setattr(publication_page, "bundle", changed)
    with pytest.raises(prepared.PreparedPageError):
        await approve(identity, review)
    async with sessions() as db:
        assert await db.scalar(select(func.count()).select_from(PublicationConsent)) == 0
        assert (await db.get(Publication, identity)).active_revision is None


async def test_private_review_requires_owner_and_banned_owner_cannot_approve():
    identity = await draft()
    review = await prepared.review(1, identity, origin=ORIGIN)
    await seed(2)
    for owner in (2, 3):
        with pytest.raises(repository.PublicationError, match="unavailable"):
            await prepared.review(owner, identity, origin=ORIGIN)
    async with sessions.begin() as db:
        (await db.get(User, 1)).banned = True
    with pytest.raises(repository.PublicationError, match="unavailable"):
        await approve(identity, review)


async def test_hash_check_is_atomic_including_receipt_replay():
    identity = await draft()
    review = await prepared.review(1, identity, origin=ORIGIN)
    operation = uuid4()
    kwargs = dict(revision=1, expected_active=None, terms_hash=TERMS, operation_id=operation)
    with pytest.raises(repository.PublicationError, match="revision_changed"):
        await repository.publish(1, identity, **kwargs, expected_content_hash="a" * 64)
    await repository.publish(1, identity, **kwargs, expected_content_hash=review["content_hash"])
    with pytest.raises(repository.PublicationError, match="intent_changed"):
        await repository.publish(1, identity, **kwargs, expected_content_hash="b" * 64)


async def test_edit_between_review_and_atomic_consent_is_rejected(monkeypatch):
    identity = await draft()
    review = await prepared.review(1, identity, origin=ORIGIN)
    original = repository.publish

    async def race(*args, **kwargs):
        await prepared.revise(
            1,
            identity,
            profile(name="تعديل متزامن"),
            plan(),
            origin=ORIGIN,
            embedded_qr=True,
            expected_revision=1,
            operation_id=uuid4(),
        )
        return await original(*args, **kwargs)

    monkeypatch.setattr(repository, "publish", race)
    with pytest.raises(repository.PublicationError, match="revision_changed"):
        await approve(identity, review)
    assert await prepared.public_bundle(identity, origin=ORIGIN) is None


async def test_changed_hosting_expiry_requires_fresh_review():
    identity = await draft()
    review = await prepared.review(1, identity, origin=ORIGIN)
    async with sessions.begin() as db:
        (await db.get(Publication, identity)).expires_at += timedelta(days=1)
    with pytest.raises(repository.PublicationError, match="revision_changed"):
        await approve(identity, review)
    assert await prepared.public_bundle(identity, origin=ORIGIN) is None


@pytest.mark.parametrize("state", ["suspended", "expired", "deleted"])
async def test_unavailable_publication_never_returns_exports_or_resurrects_on_old_review(state):
    identity = await draft()
    review = await prepared.review(1, identity, origin=ORIGIN)
    operation = await approve(identity, review)
    if state == "suspended":
        await repository.suspend(1, identity, expected_active=1)
    elif state == "deleted":
        await repository.delete_content(1, identity)
    else:
        async with sessions.begin() as db:
            (await db.get(Publication, identity)).expires_at = datetime.now(UTC) - timedelta(
                seconds=1
            )
    assert await prepared.public_bundle(identity, origin=ORIGIN) is None
    try:
        await approve(identity, review, operation=operation)
    except repository.PublicationError:
        pass
    assert await prepared.public_bundle(identity, origin=ORIGIN) is None
