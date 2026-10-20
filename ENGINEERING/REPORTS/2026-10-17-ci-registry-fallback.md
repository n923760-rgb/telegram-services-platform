# Bounded fallback for official CI images

Baseline: official main 409828c1e5181ba1a3baaad4e69a7e7779ced0ec; #96 qualified 2037 tests and 20 non-root/native checks before merge. Owner authorizes ongoing improvements and reviewed merging; production deployment is explicitly deferred. Unrelated governance PR #21 is untouched.

## Failure evidence and change

[Main a898e82 workflow 39032364723](https://github.com/n923760-rgb/telegram-services-platform/actions/runs/39032364723) attempts 1 and 2 failed during Initialize containers, before checkout, pulling public.ecr.aws/docker/library/postgres:16-bookworm with toomanyrequests: Data limit exceeded. The pre-merge #95 workflow qualified identical application bytes; these later failures are not evidence of an application regression.

GitHub service-container initialization happens before repository steps, leaving no place to implement a pull fallback there. The new workflow checks out source first, then runs a standard-library helper with a fixed allowlist: PostgreSQL 16-bookworm, Redis 7-alpine and Python 3.12-slim. Each image has at most one 90-second client pull attempt from ECR Public, then one from Docker Hub. Missing CI/output context rejects before network work; arbitrary image overrides are not accepted. All three outputs are emitted only after all pulls succeed. Both-source failure fails the job. No registry credentials, new publisher or image pushes.

The two test services move into a separate CI-only Compose file with the existing database/user, synthetic password and health probes. Bindings and test URLs explicitly use IPv4 loopback. The project name includes the GitHub run and attempt. Compose up requires health with --wait --wait-timeout 120 and --pull never against already selected images. Cleanup always targets only this file/project, removing its disposable containers/network/anonymous volumes. No production resources or external volumes are referenced.

The worker build receives the selected Python image with pull disabled. Every original gate remains mandatory: lint, format, migrations, full pytest, Alembic drift, production Compose syntax and the non-root/network-disabled native worker qualification. The embedded worker qualification Python is unchanged byte-for-byte. No dependency, production image default, Dockerfile, service, provider, financial or data-model change.

## Qualification and limits

PASS LOCALLY: 17 helper/architecture checks, global Ruff lint/format and diff. Mocked tests cover primary success, nonzero/quota fallback and timeout fallback for each image, fixed image series, both registries unavailable with no partial output, missing CI context, ignored image overrides and mandatory/scoped workflow gates. Workflow/CI Compose YAML parses; embedded Python compiles; native worker body equality verified against the baseline. Docker is unavailable locally, so actual Compose startup, selected registry reachability and worker builds require the full hosted workflow before merge. No local Docker execution claim.

Docker documents these official images on ECR Public and Docker Hub. Existing version tags can change or mirrors lag; no cross-registry immutable digest identity is claimed. Client timeouts bound helper waits; Docker's daemon implementation may continue background work after a timed-out CLI. Both sources and other dependencies can be unavailable, so this reduces a single-registry failure mode rather than guaranteeing CI availability. No check is skipped to manufacture a green result. Do not run the CI Compose stack on the production VPS; the CI-context check is an operational guard, not a security sandbox.

References checked 2026-10-17: [Docker official image mirror](https://www.docker.com/blog/news-from-aws-reinvent-docker-official-images-on-amazon-ecr-public/), [Compose health/pull controls](https://docs.docker.com/reference/cli/docker/compose/up/), [Compose scoped cleanup](https://docs.docker.com/reference/cli/docker/compose/down/).
