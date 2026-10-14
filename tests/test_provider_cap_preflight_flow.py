from decimal import Decimal
from unittest.mock import AsyncMock

from pydantic import SecretStr
from sqlalchemy import func, select

from app.core.db import sessions
from app.core.models import CostHold, CostUsage, Setting
from app.core.settings import config
from app.ops.costs import reserve_call, uncertain_call
from app.ops.provider_cap_preflight import prepare
from tests.test_operations import running


async def test_owner_preflight_keeps_pause_holds_and_ledger_and_never_calls_provider(monkeypatch):
    from app.ops import provider_cap_preflight
    from app.providers.ai.openai_compatible import OpenAICompatible

    _, jid = await running()
    unknown = await reserve_call(jid, 1, Decimal(".01"))
    await uncertain_call(unknown)
    cfg = config()
    for key, value in {
        "admin_ids": [1],
        "ai_enabled": True,
        "ai_api_key": SecretStr("test-only-secret"),
        "ai_base_url": "https://api.deepseek.com",
        "ai_input_usd_per_million": Decimal("1"),
        "ai_output_usd_per_million": Decimal("1"),
    }.items():
        monkeypatch.setattr(cfg, key, value)
    async with sessions.begin() as db:
        await db.merge(Setting(key="PROVIDER_PAUSED", value={"value": True}))
    client = AsyncMock()
    adapter = OpenAICompatible(client)
    monkeypatch.setattr(provider_cap_preflight, "provider", lambda: adapter)
    result = await prepare()
    assert result["status"] == "prepared" and result["provider_paused"] is True
    assert result["limit_field"] == "max_tokens" and result["probe_output_limit"] == 128
    assert result["live_execution"] == "not_performed" and result["actions_performed"] == []
    assert Decimal(result["calculated_reservation_bound_sar"]) > 0
    assert "test-only-secret" not in str(result) and len(result["body_sha256"]) == 64
    assert cfg.ai_max_output_tokens == 8192
    client.post.assert_not_awaited()
    async with sessions() as db:
        assert (await db.get(CostHold, unknown)).status == "uncertain"
        assert (await db.get(Setting, "PROVIDER_PAUSED")).value == {"value": True}
        assert await db.scalar(select(func.count(CostHold.id))) == 1
        assert await db.scalar(select(func.count(CostUsage.id))) == 0
