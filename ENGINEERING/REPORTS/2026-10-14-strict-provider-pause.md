# Strict provider pause admission

## Authority and baseline

Owner requested continued service review and development. Baseline main 0576026
(#82); #81/#82 deployment unconfirmed. Last supplied server evidence is #80,
provider paused with historical uncertain exposure retained.

## Finding and change

FACT: The new UI hint accepts only a missing pause row or explicit boolean false.
Financial admission used the generic settings reader followed by truthiness.
Values such as `{"value": 0}` or `{"value": null}` could permit calls; absent
keys and non-object settings could raise unclassified errors.

CHANGE: `app.ops.settings.provider_paused` supplies a shared read-only, fail-closed
interpretation to the UI, submit, Stars pre-checkout, reserve_call and readiness.
The existing missing-row default is retained. True or malformed values block AI.
Direct/mixed direct paths do not require this gate. A valid false keeps ordinary
budget-controlled operation available. No settings repair or write is performed.

## Verification

PASS LOCALLY: 46 pure pause/UI/readiness/architecture cases, global lint/format and diff
checks. Hosted workflow required before merge; no PostgreSQL flow result claimed
locally. New hosted tests cover four malformed stored values at submission,
Stars stale pre-checkout and concurrent job-scoped gateway admission. Assert no
new credit reservation/order/invoice acceptance/provider request/usage/hold,
direct submission remains available, original unknown exposure and budgets stay
unchanged, and explicit false permits a later reservation without clearing it.

LIMITS: No migrations, dependencies, price/service contract/gate, rates or env
changes. No actual provider call or cap qualification. A live probe must not bypass
the operational pause or existing job budget gateway. Historical unknown costs
are not settled or inferred. This source update still needs operator deployment.

Initial hosted run 38649278446: 1804 passed, seven fixture failures. Six readiness
tests still mocked the removed generic reader; now mock the shared pause reader.
The correction fixture used ORM JSON assignment of zero to false, which Python
equality treated as unchanged; now explicit SQL update plus strict readback models
the operator correction. No production guard was weakened. Full rerun required.
