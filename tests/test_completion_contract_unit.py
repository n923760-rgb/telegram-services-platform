import json
from unittest.mock import AsyncMock

import httpx
import pytest
from pydantic import ValidationError

from app.builders.schema import StrictModel
from app.providers.ai import gateway
from app.providers.ai.gateway import AI
from app.providers.ai.openai_compatible import OpenAICompatible
from app.providers.ai.usage_audit import completion_details, diagnostic_audit
from app.services.base import ServiceError
from tests.test_provider_contract_unit import configuration


@pytest.fixture(autouse=True)
def database():
    yield


class Outcome(StrictModel):
    ok: bool


@pytest.mark.parametrize("model", ["deepseek-flash", "deepseek-v4-pro"])
@pytest.mark.parametrize("mode", ["disabled", "enabled"])
@pytest.mark.parametrize("operation", ["text", "image", "translate"])
async def test_documented_deepseek_mode_is_explicit_on_every_wire_path(model, mode, operation):
    requests = []

    def transport(request):
        requests.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "content": '{"ok":true}',
                            "reasoning_content": "private reasoning never retained",
                        },
                    }
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "completion_tokens_details": {"reasoning_tokens": 7},
                },
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
        adapter = OpenAICompatible(client)
        adapter.cfg = configuration("https://API.DEEPSEEK.COM/v1").model_copy(
            update={"ai_model": model, "ai_deepseek_thinking": mode}
        )
        if operation == "translate":
            result = await adapter.translate({}, "source", "ar", "formal")
        elif operation == "image":
            result = await adapter.extract_from_image({}, "source", "extract", [b"image"])
        else:
            result = await adapter.extract_from_text({}, "source", "extract")
    assert requests[0]["thinking"] == {"type": mode}
    assert requests[0]["max_tokens"] == 8192
    assert ("temperature" in requests[0]) == (mode == "disabled")
    assert result.usage.output_tokens == 20
    assert result.usage.cost_sar == adapter.cost(10, 20)
    assert result.usage.rates["completion"]["reasoning_tokens"] == 7
    assert result.usage.rates["completion"]["requested_thinking"] == mode
    assert "private reasoning" not in json.dumps(result.usage.rates)


@pytest.mark.parametrize(
    "url,model",
    [
        ("https://api.openai.com/v1", "deepseek-flash"),
        ("https://api.deepseek.com.proxy.example/v1", "deepseek-flash"),
        ("https://proxy.example/v1", "deepseek-v4-pro"),
        ("https://api.deepseek.com", "legacy-model"),
    ],
)
def test_vendor_extension_is_not_sent_to_other_endpoints_or_unknown_models(url, model):
    adapter = OpenAICompatible()
    adapter.cfg = configuration(url).model_copy(update={"ai_model": model})
    assert "thinking" not in adapter.request_body({}, "source", "extract", [])


def test_default_is_explicit_disabled_and_invalid_config_rejected():
    cfg = configuration("https://api.deepseek.com")
    assert cfg.ai_deepseek_thinking == "disabled"
    with pytest.raises(ValidationError):
        type(cfg)(_env_file=None, ai_deepseek_thinking="arbitrary")


@pytest.mark.parametrize("value", [True, -1, 21, "7", {"secret": "raw text"}])
def test_bad_reasoning_counts_never_change_totals_or_expose_content(value):
    result = completion_details(
        {"choices": [{"finish_reason": {"secret": "raw text"}}]},
        {"completion_tokens": 20, "completion_tokens_details": {"reasoning_tokens": value}},
    )
    assert result["reasoning_state"] == "invalid"
    assert result["reasoning_tokens"] is None and result["finish_reason"] is None
    assert "raw text" not in json.dumps(result)


def test_old_and_missing_completion_evidence_remains_unknown():
    assert completion_details({}, {"completion_tokens": 20})["reasoning_state"] == "not_reported"
    old = diagnostic_audit({"basis": "returned_tokens"})
    assert old["finish_reason"] is old["reasoning_tokens"] is old["requested_thinking"] is None
    assert (
        diagnostic_audit(
            {
                "completion": {
                    "finish_reason": ["secret"],
                    "reasoning_tokens": True,
                    "requested_thinking": {"secret": "text"},
                }
            }
        )["finish_reason"]
        is None
    )


@pytest.mark.parametrize("recover", [True, False])
async def test_truncated_valid_json_is_settled_then_uses_only_existing_repair(monkeypatch, recover):
    settle, pause = AsyncMock(), AsyncMock()
    monkeypatch.setattr(gateway, "reserve_call", AsyncMock(return_value="hold"))
    monkeypatch.setattr(gateway, "settle_call", settle)
    monkeypatch.setattr(gateway, "pause_provider", pause)
    calls = []

    def transport(request):
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
        adapter = OpenAICompatible(client)
        adapter.cfg = configuration("https://api.deepseek.com")
        ai = AI(adapter, "job", 1)
        if recover:
            assert (await ai.extract(Outcome, "source", "extract")).ok
        else:
            with pytest.raises(ServiceError, match="provider_invalid"):
                await ai.extract(Outcome, "source", "extract")
    assert len(calls) == settle.await_count == 2
    pause.assert_not_awaited()
