"""Architecture gates for future plugins; executable plugins remain trusted code."""

import ast
from pathlib import Path

from app.services.registry import registry

ROOT = Path(__file__).resolve().parents[1]


def test_plugins_keep_telegram_and_network_clients_out():
    forbidden = {
        "aiogram",
        "telegram",
        "httpx",
        "requests",
        "aiohttp",
        "urllib",
        "openai",
        "anthropic",
        "boto3",
    }
    for path in (ROOT / "app/services").glob("*/**/*.py"):
        if path.name.startswith("test_"):
            continue
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            assert not any(name.split(".")[0] in forbidden for name in names), path


def test_core_policy_has_no_named_service_branches():
    slugs = set(registry.types)
    for folder in ("wallet", "orders", "workers", "core"):
        for path in (ROOT / "app" / folder).rglob("*.py"):
            tree = ast.parse(path.read_text())
            constants = {
                node.value
                for node in ast.walk(tree)
                if isinstance(node, ast.Constant) and isinstance(node.value, str)
            }
            assert not constants & slugs, path


def test_plugin_contract_files_and_governance_are_present():
    for slug in registry.types:
        folder = ROOT / "app/services" / slug
        assert all(
            (folder / name).is_file()
            for name in ("schema.py", "prompt.py", "service.py", "test_service.py")
        )
    assert len((ROOT / "AGENTS.md").read_text().splitlines()) < 120
