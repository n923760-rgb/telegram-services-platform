"""Pure authorization/metadata checks; no PostgreSQL or provider calls."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.i18n import tr
from app.core.settings import config
from app.ops import activation
from app.services.base import ServiceError
from app.services.registry import registry


@pytest.fixture(autouse=True)
def database():
    pass


def test_evidence_digest_is_key_order_independent_and_changes_on_payment_or_state():
    first = {"orders": [{"id": "a", "status": "queued"}], "charges": []}
    assert activation.digest(first) == activation.digest({"charges": [], "orders": first["orders"]})
    assert activation.digest(first) != activation.digest({**first, "charges": [{"amount": 20}]})
    assert activation.digest(first) != activation.digest(
        {**first, "orders": [{"id": "a", "status": "delivering"}]}
    )


def test_totals_keep_test_credit_and_stars_independent_and_include_extra_receipts():
    evidence = {
        "orders": [
            {"id": "credit", "mode": "test_credit", "halalas": 12550},
            {"id": "paid", "mode": "stars", "halalas": 100},
            {"id": "unpaid", "mode": "stars", "halalas": 100},
        ],
        "charges": [
            {"order": "paid", "amount": 20, "accepted": True, "state": "paid"},
            {"order": "paid", "amount": 20, "accepted": False, "state": "paid"},
            {"order": "paid", "amount": 20, "accepted": False, "state": "refund_uncertain"},
        ],
    }
    assert activation.totals(evidence) == {
        "active": 3,
        "test_credit": 12550,
        "unpaid": 1,
        "paid_stars": 40,
        "refunds_in_progress": 1,
    }


@pytest.mark.parametrize("enabled", [0, 1, None, "true"])
async def test_non_boolean_target_rejected_before_database(monkeypatch, enabled):
    monkeypatch.setattr(config(), "admin_ids", [7])
    with pytest.raises(ServiceError, match="input_invalid"):
        await activation.change_activation(
            "echo", enabled, actor_id=7, expected_hash="0" * 64, change_id="bad"
        )


@pytest.mark.parametrize("actor", [True, 1, "7", None])
def test_unauthorized_actor_rejected(monkeypatch, actor):
    monkeypatch.setattr(config(), "admin_ids", [7])
    with pytest.raises(ServiceError, match="not_allowed"):
        activation.authorize(actor)


@pytest.mark.parametrize("lang", ["ar", "en"])
def test_confirmation_and_callbacks_fit_telegram_limits(lang):
    text = tr(
        "admin_activation_review",
        lang,
        name="x" * 200,
        action=tr("admin_deactivate", lang),
        active=100,
        credit="1000000000.00",
        unpaid=100,
        stars=500000000,
        refunds=500,
    )
    text += "\n\n" + tr("admin_activation_disable_warning", lang)
    assert len(text.encode("utf-16-le")) // 2 < 4096
    assert len(("admin:activation_confirm:" + "a" * 32).encode()) <= 64
    assert len(("admin:activation:" + "a" * 40 + ":1").encode()) <= 64


@pytest.mark.parametrize("state", ["off", "paused", "invalid"])
async def test_required_ai_cannot_be_enabled_without_configuration(state):
    service = SimpleNamespace(
        enabled=False,
        version=registry.types["text_translation"].version,
        slug="text_translation",
        price_stars=20,
    )
    evidence = {"source_version": service.version, "ai_state": state}
    with pytest.raises(ServiceError, match="provider_config"):
        await activation.validate_target(
            SimpleNamespace(scalar=AsyncMock()), service, evidence, True
        )


async def test_previously_pending_disable_blocks_enable_without_provider_call(monkeypatch):
    monkeypatch.setattr(config(), "stars_enabled", False)
    service = SimpleNamespace(
        enabled=False,
        version=registry.types["images_to_pdf"].version,
        slug="images_to_pdf",
        price_stars=None,
    )
    evidence = {"source_version": service.version, "ai_state": "off"}
    with pytest.raises(ServiceError, match="admin_activation_pending"):
        await activation.validate_target(
            SimpleNamespace(scalar=AsyncMock(return_value="pending")), service, evidence, True
        )
