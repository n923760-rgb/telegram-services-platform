from decimal import Decimal

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import select

from app.builders.schema import StrictModel
from app.core.db import sessions
from app.core.models import CostBudget, CostHold, CostUsage, Setting
from app.core.settings import config
from app.ops.costs import keys, reserve_call, uncertain_call
from app.providers.ai.gateway import AI
from app.providers.ai.openai_compatible import OpenAICompatible
from app.services.base import ServiceError
from tests.test_operations import running


class Outcome(StrictModel):
    ok: bool


@pytest.mark.parametrize("excess", [False, True])
async def test_correct_wire_limit_preserves_accounting_and_unknown_exposure(monkeypatch, excess):
    _, jid = await running()
    cfg = config()
    for key, value in {
        "ai_enabled": True,
        "ai_api_key": SecretStr("test-only-secret"),
        "ai_base_url": "https://api.deepseek.com",
        "ai_model": "deepseek-flash",
        "ai_token_limit_parameter": "auto",
        "ai_input_usd_per_million": Decimal("1"),
        "ai_output_usd_per_million": Decimal("1"),
    }.items():
        monkeypatch.setattr(cfg, key, value)
    old_hold = await reserve_call(jid, 1, Decimal(".01"))
    await uncertain_call(old_hold)
    tokens = 15532 if excess else 8192

    def transport(request):
        import json

        body = json.loads(request.content)
        assert body["max_tokens"] == 8192 and "max_completion_tokens" not in body
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": '{"ok":true}'}}],
                "usage": {"prompt_tokens": 1590, "completion_tokens": tokens},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
        provider = OpenAICompatible(client)
        ai = AI(provider, jid, 1)
        if excess:
            with pytest.raises(ServiceError, match="provider_usage"):
                await ai.extract(Outcome, "source", "extract")
        else:
            assert (await ai.extract(Outcome, "source", "extract")).ok
    async with sessions() as db:
        holds = list(await db.scalars(select(CostHold).where(CostHold.job_id == jid)))
        assert sorted(h.status for h in holds) == ["settled", "uncertain"]
        assert (await db.get(CostHold, old_hold)).amount == Decimal(".01")
        usage = await db.scalar(select(CostUsage).where(CostUsage.job_id == jid))
        assert usage.output_tokens == tokens and usage.cost_sar == provider.cost(1590, tokens)
        budget = await db.get(CostBudget, keys(1)[0])
        assert budget.reserved == Decimal(".01") and budget.spent == usage.cost_sar
        pause = await db.get(Setting, "PROVIDER_PAUSED")
        assert bool(pause and pause.value["value"]) == excess
