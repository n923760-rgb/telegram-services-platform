"""HTTP auth, consent integrity, default gates and bounded anonymous rendering."""

import asyncio
import json
import re
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from threading import Event
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from fastapi import HTTPException
from pydantic import SecretStr, ValidationError

from app.api import publications as public
from app.api.main import app
from app.core.settings import Config, config
from app.miniapp import publications as owner
from app.miniapp.review_tokens import issue
from app.publications import prepared_page as prepared
from app.publications import repository
from tests.profile_page_fixtures import plan, profile
from tests.test_miniapp import TOKEN, signed

ORIGIN = "https://test"
RATE_LIMIT = public.rate_limit


@pytest.fixture(autouse=True)
def database():
    pass


@pytest.fixture
def enabled(monkeypatch):
    cfg = config()
    for key, value in {
        "publications_enabled": True,
        "miniapp_intake_enabled": True,
        "publication_origin": ORIGIN,
        "bot_token": SecretStr(TOKEN),
        "publication_terms_version": "test-v1",
        "publication_terms_ar": "شروط استضافة افتراضية للاختبار فقط.",
        "publication_terms_en": "Synthetic hosting terms for tests only.",
    }.items():
        monkeypatch.setattr(cfg, key, value)

    @asynccontextmanager
    async def runtime(_):
        yield None

    async def limit():
        pass

    monkeypatch.setattr(owner, "runtime", runtime)
    monkeypatch.setattr(public, "rate_limit", limit)


@pytest.fixture
async def http(enabled):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url=ORIGIN) as client:
        yield client


def auth(user=11):
    return signed(user_id=user, issued=int(datetime.now(UTC).timestamp()))


@pytest.fixture
def source(monkeypatch):
    identity = uuid4()
    content = prepared.prepare(profile(), plan(), publication_id=identity, origin=ORIGIN)
    data = {
        "revision": 1,
        "active_revision": None,
        "expires_at": datetime.now(UTC) + timedelta(days=30),
        "content_hash": repository.content_snapshot(content)[1],
        "content": content,
        "state": "draft",
        "consent_count": 0,
    }
    calls = []

    async def review(user, key):
        if user != 11 or key != identity:
            raise repository.PublicationError("unavailable")
        return data

    async def approve(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(repository, "review", review)
    monkeypatch.setattr(prepared, "approve", approve)
    return identity, data, calls


async def view(http, identity, *, user=11, origin=ORIGIN, extra=None):
    return await http.post(
        "/miniapp/api/publications",
        headers={"Origin": origin},
        json={"init_data": auth(user), "publication_id": str(identity), **(extra or {})},
    )


async def decision(http, review, *, user=11, **extra):
    return await http.post(
        "/miniapp/api/publication-consent",
        headers={"Origin": ORIGIN},
        json={
            "init_data": auth(user),
            "token": review["stop_token"] if extra.get("action") == "suspend" else review["token"],
            "intent": review["intent"],
            "operation_id": str(uuid4()),
            "accepted": True,
            **extra,
        },
    )


async def test_owner_gets_full_sandboxable_page_exact_terms_and_separate_consent(http, source):
    identity, data, calls = source
    response = await view(http, identity)
    assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
    review = response.json()["review"]
    assert "set-cookie" not in response.headers
    assert review["html"].startswith("<!doctype html>")
    assert "استوديو مدى" in review["html"] and "init_data" not in review["html"]
    assert review["public_url"] == f"{ORIGIN}/p/{identity.hex}"
    assert review["intent"]["content_hash"] == data["content_hash"]
    assert review["terms"]["notice_ar"] and review["terms"]["en"]
    assert review["links"] == profile()["actions"]
    assert calls == []
    assert (await decision(http, review)).status_code == 200
    assert calls[0][1]["expected_expires_at"] == data["expires_at"]
    assert calls[0][1]["content_hash"] == data["content_hash"]


@pytest.mark.parametrize(
    "change",
    [
        "owner",
        "terms",
        "expiry",
        "content",
        "revision",
        "active",
        "accepted",
        "purpose",
        "state",
        "count",
        "expired",
    ],
)
async def test_review_proof_cannot_be_transferred_or_rewritten(http, source, monkeypatch, change):
    identity, _, calls = source
    review = (await view(http, identity)).json()["review"]
    extra = {}
    if change == "owner":
        extra["user"] = 22
    elif change == "terms":
        monkeypatch.setattr(
            config(), "publication_terms_en", "Changed terms after the review was shown."
        )
    elif change == "expiry":
        review["intent"]["expires_at"] = (datetime.now(UTC) + timedelta(days=90)).isoformat()
    elif change == "content":
        review["intent"]["content_hash"] = "a" * 64
    elif change == "revision":
        review["intent"]["revision"] = 2
    elif change == "active":
        review["intent"]["expected_active"] = 1
    elif change == "state":
        review["intent"]["state"] = "suspended"
    elif change == "count":
        review["intent"]["consent_count"] = 9
    elif change == "expired":
        review["token"] = issue(
            11,
            identity.hex,
            owner.intent_digest(owner.Intent.model_validate_json(json.dumps(review["intent"]))),
            purpose="publication",
            now=int(datetime.now(UTC).timestamp()) - 3601,
        )
    elif change == "accepted":
        extra["accepted"] = False
    else:
        review["token"] = issue(
            11,
            identity.hex,
            owner.intent_digest(owner.Intent.model_validate_json(json.dumps(review["intent"]))),
            purpose="result",
        )
    assert (await decision(http, review, **extra)).status_code in {400, 409}
    assert calls == []


@pytest.mark.parametrize("origin", ["https://other.invalid", "http://test", "null", ""])
async def test_private_review_rejects_cross_origin_even_with_signed_identity(http, source, origin):
    assert (await view(http, source[0], origin=origin)).status_code == 403


async def test_unsigned_wrong_owner_oversized_or_extra_identity_cannot_read(http, source):
    identity = source[0]
    assert (await view(http, identity, user=22)).status_code == 409
    assert (await view(http, identity, extra={"owner_id": 11})).status_code == 400
    response = await http.post(
        "/miniapp/api/publications", headers={"Origin": ORIGIN}, json={"init_data": "unsigned"}
    )
    assert response.status_code == 401
    response = await http.post(
        "/miniapp/api/publications",
        headers={"Origin": ORIGIN, "Content-Type": "application/json"},
        content=b"x" * 12289,
    )
    assert response.status_code == 413


async def test_disabled_routes_reject_before_db_or_anonymous_limit(http, monkeypatch):
    monkeypatch.setattr(config(), "publications_enabled", False)
    assert (await view(http, uuid4())).status_code == 404
    assert (await http.get(f"/p/{uuid4()}")).status_code == 404
    assert (
        await http.post("/miniapp/api/publication-consent", headers={"Origin": ORIGIN}, json={})
    ).status_code == 404


async def test_public_page_and_downloads_have_strict_headers_and_never_expose_drafts(
    http, source, monkeypatch
):
    identity, data, _ = source
    visible = False

    async def content(key):
        return data["content"] if visible and str(key) == str(identity) else None

    monkeypatch.setattr(repository, "public_content", content)
    assert (await http.get(f"/p/{identity}")).status_code == 404
    visible = True
    page = await http.get(f"/p/{identity}")
    assert page.status_code == 200 and page.headers["cache-control"] == "no-store"
    assert "sha256-" in page.headers["content-security-policy"]
    assert "frame-ancestors 'none'" in page.headers["content-security-policy"]
    assert "init_data" not in page.text and '"content_hash"' not in page.text
    for filename, mime in public.MIMES.items():
        result = await http.get(f"/p/{identity}/{filename}")
        assert result.status_code == 200 and mime in result.headers["content-type"]
        assert result.headers["content-disposition"] == f'attachment; filename="{filename}"'
    assert (await http.get(f"/p/{identity}/snapshot.json")).status_code == 404
    data["content"]["digests"]["profile.html"] = "a" * 64
    assert (await http.get(f"/p/{identity}")).status_code == 404


async def test_public_limiter_fails_closed_without_exposing_backend_failure(http, monkeypatch):
    async def failed():
        raise RuntimeError("private backend failure")

    monkeypatch.setattr(public, "rate_limit", failed)
    result = await http.get(f"/p/{uuid4()}")
    assert result.status_code == 503 and "private" not in result.text


@pytest.mark.parametrize("change", ["ban", "revision"])
async def test_private_review_rechecks_owner_and_version_after_native_work(
    http, source, monkeypatch, change
):
    identity, current, _ = source
    original = repository.review
    calls = 0

    async def changing(user, key):
        nonlocal calls
        calls += 1
        if calls > 1:
            if change == "ban":
                raise repository.PublicationError("unavailable")
            current["revision"] = 2
        return await original(user, key)

    monkeypatch.setattr(repository, "review", changing)
    response = await view(http, identity)
    assert response.status_code == 409 and "استوديو" not in response.text


async def test_private_preview_style_nonce_is_fresh_and_does_not_relax_scripts(http, monkeypatch):
    pages = [await http.get("/miniapp") for _ in range(2)]
    nonces = []
    for page in pages:
        nonce = re.search(r'name="publication-style-nonce" content="([A-Za-z0-9_-]+)"', page.text)[
            1
        ]
        nonces.append(nonce)
        policy = page.headers["content-security-policy"]
        assert f"'nonce-{nonce}'" in policy
        assert "script-src 'self' https://telegram.org;" in policy
        assert "form-action 'none'" in policy and "unsafe-inline" not in policy
        assert page.headers["cache-control"] == "no-store"
    assert nonces[0] != nonces[1]
    monkeypatch.setattr(config(), "publications_enabled", False)
    disabled = await http.get("/miniapp")
    assert "publication-style-nonce" not in disabled.text
    assert "'nonce-" not in disabled.headers["content-security-policy"]


@pytest.mark.parametrize("count", [120, 121])
async def test_global_anonymous_quota_and_connection_cleanup(monkeypatch, count):
    closed = []

    class Client:
        async def eval(self, *args):
            assert args[1:] == (1, "publication-read:global", 60)
            return count

        async def aclose(self):
            closed.append(True)

    monkeypatch.setattr(public, "Redis", SimpleNamespace(from_url=lambda *args, **kwargs: Client()))
    if count == 121:
        with pytest.raises(HTTPException) as failure:
            await RATE_LIMIT()
        assert failure.value.status_code == 429 and failure.value.headers["Retry-After"] == "60"
    else:
        await RATE_LIMIT()
    assert closed == [True]


async def test_native_concurrency_limit_remains_held_after_request_cancellation(monkeypatch):
    slots = asyncio.Semaphore(2)
    monkeypatch.setattr(prepared, "_render_slots", slots)
    entered = [Event(), Event()]
    release = Event()
    count = 0

    def render(*args, **kwargs):
        nonlocal count
        index = count
        count += 1
        entered[index].set()
        assert release.wait(5)
        return {}

    monkeypatch.setattr(prepared, "render", render)
    tasks = [
        asyncio.create_task(prepared.render_async({}, publication_id=uuid4(), origin=ORIGIN))
        for _ in range(2)
    ]
    try:
        for event in entered:
            assert await asyncio.to_thread(event.wait, 3)
        tasks[0].cancel()
        with pytest.raises(asyncio.CancelledError):
            await tasks[0]
        with pytest.raises(prepared.RenderBusy):
            await prepared.render_async({}, publication_id=uuid4(), origin=ORIGIN)
        assert count == 2 and slots.locked()
    finally:
        release.set()
        await asyncio.gather(*tasks, return_exceptions=True)
        await asyncio.gather(*list(prepared._renders), return_exceptions=True)
        await asyncio.sleep(0)
    assert slots._value == 2


def config_values(**extra):
    return {
        "_env_file": None,
        "publications_enabled": True,
        "miniapp_intake_enabled": True,
        "bot_token": TOKEN,
        "publication_origin": ORIGIN,
        "publication_terms_version": "test-v1",
        "publication_terms_ar": "شروط افتراضية للاختبار فقط.",
        "publication_terms_en": "Synthetic hosting terms for tests only.",
        **extra,
    }


@pytest.mark.parametrize(
    "extra",
    [
        {"publication_origin": "http://test"},
        {"publication_origin": "https://test/path"},
        {"publication_origin": "https://test:bad"},
        {"publication_origin": "https://user:password@test"},
        {"publication_terms_en": ""},
        {"publication_terms_version": ""},
        {"miniapp_intake_enabled": False},
        {"bot_token": ""},
    ],
)
def test_activation_requires_explicit_safe_configuration(extra):
    with pytest.raises(ValidationError):
        Config(**config_values(**extra))


def test_publications_default_off_and_valid_config_does_not_invent_a_price():
    assert not Config(_env_file=None).publications_enabled
    assert Config(**config_values()).publications_enabled


@pytest.mark.parametrize(
    "state,count", [("deleted", 0), ([], 0), ("draft", True), ("draft", -1), ("draft", 2**63)]
)
async def test_invalid_review_gate_is_rejected_before_db(state, count):
    with pytest.raises(repository.PublicationError, match="invalid_input"):
        await repository.publish(
            1,
            uuid4(),
            revision=1,
            expected_active=None,
            terms_hash="a" * 64,
            operation_id=uuid4(),
            expected_state=state,
            expected_consents=count,
        )


async def test_renderer_failure_never_offers_publication_but_owner_can_still_stop(
    http, source, monkeypatch
):
    identity, current, _ = source
    current.update(state="published", active_revision=1, consent_count=1)
    current["content"]["digests"]["profile.html"] = "a" * 64
    response = await view(http, identity)
    review = response.json()["review"]
    assert review["html"] is None and review["token"] is None
    assert review["stop_token"] and "set-cookie" not in response.headers
    stopped = []

    async def suspend(*args, **kwargs):
        stopped.append(kwargs)

    monkeypatch.setattr(repository, "suspend", suspend)
    assert (await decision(http, review)).status_code == 400
    response = await decision(http, review, action="suspend")
    assert response.status_code == 200 and stopped[0]["expected_consents"] == 1


def test_receipt_commitment_includes_state_and_immutable_consent_count():
    base = "a" * 64
    assert repository.consent_terms_hash(base, None, None) == base
    assert (
        len(
            {
                repository.consent_terms_hash(base, "draft", 0),
                repository.consent_terms_hash(base, "suspended", 1),
                repository.consent_terms_hash(base, "suspended", 2),
            }
        )
        == 3
    )
