"""HTTP privacy, content bounds and stale-preview rejection with synthetic storage."""

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from io import BytesIO
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from PIL import Image
from pydantic import SecretStr

from app.api.main import app
from app.core.models import Order, Service, User
from app.core.settings import config
from app.miniapp import result_review
from app.providers.storage import LocalStorage
from app.services.base import Result
from tests.test_miniapp import TOKEN, signed


def png(size=(100, 140)):
    output = BytesIO()
    Image.new("RGB", size, "white").save(output, format="PNG")
    return output.getvalue()


@pytest.fixture
async def review(monkeypatch, tmp_path):
    monkeypatch.setattr(config(), "miniapp_intake_enabled", True)
    monkeypatch.setattr(config(), "bot_token", SecretStr(TOKEN))
    store = LocalStorage(tmp_path)
    artifact = store.save(11, "preview.png", png(), "image/png")
    row = Order(
        id=uuid4(),
        user_id=11,
        service_slug="echo",
        payment_mode="test_credit",
        status="waiting_confirmation",
        result=Result(
            needs_confirmation=True,
            continuation={"private": "do not expose"},
            preview="Summary",
            review_details_localizations={"ar": "تفاصيل كاملة", "en": "Full details"},
            preview_artifacts=[artifact],
        ).model_dump(mode="json"),
    )
    user = SimpleNamespace(banned=False)
    service = Service(name_ar="خدمة", name_en="Service", enabled=False)

    class DB:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, model, key):
            if model is User:
                return user if key == 11 else SimpleNamespace(banned=False)
            if model is Order:
                return row if key == row.id else None
            return service

        async def scalar(self, statement):
            return 1

    @asynccontextmanager
    async def runtime(user_id):
        yield None

    monkeypatch.setattr(result_review, "sessions", DB)
    monkeypatch.setattr(result_review, "runtime", runtime)
    monkeypatch.setattr(result_review, "storage", lambda: store)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="https://test"
    ) as client:

        async def call(*, user_id=11, origin="https://test", extra=None):
            return await client.post(
                "/miniapp/api/result-review",
                headers={"Origin": origin},
                json={
                    "init_data": signed(user_id=user_id, issued=int(datetime.now(UTC).timestamp())),
                    "order_id": str(row.id),
                    **(extra or {}),
                },
            )

        yield call, row, user, store, artifact, client


async def test_owner_gets_complete_review_and_valid_png_without_internal_payloads(review):
    call, row, _, _, artifact, _ = review
    response = await call()
    assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
    data = response.json()["review"]
    assert data["text_ar"] == "تفاصيل كاملة" and data["text_en"] == "Full details"
    assert data["image"].startswith("data:image/png;base64,")
    assert artifact.key not in response.text and "continuation" not in response.text
    assert "do not expose" not in response.text and "cost_sar" not in response.text
    assert row.status == "waiting_confirmation"


async def test_identity_origin_and_client_storage_or_payment_fields_are_rejected(review):
    call, row, user, _, _, _ = review
    assert (await call(user_id=22)).status_code == 404
    assert (await call(extra={"order_id": str(uuid4())})).status_code == 404
    assert (await call(origin="https://other.test")).status_code == 403
    assert (await call(extra={"init_data": "unsigned"})).status_code == 401
    for key in ("key", "approved", "user_id", "price"):
        assert (await call(extra={key: "override"})).status_code == 400
    user.banned = True
    assert (await call()).status_code == 403
    assert row.status == "waiting_confirmation"


@pytest.mark.parametrize("changed", ["queued", "completed", "cancelled", "invalid_result"])
async def test_only_current_valid_waiting_reviews_can_be_read(review, changed):
    call, row, *_ = review
    if changed == "invalid_result":
        row.result = None
    else:
        row.status = changed
    assert (await call()).status_code == 409


@pytest.mark.parametrize(
    "bad", ["expired", "other_owner", "not_png", "oversized", "dimensions", "pixels"]
)
async def test_missing_unsafe_or_unbounded_image_never_leaks_bytes_or_keys(review, bad):
    call, row, _, store, artifact, _ = review
    if bad == "expired":
        store.delete(artifact.key, 11)
    else:
        data = (
            b"<svg>private bytes</svg>"
            if bad == "not_png"
            else b"x" * (3 * 1024 * 1024 + 1)
            if bad == "oversized"
            else png((2049, 1))
            if bad == "dimensions"
            else png((2048, 2048))
            if bad == "pixels"
            else png()
        )
        replacement = store.save(
            22 if bad == "other_owner" else 11, "preview.png", data, "image/png"
        )
        row.result = {**row.result, "preview_artifacts": [replacement.model_dump()]}
    response = await call()
    assert response.status_code == 200
    data = response.json()["review"]
    assert data["image"] is None and data["image_unavailable"] is True
    assert data["text_en"] == "Full details" and "private bytes" not in response.text
    assert "preview_artifacts" not in response.text


@pytest.mark.parametrize("change", ["status", "result", "ban"])
async def test_change_during_storage_read_invalidates_response(review, monkeypatch, change):
    call, row, user, *_ = review

    def changed(*args):
        if change == "status":
            row.status = "queued"
        elif change == "result":
            row.result = {**row.result, "preview": "Changed"}
        else:
            user.banned = True
        return "data:image/png;base64,AA=="

    monkeypatch.setattr(result_review, "preview_image", changed)
    assert (await call()).status_code == (403 if change == "ban" else 409)


async def test_rollout_flag_content_type_and_body_boundaries(review, monkeypatch):
    call, _, _, _, _, client = review
    monkeypatch.setattr(config(), "miniapp_intake_enabled", False)
    assert (await call()).status_code == 404
    monkeypatch.setattr(config(), "miniapp_intake_enabled", True)
    response = await client.post("/miniapp/api/result-review", content="form=data")
    assert response.status_code == 415
    response = await client.post(
        "/miniapp/api/result-review",
        headers={"Content-Type": "application/json"},
        content=b"x" * 10241,
    )
    assert response.status_code == 413


async def test_structural_review_without_image_and_full_text_remains_complete(review):
    call, row, *_ = review
    row.result = {
        **row.result,
        "preview_artifacts": [],
        "review_details_localizations": {"en": "A" * 50000},
    }
    response = await call()
    assert response.status_code == 200
    data = response.json()["review"]
    assert data["image"] is None and data["image_unavailable"] is False
    assert data["text_en"] == "A" * 50000
