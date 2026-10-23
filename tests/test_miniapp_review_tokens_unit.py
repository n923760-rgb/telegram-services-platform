import pytest
from pydantic import SecretStr, ValidationError

from app.core.settings import config
from app.miniapp.confirmation import ConfirmRequest
from app.miniapp.review_tokens import InvalidReviewToken, issue, verify


@pytest.fixture
def token(monkeypatch):
    monkeypatch.setattr(config(), "bot_token", SecretStr("12345:synthetic-only"))
    return issue(11, "a" * 32, "b" * 64, now=1700000000)


def test_review_is_bound_to_owner_draft_and_exact_revision(token):
    assert verify(11, token, now=1700000001) == ("a" * 32, "b" * 64)
    with pytest.raises(InvalidReviewToken):
        verify(22, token, now=1700000001)


def test_result_and_purchase_tokens_are_not_interchangeable(token):
    result = issue(11, "a" * 32, "b" * 64, now=1700000000, purpose="result")
    assert verify(11, result, now=1700000001, purpose="result") == ("a" * 32, "b" * 64)
    with pytest.raises(InvalidReviewToken):
        verify(11, token, now=1700000001, purpose="result")
    with pytest.raises(InvalidReviewToken):
        verify(11, result, now=1700000001)


@pytest.mark.parametrize("change", ["key", "revision", "signature", "future", "expired", "empty"])
def test_changed_or_expired_review_cannot_authorize_confirmation(token, change):
    current = 1700000001
    if change == "key":
        token = token.replace("a" * 32, "c" * 32)
    if change == "revision":
        token = token.replace("b" * 64, "c" * 64)
    if change == "signature":
        token = token[:-1] + ("0" if token[-1] != "0" else "1")
    if change == "future":
        current = 1699999900
    if change == "expired":
        current = 1700003601
    if change == "empty":
        token = ""
    with pytest.raises(InvalidReviewToken):
        verify(11, token, now=current)


@pytest.mark.parametrize(
    "extra",
    [
        {"user_id": 22},
        {"price": 1},
        {"inputs": {}},
        {"key": "x"},
        {"accepted": 1},
        {"accepted": "true"},
    ],
)
def test_customer_cannot_override_financial_contract_or_use_coerced_consent(token, extra):
    with pytest.raises(ValidationError):
        ConfirmRequest.model_validate(
            {"init_data": "signed", "token": token, "accepted": True, **extra}
        )
