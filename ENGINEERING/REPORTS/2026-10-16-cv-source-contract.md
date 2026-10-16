# Request-specific CV output contract

## Authority and evidence

- OWNER AUTHORITY: Continue the existing CV quality and all-service acceptance work. Source baseline main 677f24dd788224b5ef1c2696be6fdd6bf45715ea verified clean and current before mutation.
- FACT: Operator rerun of cv_en failed after two provider calls, both stage=generation/outcome=invalid/categories=constraint. No content review occurred. Test active orders and reserved test credit both returned to zero; production provider remained paused. Calculated usage SAR .029236 is not an invoice.
- UNKNOWN: The old category does not identify the failing custom validator. No raw candidate is available, so do not claim a particular name, number, summary or presentation defect caused the actual response rejection.
- FACT: The previous provider JSON schema used general section/source-ID/body/summary fields; request-specific exact sets/counts and conditional summary requirements existed primarily in post-response validators. A rejected creation receives a generic repair instruction. The schema can expose more of the existing contract without relaxing fidelity or adding calls.

## Bounded change

CV v6 generates per-request segment IDs, body languages/counts, section names/counts,
and eligible summary-reference enums. The generated profile is required when no
summary was supplied; only null is accepted when the supplied summary is already
covered by source segments. Summary-reference and section uniqueness are advertised
in JSON schema and remain independently checked by the existing validators.

Existing root validators retain their checks and messages but use fixed custom
error codes. The isolated acceptance observer can expose author-declared static
category labels. It copies no raw messages, validation locations, context, source
values or custom error strings. Built-in diagnostic labels cannot be overridden;
unregistered/malformed metadata remains generic. No service branch in core policy.

No gateway repair-budget/count change, raw candidate persistence, additional model
call, provider-cap increase, financial reconciliation, price, activation, intake,
renderer, dependency, migration or production-pause change. This is a generation
contract/diagnostic improvement, not a new visual design or a proven live CV fix.

## Qualification and next step

Focused tests verify JSON enums/cardinality/summary requirements, per-request
schema isolation, fixed fidelity errors, forged-output revalidation, static-category
redaction and the existing creation/review limits. Existing CV input/profile and
source-fidelity regressions remain required, followed by the full hosted financial,
lifecycle, native-rendering and migration workflow before merge.

PASS LOCALLY: 69 focused pure contract/acceptance/review/architecture tests and 56 existing
CV source/input/profile regressions; lint/format/diff and Bash syntax. Full hosted qualification
pending at commit. No real-provider call or production deployment performed here.

After qualification, build the worker image and run only cv_en through the isolated
wrapper. Merely pulling source does not update the installed CV code inside the
existing worker image. Image build is not production container replacement; keep
production paused and inspect the new report/artifacts before making readiness claims.
