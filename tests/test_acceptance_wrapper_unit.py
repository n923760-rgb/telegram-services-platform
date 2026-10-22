"""Run the operator shell wrapper against fake Docker before any database writes."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize("preflight_code", [1, 125, 0])
def test_mount_probe_precedes_database_access_and_stops_without_test_resources(
    tmp_path, preflight_code
):
    project = tmp_path / "project"
    scripts = project / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy2(ROOT / "scripts/service-acceptance.sh", scripts)
    binary = tmp_path / "bin"
    binary.mkdir()
    git = binary / "git"
    git.write_text('#!/bin/sh\nif [ "$1" = branch ]; then echo main; fi\n')
    git.chmod(0o755)
    docker = binary / "docker"
    docker.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "with open(os.environ['DOCKER_TRACE'], 'a') as trace:\n"
        "    trace.write(json.dumps(sys.argv[1:]) + '\\n')\n"
        "if 'run' in sys.argv:\n"
        "    assert sys.stdin.read() == ''\n"
        "    raise SystemExit(int(os.environ['PREFLIGHT_CODE']))\n"
        "if 'exec' in sys.argv:\n"
        "    print('false')\n"  # Deliberately fail the existing provider-pause gate.
    )
    docker.chmod(0o755)
    trace = tmp_path / "docker.jsonl"
    result = subprocess.run(
        ["bash", str(scripts / "service-acceptance.sh")],
        input="unused parent script input\n",
        text=True,
        capture_output=True,
        timeout=10,
        env=os.environ
        | {
            "PATH": str(binary) + os.pathsep + os.environ["PATH"],
            "DOCKER_TRACE": str(trace),
            "PREFLIGHT_CODE": str(preflight_code),
        },
    )
    assert result.returncode != 0
    calls = [json.loads(line) for line in trace.read_text().splitlines()]
    assert calls[0][:7] == [
        "compose",
        "run",
        "--rm",
        "--no-deps",
        "-T",
        "-v",
        f"{project}/app/ops/service_acceptance.py:/opt/app/app/ops/service_acceptance.py:ro",
    ]
    assert (
        f"{project}/app/ops/acceptance_cases.py:/opt/app/app/ops/acceptance_cases.py:ro" in calls[0]
    )
    assert "--user" not in calls[0]  # Keep the configured non-root worker identity.
    assert len(calls) == (2 if preflight_code == 0 else 1)
    if preflight_code:
        assert (
            "chmod 0644 app/ops/service_acceptance.py app/ops/acceptance_cases.py" in result.stderr
        )
    else:
        assert "SELECT value" in calls[1][-1] and "PROVIDER_PAUSED" in calls[1][-1]
    assert not any("createdb" in " ".join(call) for call in calls)
    assert "BACKUP:" not in result.stdout and "TEST_DATABASE:" not in result.stdout
