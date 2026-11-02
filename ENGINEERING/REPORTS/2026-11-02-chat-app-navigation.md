# Chat and Mini App navigation consolidation

## Baseline and scope

- FACT: verified remote main `a46fc6fe5bf379f212ff837d6ef72a9d6ff8fd6e`;
  no open PRs returned by repository-scoped search before implementation.
- Owner requests sequential service qualification and coordinated chat/app navigation.
- FACT: the supplied source-bound acceptance archive reports 11 passing native cases
  across nine services, zero provider calls, no active orders or reserved credit.
  Verified all 12 packaged artifact SHA-256 values against that report.
- This native run does not qualify all modes or professional semantic/mobile quality.

## Navigation change

When configured Mini App intake is enabled, `/start`, `/menu` and Home send one
welcome message, remove the previous persistent reply keyboard and attach an
authenticated inline Open app button to that same message. Support and Help remain;
saved bot drafts have Resume and administrators retain their authorized panel entry.
Shared keyboard resets also remove old controls instead of restoring duplicates.

Old category/service callbacks route to the app, without querying the legacy catalog
or replacing an existing draft. Explicit request links, follow-up journeys and Resume
retain their existing contracts. With intake disabled or URL missing, legacy chat
navigation remains available. Arabic/English Help now describes the app entry and
order history accurately. Payment policy and settings are unchanged.

Telegram needs two API calls for a single visible message: send the welcome with
ReplyKeyboardRemove, then edit its inline markup. If the second call fails, the welcome
still gives accurate instructions; retry `/start` or use the configured bot menu.
No exactly-once Telegram delivery claim is made.

## Sequential service qualification

Use the current registered acceptance cases and their manual review checks. Finish
one service's automated cases, actual provider run where required, source/output review
and Telegram/mobile journey before declaring that service qualified.

1. Text editing: `editing_proofread`, `editing_rewrite`. Check grammar/register,
   negation, numbers, contacts, deadlines and both revision/change-report files.
2. Summary: `summary`; preserve decisions, pending actions and uncertainty.
3. Translation: `translation_ar`, `translation_en`; preserve direction and facts.
4. Document image enhancement, then OCR English/mixed.
5. Word/Excel, PDF creation, Word/PDF, then PowerPoint; render every page/slide.
6. Images/PDF, PDF/Word and PDF tools; compare source fidelity and page order.
7. CSV and PDF tables; verify source values and native Excel opening.
8. CV, meeting minutes, interactive cards and QR; verify each mode and mobile result.

The uploaded run leaves 13 of 18 listed services NOT_RUN or INCOMPLETE. Even the five
automatically passing services still have manual review NOT_RECORDED. Do not convert
partial native success into launch readiness.

## Validation

- PASS: 145 selected local tests using `--noconftest`: real router transport tests,
  bot information and Mini App entry tests, three architecture gates and text
  editing/translation/summary service tests. No DB fixture was used in this selection.
- PASS: whole-repository ruff lint/format and git diff whitespace check.
- NOT RUN locally: PostgreSQL integration journeys, migration checks and full suite;
  PostgreSQL/Redis/Docker executables are unavailable in this workspace. An initial
  DB-fixture invocation failed for missing disposable DB, not a successful DB test.
- NOT RUN: real Telegram/client compatibility, actual provider execution and production
  deployment. Local text-provider tests use injected mocks, not live quality evidence.
- Hosted CI must verify this branch before merging; deployment requires server evidence.
