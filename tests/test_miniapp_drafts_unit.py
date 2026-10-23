"""Bounded HTTP/auth/state/file checks with injected memory FSM and DB reads."""

import asyncio
import json
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from io import BytesIO
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from PIL import Image, ImageDraw
from pydantic import SecretStr

from app.api.main import app
from app.core.models import Service, User
from app.core.settings import config
from app.miniapp import drafts
from app.services.registry import registry
from tests.test_miniapp import TOKEN, signed


def image():
    picture = Image.new("RGB", (64, 64), "white")
    ImageDraw.Draw(picture).line((0, 0, 63, 63), fill="black", width=3)
    output = BytesIO()
    picture.save(output, format="PNG")
    return output.getvalue()


@pytest.fixture
async def intake(monkeypatch, tmp_path):
    cfg = config()
    for name, value in {
        "miniapp_intake_enabled": True,
        "bot_token": SecretStr(TOKEN),
        "miniapp_bot_username": "ExampleBot",
        "stars_enabled": False,
        "storage_root": tmp_path,
        "ai_enabled": True,
    }.items():
        monkeypatch.setattr(cfg, name, value)
    monkeypatch.setattr(registry.types["echo"], "admin_only", False)
    rows = {
        slug: Service(
            slug=slug,
            name_ar=p.name_ar,
            name_en=p.name_en,
            description_ar=p.description_ar,
            enabled=True,
            version=p.version,
            input_schema=p.input_schema.model_dump(),
            price_halala=100,
            price_stars=8,
        )
        for slug, p in registry.types.items()
    }
    users = {n: SimpleNamespace(banned=False) for n in (11, 22)}
    accepted = {"value": False}

    class DB:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, model, key):
            return users.get(key) if model is User else rows.get(key)

        async def scalar(self, query):
            return "accepted" if accepted["value"] else None

    monkeypatch.setattr(drafts, "sessions", DB)

    async def available(db):
        return cfg.ai_enabled

    monkeypatch.setattr(drafts, "ai_admission_available", available)
    store = MemoryStorage()
    states, locks = {}, {}

    @asynccontextmanager
    async def runtime(user_id):
        state = states.setdefault(
            user_id, FSMContext(store, StorageKey(bot_id=12345, chat_id=user_id, user_id=user_id))
        )
        async with locks.setdefault(user_id, asyncio.Lock()):
            yield state

    monkeypatch.setattr(drafts, "runtime", runtime)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="https://test",
        headers={"Origin": "https://test", "Sec-Fetch-Site": "same-origin"},
    ) as client:
        yield SimpleNamespace(
            client=client, rows=rows, users=users, states=states, accepted=accepted
        )
    await store.close()


def auth(user=11):
    return signed(user_id=user, issued=int(datetime.now(UTC).timestamp()))


async def call(intake, action="view", *, user=11, **values):
    return await intake.client.post(
        "/miniapp/api/draft", json={"init_data": auth(user), "action": action, **values}
    )


async def opened(intake, slug="echo"):
    result = await call(intake, "open", slug=slug)
    assert result.status_code == 200, result.text
    return result.json()["draft"]


def operation(view, **values):
    return {"revision": view["revision"], "operation": uuid4().hex, **values}


async def uploaded(intake, view, content=None, *, user=11, metadata=None):
    metadata = metadata or operation(view)
    return await intake.client.post(
        "/miniapp/api/draft/upload",
        content=image() if content is None else content,
        headers={
            "Content-Type": "image/png",
            "X-Telegram-Init-Data": auth(user),
            "X-Draft-Revision": metadata["revision"],
            "X-Draft-Operation": metadata["operation"],
        },
    )


async def test_shared_draft_is_unsubmitted_and_replayed_without_duplicate(intake):
    initial = await opened(intake)
    args = operation(initial, value="Customer content")
    first = await call(intake, "answer", **args)
    assert first.status_code == 200
    assert first.json()["draft"]["ready"]
    saved = await intake.states[11].get_data()
    assert saved["inputs"] == {"text": "Customer content"}
    assert saved["pending_prompt"] and await intake.states[11].get_state() == "confirm"
    second = await call(intake, "answer", **args)
    assert second.json() == first.json()
    assert await intake.states[11].get_data() == saved
    changed = await call(intake, "answer", **{**args, "value": "different"})
    assert changed.status_code == 409
    assert (await call(intake, "open", slug="csv_review")).json() == first.json()


async def test_private_owner_and_no_client_identity_override(intake):
    initial = await opened(intake)
    await call(intake, "answer", **operation(initial, value="private"))
    assert (await call(intake, user=22)).json() == {"draft": None}
    rejected = await call(intake, user_id=11)
    assert rejected.status_code == 400 and "private" not in rejected.text
    assert "inputs" not in (await call(intake)).json()["draft"]
    assert (await call(intake, user=999)).status_code == 403


@pytest.mark.parametrize(
    "headers",
    [
        {"Origin": "https://other.test"},
        {"Origin": "null"},
        {"Origin": ""},
        {"Sec-Fetch-Site": "cross-site"},
    ],
)
async def test_cross_origin_cannot_write(intake, headers):
    response = await intake.client.post(
        "/miniapp/api/draft",
        json={"init_data": auth(), "action": "open", "slug": "echo"},
        headers=headers,
    )
    assert response.status_code == 403
    assert response.headers["cache-control"] == "no-store"
    assert not intake.states


async def test_auth_ban_flag_and_bounded_json_fail_closed(intake, monkeypatch):
    response = await intake.client.post(
        "/miniapp/api/draft", json={"init_data": "unsigned", "action": "open", "slug": "echo"}
    )
    assert response.status_code == 401
    intake.users[11].banned = True
    assert (await call(intake)).status_code == 403
    intake.users[11].banned = False
    monkeypatch.setattr(config(), "miniapp_intake_enabled", False)
    assert (await call(intake)).status_code == 404
    monkeypatch.setattr(config(), "miniapp_intake_enabled", True)
    response = await intake.client.post(
        "/miniapp/api/draft", content=b"x" * 65537, headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 413
    assert not intake.states


@pytest.mark.parametrize(
    "action,value",
    [("skip", None), ("answer", ""), ("answer", "   "), ("answer", "a" * 12001), ("done", None)],
)
async def test_invalid_answer_keeps_draft_unchanged(intake, action, value):
    initial = await opened(intake)
    before = await intake.states[11].get_data()
    result = await call(intake, action, **operation(initial, value=value))
    assert result.status_code == 400
    assert await intake.states[11].get_data() == before


async def test_bot_change_stales_browser_and_accepted_draft_cannot_edit(intake):
    initial = await opened(intake)
    data = await intake.states[11].get_data()
    data["pending_prompt"] = False  # Bot has rendered its prompt.
    await intake.states[11].set_data(data)
    assert (await call(intake, "answer", **operation(initial, value="stale"))).status_code == 409
    intake.accepted["value"] = True
    assert (await call(intake)).status_code == 409
    assert (await intake.states[11].get_data())["inputs"] == {}


@pytest.mark.parametrize("change", ["price", "version", "schema", "disabled", "payment", "paused"])
async def test_current_contract_gates_every_edit(intake, monkeypatch, change):
    initial = await opened(intake)
    if change == "price":
        intake.rows["echo"].price_halala = 200
    if change == "version":
        intake.rows["echo"].version = "changed"
    if change == "schema":
        intake.rows["echo"].input_schema = {"fields": []}
    if change == "disabled":
        intake.rows["echo"].enabled = False
    if change == "payment":
        monkeypatch.setattr(config(), "stars_enabled", True)
    if change == "paused":
        monkeypatch.setattr(registry.types["echo"], "requires_ai", True)
        monkeypatch.setattr(config(), "ai_enabled", False)
    result = await call(intake, "answer", **operation(initial, value="not saved"))
    assert result.status_code in {400, 409}
    assert (await intake.states[11].get_data())["inputs"] == {}


async def test_upload_replay_multiple_done_skip_choice_and_owner_storage(intake):
    initial = await opened(intake, "images_to_pdf")
    meta = operation(initial)
    response = await uploaded(intake, initial, metadata=meta)
    assert response.status_code == 200
    view = response.json()["draft"]
    assert view["field"]["received"] == 1
    duplicate = await uploaded(intake, initial, metadata=meta)
    assert duplicate.json() == response.json()
    state = await intake.states[11].get_data()
    keys = state["inputs"]["images"]
    assert len(keys) == 1 and keys[0].startswith("11/") and keys[0].endswith(".png")
    assert keys[0] not in json.dumps(response.json())
    from app.providers.runtime import storage

    assert storage().read(keys[0], 11) == image()
    view = (await call(intake, "done", **operation(view))).json()["draft"]
    assert view["field"]["index"] == 1
    view = (await call(intake, "skip", **operation(view))).json()["draft"]
    assert view["field"]["choices"][0]["value"] == "auto"
    ready = (await call(intake, "answer", **operation(view, value="auto"))).json()["draft"]
    assert ready["ready"] and "11/" not in json.dumps(ready)
    assert ready["request_url"] == "https://t.me/ExampleBot?start=request_images_to_pdf"


async def test_upload_cannot_accept_keys_invalid_bytes_or_oversized_body(intake, monkeypatch):
    initial = await opened(intake, "images_to_pdf")
    assert (
        await call(intake, "answer", **operation(initial, value="22/" + "a" * 32 + "/input.png"))
    ).status_code == 400
    assert (await uploaded(intake, initial, b"not an image")).status_code == 400
    monkeypatch.setattr(config(), "max_file_bytes", 10)
    result = await uploaded(intake, initial, b"a" * 11)
    assert result.status_code == 413
    assert (await intake.states[11].get_data())["inputs"] == {}


async def test_edit_abort_and_old_confirmation_key_invalidated(intake):
    initial = await opened(intake)
    ready = (await call(intake, "answer", **operation(initial, value="original"))).json()["draft"]
    previous_key = (await intake.states[11].get_data())["key"]
    editing = (await call(intake, "edit", **operation(ready, index=0))).json()["draft"]
    assert editing["editing"]
    restored = (await call(intake, "abort", **operation(editing))).json()["draft"]
    assert restored["ready"] and not restored["editing"]
    saved = await intake.states[11].get_data()
    assert saved["inputs"] == {"text": "original"} and saved["key"] != previous_key


async def test_concurrent_duplicate_answers_are_serialized(intake):
    initial = await opened(intake)
    args = operation(initial, value="one answer")
    a, b = await asyncio.gather(call(intake, "answer", **args), call(intake, "answer", **args))
    assert a.status_code == b.status_code == 200 and a.json() == b.json()


async def test_committed_but_response_failed_can_retry_without_reapplying(intake, monkeypatch):
    initial = await opened(intake)
    actual = drafts.persist

    async def lost_response(state, data):
        await actual(state, data)
        raise OSError("synthetic acknowledgement failure")

    monkeypatch.setattr(drafts, "persist", lost_response)
    args = operation(initial, value="once")
    assert (await call(intake, "answer", **args)).status_code == 503
    saved = await intake.states[11].get_data()
    monkeypatch.setattr(drafts, "persist", actual)
    result = await call(intake, "answer", **args)
    assert result.status_code == 200 and result.json()["draft"]["ready"]
    assert await intake.states[11].get_data() == saved


async def test_mixed_ai_choice_is_only_hint_until_server_checks_it(intake, monkeypatch):
    mode = await opened(intake, "pdf_tables_excel")
    monkeypatch.setattr(config(), "ai_enabled", False)
    refreshed = (await call(intake)).json()["draft"]
    assert any(c["value"] == "labels" and c["blocked"] for c in refreshed["field"]["choices"])
    assert (await call(intake, "answer", **operation(mode, value="labels"))).status_code == 409
    assert (await call(intake, "answer", **operation(refreshed, value="direct"))).status_code == 200


async def test_file_quota_rejection_preserves_draft(intake, monkeypatch):
    initial = await opened(intake, "images_to_pdf")
    monkeypatch.setattr(config(), "storage_quota_bytes", 1)
    result = await uploaded(intake, initial)
    assert result.status_code == 400 and result.json()["detail"] == "storage_quota"
    assert (await intake.states[11].get_data())["inputs"] == {}
