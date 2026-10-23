"""Strict consent, scoped proofs and rollout/privacy guards without external calls."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.core.settings import config
from app.miniapp import result_review
from app.miniapp.review_tokens import issue, verify
from app.orders.engine import review_revision
from tests.test_miniapp import signed
from tests.test_miniapp_result_review_unit import review as review


@pytest.fixture
def native(monkeypatch):
    monkeypatch.setattr(config(), "miniapp_confirm_enabled", True)
    monkeypatch.setattr(config(), "stars_enabled", False)


async def post(client, token, **changes):
    return await client.post(
        "/miniapp/api/result-decision",
        headers={"Origin": "https://test"},
        json={
            "init_data": signed(user_id=11, issued=int(datetime.now(UTC).timestamp())),
            "token": token,
            "approved": True,
            "accepted": True,
            **changes,
        },
    )


async def test_native_review_proof_tracks_result_and_attempt_not_notification(review, native):
    call, row, *_ = review
    data = (await call()).json()["review"]["decision"]
    assert data["prepared"] is False
    assert verify(11, data["token"], purpose="result") == (
        row.id.hex,
        review_revision(row, 1),
    )
    initial = review_revision(row, 1)
    row.confirmation_notified = True
    row.updated_at = datetime.now(UTC)
    assert review_revision(row, 1) == initial
    assert review_revision(row, 2) != initial
    row.result = {**row.result, "preview": "Revised"}
    assert review_revision(row, 1) != initial


@pytest.mark.parametrize("fallback", ["flag", "stars", "payment", "image"])
async def test_bot_fallback_never_issues_native_proof(review, native, monkeypatch, fallback):
    call, row, _, store, artifact, _ = review
    if fallback == "flag":
        monkeypatch.setattr(config(), "miniapp_confirm_enabled", False)
    elif fallback == "stars":
        monkeypatch.setattr(config(), "stars_enabled", True)
    elif fallback == "payment":
        row.payment_mode = "stars"
    else:
        store.delete(artifact.key, 11)
    assert (await call()).json()["review"]["decision"] is None


async def test_exact_proof_and_consent_pass_to_existing_engine(review, native, monkeypatch):
    call, row, _, _, _, client = review
    token = (await call()).json()["review"]["decision"]["token"]
    apply = AsyncMock()
    monkeypatch.setattr(result_review, "confirm_structure", apply)
    response = await post(client, token)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    apply.assert_awaited_once_with(row.id, 11, True, expected_revision=review_revision(row, 1))


async def test_invalid_or_cross_purpose_decision_never_reaches_engine(review, native, monkeypatch):
    call, row, _, _, _, client = review
    token = (await call()).json()["review"]["decision"]["token"]
    apply = AsyncMock()
    monkeypatch.setattr(result_review, "confirm_structure", apply)
    for changes in (
        {"accepted": False},
        {"accepted": 1},
        {"approved": "true"},
        {"price": 1},
        {"user_id": 22},
    ):
        assert (await post(client, token, **changes)).status_code == 400
    assert (await post(client, issue(11, row.id.hex, review_revision(row, 1)))).status_code == 409
    assert (await post(client, token, init_data="unsigned")).status_code == 401
    assert (
        await post(
            client, token, init_data=signed(user_id=22, issued=int(datetime.now(UTC).timestamp()))
        )
    ).status_code == 409
    apply.assert_not_awaited()


async def test_disabled_stars_and_banned_guards(review, native, monkeypatch):
    call, _, user, _, _, client = review
    token = (await call()).json()["review"]["decision"]["token"]
    user.banned = True
    assert (await post(client, token)).status_code == 403
    monkeypatch.setattr(config(), "stars_enabled", True)
    assert (await post(client, token)).status_code == 404
    monkeypatch.setattr(config(), "stars_enabled", False)
    monkeypatch.setattr(config(), "miniapp_confirm_enabled", False)
    assert (await post(client, token)).status_code == 404
