# Translation email and URL fidelity

Baseline: official main 94147fae35173704bdc067bfa19718c26abe1b30. Owner authorizes continuing development and merging; production deployment is deferred. Unrelated governance PR #21 is untouched.

## Reproduced gap and bounded change

FACT: Executing the baseline independent text-translation schema against source@example.invalid and translated changed@example.invalid succeeds. The prompt already requests exact email/link preservation, but numeric-only checks do not enforce that requirement.

Translation v2 now compares exact occurrence counters for the existing text-editing email/HTTP(S)/www URL matcher independently for every nonempty source line. This rejects changed, omitted, invented, duplicated or cross-line moved contacts, even with no numbers present. Source values remain captured in request-local validation closures, not embedded in JSON Schema or new diagnostic messages. The segment schema describes the requirement to the provider; the existing prompt already states it.

No new output, input choice, AI call, review step, retry allowance, dependency or migration. The existing single repair handles invalid output; persistent failure follows existing failure/release behavior. The stricter result contract increments the plugin from v1 to v2. Existing version guards cancel/release unprepared v1 work while replaying historical prepared translation.txt without regeneration. Administrator-owned prices/activation remain untouched. The separate OCR translation helper and all other services are unchanged.

## Checks

PASS LOCALLY: 78 focused pure contract and injected-service tests, including existing translation/editing regressions; three architecture gates; global Ruff lint/format and diff checks. Baseline changed-email acceptance was reproduced directly from git source. New pure tests cover both target languages, repeated contacts, reordered response IDs, blank-line/CRLF retention, mixed-case/plus-addresses, URL paths/queries/fragments and Arabic paths, exact case, changed scheme/path/query, missing/invented/duplicate/moved tokens, schema privacy and request isolation.

Added hosted integration tests cover Arabic/English direct valid output and successful one-repair output, one capture across duplicate execution, calculated provider cost, persistent email/HTTP(S)/www changes exhausting exactly one repair then releasing all reserved credit without files, and v1 upgrade behavior for prepared/unprepared work with administrator prices preserved. PostgreSQL/Redis and native worker qualification are NOT RUN locally; require the exact-head complete hosted workflow before merge.

Initial hosted run [39040459248](https://github.com/n923760-rgb/telegram-services-platform/actions/runs/39040459248) failed: 2072 passed, nine new integration cases rejected at admission because their fixtures omitted required style. The new fixtures now supply formal explicitly, matching Telegram intake; production validation remains unchanged. Full hosted qualification must run again on the corrected head.

## Limits

Token equality is a structural safeguard, not a claim about translated meaning, names or style. The reused matcher recognizes email addresses and HTTP(S)/www URLs rather than every contact notation; bare domains and other URI schemes are outside this change. It is conservative about adjacent URL punctuation and preserves its original bytes/case; legitimate punctuation relocation can require the existing repair or fail safely. No matcher redesign or semantic certification is claimed. Prepared historical translations are reused as previously approved, not retroactively regenerated or revalidated. Live provider/Telegram tests and production deployment are NOT RUN.
