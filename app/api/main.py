import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Request
from redis.asyncio import Redis
from sqlalchemy import text

from app.core.db import engine, sessions
from app.core.settings import config


@asynccontextmanager
async def lifespan(app):
    cfg = config()
    if cfg.telegram_mode == "webhook":
        from aiogram import Bot

        from app.bot.main import create_dispatcher
        from app.services.registry import registry

        async with sessions.begin() as db:
            await registry.sync(db)
        app.state.bot = Bot(cfg.bot_token.get_secret_value())
        app.state.dispatcher = create_dispatcher()
    try:
        yield
    finally:
        if cfg.telegram_mode == "webhook":
            await app.state.bot.session.close()
            await app.state.dispatcher.storage.close()
        await engine.dispose()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)


@app.get("/health/live")
async def live():
    return {"status": "ok"}


@app.get("/health")
async def health():
    try:
        async with sessions() as db:
            await db.execute(text("SELECT 1"))
        redis = Redis.from_url(config().redis_url.get_secret_value())
        try:
            await redis.ping()
        finally:
            await redis.aclose()
        return {"status": "ok"}
    except Exception:
        raise HTTPException(503, "dependencies unavailable") from None


@app.post("/webhooks/payment")
async def payment():
    raise HTTPException(501, "payment gateways are not implemented")


@app.post("/webhooks/telegram")
async def telegram(request: Request, x_telegram_bot_api_secret_token: str = Header(default="")):
    cfg = config()
    expected = cfg.telegram_webhook_secret.get_secret_value()
    if (
        cfg.telegram_mode != "webhook"
        or not expected
        or not secrets.compare_digest(expected.encode(), x_telegram_bot_api_secret_token.encode())
    ):
        raise HTTPException(403, "forbidden")
    from aiogram.types import Update

    if not hasattr(app.state, "dispatcher"):
        raise HTTPException(503, "webhook runtime unavailable")
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > 1024 * 1024:
            raise HTTPException(413, "update too large")
        body.extend(chunk)
    try:
        update = Update.model_validate_json(body, context={"bot": app.state.bot})
    except ValueError:
        raise HTTPException(422, "invalid update") from None
    # Money updates must not wait for or be dropped by customer FSM/rate/ban gates.
    # An unavailable database propagates HTTP 500 so Telegram can retry the update.
    from app.bot.payments import handle_precheckout, handle_receipt, handle_refunded

    if update.pre_checkout_query:
        await handle_precheckout(update.pre_checkout_query, app.state.bot)
    elif update.message and update.message.successful_payment:
        await handle_receipt(update.message, app.state.bot)
    elif update.message and update.message.refunded_payment:
        await handle_refunded(update.message)
    else:
        await app.state.dispatcher.feed_update(app.state.bot, update)
    return {"ok": True}
