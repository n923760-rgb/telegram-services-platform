# Independent text translation — 2026-10-10

## Authority and baseline

Owner asks for additional useful services, specifically independent text translation.
Read current governance/roadmap/registry, existing OCR translation/provider contracts
and financial lifecycle tests. Main 99f4b6f is canonical; workflow 38066931365 passed
708 tests and every native worker gate. Existing continuing publication/merge authority
remains conditional on attributable hosted checks. No production enablement is inferred.

## Implementation

Registry-discovered `text_translation`, disabled by default, SAR 3.00 test credit;
no default Stars price. Text input plus AR/EN target and existing four style choices.
12000 characters, 80 nonempty lines; output at most 24000 characters. Source IDs
identify every nonempty line; strict integer IDs exactly once, per-line numeric-token
multisets and printable single-line outputs validated in a request-local schema.
Source order and blank lines assembled deterministically; text and owner-bound TXT.

AI sees structured source data and explicit translation instructions, through existing
job-bound injection/cost reservation/one-repair flow. Numeric rules shared with OCR via
app/services/translation.py; OCR's prior imports and model/schema contract retained.
No vendor SDK/Telegram imports in plugins, bot/core lists, financial policy, migrations,
dependency change, automatic service enablement or user/provider secret changes.

## Evidence

- PASS LOCAL: 49 database-independent unit/source-number/architecture checks. Invalid
  IDs/omitted/duplicate lines, per-line numbers, output/input bounds, control characters,
  blank lines, request isolation, injected AI/owned UTF-8 and absent-provider failure.
- Full suite collects 740 tests (708 baseline + 24 service cases + 8 lifecycle cases).
  New PostgreSQL cases cover AR/EN delivery/capture, one repair/failure release,
  cached delivery without another provider call, storage failure and admission gates.
- Exact published tree and final hosted results must be retained on the PR. Existing
  full financial/concurrency, migration/drift, Compose and native worker gates remain.
- NOT RUN LOCAL: Full PostgreSQL/Redis/container suite; unavailable here.
- NOT RUN: Real Telegram purchase, actual provider semantics/style/names/links,
  server deployment/native customer qualification and commercial prices.

## Honest value boundary

Line coverage and numeric preservation do not prove every word's meaning is translated
correctly. Names/emails/links are required by the prompt, not deterministic semantic
verification. This is ordinary pasted-text AR/EN translation; uploaded documents, OCR,
additional languages, certified/legal/medical translation and original-layout export
are separate contracts. OCR translation remains an independent existing capability.

The portfolio lists proposed writing/proofreading, summaries/revision, evidence-bound
CV writing and business packs distinctly from implemented source capabilities.
