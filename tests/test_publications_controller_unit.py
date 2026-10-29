"""Exercise the actual client controller without claiming real-browser visuals."""

import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def database():
    pass


def test_publication_ui_separate_consent_sandbox_and_uncertain_retry():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is required for the publication controller regression")
    subprocess.run(
        [node, "tests/publications_controller.cjs"],
        cwd=Path(__file__).resolve().parents[1],
        check=True,
        timeout=20,
    )
