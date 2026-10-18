# Optional meeting-minute titles — 2026-10-18

## Baseline and scope

FACT: Official main 8b0b451057f694009ca010787cac885c2acc61e9 includes #101.
Owner authorizes continued development/qualification/merge, with one production deployment
after improvements. This round addresses only the mandatory title in meeting minutes.

## Contract

CHANGE: MeetingMinutes v4 exposes required=False on the existing title field. Generic
intake supplies Skip; missing or explicit null uses minutes_default_title in the document
language: محضر اجتماع / Meeting minutes. One resolved title is used for full approval
review in both UI languages and native document creation, including continuation.
Supplied nonempty one-line titles retain existing 200-character and printable-text rules.
Blank, multiline, control, oversize and non-string titles are not silently defaulted.
No meeting name/date is inferred, no title is sent for AI classification, no AI call is added.

SAFETY: Notes, source IDs, category/owner/deadline validation, mandatory review, Word/PDF
pair, price and activation overrides, repair/cost limits, dependencies and ledger unchanged.
Version guards preserve prepared historical output and cancel/release unprepared older work.

## Verification

PASS LOCALLY: 65 focused title, source/action and injected-service tests; three architecture
gates, Ruff lint/format, diff whitespace, workflow YAML and embedded worker Python syntax.
The initial local run exposed incorrect test expectations for default serialized task fields
and the generic skip key; fixtures/assertions were corrected before publication.
NOT RUN LOCALLY: one existing real LibreOffice continuation/export test (binary unavailable).
The full hosted suite runs this test plus PostgreSQL/Redis order/financial/dispatcher tests.

Added/extended hosted tests cover omitted/null/custom titles in both languages, actual title
skip after multiline rejection, exact saved source, one provider call and capture after approval,
cached v3 replay without regeneration, and v3 cancellation/release with admin prices preserved.
Native non-root network-disabled worker qualification additionally renders untitled AR/EN
minutes, reads the localized Word title and verifies exact source numbers in the PDF.
Full exact-head hosted workflow must pass before merge; local checks are not deployment evidence.

LIMITS: Skip creates a neutral visible title, not source-based generation or a hidden title.
Real-provider/Telegram visual acceptance and production deployment NOT RUN.
