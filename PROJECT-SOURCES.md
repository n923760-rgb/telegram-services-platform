# Project sources

Use this resource map for navigation. Reverify live Git state before work.

| Resource | Location / status |
| --- | --- |
| Project | Telegram Services Bot; Arabic-first Saudi platform |
| Canonical source | origin/main after initial import; verify remote HEAD before subsequent work |
| Remote project repository | https://github.com/n923760-rgb/telegram-services-platform; origin configured |
| Official remote branch | main; verify live HEAD through GitHub before further mutations |
| Working branches | Use bounded task branches/worktrees; do not infer the current branch from historical reports |
| Authority | AGENTS.md |
| Reference and adaptations | docs/GOVERNANCE.md |
| Single roadmap | ENGINEERING/MASTER_ROADMAP.md |
| Baseline | ENGINEERING/REPORTS/2026-10-04-governance-baseline.md |
| Evidence index | ENGINEERING/EVIDENCE/README.md |
| Setup and service-extension contract | README.md and README_AR.md |
| Operations and restore | docs/OPERATIONS.md |
| Validation and environment limits | docs/VALIDATION.md |
| Real staging acceptance | docs/TELEGRAM_ACCEPTANCE.md; live Telegram/provider execution pending |
| CI definition | .github/workflows/verify.yml; attributable hosted results in ENGINEERING/EVIDENCE/README.md |
| Runtime definitions | docker-compose.yml and compose.test.yml |
| Private configuration | scripts/configure.py and .env.example; real .env stays untracked |
| Dependencies | uv.lock and requirements.lock |
| Schema evolution | migrations/versions; Alembic head at adoption is 0010 |
| Extension points | app/services/base.py, registry.py, app/providers and app/builders |

Keep credentials, temporary IPs, PIDs, leases and customer content out of this map.
Keep dated source evidence in reports; never present a historical SHA as the current HEAD.
