# Formal Arabic rewriting

Baseline: official main a3d3a37b513497e60a1b5a9da5c0ec7d76b178a9.
Authority: owner agrees to continue improving formal Arabic rewriting; earlier
authorization covers merging ready improvements and deployment handoff.

## Uploaded evidence

The representative six-case archive contains twelve deliverables with matching
reported sizes/SHA256. Actual inspection accepts the English proofreading fixes,
AR/EN translations and exact-source Word/PDF sample. Editable Word preserves all
4,978 source characters; the delivered PDF and secondary Word render each have
two visually inspected pages with readable Arabic/English and no observed clipping.
No Microsoft Office/mobile session was inspected. This is bounded synthetic quality
evidence, not certification of arbitrary source documents.

Formal Arabic rewrite is REVIEW_REQUIRED despite the model's accepted review and
the wrapper's PASS. The source prohibition changes from
`ولا ترسلونه للمحاسبة على أنه معتمد` to
`ولا ترسلونه إلى المحاسبة على أنه معتمد`, retaining the colloquial inflection.
The output contains some polishing but does not consistently reach the requested
formal grammar. This demonstrates that changed text and an accepted model review
alone do not establish a professional rewrite.

The separately uploaded summary-only archive matches both artifact hashes and
reports PASS with two calls, calculated usage 0.003909 SAR, no active orders or
reserved synthetic credit. Native text review confirms three points grounded in
the twelve source paragraphs: unapproved payment, request still open, correct
order/amount, Sam's action/deadline, provisional delivery date and no invented
approvals. This confirms the sample after the point-limit fix; production running
containers were not replaced by the isolated build/run.

## Improvement

The existing editing task defines formal only as respectful/neutral, with general
clarity and grammar guidance. Make its Arabic rewrite expectation concrete:
natural Modern Standard Arabic grammar/syntax, transformation of colloquial
constructions rather than punctuation-only polishing, and a small grammatical
example preserving the same prohibition. Content review receives this same task
and should reject remaining colloquial grammar using the existing quality issue.

Scope the conversion to formal rewriting. Proofreading preserves the source's
register; casual output may remain conversational; already suitable formal prose
may stay unchanged. Do not reject a respectful direct address alone or rewrite a
quotation that must remain literal. Preserve factual claims, exact numeric/contact
tokens, uncertainty, prohibition strength, conditions and existing segment order.

No hard-coded word rejection, grammar engine, new model or retry loop. No provider
gateway/global-review change; the existing shared contract/review path carries the
more precise service instruction. Same public schema, accepted structures, version,
prices/gates, prepared replay, per-call exposure accounting and budgets.

## Checks and next acceptance

- PASS locally: 64 professional-quality/gateway/acceptance checks. The exact
  observed source/candidate and a corrected alternative exercise bounded quality
  correction or refusal, artifacts only after accepted review, and per-call mocked
  settlement. Three additional valid-register cases cover unchanged Arabic
  proofreading, already formal rewriting and casual rewriting. All model verdicts
  in these tests are scripted; they do not prove actual model quality.
- PASS locally: Three architecture gates, global lint/format and diff checks.
- ADDED through the existing fixture matrix: Two PostgreSQL quality/refusal cases
  cover delivery interruption/prepared replay, one capture/release, cost records
  and file cleanup. NOT RUN locally: PostgreSQL unavailable. Require full hosted
  tests, migrations and worker qualification before merge.
- NOT RUN: Live provider after this instruction clarification. Build the new
  worker image and run only editing_rewrite through the isolated wrapper. Preserve
  production pause, synthetic-only accounting and existing backup evidence; no
  production container replacement is needed for that run. Inspect all three
  rewritten lines against their original before accepting the sample.
