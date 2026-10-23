"""Real DB/Redis: review reads preserve money, jobs, bot FSM and notification state."""

from datetime import UTC, datetime

import httpx
import pytest
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.redis import RedisStorage
from pydantic import SecretStr
from sqlalchemy import select

from app.api.main import app
from app.core.db import sessions
from app.core.models import Job, Ledger, Order, Service
from app.core.settings import config
from app.orders.engine import submit
from app.providers.storage import LocalStorage
from app.services.base import Result
from app.wallet.ledger import balance
from tests.test_foundation import fund
from tests.test_miniapp import TOKEN, signed
from tests.test_miniapp_result_review_unit import png


@pytest.mark.parametrize("visual", [False, True])
async def test_preview_reads_leave_reservation_job_fsm_and_original_files_unchanged(
    monkeypatch, tmp_path, visual
):
    monkeypatch.setattr(config(), "bot_token", SecretStr(TOKEN))
    monkeypatch.setattr(config(), "miniapp_intake_enabled", True)
    monkeypatch.setattr(config(), "storage_root", tmp_path)
    await fund(11)
    oid = await submit(11, "echo", {"text": "Private input"}, 100, "review-read")
    store = LocalStorage(tmp_path)
    preview = store.save(11, "preview.png", png(), "image/png")
    original = store.save(11, "result.docx", b"synthetic original", "application/octet-stream")
    result = Result(
        needs_confirmation=True,
        continuation={"private": "continuation"},
        preview="Review this structure",
        prepared_delivery=visual,
        artifacts=[original] if visual else [],
        preview_artifacts=[preview] if visual else [],
    )
    async with sessions.begin() as db:
        order = await db.get(Order, oid)
        order.status, order.result = "waiting_confirmation", result.model_dump(mode="json")
        (await db.get(Service, "echo")).enabled = False
    redis = RedisStorage.from_url(config().redis_url.get_secret_value())
    key = StorageKey(bot_id=12345, chat_id=11, user_id=11)
    names = [redis.key_builder.build(key, p) for p in ("state", "data", "lock")] + ["rate:11"]
    await redis.redis.delete(*names)
    await redis.set_state(key, "support")
    await redis.set_data(key, {"saved": "Independent bot session"})
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="https://test"
        ) as client:
            for _ in range(2):
                response = await client.post(
                    "/miniapp/api/result-review",
                    headers={"Origin": "https://test"},
                    json={
                        "init_data": signed(user_id=11, issued=int(datetime.now(UTC).timestamp())),
                        "order_id": str(oid),
                    },
                )
                assert response.status_code == 200
                assert bool(response.json()["review"]["image"]) is visual
                assert original.key not in response.text and "continuation" not in response.text
        assert await redis.get_state(key) == "support"
        assert await redis.get_data(key) == {"saved": "Independent bot session"}
        assert store.read(original.key, 11) == b"synthetic original"
        assert store.read(preview.key, 11) == png()
        async with sessions() as db:
            order = await db.get(Order, oid)
            assert order.status == "waiting_confirmation" and order.result == result.model_dump(
                mode="json"
            )
            assert order.confirmation_notified is False
            assert (await db.scalar(select(Job).where(Job.order_id == oid))).status == "pending"
            assert (await balance(db, 11)).reserved == 100
            assert list(await db.scalars(select(Ledger.kind).where(Ledger.order_id == oid))) == [
                "reserve"
            ]
    finally:
        await redis.redis.delete(*names)
        await redis.close()
