# Administrator service configuration evidence

## Authority and baseline

Owner requested continued implementation of service quality and administrator
controls with independent manual selling prices. Main `1c053b7` is the baseline;
deployment and real-provider image enhancement acceptance remain separate.

## Implemented scope

- Private `/admin` gains a separate six-item configuration browser, so existing
  services/price callbacks are not repurposed.
- Generic registry metadata drives browsing; historical replaced services are
  excluded. Invalid/unknown inspections use existing safe errors.
- Details reread activation, stored plugin version and Stars price; compare
  current code version and mirror customer menu activation/payment-price filters.
- Global AI status distinguishes settings disabled, operational pause, invalid
  local cost configuration and configured local calculation. No provider call,
  cost reservation or secret/error body display.
- Mandatory AI metadata is shown separately from input-dependent paths. Never
  call plugin `needs_ai` with invented inputs to suggest operational approval.
- Current payment mode, price and missing Stars-mode price are explicit. Refresh
  rereads values; Edit Stars price uses existing immutable audit/confirmation.
- Existing server owner authorization/private chat middleware and customer
  draft/support state are preserved. No activation or financial mutation added.

## Evidence and limits

PASS LOCAL: 19 pure listing/version/language/provider configuration tests; lint
and format. Pure cases prove no outbound provider call and no fake plugin inputs.
Added hosted dispatcher cases check refresh, retired omission, authorization
revocation before queries, source/price/flag preservation and no orders/jobs/
cost usages/price audit creation. Full disposable PostgreSQL workflow is required
before merge; local DB/native container cases are NOT RUN.

FACT: This checks local bot configuration and database metadata, not actual
worker versions, installed native tools, storage availability, daily/job/user
budget headroom, provider credentials validity at the remote server or quality
of results. It neither claims all services use AI nor guarantees that a listed
service will pass actual input-dependent admission. The displayed snapshot can
change immediately after rendering; ordinary admission remains authoritative.

NOT RUN: Live Telegram/mobile/VPS/provider acceptance. No models, dependencies,
migrations, price defaults, service enablement, payment activation or deployment.
Enable/disable impact confirmation is a separate future control because existing
disable cancels unsettled orders and may schedule paid-order refunds.
