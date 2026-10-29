"""Opt-in public reading: only consented, unexpired, unbanned prepared revisions."""

import asyncio
import re
from html import unescape
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response
from redis.asyncio import Redis

from app.bot.middleware import RATE_LUA
from app.core.settings import config
from app.publications import prepared_page

router = APIRouter()
HEADERS = {
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Robots-Tag": "noindex, nofollow, noarchive",
    "X-Frame-Options": "DENY",
}
MIMES = {"qr.png": "image/png", "qr.svg": "image/svg+xml", "share-card.png": "image/png"}


async def rate_limit():
    # Global across API processes; no trust in client-controlled forwarded IPs.
    client = Redis.from_url(
        config().redis_url.get_secret_value(), socket_connect_timeout=3, socket_timeout=3
    )
    try:
        if await client.eval(RATE_LUA, 1, "publication-read:global", 60) > 120:
            raise HTTPException(429, "rate_limited", headers={**HEADERS, "Retry-After": "60"})
    finally:
        await client.aclose()


async def bundle(publication_id):
    if not config().publications_enabled:
        raise HTTPException(404, "unavailable", headers=HEADERS)
    try:
        async with asyncio.timeout(20):
            await rate_limit()
            result = await prepared_page.public_bundle(
                publication_id, origin=config().publication_origin
            )
        if result is None:
            raise HTTPException(404, "unavailable", headers=HEADERS)
        return result
    except HTTPException:
        raise
    except Exception:
        # Never log source content, raw rendering failures or credentials.
        raise HTTPException(503, "unavailable", headers=HEADERS) from None


def html_response(content, *, private=False):
    match = re.search(rb'<meta http-equiv="Content-Security-Policy" content="([^"]+)">', content)
    if not match:
        raise HTTPException(503, "unavailable", headers=HEADERS)
    ancestor = "'self'" if private else "'none'"
    policy = unescape(match[1].decode()) + f"; frame-ancestors {ancestor}"
    return Response(
        content,
        media_type="text/html",
        headers={
            **HEADERS,
            "Content-Security-Policy": policy,
            "X-Frame-Options": "SAMEORIGIN" if private else "DENY",
        },
    )


@router.get("/p/{publication_id}")
async def page(publication_id: UUID):
    return html_response((await bundle(publication_id))["profile.html"])


@router.get("/p/{publication_id}/{filename}")
async def asset(publication_id: UUID, filename: str):
    if filename not in MIMES:
        raise HTTPException(404, "unavailable", headers=HEADERS)
    content = (await bundle(publication_id))[filename]
    return Response(
        content,
        media_type=MIMES[filename],
        headers={
            **HEADERS,
            "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
