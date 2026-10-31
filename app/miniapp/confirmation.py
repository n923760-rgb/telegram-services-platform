"""Explicit test-credit confirmation through the existing order engine.

The database order key is the durable receipt even if FSM cleanup or HTTP fails.
Stars invoices and receipts remain exclusively in their existing Telegram flow.
"""

from aiogram.fsm.storage.redis import RedisStorage
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import select

from app.core.db import sessions
from app.core.i18n import tr
from app.core.models import Order, User
from app.core.settings import config
from app.miniapp.drafts import HEADERS, authorize, body, fail, revision, runtime, service_for
from app.miniapp.review_tokens import InvalidReviewToken, verify
from app.orders.engine import submit
from app.orders.state import ALLOWED
from app.services.base import InputSchema, ServiceError
from app.wallet.ledger import WalletError, sar

router = APIRouter()


class ConfirmRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    init_data: str = Field(min_length=1, max_length=8192)
    token: str = Field(min_length=1, max_length=200)
    accepted: bool


def receipt(order):
    status = order.status if order.status in ALLOWED else "unknown"
    result = {
        "reference": str(order.id)[:8],
        "status": order.status,
        "status_ar": tr("status_" + status, "ar"),
        "status_en": tr("status_" + status, "en"),
        "price_sar": sar(order.price_halala),
        "payment_mode": "test_credit",
    }
    if order.purchase_terms_snapshot is not None:
        result["purchase_terms"] = order.purchase_terms_snapshot
    return result


async def clear_accepted(state, key):
    # Replaying an old receipt must never erase a newer draft or a support session.
    data = await state.get_data()
    if data.get("key") != key or await state.get_state() not in {"collect", "confirm"}:
        return
    store = state.storage
    if isinstance(store, RedisStorage):
        await store.redis.delete(
            store.key_builder.build(state.key, "data"), store.key_builder.build(state.key, "state")
        )
    else:
        await state.clear()


async def confirm_request(state, user_id, payload):
    if not payload.accepted:
        fail(400, "invalid_request")
    key, expected_revision = verify(user_id, payload.token)
    async with sessions() as db:
        user = await db.get(User, user_id)
        if user is None or user.banned:
            fail(403, "not_allowed")
        previous = await db.scalar(
            select(Order).where(Order.user_id == user_id, Order.idempotency_key == key)
        )
    if previous:
        if previous.payment_mode != "test_credit":
            fail(409, "payment_changed")
        await clear_accepted(state, key)
        return {"receipt": receipt(previous)}
    data = await state.get_data()
    if (
        data.get("key") != key
        or revision(data) != expected_revision
        or await state.get_state() != "confirm"
    ):
        fail(409, "stale_button")
    if config().stars_enabled or data.get("payment_mode") != "test_credit":
        fail(409, "payment_changed")
    schema = InputSchema.model_validate(data["schema"])
    if data.get("index") != len(schema.conversation()) or "_edit_original" in data:
        fail(409, "input_invalid")
    schema.validate_inputs(data["inputs"])
    async with sessions() as db:
        await service_for(db, user_id, data["slug"], data)
    order_id = await submit(
        user_id,
        data["slug"],
        data["inputs"],
        data["price"],
        data["key"],
        data["version"],
        purchase_quote=data.get("purchase_quote"),
    )
    async with sessions() as db:
        order = await db.get(Order, order_id)
        if order is None or order.user_id != user_id:
            fail(503, "input_retry")
        result = {"receipt": receipt(order)}
    await clear_accepted(state, key)
    return result


@router.post("/miniapp/api/confirm")
async def confirm_endpoint(request: Request):
    try:
        if not config().miniapp_confirm_enabled:
            fail(404, "unavailable")
        if request.headers.get("content-type", "").split(";")[0] != "application/json":
            fail(415, "invalid_request")
        payload = ConfirmRequest.model_validate_json(await body(request, 16384))
        user_id = authorize(request, payload.init_data)
        async with runtime(user_id) as state:
            result = await confirm_request(state, user_id, payload)
        return JSONResponse(result, headers=HEADERS)
    except InvalidReviewToken:
        fail(409, "stale_button")
    except ValidationError:
        fail(400, "input_invalid")
    except (ServiceError, WalletError) as error:
        fail(409, error.key)
    except HTTPException:
        raise
    except Exception:
        fail(503, "input_retry")
