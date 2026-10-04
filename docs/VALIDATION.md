# Validation record

All four implementation phases and their revised specification completed on 2026-10-04 with Python 3.12.14,
PostgreSQL 16.15 and Redis 7.0.15. Each phase used an isolated migrated database.

| Check | Result |
| --- | --- |
| Original phase 1 / 2 / 3 / 4 tests | 13 / 20 / 28 / 48 passed |
| Revised phase 1 tests | 51 passed |
| Revised phase 2 tests | 58 passed |
| Revised phase 3 tests | 72 passed |
| Revised phase 4 final suite | 83 passed |
| Real Redis/ARQ queue fulfillment | Passed with fake Telegram delivery |
| Concurrent reservations and cost holds | Passed against PostgreSQL |
| Ledger mutation rejection and idempotent refund | Passed |
| OCR/translation, Word/Excel, ambiguity and failure release | Passed with mocked AI |
| Long OCR TXT/DOCX and input/result deletion | Passed |
| Alembic head → base → head | Passed on disposable DB |
| Alembic metadata drift | No new operations |
| Live uvicorn HTTP /health | 200, DB/Redis ready |
| PostgreSQL custom-format dump → replacement DB restore | Passed; revision 0010 and all 3 test ledger rows restored |
| Ruff lint / format | Passed; all Python files formatted |
| Dependency lock consistency | Passed (uv lock --check) |
| Python compilation and shell script syntax | Passed |
| Word/Excel/PowerPoint/PDF builder reopening | Passed |
| Arabic PDF visual render inspection | Passed |
| Versioned plugin contracts and generic optional/nested intake | Passed |
| Cached result recovery after aborted settlement | Passed; no repeated AI call |
| Unknown provider exposure and daily reports | Passed |
| Terminal file deletion recovery and storage abstraction | Passed |
| Webhook secret, bounded body and real aiogram dispatch | Passed with mocked transport |
| Private first-run .env and overwrite rejection | Passed |
| Governance boundaries and AGENTS.md length | Passed |
| Compose and GitHub workflow YAML syntax | Passed; workflow authored, no hosted CI run |

The ARQ queue test emits one dependency deprecation warning: ARQ calls Redis `close`
instead of `aclose`. It does not affect the test result.

No real Telegram token or AI credentials were supplied. Tests use fake Telegram requests,
mock HTTP/provider responses, and returned usage fixtures. They do not establish OCR accuracy,
provider invoice accuracy, or delivery behavior on a real account. Docker was unavailable;
Compose image build and VPS deployment still require verification. Native Office applications
were not used for visual rendering. No paid-launch approval is implied: SAR is test credit,
while Telegram requires Stars for digital-service sales.
