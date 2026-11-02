"""Stdlib-only acceptance source evidence; never reads configuration or credentials."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path, PurePosixPath

TREES = ("app", "migrations")
FILES = ("requirements.lock", "pyproject.toml", "uv.lock", "alembic.ini", "Dockerfile")
REQUIRED = {"app/__init__.py", "app/ops/acceptance_source.py", "requirements.lock"}


def scoped(name):
    if not isinstance(name, str) or not name:
        return False
    path = PurePosixPath(name)
    return (
        bool(path.parts)
        and str(path) == name
        and not path.is_absolute()
        and ".." not in path.parts
        and "__pycache__" not in path.parts
        and (name in FILES or path.parts[0] in TREES)
    )


def digest(root, name):
    path = root
    for part in PurePosixPath(name).parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("source symlink")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create(root):
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=root):
        raise ValueError("clean checkout required")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    names = (
        subprocess.check_output(["git", "ls-files", "-z", "--", *TREES, *FILES], cwd=root)
        .decode()
        .split("\0")
    )
    names = [name for name in names if name]
    if not names or not all(scoped(name) for name in names):
        raise ValueError("source scope")
    return {"source_commit": commit, "files": {name: digest(root, name) for name in names}}


def verify(root, manifest):
    if (
        root.is_symlink()
        or not isinstance(manifest, dict)
        or set(manifest) != {"source_commit", "files"}
        or not isinstance(manifest["source_commit"], str)
        or not re.fullmatch(r"[a-f0-9]{40}", manifest["source_commit"])
        or not isinstance(manifest["files"], dict)
        or not REQUIRED <= manifest["files"].keys()
    ):
        raise ValueError("source manifest")
    expected = manifest["files"]
    for name, value in expected.items():
        if (
            not scoped(name)
            or not isinstance(value, str)
            or not re.fullmatch(r"[a-f0-9]{64}", value)
            or digest(root, name) != value
        ):
            raise ValueError("source mismatch")
    actual = {name for name in FILES if (root / name).exists() or (root / name).is_symlink()}
    for folder in TREES:
        if (root / folder).is_symlink():
            raise ValueError("source symlink")
        for path in (root / folder).rglob("*"):
            name = path.relative_to(root).as_posix()
            if "__pycache__" in path.relative_to(root).parts:
                continue
            if path.is_symlink():
                raise ValueError("source symlink")
            if path.is_file():
                actual.add(name)
    if actual != set(expected):
        raise ValueError("unexpected source files")
    return {
        "source_commit": manifest["source_commit"],
        "manifest_sha256": hashlib.sha256(
            json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "files_checked": len(expected),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("create", "verify"))
    parser.add_argument("manifest", nargs="?")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        result = (
            create(args.root)
            if args.mode == "create"
            else verify(args.root, json.loads(Path(args.manifest).read_text()))
        )
    except (OSError, ValueError, TypeError, subprocess.CalledProcessError):
        raise SystemExit("SOURCE_VERIFICATION_FAILED") from None
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
