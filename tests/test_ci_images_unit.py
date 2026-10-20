"""CI image fallback stays bounded and never converts unavailable services to a pass."""

import importlib.util
from pathlib import Path
from subprocess import CompletedProcess, TimeoutExpired

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("ci_images", ROOT / ".github/scripts/ci_images.py")
images = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(images)


@pytest.fixture(autouse=True)
def database():
    yield


@pytest.mark.parametrize("name", ["postgres", "redis", "python"])
@pytest.mark.parametrize("failure", [None, "quota", "timeout"])
def test_official_registry_selection_is_bounded_and_preserves_image_series(
    monkeypatch, name, failure
):
    calls = []

    def run(args, *, timeout, check):
        calls.append(args)
        assert timeout == 90 and check is False
        if len(calls) == 1 and failure == "timeout":
            raise TimeoutExpired(args, timeout)
        return CompletedProcess(args, 1 if len(calls) == 1 and failure == "quota" else 0)

    monkeypatch.setattr(images.subprocess, "run", run)
    chosen = images.select_image(name)
    tag = images.IMAGES[name]
    assert chosen == ("docker.io/library/" if failure else "public.ecr.aws/docker/library/") + tag
    assert len(calls) == (2 if failure else 1)
    assert all(call[:2] == ["docker", "pull"] and call[-1].endswith("/" + tag) for call in calls)


def test_both_registries_unavailable_fail_closed_without_emitting_partial_outputs(
    monkeypatch, tmp_path
):
    calls = []
    output = tmp_path / "outputs"
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))

    def unavailable(args, **kwargs):
        calls.append(args)
        return CompletedProcess(args, 1)

    monkeypatch.setattr(images.subprocess, "run", unavailable)
    with pytest.raises(RuntimeError, match="No official registry"):
        images.main()
    assert len(calls) == 2 and not output.exists()


@pytest.mark.parametrize("actions,output", [("false", "outputs"), ("true", "")])
def test_helper_refuses_missing_ci_context_before_network(monkeypatch, actions, output):
    monkeypatch.setenv("GITHUB_ACTIONS", actions)
    monkeypatch.setenv("GITHUB_OUTPUT", output)

    def forbidden(*args, **kwargs):
        raise AssertionError("no network before validating CI context")

    monkeypatch.setattr(images.subprocess, "run", forbidden)
    with pytest.raises(RuntimeError, match="GitHub Actions only"):
        images.main()


def test_success_emits_only_all_three_fixed_images_not_environment_overrides(monkeypatch, tmp_path):
    output = tmp_path / "outputs"
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv("CI_POSTGRES_IMAGE", "unapproved.invalid/arbitrary:latest")
    calls = []

    def successful(args, **kwargs):
        calls.append(args)
        return CompletedProcess(args, 0)

    monkeypatch.setattr(images.subprocess, "run", successful)
    images.main()
    assert len(calls) == 3
    assert output.read_text().splitlines() == [
        f"{name}_image=public.ecr.aws/docker/library/{tag}" for name, tag in images.IMAGES.items()
    ]
    with pytest.raises(KeyError):
        images.select_image("unapproved")
    assert len(calls) == 3


def test_workflow_keeps_required_checks_and_scopes_health_and_cleanup_to_ci():
    workflow = (ROOT / ".github/workflows/verify.yml").read_text()
    for required in (
        "uv run ruff check .",
        "uv run ruff format --check .",
        "uv run alembic upgrade head",
        "uv run pytest -q",
        "uv run alembic check",
        "--network none",
        "--target document-worker",
        'docker compose -f .github/compose.ci.yml -p "$CI_INFRA_PROJECT" up -d --wait --wait-timeout 120 --pull never',
        'docker compose -f .github/compose.ci.yml -p "$CI_INFRA_PROJECT" down --volumes',
        "if: always()",
        "CI_INFRA_PROJECT: tsp-ci-${{ github.run_id }}-${{ github.run_attempt }}",
    ):
        assert required in workflow
    assert "continue-on-error" not in workflow
    compose = (ROOT / ".github/compose.ci.yml").read_text()
    assert "pg_isready -U services -d services_test" in compose and "redis-cli, ping" in compose
    assert "127.0.0.1:5432:5432" in compose and "127.0.0.1:6379:6379" in compose
    assert "env_file" not in compose and "external:" not in compose
