"""Verify effective worker files, including stale/extra/symlinked source refusal."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from app.ops.acceptance_source import create, verify

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def database():
    yield


def checkout(root):
    (root / "app/ops").mkdir(parents=True)
    (root / "app/__init__.py").write_text("")
    shutil.copy2(ROOT / "app/ops/acceptance_source.py", root / "app/ops/acceptance_source.py")
    (root / "app/ops/service_acceptance.py").write_text("# acceptance\n")
    (root / "app/ops/acceptance_cases.py").write_text("# fixtures\n")
    (root / "requirements.lock").write_text("test-dependency==1\n")
    (root / ".env").write_text("FAKE_SECRET=must-not-enter-manifest\n")
    subprocess.run(["git", "init", "-b", "main", str(root)], check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Acceptance Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-m",
            "fixture",
        ],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return root


def test_manifest_matches_effective_source_without_reading_environment(tmp_path):
    root = checkout(tmp_path / "source")
    manifest = create(root)
    assert ".env" not in manifest["files"]
    assert "must-not-enter-manifest" not in json.dumps(manifest)
    verified = verify(root, manifest)
    assert verified["source_commit"] == manifest["source_commit"]
    assert verified["files_checked"] == len(manifest["files"])
    assert len(verified["manifest_sha256"]) == 64
    # Bytecode cache is not source and must not invalidate ordinary worker imports.
    (root / "app/__pycache__").mkdir()
    (root / "app/__pycache__/__init__.cpython-312.pyc").write_bytes(b"cache")
    assert verify(root, manifest) == verified


@pytest.mark.parametrize(
    "change", ["stale", "missing", "extra", "symlink", "directory_symlink", "lock"]
)
def test_worker_source_mismatch_is_rejected(tmp_path, change):
    root = checkout(tmp_path / "source")
    manifest = create(root)
    path = root / "app/ops/service_acceptance.py"
    if change == "stale":
        path.write_text("# older implementation\n")
    elif change == "missing":
        path.unlink()
    elif change == "extra":
        (root / "app/ops/untracked.py").write_text("# unexpected importable source\n")
    elif change == "symlink":
        target = tmp_path / "same-bytes.py"
        target.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(target)
    elif change == "directory_symlink":
        (root / "app/extra").symlink_to(tmp_path, target_is_directory=True)
    else:
        (root / "requirements.lock").write_text("test-dependency==2\n")
    with pytest.raises((OSError, ValueError)):
        verify(root, manifest)


@pytest.mark.parametrize("name", [".", "", "../outside", "/absolute", "app/../outside", ".env"])
def test_manifest_cannot_select_unrelated_paths(tmp_path, name):
    root = checkout(tmp_path / "source")
    manifest = create(root)
    manifest["files"][name] = "a" * 64
    with pytest.raises(ValueError):
        verify(root, manifest)


def test_dirty_checkout_and_incomplete_manifest_are_rejected(tmp_path):
    root = checkout(tmp_path / "source")
    manifest = create(root)
    manifest["files"].pop("app/__init__.py")
    with pytest.raises(ValueError):
        verify(root, manifest)
    (root / "app/ops/service_acceptance.py").write_text("# changed\n")
    with pytest.raises(ValueError):
        create(root)


@pytest.mark.parametrize("exit_code", [1, 125])
def test_wrapper_refuses_failed_source_probe_before_creating_database(tmp_path, exit_code):
    project = checkout(tmp_path / "project")
    (project / "scripts").mkdir()
    shutil.copy2(ROOT / "scripts/service-acceptance.sh", project / "scripts")
    subprocess.run(["git", "add", "."], cwd=project, check=True, capture_output=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Acceptance Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-m",
            "wrapper",
        ],
        cwd=project,
        check=True,
        capture_output=True,
    )
    binary = tmp_path / "bin"
    binary.mkdir()
    docker = binary / "docker"
    trace = tmp_path / "trace.jsonl"
    docker.write_text(
        "#!/usr/bin/env python3\n"
        "import json,sys\n"
        f"with open({str(trace)!r}, 'a') as f: f.write(json.dumps(sys.argv[1:])+'\\n')\n"
        "if 'exec' in sys.argv: print('true')\n"
        f"if 'app.ops.acceptance_source' in sys.argv: raise SystemExit({exit_code})\n"
    )
    docker.chmod(0o755)
    import os

    result = subprocess.run(
        ["bash", "scripts/service-acceptance.sh"],
        cwd=project,
        text=True,
        capture_output=True,
        env=os.environ | {"PATH": str(binary) + os.pathsep + os.environ["PATH"]},
        timeout=15,
    )
    assert result.returncode != 0
    calls = [json.loads(line) for line in trace.read_text().splitlines()]
    assert len(calls) == 3
    assert "app.ops.acceptance_source" in calls[-1]
    assert not any("createdb" in " ".join(call) for call in calls)
    assert "BACKUP:" not in result.stdout and "TEST_DATABASE:" not in result.stdout
    assert "worker source differs" in result.stderr
    manifest_mount = next(
        arg for arg in calls[-1] if arg.endswith(":/opt/acceptance-source.json:ro")
    )
    assert not Path(manifest_mount.split(":", 1)[0]).exists()
