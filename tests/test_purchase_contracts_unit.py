from copy import deepcopy
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.bot.order_review import confirmation_text
from app.orders import contracts
from app.orders.drafts import new_draft
from app.publications.offering import CONTRACT, PRICE_HALALA
from app.services.base import ServiceError
from app.services.registry import registry


@pytest.fixture(autouse=True)
def database():
    pass


def service():
    return SimpleNamespace(slug="fixture", version="1", price_halala=PRICE_HALALA, price_stars=40)


def plugin():
    return SimpleNamespace(purchase_contract=deepcopy(CONTRACT))


def quote():
    return contracts.make_quote(service(), plugin(), stars=False)


@pytest.mark.parametrize(
    "start,expected",
    [
        ("2026-10-31T12:00:00+03:00", "2027-04-30T12:00:00+03:00"),
        ("2024-08-31T01:00:00+03:00", "2025-02-28T01:00:00+03:00"),
        ("2023-08-31T01:00:00+03:00", "2024-02-29T01:00:00+03:00"),
        ("2026-05-30T22:00:00+00:00", "2026-11-30T01:00:00+03:00"),
        ("2026-12-31T23:00:00+03:00", "2027-06-30T23:00:00+03:00"),
    ],
)
def test_six_calendar_months_use_riyadh_end_of_month_and_leap_years(start, expected):
    actual = contracts.add_months(datetime.fromisoformat(start), 6)
    assert actual == datetime.fromisoformat(expected)
    assert actual.utcoffset() == timedelta(0)


@pytest.mark.parametrize("months", [0, 13, True, "6", 6.0])
def test_reject_coerced_or_unbounded_duration(months):
    with pytest.raises(ValueError):
        contracts.add_months(datetime.now(UTC), months)


@pytest.mark.parametrize("stars", [False, True])
def test_quote_binds_approved_policy_and_distinct_payment_units(stars):
    value = contracts.make_quote(service(), plugin(), stars=stars)
    data, digest = contracts.validate(value, service(), plugin(), stars=stars)
    assert data == value and len(digest) == 64
    assert data["contract"]["months"] == 6
    assert data["price_halala"] == 2900
    assert data["price_stars"] == (40 if stars else None)
    assert data["payment_mode"] == ("stars" if stars else "test_credit")
    assert contracts.snapshot(dict(reversed(list(value.items())))) == (data, digest)


@pytest.mark.parametrize(
    "change",
    [
        "price",
        "service",
        "version",
        "mode",
        "stars",
        "terms",
        "months",
        "policy",
        "expiry",
        "validity",
        "future",
        "extra",
        "missing",
    ],
)
def test_changed_quote_rejects_before_purchase(change):
    value = quote()
    if change == "price":
        value["price_halala"] = 1500
    elif change == "service":
        value["service"] = "another"
    elif change == "version":
        value["service_version"] = "2"
    elif change == "mode":
        value["payment_mode"] = "stars"
    elif change == "stars":
        value["price_stars"] = 40
    elif change == "terms":
        value["contract"]["ar"] += " تغييرات لم تُراجع."
    elif change == "months":
        value["contract"]["months"] = 12
    elif change == "policy":
        value["contract"]["version"] = "another-version"
    elif change == "expiry":
        value["expires_at"] = (datetime.now(UTC) + timedelta(days=365)).isoformat()
    elif change == "validity":
        value["valid_until"] = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    elif change == "future":
        value["starts_at"] = (datetime.now(UTC) + timedelta(minutes=1)).isoformat()
    elif change == "extra":
        value["renew_automatically"] = True
    else:
        value = None
    with pytest.raises(ServiceError):
        contracts.validate(value, service(), plugin(), stars=False)


def test_expired_quote_and_changed_server_policy_reject():
    value = quote()
    expiry = datetime.fromisoformat(value["valid_until"])
    with pytest.raises(ServiceError):
        contracts.validate(value, service(), plugin(), stars=False, now=expiry)
    changed = plugin()
    changed.purchase_contract["months"] = 12
    with pytest.raises(ServiceError):
        contracts.validate(value, service(), changed, stars=False)


@pytest.mark.parametrize("value", [" " * 30, "س" * 30 + "\u202e", "a" * 30 + "\x00"])
def test_terms_are_bounded_readable_server_text(value):
    with pytest.raises(ValidationError):
        contracts.Contract.model_validate({**CONTRACT, "ar": value})


def test_existing_services_keep_their_original_no_contract_shape():
    assert contracts.make_quote(service(), SimpleNamespace(), stars=False) is None
    assert contracts.validate(None, service(), SimpleNamespace(), stars=False) == (None, None)
    with pytest.raises(ServiceError):
        contracts.validate(quote(), service(), SimpleNamespace(), stars=False)


@pytest.mark.parametrize("lang", ["ar", "en"])
def test_shared_review_displays_price_calendar_duration_and_exact_aware_dates(monkeypatch, lang):
    monkeypatch.setattr(registry.types["echo"], "purchase_contract", deepcopy(CONTRACT))
    row = SimpleNamespace(
        slug="echo",
        version="1",
        name_ar="خدمة اختبار",
        name_en="Test service",
        price_halala=2900,
        price_stars=None,
        input_schema=registry.types["echo"].input_schema.model_dump(),
    )
    data = new_draft(row, inputs={"text": "customer source"}, index=1)
    review = confirmation_text(data, lang)
    parsed = contracts.Quote.model_validate_json(__import__("json").dumps(data["purchase_quote"]))
    assert "29.00" in review and "6" in review
    assert (
        parsed.expires_at.astimezone(contracts.SERVICE_TIMEZONE).isoformat(timespec="minutes")
        in review
    )
    assert CONTRACT[lang] in review
    assert len(review.encode("utf-16-le")) // 2 <= 3900
