# PowerPoint source restriction retention

## Observed failure

Operator run service-acceptance-uE2Bk94W on 5107626 completed with two provider calls and calculated usage 0.009441 SAR. All cost holds settled. Reopened native slide content retained inventory 40/12/28 but omitted the source sentence saying the committee did not approve reservation or delivery. The automatic quality reviewer accepted the omission. Content completeness therefore remains REVIEW REQUIRED.

## Bounded contract

PowerPoint v8 selects nonnumeric sentences containing explicitly enumerated Arabic/English restriction markers within blank-line-delimited paragraphs containing numeric tokens. Require the selected sentence words in visible titles/bullets/table content, allowing punctuation, whitespace and direction marks to differ. Clarification questions cannot substitute for slide content. Apply the same check after provider output and on continuations. Include the selected source quotes in generation instructions; retain one repair and semantic review. A prose slide may replace a table for a topic whose restriction would otherwise be lost. No renderer/schema change to shared slide objects, pricing, provider limits or generic orchestration.

This is deliberately a narrow literal guard, not comprehensive semantic coverage. It does not infer relationships, enforce same-slide association, recognize every negation/paraphrase, or cover numeric restriction sentences and nonnumeric paragraphs. Quoted restrictions cannot be freely paraphrased under this contract. Source text remains untrusted quoted data. General source fidelity, density, Arabic reading order and meaning still need review.

The existing acceptance case now requires the exact omitted restriction phrase as well as the original identifiers, dates, contact and counts. Existing case count and call budgets stay unchanged. v7 pending jobs must follow existing version-upgrade cancellation/release; already prepared files retain cached delivery without regeneration and administrator prices/settings remain preserved.

## Validation

PASS locally: 145 focused unit/service/acceptance tests, including omitted/negated restriction rejection, English/Arabic positive wrapping, continuation/no-export checks and numeric-complete acceptance failure. Repository ruff check, formatting (681 files) and whitespace checks passed. Database-backed flow suite: 36 tests collected, NOT RUN locally because PostgreSQL/Docker are unavailable. Added repair-once/settled-cost/single-capture versus failure/release cases; hosted full CI is required before merge.

Actual-provider v8 acceptance, worker rebuild, source verification, mobile/PowerPoint viewing and production deployment are NOT RUN. Do not reuse the old v7 worker image for v8 runtime acceptance.
