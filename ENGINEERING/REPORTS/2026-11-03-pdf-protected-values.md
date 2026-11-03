# Smart PDF source-reference qualification

Operator-reported live run on `9ad78b9`: direct PDF passed without provider calls;
smart PDF failed after two generation attempts, both `document_source_tokens`.
Acceptance exited 1, with no active test orders or reserved customer credit.
The specific changed/missing/repeated token is UNKNOWN: diagnostics intentionally
omit raw candidates. No claim is made that this reproduces a particular model reply.

PDF v8 adopts the existing request-local ProtectedValues protocol already used by
Word and PowerPoint. Send masked source and literal reference metadata; resolve
references before original token-count validation, semantic review and rendering.
Keep the same one-repair allowance and reject unknown references or missing,
added/duplicated literals. No provider vendor, pricing, acceptance fixture or budget
change. Direct output remains provider-free. Resolved historical continuations
remain compatible; generic version/cache handling remains authoritative.

This is a bounded reliability improvement based on a known path difference, not a
verified explanation of the specific live failure. It must pass actual provider
qualification before smart PDF is accepted. Do not retry the old image unchanged
or relax source-fidelity validation to turn this failure into PASS.

Local regression exercises the production gateway with scripted references through
review/rendering, exact occurrence counts and terminal rejection after one repair,
without writing invalid artifacts. Existing direct/continuation and common source
diagnostic/repair tests also pass. These fixtures are not actual provider evidence.

Keep production-provider recovery separate: only restore the previous false state
after checking the failed run's accounting/holds and current production exposure.
The unqualified PDF candidate is not deployed. Preserve the failed archive at
`/home/aidev/service-acceptance-K3qqvjdz/service-acceptance-results.zip` for review.
