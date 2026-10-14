# Provider-paused customer intake

Baseline source af8b118 (#81). Operator confirms #80 deployed healthy; #81 deployment remains UNKNOWN. Owner authorizes continued service review/improvement. Global provider pause and historical uncertain exposure remain retained.

## FACT and bounded change

The final submit gate already refused new AI requests before reservation while provider was paused/off. UI selection/resume nevertheless requested long forms first; result translation shortcuts checked AI-off but omitted pause. Required-AI metadata now gates new draft creation and explicit resume, before replacing existing FSM data or asking a field. Localized category notice preserves service labels/callbacks/categories. Followup targets recheck pause along with original ownership/expiry/version/price/schema controls; source results/orders are untouched.

All behavior is generic from registered requires_ai metadata. No named-service branch, fabricated partial Inputs, provider call or AI vendor/config validation. AI-off avoids querying pause; absent pause is unpaused, explicit false is unpaused, malformed pause hints fail closed. Order submission remains authoritative; UI hints cannot bypass it.

Direct and mixed services remain selectable even while paused, allowing direct PDF and Word workflows. A mixed AI mode or pause changing after intake is rejected by existing submission checks before any new payment/reservation/invoice. Existing mid-field work is not deleted or silently redirected; this round does not introduce per-keystroke service readiness monitoring. Explicit resumes preserve saved values until service becomes available.

## Checks and limits

PASS locally: 35 pure availability/catalog/order/architecture cases and global lint/format/diff. Hosted new dispatcher tests cover every required-AI public metadata class in Arabic/English and both off/paused states; unchanged existing draft, zero orders/holds/Stars charges/reservations; available intake; direct PDF queued under pause; stale result-followup preservation; explicit paused resume and restored continuation; pause after form completion blocks both test-credit/Stars submission without changing draft.

Existing recovery/canonical-intake fixtures now explicitly enable AI when testing a successful required-AI journey. Catalog-localization assertion includes the new unavailable notice rather than weakening availability. Hosted full PostgreSQL/dispatcher/financial/native checks required before merge; actual logs retained in PR.

No dependency, migration, service input/version/default or admin price/gate changes. No wallet/financial policy, rates/credentials/pause mutation, historical cost settlement, new live AI request or quality certification. This source update and #81 still need operator deployment evidence.
