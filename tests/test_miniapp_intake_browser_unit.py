"""Run the real JavaScript controller's rejection and ambiguous-retry regression."""

import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def database():
    yield


def test_confirmation_rejection_allows_correction_but_uncertain_retry_keeps_same_token():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is required for the browser controller regression")
    subprocess.run(
        [node, "tests/miniapp_intake_browser.cjs"],
        cwd=Path(__file__).resolve().parents[1],
        check=True,
        timeout=20,
    )
