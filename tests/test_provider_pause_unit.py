from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.models import Setting
from app.ops.settings import provider_paused


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize(
    "value",
    [
        None,
        False,
        0,
        "",
        [],
        {},
        {"value": None},
        {"value": 0},
        {"value": []},
        {"value": "false"},
        {"value": True},
        {"value": {}},
        {"value": ""},
    ],
)
async def test_invalid_or_true_pause_is_closed_without_mutation(value):
    db = SimpleNamespace(get=AsyncMock(return_value=SimpleNamespace(value=value)))
    assert await provider_paused(db) is True
    db.get.assert_awaited_once_with(Setting, "PROVIDER_PAUSED")


@pytest.mark.parametrize("row", [None, SimpleNamespace(value={"value": False})])
async def test_only_missing_row_or_explicit_false_allows_admission(row):
    db = SimpleNamespace(get=AsyncMock(return_value=row))
    assert await provider_paused(db) is False
