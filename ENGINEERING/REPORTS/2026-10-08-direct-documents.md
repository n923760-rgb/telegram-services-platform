# Direct Word/PDF execution qualification

## Source and scope

- FACT: Clean baseline main faab75a4707670c325734c371d1a035d810e777b verified against
  GitHub main on 2026-10-08; no open PRs at inspection. Task branch: feat/direct-word-pdf.
- Owner-approved scope: keep the project lean and add direct Word/PDF conversion while
  preserving existing AI organization. Existing authorization permits publication and merging
  after verification; production changes remain a separate operator procedure.
- No dependency, lockfile, migration, new service, agent, n8n, dashboard or payment change.
  No unused module/dependency deletion was justified. Keep recovery/security/tests intact.

## Implementation

- Word and PDF plugin version 2 require an explicit Telegram mode. Direct mode adds a
  customer title and preserves body content without invoking a model or interpreting instructions.
- A shared bounded document-input model validates modes, titles and XML-safe text, normalizes
  CRLF/CR to LF, and preserves body whitespace. Direct content is split into bounded sections
  without classifying headings or modifying words. At most 12000 input characters and 10000 lines.
- Generic BaseService.needs_ai(inputs) separates mixed request admission/runtime from the
  unconditional requires_ai admin gate. AI-only plugins retain the old defaults. Smart Word/PDF
  and Excel still require enabled/unpaused AI before reservation; approved continuations reuse
  their validated plans without constructing a provider. Direct services remain disabled by default.
- Existing service prices/admin overrides, general cost-admission checks, immutable ledger,
  reserve/deliver/capture/release, storage ownership, retention and cached retries are unchanged.
- Telegram intake no longer strips customer body whitespace; blank and oversized values still fail.
- Shared Word builder uses leading-edge OpenXML justification for RTL/LTR interoperability,
  removes inherited Title borders and uses restrained dark titles. PDF preserves blank lines
  and drops terminal spacers that could create an extra empty page.
  PDF display whitespace still normalizes/reflows; this is not original-layout reconstruction.
- A schema/version change requires restarting old drafts. Unprepared incompatible jobs release
  credit through existing cancellation; prepared results retain cached-delivery recovery.

## Verification

- PASS: uv run ruff check .; uv run ruff format --check .; git diff --check.
- PASS: uv run pytest app/services -q: 37 tests using mocked AI, real builders and storage.
- PASS: Full-suite collection: 240 tests (37 new). Collection is not execution.
- PASS: Direct invocation of 6 pure builder and 3 architecture checks; not DB pytest evidence.
- PASS: Representative synthetic Arabic/English Word/PDF generated with actual builders,
  DOCX reopened and rendered through the skill's LibreOffice renderer; PDF rendered with Poppler.
  Initial rendering revealed inherited Word title border and RTL alignment issues; builder
  fixes were re-rendered and visually inspected. Single-page fixtures and all pages of a
  two-page DOCX and two-page PDF were inspected. An initial extra blank PDF page was fixed
  and regression-tested. Word/LibreOffice differences are not a substitute for real client testing.
- NOT RUN locally: Full DB/Redis integration execution and Alembic drift; these services/Docker
  are unavailable in this workspace. Hosted CI must supply those checks before merge.
- NOT RUN: New direct-mode deployment and authenticated Telegram acceptance; no server access.
- Coverage added: no provider construction/API usage, zero CostHold/CostUsage records,
  exact-once settlement, safe validation before reserve, release on rendering/delivery failure,
  cached delivery retry, schema version upgrade and Arabic/English dispatcher intake.

## Prior operator evidence and remaining limits

Operator-reported baseline deployment: Compose build succeeded, migrations exited 0, API/bot/worker
were healthy and /health returned HTTP 200. Telegram screenshots showed exact echo delivery,
completed history/navigation and zero held customer credit. Those observations are separate from
this task's tests and do not establish direct-mode production execution or Office output quality.
Real AI content accuracy, provider invoices, restore/off-server backups and paid launch remain
unqualified. SAR remains administrator-issued test credit.
