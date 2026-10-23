"""Owner-only previews and explicit test-credit decisions through the order engine."""

import asyncio
import base64
from io import BytesIO
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from PIL import Image
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import select

from app.core.db import sessions
from app.core.display import result_preview
from app.core.i18n import tr
from app.core.models import Job, Order, Service, User
from app.core.settings import config
from app.miniapp.drafts import HEADERS, authorize, body, fail, runtime
from app.miniapp.review_tokens import InvalidReviewToken, issue, verify
from app.orders.engine import confirm_structure, review_revision
from app.orders.state import ALLOWED
from app.providers.runtime import storage
from app.services.base import Result, ServiceError

router = APIRouter()


class ReviewRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    init_data: str = Field(min_length=1, max_length=8192)
    order_id: UUID


class DecisionRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    init_data: str = Field(min_length=1, max_length=8192)
    token: str = Field(min_length=1, max_length=200)
    approved: bool
    accepted: bool


def preview_image(artifact, user_id):
    """Never expose a storage key or serve arbitrary stored bytes as an image."""
    data = storage().read(artifact.key, user_id)
    if artifact.mime != "image/png" or not 0 < len(data) <= 3 * 1024 * 1024:
        raise ValueError("invalid preview")
    with Image.open(BytesIO(data)) as image:
        if (
            image.format != "PNG"
            or image.width > 2048
            or image.height > 3072
            or image.width * image.height > 4_000_000
            or getattr(image, "n_frames", 1) != 1
        ):
            raise ValueError("invalid preview")
        image.verify()
    return "data:image/png;base64," + base64.b64encode(data).decode("ascii")


async def load_review(user_id, order_id):
    async with sessions() as db:
        user = await db.get(User, user_id)
        if user is None or user.banned:
            fail(403, "not_allowed")
        order = await db.get(Order, order_id)
        if order is None or order.user_id != user_id:
            fail(404, "unavailable")
        if order.status != "waiting_confirmation":
            fail(409, "review_changed")
        snapshot = order.result
        result = Result.model_validate(snapshot)
        if not result.needs_confirmation:
            fail(409, "review_changed")
        service = await db.get(Service, order.service_slug)
        if service is None:
            fail(409, "unavailable")
        response = {
            "reference": str(order.id)[:8],
            "name_ar": service.name_ar,
            "name_en": service.name_en,
            "text_ar": result_preview(snapshot, "ar"),
            "text_en": result_preview(snapshot, "en"),
            "image": None,
            "image_unavailable": False,
            "decision": None,
        }
        attempts = None
        if (
            config().miniapp_confirm_enabled
            and not config().stars_enabled
            and order.payment_mode == "test_credit"
        ):
            attempts = await db.scalar(select(Job.attempts).where(Job.order_id == order.id))
    if result.preview_artifacts:
        try:
            response["image"] = await asyncio.to_thread(
                preview_image, result.preview_artifacts[0], user_id
            )
        except Exception:
            # Keep the bounded textual review available; the bot retains its own
            # review/decision controls. Missing images never imply approval.
            response["image_unavailable"] = True
    # Do not return a preview that changed while storage was read (or after a ban).
    async with sessions() as db:
        user = await db.get(User, user_id)
        current = await db.get(Order, order_id)
        if user is None or user.banned:
            fail(403, "not_allowed")
        if (
            current is None
            or current.user_id != user_id
            or current.status != "waiting_confirmation"
            or current.result != snapshot
        ):
            fail(409, "review_changed")
        if attempts is not None:
            current_attempts = await db.scalar(select(Job.attempts).where(Job.order_id == order_id))
            if current_attempts != attempts:
                fail(409, "review_changed")
            if not response["image_unavailable"] and (response["text_ar"] or response["text_en"]):
                response["decision"] = {
                    "token": issue(
                        user_id, order_id.hex, review_revision(current, attempts), purpose="result"
                    ),
                    "prepared": result.prepared_delivery,
                }
    return {"review": response}


async def decide(user_id, payload):
    if not payload.accepted:
        fail(400, "invalid_request")
    key, revision = verify(user_id, payload.token, purpose="result")
    order_id = UUID(hex=key)
    async with sessions() as db:
        user = await db.get(User, user_id)
        if user is None or user.banned:
            fail(403, "not_allowed")
        order = await db.get(Order, order_id)
        if order is None or order.user_id != user_id:
            fail(404, "unavailable")
        if order.payment_mode != "test_credit":
            fail(409, "payment_changed")
    await confirm_structure(order_id, user_id, payload.approved, expected_revision=revision)
    async with sessions() as db:
        order = await db.get(Order, order_id)
        if order is None or order.user_id != user_id:
            fail(503, "input_retry")
        status = order.status if order.status in ALLOWED else "unknown"
        return {
            "receipt": {
                "reference": str(order_id)[:8],
                "approved": payload.approved,
                "status_ar": tr("status_" + status, "ar"),
                "status_en": tr("status_" + status, "en"),
            }
        }


@router.post("/miniapp/api/result-decision")
async def decision_endpoint(request: Request):
    try:
        if not config().miniapp_confirm_enabled or config().stars_enabled:
            fail(404, "unavailable")
        if request.headers.get("content-type", "").split(";")[0] != "application/json":
            fail(415, "invalid_request")
        payload = DecisionRequest.model_validate_json(await body(request, 10240))
        user_id = authorize(request, payload.init_data)
        async with runtime(user_id):
            result = await decide(user_id, payload)
        return JSONResponse(result, headers=HEADERS)
    except ValidationError:
        fail(400, "invalid_request")
    except InvalidReviewToken:
        fail(409, "review_changed")
    except ServiceError as error:
        fail(409, error.key)
    except HTTPException:
        raise
    except Exception:
        fail(503, "input_retry")


@router.post("/miniapp/api/result-review")
async def review_endpoint(request: Request):
    try:
        if not config().miniapp_intake_enabled:
            fail(404, "unavailable")
        if request.headers.get("content-type", "").split(";")[0] != "application/json":
            fail(415, "invalid_request")
        try:
            payload = ReviewRequest.model_validate_json(await body(request, 10240))
        except ValidationError:
            fail(400, "invalid_request")
        user_id = authorize(request, payload.init_data)
        async with runtime(user_id):
            result = await load_review(user_id, payload.order_id)
        return JSONResponse(result, headers=HEADERS)
    except ValidationError:
        fail(409, "review_unavailable")
    except HTTPException:
        raise
    except Exception:
        fail(503, "input_retry")
