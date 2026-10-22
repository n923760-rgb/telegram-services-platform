# Telegram Mini App — phased rollout (owner-approved 2026-10-22)

## Product contract and current slice

The Mini App is a **new customer interface**, not a replacement backend, service
plugin, payment engine, or reason to delay output-quality P0. Maintain the Telegram
bot for actual orders, purchases, support and file delivery during transition.
Use the existing FastAPI / PostgreSQL / services registry / orders / worker; do
not fork money or service business logic in JavaScript.

### Implemented in this PR — read-only first stage

- Same-origin mobile RTL/LTR interface under GET \`/miniapp\` with catalog, latest
  owner-scoped order statuses, and owner-scoped test-credit summary (Stars mode
  states checkout method, not a fictitious Stars wallet).
- POST \`/miniapp/api/overview\` requires signed Telegram \`WebApp.initData\`
  verified on the backend with current bot token and bounded freshness (one hour).
  Unknown/duplicate fields, stale signature, invalid user ID and nonprivate chat
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
2. Publish the HTTPS API origin through the existing proxy; ensure \`/miniapp\`,
   \`/miniapp/app.js\`, \`/miniapp/styles.css\` and
   \`/miniapp/api/overview\` remain same-origin. No browser token storage.
3. After HTTPS staging acceptance set `MINIAPP_URL=https://<YOUR-HTTPS-HOST>/miniapp` in the staging environment to expose the optional bot keyboard launch button, then configure BotFather's Menu Button to open \`https://<YOUR-HTTPS-HOST>/miniapp\`
   on a dedicated test bot; do not paste tokens. \`WebApp.initDataUnsafe\` is not
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
