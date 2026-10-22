"""Read-only Telegram Mini App foundation; never creates orders or accepts money."""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.bot.availability import ai_admission_available
from app.core.db import sessions
from app.core.i18n import tr
from app.core.models import Order, Service, User
from app.core.settings import config
from app.miniapp.auth import InvalidMiniAppAuth, verify_init_data
from app.orders.state import ALLOWED
from app.services.catalog import CATEGORY_KEYS, ordered
from app.services.registry import registry
from app.wallet.ledger import balance, sar

router = APIRouter()
ASSETS = Path(__file__).resolve().parent

CSP = (
    "default-src 'none'; script-src 'self' https://telegram.org; "
    "style-src 'self'; connect-src 'self'; img-src 'self' data:; "
    "base-uri 'none'; form-action 'none'; object-src 'none'"
)
STATIC_HEADERS = {
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}


class OverviewRequest(BaseModel):
    init_data: str = Field(min_length=1, max_length=8192)


@router.get("/miniapp")
async def miniapp_page():
    return FileResponse(
        ASSETS / "index.html",
        media_type="text/html; charset=utf-8",
        headers={**STATIC_HEADERS, "Content-Security-Policy": CSP},
    )


@router.get("/miniapp/app.js")
async def miniapp_script():
    return FileResponse(
        ASSETS / "app.js", media_type="application/javascript", headers=STATIC_HEADERS
    )


@router.get("/miniapp/styles.css")
async def miniapp_styles():
    return FileResponse(ASSETS / "styles.css", media_type="text/css", headers=STATIC_HEADERS)


def visible_services(rows, *, user_id: int, stars: bool, ai_available: bool):
    """Reuse registry/admission presentation policy; never claim checkout is available."""
    result = []
    for service in ordered(rows, registry.types):
        if not registry.can_request(service.slug, admin=user_id in config().admin_ids):
            continue
        if stars and service.price_stars is None:
            continue
        plugin = registry.types[service.slug]
        result.append(
            {
                "slug": service.slug,
                "category": plugin.category,
                "name_ar": service.name_ar,
                "name_en": service.name_en,
                "description_ar": service.description_ar,
                "description_en": service.description_ar
                if not service.description_en
                else service.description_en,
                "price": service.price_stars if stars else sar(service.price_halala),
                "ai_unavailable": not ai_available and plugin.requires_ai,
                "ai_options_unavailable": not ai_available and plugin.optional_ai,
            }
        )
    return result


@router.post("/miniapp/api/overview")
async def overview(payload: OverviewRequest, response: Response):
    response.headers["Cache-Control"] = "no-store"
    try:
        user_id = verify_init_data(payload.init_data, config().bot_token.get_secret_value())
    except InvalidMiniAppAuth:
        raise HTTPException(
            401, "Mini App authentication required", headers={"Cache-Control": "no-store"}
        ) from None
    async with sessions() as db:
        user = await db.get(User, user_id)
        if user and user.banned:
            raise HTTPException(403, "access denied", headers={"Cache-Control": "no-store"})
        language = user.language if user and user.language in ("ar", "en") else "ar"
        stars = config().stars_enabled
        services = (
            await db.scalars(
                select(Service).where(Service.enabled.is_(True)).order_by(Service.slug)
            )
        ).all()
        ai_available = await ai_admission_available(db)
        orders = (
            await db.execute(
                select(Order, Service)
                .join(Service, Service.slug == Order.service_slug)
                .where(Order.user_id == user_id)
                .order_by(Order.created_at.desc(), Order.id.desc())
                .limit(8)
            )
        ).all()
        funds = None if stars else await balance(db, user_id)

    output = {
        "language": language,
        "payment_mode": "stars" if stars else "test_credit",
        "categories": [
            {"key": key, "ar": tr(label, "ar"), "en": tr(label, "en")}
            for key, label in CATEGORY_KEYS.items()
        ],
        "services": visible_services(
            services, user_id=user_id, stars=stars, ai_available=ai_available
        ),
        "orders": [
            {
                "reference": str(order.id)[:8],
                "name_ar": service.name_ar,
                "name_en": service.name_en,
                "status_ar": tr(
                    f"status_{order.status}" if order.status in ALLOWED else "status_unknown",
                    "ar",
                ),
                "status_en": tr(
                    f"status_{order.status}" if order.status in ALLOWED else "status_unknown",
                    "en",
                ),
                "created_at": order.created_at.isoformat() if order.created_at else None,
            }
            for order, service in orders
        ],
        "credit": None
        if funds is None
        else {
            "available_sar": sar(funds.available),
            "reserved_sar": sar(funds.reserved),
        },
    }
    return output
