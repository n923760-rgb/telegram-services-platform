from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.settings import config
from app.ops import service_portfolio, worker_capabilities
from app.services.base import ServiceError
from app.services.registry import Registry, registry


@pytest.fixture(autouse=True)
def database():
    yield


def test_customer_catalog_excludes_private_and_replaced_plugins():
    slugs = service_portfolio.customer_slugs()
    assert len(slugs) == 17 and "echo" not in slugs and "local_ocr" not in slugs
    assert slugs == sorted(slugs)


@pytest.mark.parametrize(
    "required,optional",
    [(["office_export"], ()), (("unknown",), ()), ((1,), ()), (("pdf_font",), ("pdf_font",))],
)
def test_registry_rejects_unknown_mutable_duplicate_worker_requirements(
    monkeypatch, required, optional
):
    plugin = registry.types["cv_formatting"]
    monkeypatch.setattr(plugin, "worker_requirements", required)
    monkeypatch.setattr(plugin, "optional_worker_requirements", optional)
    with pytest.raises(ValueError, match="invalid worker requirements"):
        Registry().discover()


def test_owner_selection_requires_one_configured_admin_or_explicit_authorized_id(monkeypatch):
    monkeypatch.setattr(config(), "admin_ids", [7])
    assert service_portfolio.owner_actor() == 7
    monkeypatch.setattr(config(), "admin_ids", [7, 8])
    with pytest.raises(ServiceError, match="choose_configured_admin"):
        service_portfolio.owner_actor()
    assert service_portfolio.owner_actor(8) == 8
    with pytest.raises(ServiceError, match="not_allowed"):
        service_portfolio.owner_actor(9)


async def test_probe_subprocess_receives_no_provider_or_database_environment(monkeypatch):
    monkeypatch.setenv("AI_API_KEY", "synthetic-secret")
    process = SimpleNamespace(
        returncode=0, communicate=AsyncMock(return_value=(b"eng\nara\n", None))
    )
    start = AsyncMock(return_value=process)
    monkeypatch.setattr(worker_capabilities.asyncio, "create_subprocess_exec", start)
    assert await worker_capabilities.command(
        "/usr/bin/tesseract", "--list-langs", capture=True
    ) == (True, b"eng\nara\n")
    assert set(start.call_args.kwargs["env"]) == {"PATH", "LANG", "HOME"}
    assert "synthetic-secret" not in str(start.call_args)


async def test_probe_timeout_kills_and_reaps_the_child(monkeypatch):
    from unittest.mock import Mock

    process = SimpleNamespace(
        returncode=None,
        communicate=AsyncMock(side_effect=TimeoutError),
        kill=Mock(),
        wait=AsyncMock(),
    )
    monkeypatch.setattr(
        worker_capabilities.asyncio, "create_subprocess_exec", AsyncMock(return_value=process)
    )
    assert await worker_capabilities.command("/usr/bin/libreoffice", "--version") == (False, b"")
    process.kill.assert_called_once()
    process.wait.assert_awaited_once()


def test_cli_inspection_is_read_only_and_errors_are_redacted(monkeypatch, capsys):
    import sys

    async def unavailable():
        raise RuntimeError("synthetic-secret endpoint database credential")

    monkeypatch.setattr(service_portfolio, "inspect", unavailable)
    monkeypatch.setattr(sys, "argv", ["service_portfolio"])
    assert service_portfolio.main() == 1
    text = capsys.readouterr().out
    assert "runtime_unavailable" in text and "synthetic-secret" not in text
