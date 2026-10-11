# Service completion navigation and activation audit

## FACT — scope

Owner requested another-service navigation after every outcome and continued
development/activation. Source baseline fbffa5815d99dfb255c91881451b72d5d730d5a4.
Telegram delivery now appends one localized completion panel after all original
text/preview chunks and artifacts. Home and another-service controls appear on
separate rows for every successful delivery, including legacy references. Declared,
eligible followups remain optional and owner-bound; do not add translation to
unrelated services. Reuse existing navigation, preserve independent intake drafts.

## Verification and recovery

Extend existing delivery tests for Arabic/English, original chunks and artifact
ordering. Dispatcher tests cover both OCR versions and independent translation,
CSV and Word/PDF source contracts, no implicit draft/order/reservation, and
preservation of a different active draft. Test an actual Telegram adapter footer
send outage through the job runner: cache original result, retry delivery without
a second provider call, capture once. Failed artifact delivery cannot announce
completion. Existing structure/visual confirmation controls remain unchanged.

Require local lint/format/pure governance checks plus exact-head hosted full
PostgreSQL/Redis regression, schema drift, Compose and eleven actual non-root
network-disabled worker gates. Record exact hosted head/tree/run/job in the PR.
PASS LOCAL: lint, formatting, diff check and 108 pure service/governance/mobile
checks. Two DB-backed mobile delivery cases excluded locally and included in the
required full hosted regression; local PostgreSQL/Redis lifecycle NOT RUN.
Delivery remains at least once: an outage/crash can duplicate prior messages/files
on retry; this change does not guarantee exactly-once external sends.

## Activation/development audit

Registry contains 18 plugins, one retired customer product (local_ocr), with 17
visible source entries including echo. Database enabled flags/overrides on the VPS
are UNKNOWN: no direct connection or runtime snapshot. SERVICE_ACTIVATION.md records
a read-only operator inventory, staged file-service and provider-assisted trials,
and source-qualified versus live-qualified boundaries. Default flags stay unchanged;
do not reactivate historical local OCR or bulk-enable unqualified extensions.

## NOT RUN

VPS update/activation and representative real Telegram/mobile/provider quality
acceptance. No financial changes, dependency, migration or input/execution version
change. Source merge is not commercial launch approval; payment remains deferred.
