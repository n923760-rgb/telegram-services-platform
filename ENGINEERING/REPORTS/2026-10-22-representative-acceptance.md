# Representative service acceptance

Baseline: official main 4a53cebdbe3ca0a00e46e70a161a96f3ce755c01.
Authority: owner requests continued service quality work and merging ready changes.

## Evidence and scope

- FACT: Operator reports successful 4a53ceb deployment and backup `/home/aidev/telegram-release-79wQ6kTI`. Server commands are operator evidence, not execution from this workspace.
- FACT: The latest uploaded ZIP contains one PPTX and its report. Its 31,731-byte native PPTX matches reported SHA256 `20187271523637bf65ca4807d09f04e911acdae56318f14e22423fe59ace7f3f`. All three slides were rendered through the available secondary office converter and visually inspected. English source stays English; native editable text/table cells preserve 00123, 125.50 SAR and the unapproved payment meaning. Report: two calls, calculated usage 0.004676 SAR, not invoice verification. No Microsoft Office/mobile session was inspected.
- FACT: Earlier 29-case results used already-correct editing text, an English-to-English translation case and very short document/summary sources. Those passes could not demonstrate correction, cross-language translation or pagination.

## Changes

Keep 29 cases across the same 16 services. Strengthen existing inputs rather than add live jobs:

| Case | New evidence sought |
| --- | --- |
| editing_proofread | Correct several actual English grammar errors without reversing payment meaning |
| editing_rewrite | Rewrite colloquial Arabic formally, preserving the prohibition and deadline |
| translation_ar | English source to Arabic, exact original identifiers and amount |
| translation_en | Arabic source to English, unapproved versus rejected and proposed versus promised |
| summary | Compress twelve paragraphs to at most three grounded points while preserving decisions/actions |
| word_pdf_direct | Longer bilingual plain paragraphs; all twelve section markers in both native Word and multi-page PDF |

For the four known-change text fixtures only, inspect the actual revision/translation file and reject equality with source after whitespace normalization. A source echo with a positive scripted review must still fail delivery qualification and release synthetic credit. Correct production text is never forced to change. Other artifacts and unrelated cases retain their previous rules. Fixed per-case manual review criteria are included in report.json, without copying source or model prompts into console diagnostics.

The long direct fixture exercises plain source paragraphs rather than inferred semantic headings. Arbitrary section-heading interpretation, bilingual CV pagination, dense slide tables, actual Office/mobile edit/reopen and realistic non-synthetic data remain separate qualifications.

## Validation

- PASS: 83 focused acceptance unit/wrapper/output/integrity checks, including twelve new unit cases for echo rejection, whitespace-only output, actual correction, retained source identifier, unchanged valid data, long editable Word preservation and bounded plan coverage.
- PASS: Three architecture gates run directly without the unrelated autouse database fixture; global ruff check/format and git diff checks.
- PASS: Real native long-source Word/PDF export using the existing production renderer with an explicitly selected available office binary. The operator's image/runtime remains separately qualified.
- ADDED: Two PostgreSQL scenarios, native long-source acceptance without provider calls and rejected echo through the full scripted provider/review/order/delivery path. NOT RUN locally: PostgreSQL unavailable. Require exact-head hosted full tests, migrations and existing non-root worker qualification before merging.
- NOT RUN: Six strengthened cases against the real provider. Existing worker image 4a53ceb suffices because only the two already-mounted operational files change. No deployment needed for this isolated run.

## Limits and operation

No new provider calls/jobs by default count, retry allowance, dependency, service version, financial policy, price, gate, provider pause, database schema or production container change. Keep the existing cumulative conservative SAR 5 bound, 96-call cap and per-job guards; larger sources can consume more budget. Passing the changed-text guard is only a minimum anti-echo check, not semantic or stylistic certification.

After merge use the targeted command in docs/OPERATIONS.md from clean main with the current qualified worker image. Preserve production pause and failed-run evidence. Inspect every returned file, not just the PASS count, before claiming live readiness.
