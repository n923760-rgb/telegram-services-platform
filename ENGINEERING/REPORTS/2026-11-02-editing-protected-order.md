# Text editing: preserve protected-token order

## Reproduced finding

FACT: on verified main `a46fc6fe5bf379f212ff837d6ef72a9d6ff8fd6e`,
the request-bound revision schema accepts both of these meaning-changing revisions:

- `Order 00123 has amount 125.50 SAR.` becomes
  `Order 125.50 has amount 00123 SAR.`
- `Send to a@example.invalid, copy b@example.invalid.` becomes
  `Send to b@example.invalid, copy a@example.invalid.`

Independent per-line counters preserve occurrence counts but allow value permutations.
The existing semantic reviewer might detect these changes; the literal schema did not.

## Change

Text editing v3 checks one ordered numeric/contact sequence for each source line.
Emails and URLs match before numeric substrings so their embedded digits are not
double-counted. Mixing token types in one sequence also rejects moving a number
across a contact while preserving each separate subsequence. The prompt now requires
the same relative order and forbids reordering protected clauses or swapping roles.

Keep whole-segment reordering in the JSON response compatible: source IDs still
restore the original source-line order. Blank lines, source privacy, price/enabled
overrides, output filenames, result caching and repair/cost bounds remain unchanged.
The version bump uses the existing stale-order/cache compatibility behavior; do not
regenerate a cached result or silently execute an older queued service contract.

This deliberately conservative contract may reject an otherwise accurate rewrite
that rearranges protected clauses. The gateway can use its existing single repair
to restore the original order. This check does not prove names, negations or all
numeric associations remain correct; semantic review and real-source inspection
are still required. No live-provider quality claim is made.

## Verification

- PASS locally: reproduction before change; both permutations accepted on baseline.
- PASS locally: 106 selected tests: editing schema/service, production gateway with
  scripted responses, professional text review, change reports and architecture gates.
- PASS locally: whole-repository lint, formatting and diff whitespace checks.
- Added PostgreSQL regression: one repair succeeds and delivers the two files once,
  or two invalid candidates fail with no output and released credit. Repeated job
  execution must not call the provider or settle the order twice.
- Updated the registry upgrade expectation from v2 to v3; historical caches and
  administrator price overrides keep their existing coverage.
- NOT RUN locally: PostgreSQL integration/full suite, native containers, actual
  Telegram and live-provider runs. A focused hosted workflow step runs the editing
  regressions before the full suite. Hosted results must be inspected before merge.

## Next service gate

After hosted verification and deployment qualification, run the existing isolated
`editing_proofread` and `editing_rewrite` acceptance cases through the actual provider.
Inspect grammar, formal Arabic register, names, negation, amounts, addresses,
deadlines, revision text and change report on the target client. Do not mark editing
complete solely from scripted provider tests. Summary remains the next service.
