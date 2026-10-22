# Telegram Mini App — phased rollout (owner-approved 2026-10-22)

## Product contract and current slice

The Mini App is a **new customer interface**, not a replacement backend, service
plugin, payment engine, or reason to delay output-quality P0. Maintain the Telegram
bot for actual orders, purchases, support and file delivery during transition.
Use the existing FastAPI / PostgreSQL / services registry / orders / worker; do
not fork money or service business logic in JavaScript.

### Implemented in this PR — read-only first stage

- Same-origin mobile RTL/LTR interface under GET `/miniapp` with catalog, latest
  owner-scoped order statuses, and owner-scoped test-credit summary (Stars mode
  states checkout method, not a fictitious Stars wallet).
- POST `/miniapp/api/overview` requires signed Telegram `WebApp.initData`
  verified on the backend with current bot token and bounded freshness (one hour).
  Duplicate fields, stale signature, invalid user ID and nonprivate chat
  type fail closed. All identity and order ownership come from verified data.
- Displayed services follow registry category, visibility, activation, payment-price
  and AI-pause hints. This is a browse-only hint, **not** admission or payment
  approval. The price shown is existing DB price; SAR is labeled test credit.
- No frontend order creation, upload, download, support, state mutation, new
  Telegram payment path, provider calls, or backend wallet writes in this phase.
  Buttons clearly return users to chat for service selection and checkout.
- No external frontend framework, Node build, new dependency or migration; same
  existing API container and domain. Existing bot flows remain unchanged.

### Stage 2 — dedicated PR after acceptance

- Add backend-authorized generic request drafts/uploads using existing input
  schemas and file validation; one confirmed source of truth for saved state.
- Ensure customer ownership, type/size/quota, version/price snapshots and
  idempotency with existing order FSM/contracts. No direct client-to-provider calls.
- Mobile preview, understandable unavailable/unsupported responses and deliberate
  user consent for any AI rewriting. Preserve classic bot UX during rollout.

### Stage 3 — separate payments and commercial acceptance

- Reuse existing Stars invoice, receipt and refund ledger, not a second checkout.
  Confirm all Telegram test-environment lifecycle journeys before enabling.
- Complete mobile file delivery, support, real Office source/visual quality, bot
  menu registration and operator-selected HTTPS launch URL after staging checks.

## Staging steps

1. Review exact-head CI, browser/mobile AR/EN and source diff. Deploy only to
   **isolated staging** after authorization; do not change production provider
   pause, Stars flag, price, migration, or customer balances.
2. Publish the HTTPS API origin through the existing proxy; ensure `/miniapp`,
   `/miniapp/app.js`, `/miniapp/styles.css` and
   `/miniapp/api/overview` remain same-origin. No browser token storage.
3. After HTTPS staging acceptance set `MINIAPP_URL=https://<YOUR-HTTPS-HOST>/miniapp` in the staging environment, then run `docker compose exec -T bot python -m app.ops.miniapp_menu` or configure BotFather's Menu Button to open that URL
   on a dedicated test bot; do not paste tokens. `WebApp.initDataUnsafe` is not
   authentication; the API must receive the unmodified signed raw initData.
4. Test valid, forged, expired and group launches; banned/other user's orders;
   stars-price-disabled services; paused AI; test-credit balances, empty history,
   mobile RTL/LTR/themes, narrow devices, fallback chat navigation.
5. Only after a complete evidence-backed test may a production rollout be proposed.

### Limitations

No source-bound real mobile/BotFather deployment has been executed in this PR.
The one-hour authentication window favors safe short-lived read sessions; after
expiry users must reopen the Mini App. Authentication alone does not rate-limit
traffic; any future mutating endpoint must add existing Guard-equivalent protection,
CSRF/replay/idempotency controls and transaction-safe admission checks. No stable
production mini-app URL or Telegram setup has been configured automatically.

Official reference: https://core.telegram.org/bots/webapps

## Service-to-chat handoff — 2026-10-23

This is a bounded bridge, **not completion of Stage 2**. Service details offer
"Start request in bot" only when `MINIAPP_BOT_USERNAME` is configured and the
service is not unconditionally AI-blocked. Set the plain username of **this same
bot**, without `@` or a URL. Empty configuration retains the close-to-chat fallback.
There is no new HTTP write, upload endpoint, invoice path or purchase on opening.

The button calls Telegram `openTelegramLink` with
`https://t.me/<bot_username>?start=request_<registered_slug>` on a user gesture.
Telegram may show a Start button that the customer must press. The payload is
only a public service hint, never identity, price, consent, an order key or auth.
The bot uses its existing private-chat/rate/ban guards, registry visibility and
current service/payment/AI gates, then the usual schema-driven intake. An active
draft is preserved rather than replaced; a pending failed prompt is recoverable.
Uploads, review, explicit confirmation, idempotent submission and payment stay
in the existing bot flows. The bot's current price/contract is reviewed there.

After configuring the username, run the explicit menu command with MINIAPP_URL
as before. It checks `getMe` matches the configured username **before** changing
the menu, failing closed on mismatch; it never changes `.env` or settings itself.
Recreate the API/bot containers after an environment change; a plain restart
does not reload Compose `env_file`. Clearing the username removes request links
after recreation; existing public links still pass all normal bot guards.

Operator reports phase-1 HTTPS 200, unsigned overview 401, menu setup and initial
opening/display acceptance on the production deployment. This is not a complete
iOS/Android, payment, file-delivery or provider-output qualification. Verify the
handoff with a dedicated test account: both languages, different service while
a draft exists, disabled/admin-only/paused/unpriced service, failed prompt recovery,
no charge before confirmation, then exactly one normal confirmed order.

References: https://core.telegram.org/bots/features#deep-linking and
https://core.telegram.org/bots/webapps#initializing-mini-apps .

## Navigation follow-up — 2026-10-23

Service detail retains its selected service when switching AR/EN, including price
and availability hints. Use either the visible Back to services button or
Telegram's native BackButton to return to the selected category; keyboard focus
returns to the opened service. Switching a bottom tab clears detail state.
Language switching also works before authentication succeeds and on errors.

Manual staging checks: choose a category, open a service, change language, use
each back control, then switch tabs from a detail. Confirm category/focus
restoration, translated labels, no unexpected close and no extra overview
request. Verify unavailable hints and prices in both catalog and detail. Check
error/outside-Telegram notices in both languages. Actual iOS/Android rendering,
safe areas, theme integration and mobile assistive technology remain unqualified.

## Authenticated launch requirement

Use the bot Menu Button (or an inline WebApp button), not a reply KeyboardButton.
Telegram documents that WebAppInitData is empty for keyboard-button launches:
https://core.telegram.org/bots/webapps#webappinitdata . This interface requires
verified user data; never weaken that check to make a simple keyboard launch work.
The explicit `python -m app.ops.miniapp_menu` command sets the default bot menu
from validated MINIAPP_URL and fails on missing URL or rejected Telegram response.
It sends no customer messages and runs only when the operator invokes it after
HTTPS reachability checks. Clearing MINIAPP_URL does not reset a previously
registered remote menu; reset that via BotFather when rolling back.
