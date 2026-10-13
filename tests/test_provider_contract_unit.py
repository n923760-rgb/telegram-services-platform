import json
from decimal import Decimal

import httpx
import pytest
from pydantic import ValidationError

from app.core.settings import Config
from app.providers.ai.openai_compatible import OpenAICompatible


def configuration(url, field="auto"):
    return Config(
        _env_file=None,
        ai_enabled=True,
        ai_api_key="test-only-not-a-secret",
        ai_base_url=url,
        ai_token_limit_parameter=field,
        ai_input_usd_per_million=Decimal("1"),
        ai_output_usd_per_million=Decimal("1"),
    )


@pytest.mark.parametrize(
    ("url", "selected", "expected"),
    [
        ("https://api.deepseek.com", "auto", "max_tokens"),
        ("https://api.deepseek.com/v1", "auto", "max_tokens"),
        ("https://API.DEEPSEEK.COM/beta", "auto", "max_tokens"),
        ("https://api.openai.com/v1", "auto", "max_completion_tokens"),
        ("https://proxy.example/v1", "auto", "max_completion_tokens"),
        ("https://api.deepseek.com.proxy.example/v1", "auto", "max_completion_tokens"),
        ("https://proxy.example/v1", "max_tokens", "max_tokens"),
        ("https://api.deepseek.com", "max_completion_tokens", "max_completion_tokens"),
    ],
)
@pytest.mark.parametrize("operation", ["text", "image", "translate"])
async def test_wire_output_limit_matches_contract(url, selected, expected, operation):
    requests = []

    def transport(request):
        requests.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "{}"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 20},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
        provider = OpenAICompatible(client)
        provider.cfg = configuration(url, selected)
        if operation == "text":
            await provider.extract_from_text({}, "source", "extract")
        elif operation == "image":
            await provider.extract_from_image({}, "source", "extract", [b"test-image"])
        else:
            await provider.translate({}, "source", "ar", "formal")
    body = requests[0]
    assert body[expected] == provider.max_output_tokens == 8192
    assert {"max_tokens", "max_completion_tokens"}.intersection(body) == {expected}
    assert "thinking" not in body and "reasoning_effort" not in body
    assert provider.upper_bound({}, "", "", []) >= provider.cost(0, body[expected])


async def test_excess_reported_usage_is_not_clamped_or_hidden():
    # Even a vendor ignoring the corrected limit must be settled by the existing
    # gateway: record real usage, trip the bound/pause, never fabricate a lower bill.
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "{}"}}],
                    "usage": {
                        "prompt_tokens": 1590,
                        "completion_tokens": 15532,
                        "completion_tokens_details": {"reasoning_tokens": 14000},
                    },
                },
            )
        )
    ) as client:
        provider = OpenAICompatible(client)
        provider.cfg = configuration("https://api.deepseek.com")
        response = await provider.extract_from_text({}, "source", "extract")
    assert response.usage.output_tokens == 15532
    assert response.usage.cost_sar == provider.cost(1590, 15532)


def test_invalid_token_parameter_is_rejected():
    with pytest.raises(ValidationError):
        configuration("https://api.deepseek.com", "arbitrary_customer_key")
