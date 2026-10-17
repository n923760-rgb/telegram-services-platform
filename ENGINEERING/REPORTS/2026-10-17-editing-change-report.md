# Editing comparison reports

Baseline: official main a898e82932d2b1c1e6b64a846ae4f349d1139aaf. Owner authorizes continued development and reviewed merges; explicitly defers production deployment until service development/improvement is complete. Unrelated governance PR #21 remains untouched.

## Customer behavior

Text editing v2 returns the same clean edited chat text and revision.txt, with an additional changes.txt. The report lists only changed physical lines in its comparison section, with exact before/after text and line numbers counting blank lines. A full original appendix gives context for unchanged records and numeric/contact references. It explicitly says when no literal changes occurred. CRLF/CR line endings normalize to LF, consistent with existing intake/render behavior. Labels follow the source text's existing RTL classification (AR or EN), independently of the bot UI language.

The comparison is deterministic: no AI request, schema change, review loop or inferred correction taxonomy is introduced. It is a literal comparison, not proof of semantic/grammar/style accuracy, a word-level diff or a Word tracked-changes document. The edited text stays separate and ready to copy; comparison labels never enter it. The report contains customer source text and is handled as a private customer artifact under existing ownership/retention rules, not operational logs.

## Bounds and failures

Existing source <=12000 characters/80 nonempty lines and edited <=24000 characters remain. The builder rejects mismatched line counts and bounds the comparison at 64000 characters without truncation; maximum-size Arabic fixtures preserve every changed line and the full original. Only current accepted output is compared; no stale model drafts are exposed.

If the second save fails, first-file deletion is attempted and the original storage failure is retained. If immediate deletion also fails, existing unreferenced-file TTL expiry applies; no claim of transactional storage/crash-window guarantees. Successful/prepared results use normal durable delivery and terminal artifact cleanup. No service-specific core branching or ledger/retention policy change.

## Qualification and version behavior

PASS LOCALLY: 84 focused pure comparison, injected service, existing source/fidelity, AI policy and architecture tests. Global Ruff lint/format and diff checks pass. Cases include AR/EN, no changes, physical blank-line numbering, CRLF normalization, complete long lines, exact original context and source tokens, size/alignment rejection, one AI generation call, storage rollback and TTL fallback.

Hosted full CI is required for new/extended DB flows: two-file completion with one capture and unchanged provider costs, delivery retry without regeneration, first/second save failures releasing credit and clearing partial output, and v1 upgrades. Existing queued v1 work cancels/releases under normal version rules; a prepared historical revision.txt-only result replays as one file without generating a new comparison. Administrator credit/Stars prices and activation are retained. New prepared v2 results replay both files.

No input choices, prices/gates, provider caps/retries, dependencies, migrations or production changes. The full existing native worker qualification remains required. NOT RUN: live provider meaning/style acceptance, live Telegram delivery/mobile TXT readability or production deployment. Deployment is deliberately deferred, not blocked on permission.
