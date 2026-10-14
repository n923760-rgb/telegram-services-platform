import json
from decimal import Decimal

import httpx
import pytest

from app.providers.ai.openai_compatible import OpenAICompatible
from app.providers.ai.usage_audit import cache_details, diagnostic_audit
from tests.test_provider_contract_unit import configuration


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize(
    "details,hit,miss",
    [
        ({"prompt_tokens_details": {"cached_tokens": 40}}, 40, 60),
        ({"prompt_cache_hit_tokens": 40, "prompt_cache_miss_tokens": 60}, 40, 60),
        ({"prompt_cache_hit_tokens": 0}, 0, 100),
        ({"prompt_cache_miss_tokens": 0}, 100, 0),
        ({"prompt_tokens_details": {"cached_tokens": 40}, "prompt_cache_hit_tokens": 40}, 40, 60),
    ],
)
def test_reported_cache_fields_are_consistent_and_not_guessed(details, hit, miss):
    result = cache_details({"prompt_tokens": 100, **details})
    assert result["state"] == "reported"
    assert (result["hit_tokens"], result["miss_tokens"]) == (hit, miss)


@pytest.mark.parametrize(
    "details",
    [
        {"prompt_cache_hit_tokens": True},
        {"prompt_cache_hit_tokens": -1},
        {"prompt_cache_hit_tokens": 101},
        {"prompt_cache_hit_tokens": "40"},
        {"prompt_cache_hit_tokens": {}},
        {"prompt_tokens_details": "raw source secret"},
        {"prompt_cache_hit_tokens": 40, "prompt_cache_miss_tokens": 40},
        {"prompt_tokens_details": {"cached_tokens": 30}, "prompt_cache_hit_tokens": 40},
    ],
)
def test_invalid_optional_cache_data_is_bounded_without_discarding_total_usage(details):
    assert cache_details({"prompt_tokens": 100, **details}) == {
        "state": "invalid",
        "hit_tokens": None,
        "miss_tokens": None,
    }


def test_absent_cache_and_historical_audit_remain_unknown():
    assert cache_details({"prompt_tokens": 100})["hit_tokens"] is None
    old = diagnostic_audit({"basis": "returned_tokens"})
    assert old["cost_kind"] == "calculated" and old["invoice_verified"] is None
    assert old["cache_state"] == "not_recorded"
    assert old["requested_output_limit"] is None
    assert diagnostic_audit({})["cost_kind"] == "unclassified"


@pytest.mark.parametrize(
    "cache", [{}, {"prompt_cache_hit_tokens": 40}, {"prompt_cache_hit_tokens": "secret"}]
)
async def test_adapter_records_full_conservative_cost_and_safe_cache_metadata(cache):
    body = {
        "id": "request-id",
        "choices": [{"message": {"content": "{}"}}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 20, **cache},
    }
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda req: httpx.Response(200, json=body))
    ) as client:
        adapter = OpenAICompatible(client)
        adapter.cfg = configuration("https://api.deepseek.com")
        response = await adapter.extract_from_text({}, "source", "extract")
    usage = response.usage
    assert usage.cost_sar == adapter.cost(100, 20) == Decimal(".000450")
    assert usage.rates["cost_kind"] == "calculated"
    assert usage.rates["invoice_verified"] is False
    assert usage.rates["provider_request_id"] == "request-id"
    assert "secret" not in json.dumps(usage.rates)
    assert usage.rates["requested_output_limit"] == 8192
    assert not usage.rates["output_limit_exceeded"]


def test_malformed_stored_metadata_is_safe_and_never_prints_source():
    result = diagnostic_audit(
        {"cache": {"state": {"secret": "customer content"}}, "requested_output_limit": True}
    )
    assert result["cache_state"] == "not_recorded" and result["requested_output_limit"] is None
    assert "customer content" not in str(result)


async def test_unauthorized_preflight_rejects_before_db_or_provider(monkeypatch):
    from unittest.mock import Mock

    from app.core.settings import config
    from app.ops import provider_cap_preflight
    from app.services.base import ServiceError

    monkeypatch.setattr(config(), "admin_ids", [7])
    factory = Mock(side_effect=AssertionError("must not construct provider"))
    monkeypatch.setattr(provider_cap_preflight, "provider", factory)
    with pytest.raises(ServiceError, match="not_allowed"):
        await provider_cap_preflight.prepare(8)
    factory.assert_not_called()
