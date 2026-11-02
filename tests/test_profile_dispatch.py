import asyncio
from unittest.mock import AsyncMock

from sqlalchemy import func, select

from app.core.db import sessions
from app.core.models import OrderCompletion, Publication, PublicationConsent
from app.core.settings import config
from app.publications.dispatch import dispatch_profiles
from app.workers.runner import execute_job
from tests.test_foundation import job_for
from tests.test_hosted_profile_flow import pilot as pilot
from tests.test_hosted_profile_flow import purchase, runtime


async def test_restart_and_duplicate_dispatch_project_one_private_page_without_ai(pilot, tmp_path):
    identity = await purchase()
    provider, _, ctx = runtime(tmp_path)
    await execute_job(ctx, str(await job_for(identity)))
    assert provider.calls == 2
    results = await asyncio.gather(dispatch_profiles({}), dispatch_profiles({}))
    assert sum(r["applied"] for r in results) == 1
    assert (await dispatch_profiles({}))["selected"] == 0
    async with sessions() as db:
        assert (await db.get(OrderCompletion, identity)).state == "applied"
        assert await db.scalar(select(func.count()).select_from(Publication)) == 1
        page = await db.scalar(select(Publication))
        assert page.state == "draft"
        assert await db.scalar(select(func.count()).select_from(PublicationConsent)) == 0
    assert provider.calls == 2


async def test_failed_transfer_remains_pending_for_restart(pilot, tmp_path, monkeypatch):
    from app.publications import dispatch as flow

    identity = await purchase()
    provider, _, ctx = runtime(tmp_path)
    await execute_job(ctx, str(await job_for(identity)))
    actual = flow.transfer_purchased
    monkeypatch.setattr(
        flow, "transfer_purchased", AsyncMock(side_effect=OSError("synthetic interruption"))
    )
    assert (await dispatch_profiles({}))["deferred"] == 1
    async with sessions() as db:
        assert (await db.get(OrderCompletion, identity)).state == "pending"
        assert await db.scalar(select(func.count()).select_from(Publication)) == 0
    monkeypatch.setattr(flow, "transfer_purchased", actual)
    assert (await dispatch_profiles({}))["applied"] == 1
    assert provider.calls == 2


async def test_revoked_admin_is_not_selected(pilot, tmp_path, monkeypatch):
    identity = await purchase()
    _, _, ctx = runtime(tmp_path)
    await execute_job(ctx, str(await job_for(identity)))
    monkeypatch.setattr(config(), "admin_ids", [22])
    assert (await dispatch_profiles({}))["selected"] == 0
    async with sessions() as db:
        assert (await db.get(OrderCompletion, identity)).state == "pending"
