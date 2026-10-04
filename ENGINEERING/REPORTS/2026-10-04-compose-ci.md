# Compose CI environment correction

Date: 2026-10-04. Task branch: fix/ci-compose-env.
Starting official source: e055d2b98d6aaaed5111f25203c34ba7d3e4caaa on origin/main.
Repository: https://github.com/n923760-rgb/telegram-services-platform.
Initial import tree: 32fff1f90ef325949a88832d1150ac01ef051363; 127 tracked files.
The recursive remote tree and file modes matched the local prepared source exactly.

## Hosted evidence

[Initial run](https://github.com/n923760-rgb/telegram-services-platform/actions/runs/37206089325)
and job 111447454192 demonstrate 83 tests passed with one ARQ/Redis dependency warning,
plus successful dependency installation, lint, formatting, migrations and Alembic drift.
The final Compose check failed with: env file .env not found.
This is an attributable hosted result, not the earlier local test summary.

## Cause and correction

Compose services declare env_file: .env. The CLI --env-file .env.example supplies variable
interpolation but does not replace those declared service files. A fresh checkout deliberately
has no private .env. Copy the non-secret example to .env inside the isolated CI runner before
the existing config validation. Never upload real credentials or customer data for this check.
This changes only CI setup and the corresponding engineering records.

## Verification

PASS: Reproduced missing .env failure with checksum-verified official Compose v5.6.0.
PASS: The same isolated checkout validates after copying the example to its service .env.
PASS: Ruff lint/format, complete diff check, documentation links and AGENTS.md length.
The PR workflow provides the exact-source hosted validation; inspect its actual result.
No container image build, deployed stack or authenticated Telegram/AI journey is implied.

## Review boundary

The source upload is complete on main. Submit this single confirmed CI issue as one branch/PR.
Do not merge implicitly: root AGENTS.md requires explicit owner authorization for merge.
