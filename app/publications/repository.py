"""DB-only publication operations. Adapters must supply verified owner identity.

No file keys, network calls, charging, renewal, or HTML interpretation. Public
content is validated JSON, never markup trusted for insertion into a web page.
"""

import hashlib
import json
import re
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, func, select, text, update

from app.core.db import sessions
from app.core.models import (
    Order,
    Publication,
    PublicationConsent,
    PublicationRevision,
    User,
)
from app.core.transactions import transaction_retry

MAX_CONTENT_BYTES = 32768
MAX_REVISIONS = 20


def review_gate(state, consents):
    if state is not None and (
        type(state) is not str or state not in {"draft", "published", "suspended"}
    ):
        raise PublicationError("invalid_input")
    if consents is not None and (type(consents) is not int or not 0 <= consents < 2**63):
        raise PublicationError("invalid_input")


def consent_terms_hash(terms_hash, state, consents):
    """Commit the review gate into the existing immutable terms-hash receipt."""
    if state is None and consents is None:
        return terms_hash
    value = {"terms_hash": terms_hash, "expected_state": state, "expected_consents": consents}
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


async def consent_count(db, row):
    return await db.scalar(
        select(func.count())
        .select_from(PublicationConsent)
        .where(PublicationConsent.publication_id == row.id)
    )


async def check_review_gate(db, row, state, consents):
    if (state is not None and row.state != state) or (
        consents is not None and await consent_count(db, row) != consents
    ):
        raise PublicationError("revision_changed")


class PublicationError(ValueError):
    pass


def identity(owner_id):
    if type(owner_id) is not int or not 0 < owner_id < 2**63:
        raise PublicationError("unavailable")


def uuid(value):
    try:
        return UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        raise PublicationError("invalid_input") from None


def number(value, *, optional=False):
    if optional and value is None:
        return
    if type(value) is not int or not 0 <= value <= MAX_REVISIONS:
        raise PublicationError("invalid_input")


def content_snapshot(content):
    def visit(value, depth=0):
        if depth > 8:
            raise PublicationError("invalid_content")
        if type(value) is dict:
            if any(type(key) is not str for key in value):
                raise PublicationError("invalid_content")
            for item in value.values():
                visit(item, depth + 1)
        elif type(value) is list:
            for item in value:
                visit(item, depth + 1)
        elif type(value) not in (str, int, bool, type(None)):
            raise PublicationError("invalid_content")

    if type(content) is not dict or not content:
        raise PublicationError("invalid_content")
    visit(content)
    try:
        raw = json.dumps(
            content, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
    except (ValueError, UnicodeError, OverflowError):
        raise PublicationError("invalid_content") from None
    if len(raw) > MAX_CONTENT_BYTES:
        raise PublicationError("invalid_content")
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


async def owned(db, publication_id, owner_id):
    identity(owner_id)
    row = await db.scalar(
        select(Publication)
        .where(Publication.id == uuid(publication_id), Publication.owner_id == owner_id)
        .with_for_update()
    )
    user = await db.get(User, owner_id)
    if row is None or user is None or user.banned:
        raise PublicationError("unavailable")
    return row


async def operation_lock(db, kind, operation_id):
    await db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key,0))"),
        {"key": f"publication-{kind}:{operation_id}"},
    )


async def now(db):
    return await db.scalar(select(func.now()))


async def editable(db, row):
    if row.state in {"deleted", "expired"} or row.expires_at <= await now(db):
        raise PublicationError("unavailable")


@transaction_retry
async def create(owner_id, order_id, *, expires_at):
    identity(owner_id)
    order_id = uuid(order_id)
    if not isinstance(expires_at, datetime) or expires_at.utcoffset() is None:
        raise PublicationError("invalid_input")
    expires_at = expires_at.astimezone(UTC)
    async with sessions.begin() as db:
        await db.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key,0))"),
            {"key": f"publication-order:{order_id}"},
        )
        order = await db.get(Order, order_id)
        user = await db.get(User, owner_id)
        if order is None or order.user_id != owner_id or user is None or user.banned:
            raise PublicationError("unavailable")
        if order.status != "completed":
            raise PublicationError("order_not_completed")
        previous = await db.scalar(select(Publication).where(Publication.order_id == order_id))
        if previous:
            if previous.owner_id != owner_id or previous.expires_at != expires_at:
                raise PublicationError("intent_changed")
            return previous.id  # Never resurrect or extend on replay.
        current = await now(db)
        if not current < expires_at <= current + timedelta(days=366):
            raise PublicationError("invalid_expiry")
        row = Publication(owner_id=owner_id, order_id=order_id, expires_at=expires_at)
        db.add(row)
        await db.flush()
        return row.id


@transaction_retry
async def revise(owner_id, publication_id, content, *, expected_revision, operation_id):
    number(expected_revision)
    operation_id = uuid(operation_id)
    content, digest = content_snapshot(content)
    async with sessions.begin() as db:
        await operation_lock(db, "revision", operation_id)
        row = await owned(db, publication_id, owner_id)
        await editable(db, row)
        previous = await db.scalar(
            select(PublicationRevision).where(PublicationRevision.operation_id == operation_id)
        )
        if previous:
            if (previous.publication_id, previous.base_revision, previous.content_hash) != (
                row.id,
                expected_revision,
                digest,
            ):
                raise PublicationError("intent_changed")
            return previous.number  # Never replace the latest revision on replay.
        if row.latest_revision != expected_revision:
            raise PublicationError("revision_changed")
        if row.latest_revision >= MAX_REVISIONS:
            raise PublicationError("revision_limit")
        revision = PublicationRevision(
            publication_id=row.id,
            number=expected_revision + 1,
            operation_id=operation_id,
            base_revision=expected_revision,
            content=content,
            content_hash=digest,
        )
        db.add(revision)
        row.latest_revision = revision.number
        await db.flush()
        return revision.number


async def review(owner_id, publication_id):
    """Private latest revision for a verified owner, never a public lookup."""
    async with sessions.begin() as db:
        row = await owned(db, publication_id, owner_id)
        await editable(db, row)
        item = await db.get(PublicationRevision, (row.id, row.latest_revision))
        if item is None:
            raise PublicationError("unavailable")
        return {
            "revision": item.number,
            "active_revision": row.active_revision,
            "expires_at": row.expires_at,
            "content_hash": item.content_hash,
            "content": item.content,
            "state": row.state,
            "consent_count": await consent_count(db, row),
        }


@transaction_retry
async def publish(
    owner_id,
    publication_id,
    *,
    revision,
    expected_active,
    terms_hash,
    operation_id,
    expected_content_hash=None,
    expected_expires_at=None,
    expected_state=None,
    expected_consents=None,
):
    review_gate(expected_state, expected_consents)
    number(revision)
    number(expected_active, optional=True)
    operation_id = uuid(operation_id)
    if expected_expires_at is not None:
        if not isinstance(expected_expires_at, datetime) or expected_expires_at.utcoffset() is None:
            raise PublicationError("invalid_input")
        expected_expires_at = expected_expires_at.astimezone(UTC)
    if (
        revision == 0
        or expected_active == 0
        or type(terms_hash) is not str
        or not re.fullmatch(r"[0-9a-f]{64}", terms_hash)
        or (
            expected_content_hash is not None
            and (
                type(expected_content_hash) is not str
                or not re.fullmatch(r"[0-9a-f]{64}", expected_content_hash)
            )
        )
    ):
        raise PublicationError("invalid_input")
    terms_hash = consent_terms_hash(terms_hash, expected_state, expected_consents)
    async with sessions.begin() as db:
        await operation_lock(db, "consent", operation_id)
        row = await owned(db, publication_id, owner_id)
        if expected_expires_at is not None and row.expires_at != expected_expires_at:
            raise PublicationError("revision_changed")
        receipt = await db.get(PublicationConsent, operation_id)
        if receipt:
            if (
                receipt.publication_id,
                receipt.actor_id,
                receipt.revision,
                receipt.previous_active,
                receipt.terms_hash,
                receipt.expires_at,
            ) != (row.id, owner_id, revision, expected_active, terms_hash, row.expires_at) or (
                expected_content_hash is not None and receipt.content_hash != expected_content_hash
            ):
                raise PublicationError("intent_changed")
            return receipt.operation_id  # Old consent never republishes suspended/deleted content.
        await editable(db, row)
        await check_review_gate(db, row, expected_state, expected_consents)
        if row.active_revision != expected_active or row.latest_revision != revision:
            raise PublicationError("revision_changed")
        item = await db.get(PublicationRevision, (row.id, revision))
        if item is None:
            raise PublicationError("unavailable")
        if expected_content_hash is not None and item.content_hash != expected_content_hash:
            raise PublicationError("revision_changed")
        db.add(
            PublicationConsent(
                operation_id=operation_id,
                publication_id=row.id,
                actor_id=owner_id,
                revision=revision,
                previous_active=expected_active,
                content_hash=item.content_hash,
                terms_hash=terms_hash,
                expires_at=row.expires_at,
            )
        )
        row.state = "published"
        row.active_revision = revision
        return operation_id


async def public_content(publication_id):
    try:
        publication_id = uuid(publication_id)
    except PublicationError:
        return None
    async with sessions() as db:
        return await db.scalar(
            select(PublicationRevision.content)
            .join(
                Publication,
                (Publication.id == PublicationRevision.publication_id)
                & (Publication.active_revision == PublicationRevision.number),
            )
            .join(User, User.id == Publication.owner_id)
            .where(
                Publication.id == publication_id,
                Publication.state == "published",
                Publication.expires_at > func.now(),
                User.banned.is_(False),
            )
        )


@transaction_retry
async def suspend(
    owner_id, publication_id, *, expected_active, expected_state=None, expected_consents=None
):
    review_gate(expected_state, expected_consents)
    number(expected_active, optional=True)
    async with sessions.begin() as db:
        row = await owned(db, publication_id, owner_id)
        if row.state == "deleted":
            raise PublicationError("unavailable")
        await check_review_gate(db, row, expected_state, expected_consents)
        if row.active_revision != expected_active:
            raise PublicationError("revision_changed")
        row.state, row.active_revision = "suspended", None


@transaction_retry
async def delete_content(owner_id, publication_id):
    async with sessions.begin() as db:
        row = await owned(db, publication_id, owner_id)
        row.state, row.active_revision = "deleted", None
        await db.flush()  # Release the active FK before purging all content revisions.
        await db.execute(
            delete(PublicationRevision).where(PublicationRevision.publication_id == row.id)
        )


@transaction_retry
async def expire():
    async with sessions.begin() as db:
        await db.execute(
            update(Publication)
            .where(
                Publication.expires_at <= func.now(),
                Publication.state.in_(("draft", "published", "suspended")),
            )
            .values(state="expired", active_revision=None)
        )
