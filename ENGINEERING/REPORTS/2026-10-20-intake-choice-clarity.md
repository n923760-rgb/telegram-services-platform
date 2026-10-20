# Document intake choice and unavailable-service clarity

FACT: Main 248fafdb515cdd2e358e6adecb4b9a8bd1577c1b is owner-reported
deployed with healthy application services. The supplied Telegram screenshot shows
two identical Preserve text buttons: an explicit direct choice and the optional
field's skip alias. A second screenshot shows provider_config's Arabic wording
being read as an order in progress, although submission was rejected.

CHANGE: The generic intake renderer omits a skip button when its translation key
already appears among that field's choice keys. Explicit choices keep their
original indexes/callbacks. Distinct optional skip buttons, title skipping and
old skip callbacks remain available. No schema/default/version change; old drafts
and direct/smart behavior are preserved. Remove the now-unnecessary skip explanation
from the Word/PDF mode prompt in both languages.

CHANGE: Replace the provider_config "being prepared/not configured yet" wording
with an explicit currently-unavailable message and another-service/later guidance
in Arabic/English. Keep the existing no-charge statement. Do not claim that no
order exists in every context: the same error key can also describe worker failures.
Provider pause, credentials, pricing and wallet/order policy are unchanged.

Verification: Focused tests invoke the actual intake callbacks with in-memory FSM
state and a synthetic transport, with no DB/provider/Telegram calls. Cover both
languages, one visible direct choice, direct/smart advancement, old skip callbacks,
title skipping, distinct optional skips and a rejected submission retaining its
draft without a queued message. Existing output/AI-policy/availability tests also
pass locally: 75 checks including 10 new callback regressions, plus three architecture
gates and global lint/format/diff checks. Full hosted checks and offline native worker qualification are required
before merge; record final source-bound evidence in the PR.

Limits: Exact translation-key aliases only, not arbitrary matching translated
labels or automatic inference that two different actions have identical semantics.
This UI fix does not resume the provider or qualify live AI output. Server update
and subsequent Telegram verification require separate actual evidence.
