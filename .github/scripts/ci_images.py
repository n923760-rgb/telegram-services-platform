"""Bounded pulls of the existing official CI images; never accepts image overrides."""

import os
import subprocess
from pathlib import Path

IMAGES = {
    "postgres": "postgres:16-bookworm",
    "redis": "redis:7-alpine",
    "python": "python:3.12-slim",
}


def select_image(name):
    image = IMAGES[name]
    for registry in ("public.ecr.aws/docker/library/", "docker.io/library/"):
        candidate = registry + image
        print(f"Pulling CI {name}: {candidate}", flush=True)
        try:
            result = subprocess.run(["docker", "pull", candidate], timeout=90, check=False)
        except subprocess.TimeoutExpired:
            print(f"Timed out pulling {candidate}", flush=True)
            continue
        if result.returncode == 0:
            print(f"Selected CI {name}: {candidate}", flush=True)
            return candidate
    raise RuntimeError(f"No official registry source available for {name}")


def main():
    output = os.environ.get("GITHUB_OUTPUT")
    if os.environ.get("GITHUB_ACTIONS") != "true" or not output:
        raise RuntimeError("This helper is for GitHub Actions only")
    selected = {name: select_image(name) for name in IMAGES}
    with Path(output).open("a", encoding="utf-8") as stream:
        for name, image in selected.items():
            stream.write(f"{name}_image={image}\n")


if __name__ == "__main__":
    main()
