# Provider output token contract

Owner-reported runtime: main f352c27, PDF-to-Word v4, DeepSeek official API,
deepseek-flash, configured output cap 8192. Failed order had one uncertain cost
hold and one settled call with 15532 completion tokens and cost above its bound.
Wallet reserve/release matched; provider pause was true. No response body or
customer content was retrieved, so the first call's cause/bill remains unknown.

The adapter sent max_completion_tokens. DeepSeek's current official contract uses
max_tokens and defaults to thinking mode with a larger cap when max_tokens is
omitted. This is a confirmed wire-contract defect; the observed overrun is
consistent with the effective cap being absent, not proof of the first call's cause.

Official primary reference reviewed 2026-10-13:
https://api-docs.deepseek.com/api/create-chat-completion/

## Fix and compatibility

Validated AI_TOKEN_LIMIT_PARAMETER supports auto/max_tokens/max_completion_tokens.
Auto selects max_tokens only for exact api.deepseek.com; other hosts retain the
existing parameter. Custom proxies may select explicitly. All text/image/translation
requests send exactly one cap equal to the bound's configured output cap. No model,
thinking/effort, timeout, token count or price changes. Reasoning usage is not
subtracted or clamped. Existing settlement records excess usage and pauses calls.

No service contract/version, migration/dependency, ledger or settlement changes.
Existing installations need no secret edit for the official DeepSeek endpoint.
No automatic resume or unknown-hold release; require deployed request verification,
provider billing reconciliation and operator-controlled recovery before retry.

## Verification and limits

29 local adapter/config/architecture cases PASS, including all call types, host
matching and explicit overrides. Added hosted integration cases for bounded and
excess usage through the actual adapter/gateway, pause protection and preservation
of previously uncertain exposure. Full PostgreSQL/Redis/native CI required before
merge. No live provider call, deployment, unpause or reconciliation performed here.
Documented request correctness does not guarantee a vendor honors a cap; actual
provider acceptance remains a separate, accounted operating check.
