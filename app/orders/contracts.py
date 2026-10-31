"""Generic, server-declared purchase terms. Independent of payment/public consent."""

import calendar
import hashlib
import json
import unicodedata
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StrictInt, field_validator

from app.services.base import ServiceError

SERVICE_TIMEZONE = ZoneInfo("Asia/Riyadh")


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, revalidate_instances="always")
    kind: str = Field(pattern=r"^[a-z][a-z0-9_]{0,63}$")
    version: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,40}$")
    months: StrictInt = Field(ge=1, le=12)
    ar: str = Field(min_length=20, max_length=400)
    en: str = Field(min_length=20, max_length=400)

    @field_validator("ar", "en")
    @classmethod
    def readable(cls, text):
        if not text.strip() or any(
            unicodedata.category(c) in {"Cc", "Cf", "Cs"} and c != "\n" for c in text
        ):
            raise ValueError("readable plain purchase terms required")
        return text


class Quote(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    contract: Contract
    service: str
    service_version: str
    price_halala: StrictInt = Field(gt=0)
    price_stars: StrictInt | None
    payment_mode: str
    starts_at: AwareDatetime
    expires_at: AwareDatetime
    valid_until: AwareDatetime


def add_months(start, months):
    if not isinstance(start, datetime) or start.utcoffset() is None:
        raise ValueError("aware start required")
    if type(months) is not int or not 1 <= months <= 12:
        raise ValueError("invalid calendar duration")
    start = start.astimezone(SERVICE_TIMEZONE)
    year, month = divmod(start.year * 12 + start.month - 1 + months, 12)
    month += 1
    return start.replace(
        year=year, month=month, day=min(start.day, calendar.monthrange(year, month)[1])
    ).astimezone(UTC)


def declaration(plugin):
    raw = getattr(plugin, "purchase_contract", None)
    return Contract.model_validate(raw) if raw is not None else None


def make_quote(service, plugin, *, stars, now=None):
    contract = declaration(plugin)
    if contract is None:
        return None
    start = now or datetime.now(UTC)
    if not isinstance(start, datetime) or start.utcoffset() is None:
        raise ValueError("aware quote time required")
    start = start.astimezone(UTC)
    return Quote(
        contract=contract,
        service=service.slug,
        service_version=service.version,
        price_halala=service.price_halala,
        price_stars=service.price_stars if stars else None,
        payment_mode="stars" if stars else "test_credit",
        starts_at=start,
        expires_at=add_months(start, contract.months),
        valid_until=start + timedelta(hours=1),
    ).model_dump(mode="json")


def snapshot(value):
    if value is None:
        return None, None
    # JSON validation permits serialized aware datetimes, while strict fields
    # still reject coercion of numbers/bools or unknown customer fields.
    try:
        raw = json.dumps(value, ensure_ascii=False, allow_nan=False)
        if len(raw.encode()) > 8192:
            raise ValueError("oversized purchase quote")
        checked = Quote.model_validate_json(raw)
        data = checked.model_dump(mode="json")
        canonical = json.dumps(
            data, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode()
        return data, hashlib.sha256(canonical).hexdigest()
    except (ValueError, TypeError, UnicodeError, OverflowError):
        raise ServiceError("service_changed") from None


def validate(value, service, plugin, *, stars, now=None):
    data, digest = snapshot(value)
    try:
        expected = declaration(plugin)
        if expected is None:
            if data is not None:
                raise ValueError("unexpected purchase terms")
            return None, None
        if data is None:
            raise ValueError("purchase terms required")
        quote = Quote.model_validate_json(json.dumps(data))
        start, end = quote.starts_at, quote.expires_at
        current = now or datetime.now(UTC)
        if (
            quote.contract != expected
            or (
                quote.service,
                quote.service_version,
                quote.price_halala,
                quote.price_stars,
                quote.payment_mode,
            )
            != (
                service.slug,
                service.version,
                service.price_halala,
                service.price_stars if stars else None,
                "stars" if stars else "test_credit",
            )
            or not start <= current < quote.valid_until
            or quote.valid_until != start + timedelta(hours=1)
            or end != add_months(start, expected.months)
        ):
            raise ValueError("purchase quote changed")
        return data, digest
    except (ValueError, TypeError, OverflowError):
        raise ServiceError("service_changed") from None
