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

## Historical documentation verification — 2026-10-04

PASS on 2026-10-04 for this documentation-only round:

- pytest tests/test_governance.py -q: 3 passed against a disposable migrated PostgreSQL/Redis setup.
- ruff check . and ruff format --check .: passed.
- git diff --check: passed.
- Local documentation links, a single roadmap, all baseline A-W sections and AGENTS.md length: passed.

Application source, migrations, dependency locks and workflow were unchanged from the retained
83-test implementation snapshot. The full application suite was not redundantly rerun.
Hosted CI, Docker and authenticated Telegram/provider checks remain NOT RUN/BLOCKED as above.

## Continuation qualification — 2026-10-07

| Source | Attributable check | Result and limits |
| --- | --- | --- |
| UX head f498413898bf6628b31b26eeb7525556f19c4b26 | [workflow 37575252712](https://github.com/n923760-rgb/telegram-services-platform/actions/runs/37575252712) | PASS: 152 tests, lint/format, migrations/drift and Compose configuration; real Telegram/provider NOT RUN |
| UX merge a8f70f7eb58d457dfefb4e378c5085e6fc9d3092 | [main workflow 37575645208](https://github.com/n923760-rgb/telegram-services-platform/actions/runs/37575645208) | PASS: post-merge hosted workflow |
| PDF-to-Word head a0cce87ee0326efa55ad1c3e8d0a28a0263db032 | [workflow 37576254914](https://github.com/n923760-rgb/telegram-services-platform/actions/runs/37576254914) | PASS: 171 tests, lint/format, migrations/drift and Compose configuration; 19 focused service/settlement cases |
| PDF-to-Word local source equivalent to reviewed head | ../REPORTS/2026-10-07-pdf-to-word-review.md | PASS: locked install, lint/format/diff, collection and isolated actual PDF/DOCX smoke; no local PostgreSQL execution |

PR #7 merged at a8f70f7; PR #5 merged at a3aaf573238a497659bfa3137073185bf10b7340.
Inspect current main's workflow separately; branch-head evidence must not be treated as an
uninspected post-merge result. Production deployment and authenticated Telegram/provider
journeys remain NOT RUN here. Runtime qualification follows docs/TELEGRAM_ACCEPTANCE.md.
