# PowerPoint contact/prose direction — 2026-10-19

## Baseline and reproduced defect

FACT: Official main 07ecdb397359a5112586f2f8118dd6df0a77891b includes #105.
On 2026-10-18 the native builder reproduced rtl=0 in both title and body for
«تواصل: help@demo.invalid». The email's Latin letters outweighed the Arabic prose.
Work resumed 2026-10-19 after checking main and open PRs; baseline remained unchanged.
Owner authorizes continuing tested improvements/merges, with production deployment deferred.

## Bounded correction

CHANGE: PPTX v6 excludes recognized dates/emails/HTTP(S)/www contacts from the direction
vote using Word's existing INLINE_LTR matcher. No rendered content is removed or replaced:
titles/bullets/cells retain exact customer text, with the pre-existing ISO-date display marks.
Apply the rule to heading direction, bullet direction/indentation, table direction and each
cell independently. Centered covers remain centered. Plain contacts and English prose remain
LTR; mixed prose uses the existing dominant-script policy after identifier exclusion.

SAFETY: No AI schema/prompt/review, provider stage/call limit, density/count/layout budget,
price/activation, file count, dependency or financial policy changes. Version guard behavior
is unchanged: prepared historical files replay; unprepared older jobs cancel/release.

## Verification and limits

PASS LOCALLY: 95 focused contact/count/service tests and 17 existing pure native layout
tests, three architecture gates, global Ruff lint/format, diff whitespace and workflow/worker
syntax. Native tests cover AR/EN contacts, URLs/dates, title/body cover/content alignment,
table and cell direction, unchanged strings/source plan, indentation and footer counts.
Initial invocation of the old layout tests hit the shared DB fixture (no local DB). Those
17 pure tests were rerun with --noconftest only locally; hosted DB gates remain unchanged.
After the runtime resumed, the old venv Python executable was unavailable; reran using the
current Python 3.12 runtime with the existing installed packages, without dependency changes.

Hosted lifecycle extends exact one-slide contact output, one provider call/capture/cost,
v5 pending cancellation and cached v4/v5 replay retaining administrator overrides. Non-root
network-disabled worker qualification adds source-bound exact-email and RTL readback.
Full exact-head hosted qualification required before merge.

LIMITS: This reuses a conservative existing matcher, not universal language/contact parsing.
The change does not claim every bidi punctuation sequence is visually correct in every
viewer. Real-provider/PowerPoint/mobile visual acceptance and production deployment NOT RUN.
