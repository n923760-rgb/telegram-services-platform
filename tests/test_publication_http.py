"""Real PostgreSQL HTTP review/consent/publication with synthetic, uncharged pages."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import func, select

from app.api.main import app
from app.core.db import sessions
from app.core.models import Publication, PublicationConsent, User
from app.core.settings import config
from app.publications import prepared_page as prepared
from app.publications import repository
from tests.profile_page_fixtures import plan, profile
from tests.test_publication_http_unit import auth, decision, view
from tests.test_publication_http_unit import enabled as enabled
from tests.test_publications import seed


@pytest.fixture
async def page(enabled):
    order = await seed(11)
    identity = await repository.create(11, order, expires_at=datetime.now(UTC) + timedelta(days=30))
    await prepared.revise(
        11,
        identity,
        profile(),
        plan(),
        origin="https://test",
        embedded_qr=True,
        expected_revision=0,
        operation_id=uuid4(),
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="https://test"
    ) as client:
        yield identity, client


async def test_end_to_end_exact_private_preview_public_consent_and_idempotent_receipt(page):
    identity, client = page
    review = (await view(client, identity)).json()["review"]
    preview = review["html"].encode()
    assert (await client.get(f"/p/{identity}")).status_code == 404
    operation = str(uuid4())
    for _ in range(2):
        response = await decision(client, review, operation_id=operation)
        assert response.status_code == 200 and response.json() == {"recorded": True}
    public = await client.get(f"/p/{identity}")
    assert public.status_code == 200 and public.content == preview
    refreshed = (await view(client, identity)).json()["review"]
    assert refreshed["active"] is True
    async with sessions() as db:
        assert await db.scalar(select(func.count()).select_from(PublicationConsent)) == 1
        receipt = await db.get(PublicationConsent, UUID(operation))
        assert receipt.content_hash == review["intent"]["content_hash"]
        assert receipt.terms_hash == repository.consent_terms_hash(
            review["intent"]["terms_hash"], "draft", 0
        )
    await prepared.revise(
        11,
        identity,
        profile(name="مسودة جديدة"),
        plan(),
        origin="https://test",
        embedded_qr=True,
        expected_revision=1,
        operation_id=uuid4(),
    )
    result = await client.post(
        "/miniapp/api/publications", headers={"Origin": "https://test"}, json={"init_data": auth()}
    )
    assert result.json()["pages"][0]["changes_pending"] is True
    assert (await client.get(f"/p/{identity}")).content == preview


async def test_owner_listing_and_review_cannot_cross_tenants_or_bans(page):
    identity, client = page
    await seed(22)
    assert (await view(client, identity, user=22)).status_code == 409
    listing = await client.post(
        "/miniapp/api/publications", headers={"Origin": "https://test"}, json={"init_data": auth()}
    )
    assert [row["id"] for row in listing.json()["pages"]] == [str(identity)]
    assert listing.json()["pages"][0]["title"] == profile()["name"]
    review = (await view(client, identity)).json()["review"]
    assert (await decision(client, review)).status_code == 200
    async with sessions.begin() as db:
        (await db.get(User, 11)).banned = True
    assert (await client.get(f"/p/{identity}")).status_code == 404
    assert (await view(client, identity)).status_code == 409


@pytest.mark.parametrize("change", ["draft", "expiry", "terms"])
async def test_stale_http_intent_cannot_create_a_consent_receipt(page, monkeypatch, change):
    identity, client = page
    review = (await view(client, identity)).json()["review"]
    if change == "draft":
        await prepared.revise(
            11,
            identity,
            profile(name="نسخة أخرى"),
            plan(),
            origin="https://test",
            embedded_qr=True,
            expected_revision=1,
            operation_id=uuid4(),
        )
    elif change == "expiry":
        async with sessions.begin() as db:
            (await db.get(Publication, identity)).expires_at += timedelta(days=1)
    else:
        monkeypatch.setattr(
            config(), "publication_terms_en", "Changed test hosting terms after private review."
        )
    assert (await decision(client, review)).status_code == 409
    async with sessions() as db:
        assert await db.scalar(select(func.count()).select_from(PublicationConsent)) == 0


@pytest.mark.parametrize("state", ["suspended", "expired", "deleted"])
async def test_public_html_and_every_export_hide_unavailable_publications(page, state):
    identity, client = page
    review = (await view(client, identity)).json()["review"]
    assert (await decision(client, review)).status_code == 200
    if state == "suspended":
        await repository.suspend(11, identity, expected_active=1)
    elif state == "deleted":
        await repository.delete_content(11, identity)
    else:
        async with sessions.begin() as db:
            (await db.get(Publication, identity)).expires_at = datetime.now(UTC) - timedelta(
                seconds=1
            )
    for suffix in ("", "/qr.png", "/qr.svg", "/share-card.png"):
        response = await client.get(f"/p/{identity}{suffix}")
        assert response.status_code == 404 and response.headers["cache-control"] == "no-store"


async def test_old_review_cannot_republish_after_stop_even_when_active_returns_to_none(page):
    identity, client = page
    initial = (await view(client, identity)).json()["review"]
    first_operation = str(uuid4())
    assert (await decision(client, initial, operation_id=first_operation)).status_code == 200
    published = (await view(client, identity)).json()["review"]
    assert published["intent"]["consent_count"] == 1
    stopped = await decision(client, published, action="suspend")
    assert stopped.status_code == 200 and stopped.json()["action"] == "suspend"
    assert (await decision(client, initial)).status_code == 409
    assert (await decision(client, initial, operation_id=first_operation)).status_code == 200
    assert (await client.get(f"/p/{identity}")).status_code == 404
    suspended = (await view(client, identity)).json()["review"]
    assert suspended["intent"]["state"] == "suspended"
    assert (await decision(client, suspended)).status_code == 200
    assert (await decision(client, published, action="suspend")).status_code == 409
    current = (await view(client, identity)).json()["review"]
    assert (await decision(client, current, action="suspend")).status_code == 200
    assert (await decision(client, suspended)).status_code == 409
    assert (await client.get(f"/p/{identity}")).status_code == 404
