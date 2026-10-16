# Explicit provider completion contract

Baseline: official main 4b4c817702292bcf66432b19d0f229ed6357602d.
Authority: owner asks to resolve provider-usage friction and continue general service development. PR #89 is a separate review-only input validation task and is not merged or modified here.

## Evidence and interpretation

FACT: Current official DeepSeek thinking guide states thinking is enabled by default at high effort. The current Chat Completions reference documents thinking.type enabled/disabled, max_tokens and optional completion reasoning counts; finish_reason length can indicate a cut-off JSON answer. References retrieved 2026-10-17:
- https://api-docs.deepseek.com/guides/thinking_mode/
- https://api-docs.deepseek.com/api/create-chat-completion/
- https://api-docs.deepseek.com/guides/vision/

FACT: The previous adapter sent max_tokens for the official host but omitted thinking; temperature=0 does not disable thinking. Older reviewed live output had long generations and one invalid JSON review repaired. Latest operator CV v7 AR/EN passed and bilingual failed provider_usage, but the new archive is unavailable here.

INFERENCE: Implicit high-effort thinking can consume output budget unnecessarily for these bounded JSON tasks. It is not a proven explanation of historical cap overruns or the latest bilingual failure. No permanent vendor reliability promise is possible from source tests. No invoice or old-hold correction is attempted.

## Change

Explicit non-thinking default for the exact official DeepSeek host and the two documented Flash/Pro model IDs. Operator may select enabled via a validated literal setting, with ignored temperature omitted in that mode. Other endpoints/models and token-limit selection retain their request contract. No SDK/vendor dependencies in plugins.

Completion audit stores only fixed finish-reason labels, validated reasoning count/state and requested mode. No raw content or reasoning text, no subtraction from completion totals, no cache repricing and no historical record mutation. Preflight shows requested mode.

A length-terminated result is incomplete even if its JSON parses. The gateway settles its full usage then uses only the existing schema-repair allowance; exhausted repair fails safely as provider_invalid. True token or monetary overruns retain provider_usage/full settlement/pause. Unknown exposure remains held. No additional loop, cap increase or automatic unpause.

## Validation

PASS LOCALLY: 88 focused completion/audit/review/acceptance tests, lint/format/diff. The first combined command also selected legacy provider contract tests inheriting the shared database fixture: 26 setup errors because local PostgreSQL is absent, not product assertion failures. The pure subset was rerun cleanly. Legacy adapter and new DB accounting cases require the full hosted workflow before merge.

New DB cases verify two billed calls for truncation/recovery, no global pause for ordinary truncation, exact summed spend and retained old uncertain hold. Existing real cap-breach tests remain unchanged. Existing bounded quality-review regressions pass locally. New live calls, customer/mobile quality, invoice verification and production deployment NOT RUN.

## Next operational evidence

After source qualification, build worker and verify exact host/model/thinking mode without printing secrets. Run the existing isolated synthetic CV matrix first, preserve ZIP/report and inspect usage completion metadata. Keep production paused until new runtime/output acceptance supports a deliberate resume. General direct-service and source development can continue independently; historical reconciliation is not a gate for isolated testing.
