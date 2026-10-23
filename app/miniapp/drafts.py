"""Authenticated intake into the bot's existing, isolated, expiring request FSM.

No order submission, provider call, invoice or wallet write belongs here.
"""

import asyncio
import hashlib
import json
from contextlib import asynccontextmanager
from copy import deepcopy
from typing import Literal
from urllib.parse import urlsplit

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.redis import RedisStorage
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import select

from app.bot.availability import ai_admission_available, declared_ai_choices
from app.bot.draft_edit import abort_edit, advance, begin_edit, next_index
from app.bot.middleware import RATE_LUA
from app.bot.order_review import confirmation_text, field_label
from app.core.db import sessions
from app.core.i18n import tr
from app.core.models import Order, Service, User
from app.core.settings import config
from app.files.uploads import save_upload
from app.miniapp.auth import InvalidMiniAppAuth, verify_init_data
from app.orders.drafts import new_draft
from app.payments.stars import terms_hash
from app.services.base import InputSchema, ServiceError, active_field, get_input, set_input
from app.services.registry import registry

router = APIRouter()
HEADERS = {"Cache-Control": "no-store"}


class DraftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    init_data: str = Field(min_length=1, max_length=8192)
    action: Literal["view", "open", "answer", "skip", "done", "edit", "abort"] = "view"
    slug: str | None = Field(default=None, pattern=r"^[a-z][a-z0-9_]{0,39}$")
    revision: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    operation: str | None = Field(default=None, pattern=r"^[a-f0-9]{32}$")
    value: str | None = Field(default=None, max_length=12000)
    index: int | None = Field(default=None, ge=0, le=1000)


def fail(status, key):
    raise HTTPException(status, key, headers=HEADERS)


def authorize(request, raw):
    if not config().miniapp_intake_enabled:
        fail(404, "unavailable")
    # Signed initData is a bearer credential. Never allow another origin to use it
    # through cookie authentication, permissive CORS, or form posts.
    origin = urlsplit(request.headers.get("origin", ""))
    if (
        origin.scheme not in {"http", "https"}
        or origin.netloc != request.url.netloc
        or origin.path
        or origin.query
        or origin.fragment
        or request.headers.get("sec-fetch-site", "same-origin") != "same-origin"
    ):
        fail(403, "not_allowed")
    try:
        return verify_init_data(raw, config().bot_token.get_secret_value())
    except InvalidMiniAppAuth:
        fail(401, "not_allowed")


async def body(request, limit):
    content = bytearray()
    async with asyncio.timeout(20):
        async for chunk in request.stream():
            if len(content) + len(chunk) > limit:
                fail(413, "file_invalid")
            content.extend(chunk)
    return bytes(content)


@asynccontextmanager
async def runtime(user_id):
    store = RedisStorage.from_url(
        config().redis_url.get_secret_value(),
        state_ttl=3600,
        data_ttl=3600,
        connection_kwargs={"socket_connect_timeout": 5, "socket_timeout": 5},
    )
    key = StorageKey(
        bot_id=int(config().bot_token.get_secret_value().split(":", 1)[0]),
        chat_id=user_id,
        user_id=user_id,
    )
    try:
        count = await store.redis.eval(RATE_LUA, 1, f"rate:{user_id}", 60)
        if count > 30:
            fail(429, "rate_limited")
        # Identical default key builder and lock namespace to create_dispatcher.
        async with store.create_isolation(lock_kwargs={"timeout": 60, "blocking_timeout": 5}).lock(
            key
        ):
            async with asyncio.timeout(45):
                yield FSMContext(storage=store, key=key)
    finally:
        await store.close()


async def persist(state, data):
    data["pending_prompt"] = True
    fields = InputSchema.model_validate(data["schema"]).conversation()
    data["index"] = next_index(data, fields)
    stage = "confirm" if data["index"] >= len(fields) else "collect"
    if stage == "confirm":
        InputSchema.model_validate(data["schema"]).validate_inputs(data["inputs"])
    store = state.storage
    # Production writes both FSM records and expiry together, under the same lock
    # used by bot updates. MemoryStorage remains injectable for isolated unit tests.
    if isinstance(store, RedisStorage):
        async with store.redis.pipeline(transaction=True) as pipe:
            pipe.set(store.key_builder.build(state.key, "data"), store.json_dumps(data), ex=3600)
            pipe.set(store.key_builder.build(state.key, "state"), stage, ex=3600)
            await pipe.execute()
    else:
        await state.set_data(data)
        await state.set_state(stage)


def revision(data):
    value = {k: v for k, v in data.items() if k != "_miniapp_last"}
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


async def service_for(db, user_id, slug, data=None):
    user = await db.get(User, user_id)
    # A private bot conversation must have registered this account first.
    if user is None or user.banned:
        fail(403, "not_allowed")
    service = await db.get(Service, slug)
    plugin = registry.types.get(slug)
    if (
        not service
        or not service.enabled
        or not registry.can_request(slug, admin=user_id in config().admin_ids)
    ):
        fail(409, "unavailable")
    if config().stars_enabled and service.price_stars is None:
        fail(409, "unavailable")
    schema = InputSchema.model_validate(service.input_schema)
    if service.version != plugin.version or schema != plugin.input_schema:
        fail(409, "service_changed")
    ai_available = await ai_admission_available(db)
    if not ai_available and plugin.requires_ai:
        fail(409, "service_ai_unavailable")
    if data:
        if await db.scalar(
            select(Order.id).where(Order.user_id == user_id, Order.idempotency_key == data["key"])
        ):
            fail(409, "review_edit_submitted")
        if data["version"] != service.version or data["schema"] != service.input_schema:
            fail(409, "service_changed")
        stars = data.get("payment_mode") == "stars"
        if stars != config().stars_enabled or (
            stars
            and (
                data.get("terms_version") != config().stars_terms_version
                or data.get("terms_hash") != terms_hash()
            )
        ):
            fail(409, "payment_changed")
        if data["price"] != service.price_halala or (
            stars and data.get("stars_price") != service.price_stars
        ):
            fail(409, "price_changed")
    return service, ai_available


def view(data, ai_available):
    schema = InputSchema.model_validate(data["schema"])
    fields = schema.conversation()
    data = deepcopy(data)
    index = next_index(data, fields)
    ready = index >= len(fields)
    output = {
        "slug": data["slug"],
        "name_ar": data["name_ar"],
        "name_en": data["name_en"],
        "revision": revision(data),
        "ready": ready,
        "editing": "_edit_original" in data,
        "field": None,
        "review": None,
        "request_url": f"https://t.me/{config().miniapp_bot_username}?start=request_{data['slug']}"
        if config().miniapp_bot_username
        else None,
    }
    if ready:
        schema.validate_inputs(data["inputs"])
        output["review"] = {lang: confirmation_text(data, lang) for lang in ("ar", "en")}
        output["editable"] = [
            {"index": n, "ar": field_label(f, n + 1, "ar"), "en": field_label(f, n + 1, "en")}
            for n, f in enumerate(fields)
            if active_field(f, data["inputs"])
        ]
    else:
        field = fields[index]
        blocked = declared_ai_choices(data).get(field.name, ()) if not ai_available else ()
        output["field"] = {
            "index": index,
            "kind": field.kind,
            "required": field.required,
            "prompt": {lang: tr(field.prompt_key, lang) for lang in ("ar", "en")},
            "max_length": field.max_length,
            "single_line": field.single_line,
            "multiple": field.multiple,
            "max_items": field.max_items,
            "received": len(get_input(data["inputs"], field.name) or []) if field.multiple else 0,
            "max_bytes": config().max_file_bytes,
            "skip": {lang: tr(field.skip_key, lang) for lang in ("ar", "en")},
            "choices": [
                {
                    "value": value,
                    "ar": tr(field.choice_keys[n], "ar"),
                    "en": tr(field.choice_keys[n], "en"),
                    "blocked": value in blocked,
                }
                for n, value in enumerate(field.choices)
            ],
            "skip_blocked": any(
                value in blocked and field.choice_keys[n] == field.skip_key
                for n, value in enumerate(field.choices)
            ),
        }
    return output


def check_operation(data, payload, digest):
    if not payload.operation or not payload.revision:
        fail(400, "invalid_request")
    previous = data.get("_miniapp_last", {})
    if previous.get("operation") == payload.operation:
        if previous.get("digest") == digest and previous.get("after") == revision(data):
            return True
        fail(409, "stale_button")
    if payload.revision != revision(data):
        fail(409, "stale_button")
    return False


async def apply_request(state, user_id, payload, *, upload=None):
    data = await state.get_data()
    stage = await state.get_state()
    if data.get("key") and stage not in {"collect", "confirm"}:
        fail(409, "draft_saved")
    if not data.get("key"):
        if payload.action == "view":
            return {"draft": None}
        if payload.action != "open" or not payload.slug or stage is not None:
            fail(409, "resume_none")
        async with sessions() as db:
            service, available = await service_for(db, user_id, payload.slug)
        data = new_draft(service)
        await persist(state, data)
        return {"draft": view(data, available)}
    async with sessions() as db:
        _, available = await service_for(db, user_id, data["slug"], data)
    if payload.action in {"view", "open"}:
        return {"draft": view(data, available)}
    digest = hashlib.sha256(
        (
            payload.model_dump_json()
            + (hashlib.sha256(upload[0]).hexdigest() + upload[1] if upload else "")
        ).encode()
    ).hexdigest()
    if check_operation(data, payload, digest):
        return {"draft": view(data, available)}
    fields = InputSchema.model_validate(data["schema"]).conversation()
    index = next_index(data, fields)
    if payload.action == "edit":
        if index < len(fields) or payload.index is None:
            fail(409, "invalid_request")
        if payload.index >= len(fields) or not active_field(fields[payload.index], data["inputs"]):
            fail(400, "input_invalid")
        data = begin_edit(data, payload.index)
    elif payload.action == "abort":
        if "_edit_original" not in data:
            fail(409, "invalid_request")
        data = abort_edit(data)
    else:
        if index >= len(fields):
            fail(409, "stale_button")
        field = fields[index]
        values = get_input(data["inputs"], field.name)
        blocked = declared_ai_choices(data).get(field.name, ()) if not available else ()
        if payload.action == "skip":
            if (
                field.required
                or values is not None
                or any(
                    v in blocked and field.choice_keys[n] == field.skip_key
                    for n, v in enumerate(field.choices)
                )
            ):
                fail(400, "input_invalid")
            advance(data)
        elif payload.action == "done":
            if not field.multiple or not values:
                fail(400, "input_invalid")
            advance(data)
        elif payload.action == "answer":
            if upload:
                if field.kind not in {"image", "file", "audio"} or field.choices:
                    fail(400, "file_invalid")
                value = await asyncio.to_thread(
                    save_upload,
                    user_id,
                    upload[0],
                    upload[1],
                    field.kind,
                    preserve_image=field.preserve_image,
                )
            else:
                value = payload.value
                if (
                    field.kind != "text"
                    or not isinstance(value, str)
                    or not value.strip()
                    or len(value) > field.max_length
                ):
                    fail(400, "input_invalid")
                if field.single_line and any(c in value for c in "\r\n\u2028\u2029"):
                    fail(400, "input_single_line")
                if field.choices and value not in field.choices:
                    fail(400, "input_invalid")
                if value in blocked:
                    fail(409, "intake_option_unavailable")
            if field.multiple:
                values = list(values or [])
                if len(values) >= field.max_items:
                    fail(400, "input_invalid")
                values.append(value)
                set_input(data["inputs"], field.name, values)
                if len(values) >= field.max_items:
                    advance(data)
            else:
                set_input(data["inputs"], field.name, value)
                advance(data)
        else:
            fail(400, "invalid_request")
    # Invalidate any confirmation buttons left in chat, including an edited draft
    # that has already been viewed there. The pending marker makes chat re-render
    # the current request before it can accept an old button.
    from uuid import uuid4

    data["key"] = uuid4().hex
    data.pop("_miniapp_last", None)
    data["pending_prompt"] = True
    data["index"] = next_index(data, fields)
    data["_miniapp_last"] = {
        "operation": payload.operation,
        "digest": digest,
        "after": revision(data),
    }
    await persist(state, data)
    return {"draft": view(data, available)}


@router.post("/miniapp/api/draft")
async def draft_endpoint(request: Request):
    try:
        if request.headers.get("content-type", "").split(";")[0] != "application/json":
            fail(415, "invalid_request")
        payload = DraftRequest.model_validate_json(await body(request, 65536))
        user_id = authorize(request, payload.init_data)
        async with sessions() as db:
            user = await db.get(User, user_id)
            if user is None or user.banned:
                fail(403, "not_allowed")
        async with runtime(user_id) as state:
            result = await apply_request(state, user_id, payload)
        from fastapi.responses import JSONResponse

        return JSONResponse(result, headers=HEADERS)
    except ValidationError:
        fail(400, "input_invalid")
    except ServiceError as error:
        fail(400, error.key)
    except HTTPException:
        raise
    except Exception:
        fail(503, "input_retry")


@router.post("/miniapp/api/draft/upload")
async def upload_endpoint(request: Request):
    try:
        user_id = authorize(request, request.headers.get("x-telegram-init-data", ""))
        payload = DraftRequest(
            init_data="upload",
            action="answer",
            revision=request.headers.get("x-draft-revision"),
            operation=request.headers.get("x-draft-operation"),
        )
        # Authenticate and reject banned/unregistered accounts before buffering bytes.
        async with sessions() as db:
            user = await db.get(User, user_id)
            if user is None or user.banned:
                fail(403, "not_allowed")
        mime = request.headers.get("content-type", "").split(";")[0].strip().lower()
        async with runtime(user_id) as state:
            content = await body(request, config().max_file_bytes)
            result = await apply_request(state, user_id, payload, upload=(content, mime))
        from fastapi.responses import JSONResponse

        return JSONResponse(result, headers=HEADERS)
    except ValidationError:
        fail(400, "input_invalid")
    except ServiceError as error:
        fail(400, error.key)
    except HTTPException:
        raise
    except Exception:
        fail(503, "input_retry")
