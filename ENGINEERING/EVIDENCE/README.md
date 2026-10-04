# Evidence index

Keep evidence sanitized and attributable to the source actually checked.
Never retain customer content, tokens, private .env files or raw provider responses.

| Source / round | Retained evidence | Limits |
| --- | --- | --- |
| Revised application snapshot retained in commit a54876dc7580f0a13ec82bd53d21872db0c720b5 | docs/VALIDATION.md: 83 tests, real PostgreSQL/Redis, migrations/drift, restore, HTTP readiness, lint/format | Application changes were tested before that commit; docs changes do not establish Docker or external-service evidence |
| Governance reference | docs/GOVERNANCE.md pins 641e4f9e45da109257ba1f38752b94604c2e4531 | Reference SHA, not bot source SHA |
| Read-only adoption baseline | ../REPORTS/2026-10-04-governance-baseline.md | Remote identity UNKNOWN; hosted PR/CI NOT RUN |
| Initial remote import e055d2b98d6aaaed5111f25203c34ba7d3e4caaa | GitHub Actions run 37206089325: 83 passed, 1 dependency warning; lint/format/migrations/drift passed | Workflow overall failed only at Compose validation due to missing .env; see the CI correction report |

For later rounds record task ID, source, commands, outcomes, affected files and sanitized
artifacts. Historical summaries do not imply raw logs were retained.
Record archive SHA-256 alongside the delivered archive, never self-referentially inside it.

## Documentation verification

PASS on 2026-10-04 for this documentation-only round:

- pytest tests/test_governance.py -q: 3 passed against a disposable migrated PostgreSQL/Redis setup.
- ruff check . and ruff format --check .: passed.
- git diff --check: passed.
- Local documentation links, a single roadmap, all baseline A-W sections and AGENTS.md length: passed.

Application source, migrations, dependency locks and workflow were unchanged from the retained
83-test implementation snapshot. The full application suite was not redundantly rerun.
Hosted CI, Docker and authenticated Telegram/provider checks remain NOT RUN/BLOCKED as above.
