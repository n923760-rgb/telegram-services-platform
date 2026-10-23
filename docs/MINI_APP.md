# Telegram Mini App — phased rollout (owner-approved 2026-10-22)

## Bot home — 2026-10-24

When `MINIAPP_URL` and `MINIAPP_INTAKE_ENABLED` are configured, the bot home shows
Services, My orders, Support and Help. `/start`, `/menu` and Services offer an
inline Web App launch with signed Telegram user data. The persistent reply
keyboard itself never launches a simple Web App. The global bot menu remains
available; its operator configuration command is unchanged.

The app handles service browsing/intake and account views. Chat remains the
delivery, support and compatible fulfillment surface (including bot-only decisions
and Stars invoices). `/wallet` and `/lang` still work, as do old catalog callbacks
and saved bot drafts. Existing keyboards refresh after `/start` or `/menu`.
Without a URL or with intake disabled, retain the six-item bot home and catalog.
No customer migration, service version change or provider pause update is needed.

## Automatic document intake — 2026-10-23

New Word/Excel, PDF and paired Word/PDF requests no longer ask the customer to
select a processing engine. Document improvement runs automatically, while
output-format and optional document-title choices remain where supported.
Native file operations stay provider-free. A complete first-line literal-export
directive is honored; AI failure never silently selects a different result.
Legacy saved draft schemas preserve their original fields/positions; internal
legacy mode values remain strictly validated. See `SERVICE_REVIEW.md` for the
full service routing matrix, observed provider failures and acceptance limits.

## Native test-credit result decisions — 2026-10-23

With both existing intake/confirmation flags enabled and Stars disabled, an
owner's current test-credit review offers an explicit consent checkbox and
Approve button. Prepared results approve delivery of the cached original files;
structural results continue the existing request. Cancellation requires a second
confirmation and uses the existing engine's reserve release. Results still arrive
in bot chat. Opening a review does not apply a decision or reserve more credit.
Missing review text or an unavailable/failed image retains the bot fallback;
the browser cannot approve a prepared result before its image has loaded.

POST `/miniapp/api/result-decision` accepts fresh signed `init_data`, a server
review token and strict `approved`/`accepted` booleans only. The owner-bound,
one-hour HMAC uses a separate purpose from purchase confirmation and binds the
order, payment mode, exact stored Result and monotonic Job attempt. Under the
existing customer/order/job locks, a changed phase, result or later review round
rejects the old proof. Notification timestamp changes alone do not invalidate it.
Existing rate/FSM locks and origin/deadline guards apply; bot support data remains
untouched. Stars decisions stay in the bot. No new provider, Telegram, wallet
policy, migration, flag or dependency is introduced.

A successful response shows the decision and current order status. Repeated or
competing bot/API decisions cannot apply twice. There is no durable HTTP receipt
replay: if the decision committed but its response was lost, retrying the same
proof returns 409 and the customer must refresh My orders. On ambiguous failure,
the UI freezes the original decision for retry; it cannot switch to cancellation.
Navigation/authentication clearing also invalidates pending response rendering.

Run `MINIAPP_TEST_DECISION=1 MINIAPP_AXE=1 node scripts/check-miniapp-result.cjs`
alongside the legacy read-only journey. Hosted PostgreSQL/Redis tests cover
approval/rejection, cached delivery and settlement, stale/identical later rounds,
HTTP/bot races and lost postcommit responses. API-only rollout is compatible with
existing bot callers. Real Telegram/mobile acceptance remains separate.

## Read-only result review — 2026-10-23

With the existing `MINIAPP_INTAKE_ENABLED=true`, a waiting-confirmation order
offers View result review. The owner can read the complete existing AR/EN review
and, where available, the stored PNG first-page preview. The image is explicitly
labeled as the first page, not a complete visual inspection of every output page.
Text-only structural reviews work too. With native confirmation disabled,
approve/cancel remains in the existing bot flow, reached through a plain same-bot
chat link. Opening this view never decides,
restarts, pays, releases or delivers an order.

POST `/miniapp/api/result-review` accepts only signed fresh raw `init_data` and
the order UUID supplied in its owner's overview. Same-origin checks, bounded JSON
(10 KiB), shared rate bucket/FSM lock and deadlines reuse intake guards; no FSM
data is read or changed. Server-side registration/ban, order ownership, current
waiting phase and valid confirmation Result are required. A second database read
rejects a review changed during storage access or an account banned meanwhile.

The endpoint returns only reference, service names, localized review text and an
optional inline PNG. It never returns storage keys, original artifacts, continuation
instructions, provider cost metadata or delivery payloads. Review text uses the
existing `result_preview` contract without truncating its bounded full details
(up to 50,000 characters per language). PNG bytes use owner-scoped storage and
content validation: one frame, at most 3 MiB, 2048x3072 dimensions and four million
pixels. Missing, expired, wrong-owner, malformed or oversized images produce an
explicit unavailable-image hint while keeping the text review and bot route.
No preview generation, provider call, notification or original-file download occurs.

Responses are no-store; the browser renders plain text and validated PNG data
URLs only, with no external image requests or persistent browser storage. Language
switching preserves the loaded review without refetching. Back/tab navigation
aborts requests and clears review content; response generations prevent late
results replacing a newer view. Authentication rejection clears the whole private
overview and preview. Changed phases clear the preview and direct the customer
to refresh My orders. Late overview responses cannot restore data after review
authentication is rejected. Native Back and focus return preserve the selected filter.

Qualification: `MINIAPP_AXE=1 node scripts/check-miniapp-result.cjs`, alongside
catalog, tracking and confirmation browser checks. Synthetic journeys cover full
text/image, safe image fallback, first-page scope, AR/EN responsive themes,
accessibility, focus/back/filter, aborted/late responses, retry and auth privacy.
Hosted DB/Redis tests repeat reads of structural/visual reviews and verify one
unchanged reservation, job/result/notification state, retained original files and
an independent bot support session. Real Telegram/mobile and provider output
acceptance remain separate. Rollout rebuilds API only with existing flags; no
new environment option, migration, dependency or financial-policy change.

## Order tracking and next actions — 2026-10-23

My orders separates All / In progress / Finished, keeps the chosen filter when
switching language or refreshing, and describes the next step for each known
order state. Awaiting payment and waiting for review direct the customer to bot
chat; completed orders point to chat for results. Opening chat is a plain link
to the configured same bot, not an order deep link, automatic payment or repeated
submission. Missing/invalid links fall back to closing into bot chat. Unknown
future statuses stay visible in All with a refresh/chat hint rather than being
classified as completed or actionable.

Overview reserves independent windows of up to eight active orders and eight
other recent orders, selected in a single SQL statement and sorted newest first
with stable ID tie-breaking. Newer finished work cannot push older active work
out of its reserved window. Both branches and the outer selection are owner-scoped;
disabled services remain visible in their customer's history. These are bounded
recent windows, not a complete archive or total account counts. The UI discloses
the limits and counts only displayed rows.

Order amounts use the order's original payment mode and frozen SAR/Stars price,
independent of current prices and checkout mode. No inputs, results, storage keys,
terms payloads or provider error details are exposed. Existing signed launch,
ban checks and no-store responses apply. Failed refresh preserves the last view;
authentication rejection clears private cards and filters. This change only reads
orders; it does not change order status, ledger entries, invoices or jobs.

Developer qualification: `MINIAPP_TEST_ORDERS=1 MINIAPP_AXE=1 node
scripts/check-miniapp-ui.cjs` runs synthetic state/filter, transition, owner-view
privacy, historical payment labels, chat-link, keyboard-focus and AR/EN light/dark
320/390/768px checks. Also run the ordinary catalog and native confirmation checks.
Hosted database tests cover both window bounds, timestamp ties, owner isolation,
old active requests, disabled services, historical payment, unknown state and no
order/job/ledger writes. Live Telegram/mobile qualification remains separate.

Rollout only rebuilds/recreates API from the reviewed SHA. Preserve existing Mini
App flags, bot/worker, provider settings, Stars configuration and proxy networks.
No migration, dependency or environment change is required.

## Explicit test-credit confirmation — 2026-10-23

With both `MINIAPP_INTAKE_ENABLED=true` and `MINIAPP_CONFIRM_ENABLED=true`,
customers can review a complete draft, its current price, and explicitly consent
to reserving test credit inside the Mini App. Opening the review never purchases
anything. The default confirmation flag is false. Stars continues through the
existing bot confirmation, invoice and receipt flow; no Stars wallet or new
payment integration is introduced.

POST `/miniapp/api/confirm` accepts only signed `init_data`, an owner-bound
one-hour review token, and strict boolean `accepted`. It uses the same Redis FSM
lock and admission engine as bot confirmation. Current draft revision, completion,
service version/activation, price, payment mode, account and provider admission
are checked server-side. Identity, price, inputs and order keys cannot be supplied
separately by the browser. A successful request creates one normal order/job and
reserves test credit through `orders.engine.submit`; HTTP never calls the provider
or Telegram, creates an invoice, or delivers a result.

The durable owner/order key recovers a receipt after an ambiguous commit or FSM
cleanup failure. Repeated confirmation returns the same order, including its
current terminal status, and does not clear a newer draft or support session.
Bot/API races share the same idempotency key. After an ambiguous response the UI
offers retry without claiming no credit was reserved. Receipts link to My orders;
results and files still arrive through bot chat. Editing invalidates the old
review; a fresh review and consent are required before a changed draft is bought.

Qualification: run the existing catalog and intake browser checks, plus
`MINIAPP_TEST_CONFIRM=1 MINIAPP_AXE=1 node scripts/check-miniapp-intake.cjs`.
Synthetic checks cover consent, exact payload, ambiguous success/retry, receipt,
Orders, AR/EN and responsive light/dark layouts. Hosted PostgreSQL/Redis tests
cover financial admission, bot/API concurrency, exactly one reservation, stale
reviews, owner isolation and receipt recovery. Real Telegram/mobile and provider
output acceptance remain separate operator checks.

Rollout: back up source, private environment and API/bot images; deploy the reviewed
SHA, set both flags, and rebuild/recreate API and bot. Preserve Stars/provider
settings, worker, budgets, balances, proxy and networks. Check health, public
assets, and unsigned confirmation returning 401 with a same-origin Origin header.
Use a dedicated funded test account to review without purchasing, confirm once,
follow its order, and receive the result in chat. To restore bot-only confirmation,
set `MINIAPP_CONFIRM_ENABLED=false` and recreate API/bot; existing orders keep
their normal processing and settlement. No migration is needed.

## Shared request intake — 2026-10-23

With `MINIAPP_INTAKE_ENABLED=true`, service detail offers Start request inside
the Mini App. This bounded Stage 2 slice collects schema-driven text, choices,
optional fields and single/multiple image/PDF/audio uploads. It shows a bounded
review, supports editing and discarding an edit, then hands off to the existing
bot confirmation and checkout. It does not create an order, reserve credit,
send an invoice, invoke a provider, or deliver a file over HTTP.

The default is false, preserving the catalog-to-bot experience until the operator
enables this rollout. The account must first have started the same private bot.
Rebuild/recreate API and bot after setting the flag; keep worker, provider pause,
Stars mode, prices, budgets, proxy and persistent edge networks unchanged.

### One draft across both interfaces

- Both adapters use the same bot FSM, Redis key builder and per-customer event
  lock. Starting another service resumes the existing draft rather than replacing
  it. Support mode is preserved. No second draft database or browser storage.
- Schema and payment snapshots come from the shared `new_draft` factory. Every
  edit rechecks ban/registration, visibility, activation, version/schema, price,
  payment mode/Stars terms and applicable AI availability. Final admission stays
  in the existing bot/order engine. Browser hints never authorize processing.
- Each edit includes the current opaque revision and a random operation ID.
  Replaying the most recent committed operation returns its current view without
  appending another file. Changed/stale requests fail closed. Bot changes invalidate
  the browser revision. Every successful edit changes the confirmation key and
  marks the bot prompt pending; an old chat button first re-renders the current
  draft instead of buying it. Never submit automatically on opening or handoff.
- Redis commits state/data/expiry and replay metadata together. Drafts expire one
  hour after the last change; signed launch data also expires after one hour and
  must be renewed by reopening the Mini App. Back/navigation preserves the saved
  draft; cancellation remains the bot's existing `/cancel` operation.

### HTTP and file boundaries

POST `/miniapp/api/draft` accepts bounded JSON with signed raw initData and one
of view/open/answer/skip/done/edit/abort. POST `/miniapp/api/draft/upload` accepts
raw file bytes, signed `X-Telegram-Init-Data`, `X-Draft-Revision` and
`X-Draft-Operation` headers. No customer ID, storage key, price or schema is
accepted from the browser. Responses are `no-store` and never return upload keys
or bulk saved inputs. Same-origin Origin/Fetch Metadata checks accompany signed
authentication; keep Caddy's original Host header when proxying. No CORS grant or
cookie-only authorization. Forged/expired launches and banned accounts fail closed.

The existing shared bot rate bucket limits authenticated requests to 30/minute.
Redis failure fails closed; lock wait is bounded, upload reads have a 20-second
deadline, and work under the 60-second FSM lease has a 45-second deadline. JSON
is capped at 64 KiB; upload streaming stops at MAX_FILE_BYTES. Existing decoded
image/PDF/audio validation, metadata normalization or declared original-image
preservation, owner namespaces and authoritative storage quotas apply through
the shared upload helper. Filenames and MIME advertisements do not bypass content
validation. Files abandoned by cancellation, expiry or an ambiguous storage/FSM
failure are recovered by the existing age-based retention policy; they are not
promised immediate deletion. Keep the normal retention worker running.

### Qualification and rollout

Run `node scripts/check-miniapp-intake.cjs` with development Playwright/Chromium
alongside the existing catalog browser check. Optional `MINIAPP_AXE=1` uses
development-only `@axe-core/playwright`; `MINIAPP_SCREENSHOT_DIR` captures internal
review images. Telegram/API data is synthetic. Hosted PostgreSQL/Redis tests
exercise the shared dispatcher lock, expiring FSM, replay, old-button invalidation
and exactly one explicit bot purchase. Mobile Telegram, upload picker behavior,
real checkout and provider/delivery quality require dedicated account acceptance.

Before enabling: back up the current source, private environment and API/bot
image IDs; deploy the reviewed SHA and recreate API/bot. Verify public assets,
health and unsigned draft requests returning 401 with the same-origin Origin
header. Then use a dedicated Telegram test account: text, conditional choices,
files, edit/abort, interrupted retry, existing draft, both languages and final
explicit bot confirmation. Disabling the flag and recreating API restores chat
entry; existing drafts remain resumable in the bot. No migration or destructive
cleanup is required for rollback.

## Customer navigation and channel roles — 2026-10-23

The Mini App is the browsing and tracking surface. Bot chat continues to collect
schema-driven inputs/files, show the authoritative review and current price,
confirm purchases, deliver results and provide support. Opening a service never
creates an order or reserves credit. Native Mini App intake/uploads remain Stage 2.

The Services home shows search and four outcome-oriented groups, generated from
registered category metadata: Documents & PDF (documents/pdf), Writing &
translation (text), Images & scanning (images), and Work & data
(professional/data). Empty groups disappear; unknown future categories fall back
to More services. All services remains available without hard-coded service lists.
Service detail shows the description, price/payment label, accurate availability,
one continuation action, and the three steps completed in bot chat.

Bottom navigation is Services / My orders / Account. Search supports Arabic
normalization and both service-name languages. Returning from detail restores the
query, group, list scroll and service focus; AR/EN switching preserves selection.
Orders show the latest server-provided history with manual refresh. Account
distinguishes administrator-issued test credit from Stars checkout. Failed
authentication or a banned-account response clears previously displayed private
data; transient server failure preserves the last successful view for retry.

No new backend endpoint, migration, payment path, production dependency or
provider-setting change is introduced. Existing authenticated Telegram launch and
server-validated service-to-chat links remain authoritative.

Developer browser check: with Playwright available in the development environment
and its Chromium installed, run `node scripts/check-miniapp-ui.cjs`.
`MINIAPP_CHROMIUM_PATH` and JSON `MINIAPP_CHROMIUM_ARGS` optionally select an
existing local browser; `MINIAPP_SCREENSHOT_DIR` captures review images. The check
uses synthetic Telegram/overview responses and current registered catalog metadata,
never a production account or database. It covers grouping/search, focus/back,
language, links, availability, refresh/privacy, empty/Stars/untrusted data and
320/390/768px layouts in both themes. Actual Telegram iOS/Android, assistive
technology, checkout and delivered-file acceptance remain separate checks.

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

## Returning to bot chat

The result and orders chat actions open the validated same-bot Telegram link and
explicitly close the Mini App, since modern Telegram clients keep it open after
`openTelegramLink`. If that API is missing or throws, the action closes back to
the launching chat. This navigation does not resend files, regenerate results,
or change an order. Verify the transition in Telegram on mobile after rollout;
synthetic browser checks cannot certify the native client transition.
