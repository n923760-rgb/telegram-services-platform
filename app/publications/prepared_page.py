"""Internal bridge from reviewed profile bytes to durable publication revisions.

Callers must authenticate owners and grant a hosting entitlement before creating
a publication. These functions are not HTTP routes or commercial eligibility.
"""

import hashlib
import re
from datetime import datetime
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, StrictBool

from app.builders import publication_page
from app.publications import repository
from app.publications.design import Plan, Profile, https_url, plan_schema

FILES = frozenset({"profile.html", "qr.png", "qr.svg", "share-card.png"})


class PreparedPageError(ValueError):
    pass


class Snapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["profile-page-v1"]
    publication_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    public_url: str
    profile: Profile
    plan: Plan
    embedded_qr: StrictBool
    digests: dict[str, str]


def public_url(origin, publication_id):
    """Derive the destination from an operator origin and an opaque DB identity."""
    try:
        https_url(origin)
        parts = urlsplit(origin)
        if origin not in {f"https://{parts.netloc}", f"https://{parts.netloc}/"}:
            raise ValueError("invalid origin")
        result = f"{origin.rstrip('/')}/p/{repository.uuid(publication_id).hex}"
        return https_url(result)
    except (ValueError, TypeError):
        raise PreparedPageError("invalid_publication") from None


def hashes(files):
    return {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}


def prepare(profile, plan, *, publication_id, origin, embedded_qr=True):
    """No AI call: pin all four native artifacts after job-scoped composition."""
    try:
        source = Profile.model_validate(profile)
        design = plan_schema(source).model_validate(
            plan.model_dump(mode="json") if isinstance(plan, Plan) else plan
        )
        url = public_url(origin, publication_id)
        files = publication_page.bundle(source, design, public_url=url, embedded_qr=embedded_qr)
        snapshot = Snapshot(
            kind="profile-page-v1",
            publication_id=repository.uuid(publication_id).hex,
            public_url=url,
            profile=source,
            plan=design,
            embedded_qr=embedded_qr,
            digests=hashes(files),
        )
        # Same JSON/size/depth contract as durable revisions; reject before writes.
        return repository.content_snapshot(snapshot.model_dump(mode="json"))[0]
    except (ValueError, TypeError):
        raise PreparedPageError("invalid_prepared_page") from None


def render(content, *, publication_id, origin):
    """Rebuild only byte-identical exports; renderer/font/library drift fails closed.

    A renderer upgrade must retain old rendering support or obtain fresh review;
    it cannot silently change a consented page. No raw stored HTML is trusted.
    """
    try:
        content, _ = repository.content_snapshot(content)
        snapshot = Snapshot.model_validate(content)
        if (
            snapshot.publication_id != repository.uuid(publication_id).hex
            or snapshot.public_url != public_url(origin, publication_id)
            or set(snapshot.digests) != FILES
            or any(not re.fullmatch(r"[a-f0-9]{64}", h) for h in snapshot.digests.values())
        ):
            raise ValueError("snapshot mismatch")
        files = publication_page.bundle(
            snapshot.profile,
            snapshot.plan,
            public_url=snapshot.public_url,
            embedded_qr=snapshot.embedded_qr,
        )
        if hashes(files) != snapshot.digests:
            raise ValueError("rendered bytes changed")
        return files
    except (ValueError, TypeError):
        raise PreparedPageError("prepared_page_unavailable") from None


async def revise(
    owner_id, publication_id, profile, plan, *, origin, embedded_qr, expected_revision, operation_id
):
    content = prepare(
        profile, plan, publication_id=publication_id, origin=origin, embedded_qr=embedded_qr
    )
    return await repository.revise(
        owner_id,
        publication_id,
        content,
        expected_revision=expected_revision,
        operation_id=operation_id,
    )


async def review(owner_id, publication_id, *, origin):
    """An authenticated adapter may show these exact bytes and revision metadata."""
    revision = await repository.review(owner_id, publication_id)
    files = render(revision["content"], publication_id=publication_id, origin=origin)
    return {**revision, "files": files}


async def approve(
    owner_id,
    publication_id,
    *,
    origin,
    revision,
    expected_active,
    expected_expires_at,
    content_hash,
    terms_hash,
    operation_id,
):
    """No receipt is recorded unless the current prepared bytes still match review."""
    if not isinstance(expected_expires_at, datetime) or expected_expires_at.utcoffset() is None:
        raise repository.PublicationError("invalid_input")
    current = await review(owner_id, publication_id, origin=origin)
    if (current["revision"], current["content_hash"]) != (revision, content_hash):
        raise repository.PublicationError("revision_changed")
    return await repository.publish(
        owner_id,
        publication_id,
        revision=revision,
        expected_active=expected_active,
        expected_content_hash=content_hash,
        expected_expires_at=expected_expires_at,
        terms_hash=terms_hash,
        operation_id=operation_id,
    )


async def public_bundle(publication_id, *, origin):
    """No provider call or renewal on reads; unavailable states reveal no content."""
    content = await repository.public_content(publication_id)
    if content is None:
        return None
    try:
        return render(content, publication_id=publication_id, origin=origin)
    except PreparedPageError:
        return None
