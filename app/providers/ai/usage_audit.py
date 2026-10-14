"""Bounded usage metadata; billing totals are never inferred from cache counts."""

import re


def count(value, maximum):
    return type(value) is int and 0 <= value <= maximum


def cache_details(usage):
    total = usage["prompt_tokens"]
    hits = []
    misses = []
    sources = []
    invalid = False
    if "prompt_tokens_details" in usage:
        details = usage["prompt_tokens_details"]
        if not isinstance(details, dict):
            invalid = True
        elif "cached_tokens" in details:
            hits.append(details["cached_tokens"])
            sources.append("prompt_tokens_details.cached_tokens")
    for key, values in (("prompt_cache_hit_tokens", hits), ("prompt_cache_miss_tokens", misses)):
        if key in usage:
            values.append(usage[key])
            sources.append(key)
    if not sources and not invalid:
        return {"state": "not_reported", "hit_tokens": None, "miss_tokens": None}
    if (
        invalid
        or any(not count(value, total) for value in hits + misses)
        or len(set(hits)) > 1
        or len(set(misses)) > 1
        or (hits and misses and hits[0] + misses[0] != total)
    ):
        return {"state": "invalid", "hit_tokens": None, "miss_tokens": None}
    hit = hits[0] if hits else total - misses[0]
    return {
        "state": "reported",
        "hit_tokens": hit,
        "miss_tokens": total - hit,
        "fields": sources,
    }


def response_audit(data, usage, limit, limit_field):
    identifier = data.get("id")
    identifier = (
        identifier
        if isinstance(identifier, str) and re.fullmatch(r"[A-Za-z0-9._:-]{1,200}", identifier)
        else None
    )
    return {
        "cost_kind": "calculated",
        "invoice_verified": False,
        "input_pricing": "all_prompt_tokens_at_configured_rate",
        "cache": cache_details(usage),
        "provider_request_id": identifier,
        "requested_output_limit": limit,
        "output_limit_field": limit_field,
        "output_limit_exceeded": usage["completion_tokens"] > limit,
    }


def diagnostic_audit(snapshot):
    # Old records remain old: never invent missing cache details or wire limits.
    if not isinstance(snapshot, dict):
        snapshot = {}
    known = snapshot.get("basis") == "returned_tokens"
    result = {
        "cost_kind": "calculated" if known else "unclassified",
        "invoice_verified": False if snapshot.get("invoice_verified") is False else None,
    }
    cache = snapshot.get("cache")
    if (
        isinstance(cache, dict)
        and isinstance(cache.get("state"), str)
        and cache["state"] in {"reported", "not_reported", "invalid"}
    ):
        result["cache_state"] = cache["state"]
        for key in ("hit_tokens", "miss_tokens"):
            value = cache.get(key)
            result[key] = value if type(value) is int and value >= 0 else None
    else:
        result["cache_state"] = "not_recorded"
    limit = snapshot.get("requested_output_limit")
    result["requested_output_limit"] = limit if type(limit) is int and limit > 0 else None
    exceeded = snapshot.get("output_limit_exceeded")
    result["output_limit_exceeded"] = exceeded if type(exceeded) is bool else None
    return result
