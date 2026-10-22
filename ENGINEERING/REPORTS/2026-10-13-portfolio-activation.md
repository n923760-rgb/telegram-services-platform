# All-current-service activation — 2026-10-13

OWNER AUTHORITY: Develop and activate all services. Baseline main `3095ecf` / PR #66.
FACT: Registry has 18 plugins: 16 public canonical services, one private administrator
utility and one retired OCR product. No SSH/server control is available in this
session; live activation cannot be asserted from repository work.

## Development slice

Declare validated immutable worker requirements in plugin metadata, outside input
contracts. Fixed worker probes check office executable/fonts, OCR binary/AR+EN
packs and imports for tables, image processing, images/PDF and PDF previews. Native
OCR is optional for canonical AI fallback. Probe children use a fresh temporary
HOME, stripped environment, fixed commands, 10-second timeout and kill/reap on
timeout/cancellation. These are local presence/import checks, not a sandbox or
provider/customer-output certificate. Run in worker, not lean bot/API containers.

Read-only `app.ops.service_portfolio` checks each public service's stored/code input
schema/version, activation/prices, active-order count, local AI/pause evidence,
worker requirements, Stars prices and pending disable recovery. No fake customer
inputs, provider calls, order/receipt identifiers or secrets in the public report.
At most 64 services with existing 100-order/500-receipt per-service snapshot bounds.

Explicit `--enable` uses the configured single owner or an explicitly named
configured admin. Initial blockers prevent all writes. Existing `change_activation`
per-service API commits the immutable actor/snapshot audit and circuit baseline;
no new financial operations or raw flag writes. A concurrent change can stop with
partial success; rerun inspection. Already enabled services skip audit/reset.
Unknown DB commit outcomes remain explicitly unknown. No all-or-nothing or batch
exactly-once guarantee. Registry discovery excludes private/retired products.

Input contracts, versions, defaults, prices, ledger, Stars/payment/provider flags,
dependencies and DB schema are unchanged. Technical activation does not assert
paid launch, semantic accuracy, provider connectivity or server-wide capacity.
Correct outdated OCR/minutes/enhancement portfolio descriptions; retain separate
future CV writing, study and design contracts rather than inventing features.

## Evidence and operational next step

PASS locally: nine pure catalog/metadata/authorization/probe/redaction cases,
three architecture gates, lint/format/diff and CLI help. Local probes see fonts and
Python engines; LibreOffice and native OCR are absent here, correctly reported
unavailable. Local PostgreSQL financial activation tests NOT RUN.

Full suite collects 1357 tests. New hosted DB cases exercise all 16 audited enables,
convergent rerun, retained prices/ledger, eight initial blockers, optional native OCR,
unauthorized actor, changed-snapshot partial stop and no fabricated mixed inputs.
Existing non-root/network-disabled native suite adds mandatory capability preflight.
Full final-source hosted qualification required before merge.

Live deployment, actual 16-service enablement, Telegram/mobile/provider acceptance
and payment qualification NOT RUN. Obtain current host HEAD/clean state, container
health and unfinished-order counts before preparing an exact-source update; preserve
backup and price/secret configuration. Then inspect and enable through the worker
using docs/SERVICE_ACTIVATION.md, retaining its JSON evidence. Do not report enabled
until the deployed database report confirms it.
