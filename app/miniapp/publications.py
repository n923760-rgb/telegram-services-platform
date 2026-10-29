"""Owner-only prepared-page review and separate, exact publication consent.

No publication creation, AI generation, hosting entitlement or payment here.
"""

import asyncio
import hashlib
import json
import time
from datetime import UTC, datetime
from typing import Literal
from urllib.parse import urlsplit
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictInt, ValidationError
from sqlalchemy import select

from app.api import publications as public_http
from app.core.db import sessions
from app.core.i18n import tr
from app.core.models import Publication, PublicationRevision, User
from app.core.settings import config
from app.miniapp.drafts import authorize, body, fail, runtime
from app.miniapp.review_tokens import InvalidReviewToken, issue, verify
from app.publications import prepared_page, repository

router = APIRouter()
HEADERS = {
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}
PREVIEW_COOKIE = "__Secure-publication-preview"


def preview_path(identity):
    return f"/miniapp/publication-preview/{identity}"


class ViewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    init_data: str = Field(min_length=1, max_length=8192)
    publication_id: UUID | None = None


class Intent(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    revision: StrictInt = Field(ge=1, le=20)
    expected_active: StrictInt | None = Field(ge=1, le=20)
    expires_at: datetime
    content_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    terms_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    state: Literal["draft", "published", "suspended"]
    consent_count: StrictInt = Field(ge=0, lt=2**63)


class DecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    init_data: str = Field(min_length=1, max_length=8192)
    token: str = Field(min_length=1, max_length=200)
    intent: Intent
    operation_id: UUID
    accepted: bool
    action: Literal["publish", "suspend"] = "publish"


def terms():
    cfg = config()
    value = {
        "version": cfg.publication_terms_version,
        "origin": cfg.publication_origin,
        "ar": cfg.publication_terms_ar,
        "en": cfg.publication_terms_en,
        "notice_ar": tr("publication_notice", "ar"),
        "notice_en": tr("publication_notice", "en"),
    }
    return value, digest(value)


def digest(value):
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def intent_digest(intent):
    if intent.expires_at.utcoffset() is None:
        raise ValueError("aware expiry required")
    value = intent.model_dump(mode="json")
    value["expires_at"] = intent.expires_at.astimezone(UTC).isoformat()
    return digest(value)


async def listing(owner):
    async with sessions() as db:
        user = await db.get(User, owner)
        if user is None or user.banned:
            fail(403, "not_allowed")
        rows = (
            await db.execute(
                select(Publication, PublicationRevision.content)
                .outerjoin(
                    PublicationRevision,
                    (PublicationRevision.publication_id == Publication.id)
                    & (PublicationRevision.number == Publication.latest_revision),
                )
                .where(Publication.owner_id == owner, Publication.state != "deleted")
                .order_by(Publication.created_at.desc(), Publication.id.desc())
                .limit(21)
            )
        ).all()
        return {
            "pages": [
                {
                    "id": str(row.id),
                    "reference": row.id.hex[:8],
                    "title": page_title(content, row.id.hex[:8]),
                    "changes_pending": row.state == "published"
                    and row.latest_revision != row.active_revision,
                    "state": "expired" if row.expires_at <= datetime.now(UTC) else row.state,
                    "expires_at": row.expires_at.isoformat(),
                }
                for row, content in rows[:20]
            ],
            "more": len(rows) > 20,
        }


def page_title(content, fallback):
    source = content.get("profile") if type(content) is dict else None
    name = source.get("name") if type(source) is dict else None
    return name if type(name) is str and 1 <= len(name) <= 64 else fallback


async def load(owner, identity):
    current = await repository.review(owner, identity)
    ready = False
    try:
        await prepared_page.render_async(
            current["content"], publication_id=identity, origin=config().publication_origin
        )
        ready = True
    except Exception:
        # A broken/busy renderer must not prevent the owner from stopping access.
        # Never offer publication approval without the exact prepared preview.
        pass
    policy, policy_hash = terms()
    intent = Intent(
        revision=current["revision"],
        expected_active=current["active_revision"],
        expires_at=current["expires_at"],
        content_hash=current["content_hash"],
        terms_hash=policy_hash,
        state=current["state"],
        consent_count=current["consent_count"],
    )
    proof = intent_digest(intent)
    return {
        "_preview_cookie": (
            f"{owner}." + issue(owner, identity.hex, proof, purpose="publication_preview")
        )
        if ready
        else None,
        "review": {
            "preview_url": preview_path(identity) if ready else None,
            "links": current["content"]["profile"]["actions"] if ready else [],
            "public_url": prepared_page.public_url(config().publication_origin, identity),
            "terms": policy,
            "intent": intent.model_dump(mode="json"),
            "token": issue(owner, identity.hex, proof, purpose="publication") if ready else None,
            "stop_token": issue(owner, identity.hex, proof, purpose="publication_suspend")
            if current["active_revision"] is not None
            else None,
            "active": current["active_revision"] == current["revision"],
        },
    }


async def decide(owner, payload):
    if not payload.accepted:
        fail(400, "invalid_request")
    key, reviewed = verify(
        owner,
        payload.token,
        purpose="publication_suspend" if payload.action == "suspend" else "publication",
    )
    if intent_digest(payload.intent) != reviewed or payload.intent.terms_hash != terms()[1]:
        fail(409, "review_changed")
    identity = UUID(hex=key)
    if payload.action == "suspend":
        if payload.intent.expected_active is None:
            fail(400, "invalid_request")
        current = await repository.review(owner, identity)
        if (current["revision"], current["content_hash"], current["expires_at"]) != (
            payload.intent.revision,
            payload.intent.content_hash,
            payload.intent.expires_at,
        ):
            fail(409, "review_changed")
        await repository.suspend(
            owner,
            identity,
            expected_active=payload.intent.expected_active,
            expected_state=payload.intent.state,
            expected_consents=payload.intent.consent_count,
        )
        return {"recorded": True, "action": "suspend"}
    await prepared_page.approve(
        owner,
        identity,
        origin=config().publication_origin,
        revision=payload.intent.revision,
        expected_active=payload.intent.expected_active,
        expected_expires_at=payload.intent.expires_at,
        content_hash=payload.intent.content_hash,
        terms_hash=payload.intent.terms_hash,
        operation_id=payload.operation_id,
        expected_state=payload.intent.state,
        expected_consents=payload.intent.consent_count,
    )
    return {"recorded": True}  # No payment/renewal or claim that an old replay restored a page.


async def handle(request, *, decision=False):
    try:
        if not config().publications_enabled:
            fail(404, "unavailable")
        if request.headers.get("content-type", "").split(";")[0] != "application/json":
            fail(415, "invalid_request")
        schema = DecisionRequest if decision else ViewRequest
        payload = schema.model_validate_json(await body(request, 12288))
        if urlsplit(request.headers.get("origin", "")).scheme != "https":
            fail(403, "not_allowed")
        owner = authorize(request, payload.init_data)
        async with runtime(owner):
            if decision:
                result = await decide(owner, payload)
            elif payload.publication_id:
                result = await load(owner, payload.publication_id)
            else:
                result = await listing(owner)
        cookie = result.pop("_preview_cookie", None)
        response = JSONResponse(result, headers=HEADERS)
        if cookie:
            response.set_cookie(
                PREVIEW_COOKIE,
                cookie,
                max_age=120,
                path=preview_path(payload.publication_id),
                secure=True,
                httponly=True,
                samesite="strict",
            )
        return response
    except InvalidReviewToken:
        fail(409, "review_changed")
    except ValidationError:
        fail(400, "invalid_request")
    except (repository.PublicationError, prepared_page.PreparedPageError):
        fail(409, "review_unavailable")
    except HTTPException:
        raise
    except Exception:
        fail(503, "input_retry")


@router.post("/miniapp/api/publications")
async def view(request: Request):
    return await handle(request)


@router.post("/miniapp/api/publication-consent")
async def consent(request: Request):
    return await handle(request, decision=True)


@router.get("/miniapp/publication-preview/{identity}")
async def preview(request: Request, identity: UUID):
    try:
        if (
            not config().publications_enabled
            or request.headers.get("sec-fetch-site", "same-origin") != "same-origin"
        ):
            fail(404, "unavailable")
        actor, token = request.cookies.get(PREVIEW_COOKIE, "").split(".", 1)
        owner = int(actor)
        repository.identity(owner)
        key, proof = verify(owner, token, purpose="publication_preview")
        if key != identity.hex or time.time() - int(token.rsplit(".", 2)[1]) > 120:
            fail(404, "unavailable")
        async with asyncio.timeout(20):
            await public_http.rate_limit()
            current = await prepared_page.review(
                owner, identity, origin=config().publication_origin
            )
        intent = Intent(
            revision=current["revision"],
            expected_active=current["active_revision"],
            expires_at=current["expires_at"],
            content_hash=current["content_hash"],
            terms_hash=terms()[1],
            state=current["state"],
            consent_count=current["consent_count"],
        )
        if intent_digest(intent) != proof:
            fail(404, "unavailable")
        return public_http.html_response(current["files"]["profile.html"], private=True)
    except HTTPException:
        raise
    except ValueError:
        fail(404, "unavailable")
    except Exception:
        fail(503, "input_retry")
