from decimal import Decimal

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import select

from app.core.db import sessions
from app.core.models import CostBudget, CostHold, CostUsage, Setting
from app.core.settings import config
from app.ops.costs import keys, reserve_call, uncertain_call
from app.providers.ai.gateway import AI
from app.providers.ai.openai_compatible import OpenAICompatible
from app.services.base import ServiceError
from tests.test_operations import running
from tests.test_provider_contract_flow import Outcome


@pytest.mark.parametrize("recover", [True, False])
async def test_truncation_retains_each_billable_call_without_global_pause(monkeypatch, recover):
    _, jid = await running()
    cfg = config()
    for key, value in {
        "ai_enabled": True,
        "ai_api_key": SecretStr("test-only-secret"),
        "ai_base_url": "https://api.deepseek.com",
        "ai_model": "deepseek-flash",
        "ai_input_usd_per_million": Decimal("1"),
        "ai_output_usd_per_million": Decimal("1"),
    }.items():
        monkeypatch.setattr(cfg, key, value)
    old = await reserve_call(jid, 1, Decimal(".01"))
    await uncertain_call(old)
    calls = []

    def transport(request):
        import json

        assert json.loads(request.content)["thinking"] == {"type": "disabled"}
        calls.append(1)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop" if recover and len(calls) == 2 else "length",
                        "message": {"content": '{"ok":true}'},
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 20},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
        ai = AI(OpenAICompatible(client), jid, 1)
        if recover:
            assert (await ai.extract(Outcome, "source", "extract")).ok
        else:
            with pytest.raises(ServiceError, match="provider_invalid"):
                await ai.extract(Outcome, "source", "extract")
    async with sessions() as db:
        usages = list(await db.scalars(select(CostUsage).where(CostUsage.job_id == jid)))
        holds = list(await db.scalars(select(CostHold).where(CostHold.job_id == jid)))
        assert len(calls) == len(usages) == 2
        assert sorted(h.status for h in holds) == ["settled", "settled", "uncertain"]
        assert (await db.get(CostHold, old)).status == "uncertain"
        budget = await db.get(CostBudget, keys(1)[0])
        assert budget.reserved == Decimal(".01")
        assert budget.spent == sum(u.cost_sar for u in usages)
        assert await db.get(Setting, "PROVIDER_PAUSED") is None


@pytest.mark.parametrize("excess", [False, True])
async def test_token_contract_breach_pauses_even_below_cost_bound_and_retains_old_unknown(
    monkeypatch, excess
):
    _, jid = await running()
    cfg = config()
    for key, value in {
        "ai_enabled": True,
        "ai_api_key": SecretStr("test-only-secret"),
        "ai_base_url": "https://api.deepseek.com",
        "ai_max_output_tokens": 8,
        "ai_input_usd_per_million": Decimal("1"),
        "ai_output_usd_per_million": Decimal("1"),
    }.items():
        monkeypatch.setattr(cfg, key, value)
    old = await reserve_call(jid, 1, Decimal(".01"))
    await uncertain_call(old)
    tokens = 9 if excess else 8
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda req: httpx.Response(
                200,
                json={
                    "id": "probe-fixture",
                    "choices": [{"message": {"content": '{"ok":true}'}}],
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": tokens,
                        "prompt_cache_hit_tokens": 4,
                        "prompt_cache_miss_tokens": 6,
                    },
                },
            )
        )
    ) as client:
        adapter = OpenAICompatible(client)
        ai = AI(adapter, jid, 1)
        if excess:
            with pytest.raises(ServiceError, match="provider_usage"):
                await ai.extract(Outcome, "source", "extract")
        else:
            assert (await ai.extract(Outcome, "source", "extract")).ok
    async with sessions() as db:
        usage = await db.scalar(select(CostUsage).where(CostUsage.job_id == jid))
        settled = await db.get(CostHold, usage.hold_id)
        assert usage.cost_sar < settled.amount
        assert usage.output_tokens == tokens
        assert usage.rate_snapshot["cache"]["hit_tokens"] == 4
        assert usage.rate_snapshot["invoice_verified"] is False
        assert (await db.get(CostHold, old)).status == "uncertain"
        budget = await db.get(CostBudget, keys(1)[0])
        assert budget.reserved == Decimal(".01") and budget.spent == usage.cost_sar
        pause = await db.get(Setting, "PROVIDER_PAUSED")
        assert bool(pause and pause.value["value"]) == excess
    if excess:
        with pytest.raises(ServiceError, match="provider_usage"):
            await reserve_call(jid, 1, Decimal(".001"))


async def test_under_budget_cap_breach_releases_customer_credit_once_without_file(
    tmp_path, monkeypatch
):
    from types import SimpleNamespace

    from sqlalchemy import func

    from app.core.models import Ledger, Order
    from app.orders.engine import submit
    from app.providers.storage import OwnedStorage
    from app.wallet.ledger import balance
    from app.workers.runner import deliver_failures, execute_job
    from tests.test_foundation import job_for
    from tests.test_real_services import setup

    store, _, delivery, ctx, price = await setup("text_to_pdf", [], tmp_path, monkeypatch)
    cfg = config()
    for key, value in {
        "ai_api_key": SecretStr("test-only-secret"),
        "ai_base_url": "https://api.deepseek.com",
        "ai_max_output_tokens": 8,
        "ai_input_usd_per_million": Decimal("1"),
        "ai_output_usd_per_million": Decimal("1"),
    }.items():
        monkeypatch.setattr(cfg, key, value)
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda req: httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "content": '{"document":{"title":"Report","sections":[{"paragraphs":["Source"]}]}}'
                            }
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 9,
                        "prompt_tokens_details": {"cached_tokens": 4},
                    },
                },
            )
        )
    ) as client:
        adapter = OpenAICompatible(client)
        ctx["runtime_factory"] = lambda jid, uid: SimpleNamespace(
            ai=AI(adapter, jid, uid), storage=OwnedStorage(store, uid)
        )
        oid = await submit(
            1, "text_to_pdf", {"text": "Source", "mode": "smart"}, price, "cap-breach"
        )
        jid = await job_for(oid)
        await execute_job(ctx, str(jid))
        await execute_job(ctx, str(jid))
        await deliver_failures(ctx)
        await deliver_failures(ctx)
    async with sessions() as db:
        order = await db.get(Order, oid)
        assert order.status == "failed" and order.error_key == "provider_usage"
        funds = await balance(db, 1)
        assert funds.available == 1000 and funds.reserved == 0
        usage = await db.scalar(select(CostUsage).where(CostUsage.job_id == jid))
        assert usage.cost_sar < (await db.get(CostHold, usage.hold_id)).amount
        assert usage.output_tokens == 9 and usage.rate_snapshot["output_limit_exceeded"] is True
        assert await db.scalar(select(func.count(Ledger.id)).where(Ledger.kind == "release")) == 1
        assert (await db.get(Setting, "PROVIDER_PAUSED")).value == {"value": True}
    assert not delivery.files and len(delivery.errors) == 1
