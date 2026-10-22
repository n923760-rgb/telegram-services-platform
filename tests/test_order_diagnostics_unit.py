import json
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import UUID

import pytest

from app.core.settings import config
from app.ops import order_diagnostics
from app.services.base import ServiceError


def entry(kind, available, reserved):
    return SimpleNamespace(kind=kind, available_delta=available, reserved_delta=reserved)


@pytest.mark.parametrize("value", ["12345678", "ABCDEF12", "12345678-0000-0000-0000-000000000001"])
def test_native_uuid_reference_bounds(value):
    lower, upper = order_diagnostics.reference_bounds(value)
    if len(value) == 8:
        assert str(lower)[:8] == str(upper)[:8] == value.lower()
        assert lower.int < upper.int
    else:
        assert lower == upper == UUID(value)


@pytest.mark.parametrize("value", ["", "123", "1234567%", "12345678%", "x" * 1000, "not-a-uuid"])
def test_invalid_references_fail_before_query(value):
    with pytest.raises(ServiceError, match="invalid_reference"):
        order_diagnostics.reference_bounds(value)


def test_release_evidence_requires_exact_order_ledger_and_payment_mode():
    rows = [entry("reserve", -500, 500), entry("release", 500, -500)]
    assert order_diagnostics.wallet_evidence("test_credit", 500, rows)[
        "test_credit_release_confirmed"
    ]
    for mode, price, entries in (
        ("stars", 500, rows),
        ("test_credit", 777, rows),
        ("test_credit", 0, rows),
        ("test_credit", 500, []),
        ("test_credit", 500, rows[:1]),
        ("test_credit", 500, [*rows, entry("capture", 0, -500)]),
        ("test_credit", 500, [entry("reserve", -500, 500), entry("release", 500, -400)]),
    ):
        assert not order_diagnostics.wallet_evidence(mode, price, entries)[
            "test_credit_release_confirmed"
        ]


async def test_unauthorized_actor_cannot_open_database(monkeypatch):
    monkeypatch.setattr(config(), "admin_ids", [7])
    database = Mock(side_effect=AssertionError("must not open database"))
    monkeypatch.setattr(order_diagnostics, "sessions", database)
    with pytest.raises(ServiceError, match="not_allowed"):
        await order_diagnostics.inspect("12345678", actor_id=8)
    database.begin.assert_not_called()


def test_cli_redacts_runtime_error_and_never_claims_a_success(monkeypatch, capsys):
    import sys

    async def unavailable(*args):
        raise RuntimeError("database password, provider key and customer content")

    monkeypatch.setattr(order_diagnostics, "inspect", unavailable)
    monkeypatch.setattr(sys, "argv", ["order_diagnostics", "12345678"])
    assert order_diagnostics.main() == 1
    report = json.loads(capsys.readouterr().out)
    assert report == {"status": "unknown", "error": "runtime_unavailable"}
