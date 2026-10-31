# Hosted customer profiles: foundation proposal

Status: internal persistence/rendering and default-disabled owner/public HTTP implemented;
purchase/generation integration and public activation remain incomplete.

The independent [completed-order handoff](COMPLETION_HANDOFF.md) now provides a
bounded atomic data transfer before ordinary result expiry. No page plugin,
handler, dispatcher or hosting entitlement is connected to it yet.
Baseline: main 5c563f6970832db94a0ac2c16aaa6b7fb56ed05c, verified 2026-10-29.
The owner asked which delivery model is preferable. Recommend a hosted public
link with future revisions at the same URL. Hosting term and pricing remain
undecided; no subscription, renewal charge or perpetual-hosting promise exists.

## Customer outcome

A responsive Arabic/English public page containing supplied identity, business
summary, offerings and exact contact/social destinations. Customers describe
profession, audience and visual preferences freely. AI proposes bounded design
and source-grounded section arrangement, rather than selecting a profession menu.
Existing interactive_card remains a separately purchased PDF service at its
administrator-owned price. A public page is a distinct product and lifecycle.

A visitor opens the link without Telegram authentication. Owner editing and
publication require verified Telegram identity; knowing a public URL never grants
edit rights. Show the exact public content and hosting term before publication.
Do not publish customer phone numbers or profile text merely because an order was
submitted or a file was delivered. Payment is not publication consent.

## Recommended delivery model

Host within the existing VPS with logical isolation and bounded resources.
Use a stable opaque public path. A later paid revision can replace the visible
revision atomically while retaining the URL. Offer a portable static export later
if useful; do not claim that customers cannot copy or edit downloaded material.
Price creation and a defined hosting period explicitly. Agree a renewal price,
expiry behavior and revision scope before enabling checkout; no automatic charge.
Do not reuse the PDF price or silently convert SAR test credit into money or Stars.

## Required generic foundation

AGENTS.md requires proposing a generic foundation if a plugin needs bot/core
changes. Public hosting cannot be delivered by adding a PDF-style plugin alone:

- Ordinary artifacts in app/files/retention.py and app/providers/storage.py expire.
  Durable published pages need their own retention contract and referenced assets;
  never bypass or disable ordinary customer-file cleanup to preserve public pages.
- Add a generic publication adapter/repository, independent of a service slug.
  Persist owner, order, opaque public ID, active revision, hosting expiry, state,
  consent receipt and minimal audit metadata through an Alembic migration.
- Store immutable validated revisions; switch the active revision transactionally.
  Model draft, published, suspended, expired and deleted explicitly. Define backup,
  restoration, deletion and expiry jobs before promising hosted availability.
- Keep service generation in app/services and rendering in app/builders. Inject
  publication operations; do not put a profile-slug branch into wallet/order/worker
  policy. Agree generic result/publication capabilities before changing core code.
- Render trusted markup from validated structured content. AI never supplies
  executable HTML, JavaScript, CSS, URLs or payment logic. Escape all text; preserve
  exact supplied link targets and deterministic WhatsApp generation.
- Reuse the normal metered AI gateway, budgets, bounded repair, lifecycle billing
  and prepared-result replay. Do not regenerate on page views or repeat delivery.
- Public reading exposes only the published revision and no private draft, Telegram
  ID, internal order ID, credentials or admin state. Authorize every mutation by
  verified owner; protect cookies/initData routes against cross-origin writes.
- Use restrictive CSP, no arbitrary embeds or server-side URL fetching. Start with
  text and safe HTTPS contact links; logo/photos require a separately bounded image
  ingestion and durable-asset design. Add bounded page sizes and request limits.

## Implementation and qualification sequence

1. Agree hosting term, proposed commercial price, renewal and revision boundaries.
2. Review the generic publication contract, consent, expiry and deletion behavior.
3. Implement migrations/repository with tenant-isolation, atomic revision and
   retry/replay checks; prove ordinary artifact cleanup cannot erase live pages.
4. Build responsive native rendering and free-form AI planning. Verify Arabic RTL,
   narrow mobile screens, long text, safe markup and exact destinations.
5. Integrate owner preview/publish and later edit through generic authenticated
   controls. Use new consent for changed public content; preserve the previous
   published version when generation or publication fails.
6. Require exact-head hosted financial/migration/security checks, actual provider
   evidence, visual/mobile acceptance and rollback/restore testing before activation.

No public profile route, customer page, hosting commitment, schema migration,
price change or provider call is performed by this proposal.

## Foundation implementation (2026-10-29)

Migration 0014 adds publications, append-only numbered revisions and immutable
minimal consent receipts. The internal repository accepts verified numeric owner
IDs from future authenticated adapters; it is not an authentication mechanism.
One publication per completed owner-bound order is idempotent, with explicit
aware expiry no more than 366 days ahead. This is a technical ceiling, not a
commercial hosting entitlement. No existing service grants publication eligibility;
a future adapter must check the reviewed result capability before using create().

Content is bounded plain JSON (32 KiB, depth eight, twenty revisions). There are
no storage keys or HTML templates in this foundation. Native renderers must still
validate their own content schema, escape text and restrict URLs before serving.
Preparing a draft leaves live content intact. Publication requires the exact
latest revision, expected active revision and terms hash; the consent receipt
binds those to content hash, actor and expiry. Old operation replay does not
restore a suspended, expired or deleted page. Owner deletion purges content and
retains hash-only consent metadata. Revisions reject SQL UPDATE; receipts reject
SQL UPDATE/DELETE. Downgrade refuses populated publication tables.

Read eligibility checks expiry and owner ban on every lookup, even before the
expiry sweep. expire() is internal and not yet scheduled. Expired content cleanup,
minimal audit retention, renewal, uploaded assets, commercial entitlements, owner
UI, public HTTP route, abuse handling and restored-backup qualification are later
work; this slice must not be advertised as a hosted customer page service.

## Profile composition and whole-page QR (2026-10-29)

The internal renderer now accepts bounded source identity, role, introduction,
one to six exact HTTPS actions and up to six source sections. It generates an
original responsive HTML composition with localized Arabic/English labels,
RTL/bidi handling, light/dark surfaces, original geometric detail, clear primary
action, native disclosure for sharing and hash-bound inline CSS under a restrictive
CSP. All customer strings are escaped; there is no executable model-authored markup,
remote resource, embedded third-party frame, form submission or client JavaScript.

An injected job-scoped metered AI adapter can choose a validated design plan from
the customer's free-form profession, audience, goal and taste. Only action labels
and indices are passed through the action metadata path; source prose may itself
contain URLs supplied by the customer. The plan cannot rewrite facts or destinations,
omit/duplicate indices, or inject CSS. No silent native fallback on invalid AI.
No named profession template menu exists. Pure tests use synthetic AI responses,
not actual-provider aesthetic/cost qualification.

The builder takes a separate trusted whole-page HTTPS URL. Native ReportLab QR
matrices are exported as PNG and SVG with four-module quiet zones; PNG sharing
cards can include the same symbol or omit it. Separate QR assets are always part
of the bundle, independently of embedding. QR targets are not individual action
URLs unless the caller explicitly supplies one. The future publication adapter
must derive the real page URL from configured origin and stable publication ID;
AI must never select or invent that URL. No hosted-PDF URL is created in this slice.

A bundle contains profile.html, qr.png, qr.svg and share-card.png. The public HTML
includes QR/download disclosure only when embedding is selected and a URL exists.
The PNG share card expands for long identities/URLs. None of these rendering calls
publishes data, creates a route, changes a price, or modifies durable publications.

Qualification: pure literal-content/URL/escaping/CSP/AI-rejection tests and independent
QR decoding cover standalone PNG and integrated share cards, Arabic URI payloads,
long destinations, minimum/maximum action counts and dark/light text contrast.
The hosted worker gate repeats actual QR read-back with its network disabled.
Browser/mobile visual acceptance and actual-provider composition are still required
before activation. Local browser preview was blocked by environment capability:
Chromium could not be downloaded, and cloud preview could not access the local HTTP
server; file URL access was denied. No alternate cloud-file access was attempted.
The delivered HTML preview is synthetic and uses a deliberately unpublished .invalid
page target. Images, customer intake, authenticated preview/publish controls, hosting
terms, renewal and durable asset delivery remain later integration work.

## Prepared review binding (2026-10-29)

The internal prepared_page coordinator now joins the renderer to durable revisions.
It derives the whole-page /p/<opaque UUID> URL from a caller-supplied operator HTTPS
origin, never a request Host header, customer field or AI result. Only a bare origin
(optional final slash) is accepted. The coordinator does not create publications:
future authenticated adapters must separately check a completed eligible order and
an explicitly agreed hosting entitlement before calling repository.create().

A revision stores a bounded profile-page-v1 JSON envelope: literal profile, validated
design plan, embedding choice, publication identity/destination and SHA-256 digests
of all four exports. It contains no trusted raw HTML, storage keys or AI credentials.
Owner review loads the latest revision and rebuilds the bundle, requiring exact byte
agreement with all digests. Approve rechecks those bytes and passes the reviewed
content hash to the repository's locked consent transaction. A newer draft, changed
active revision, wrong hash or changed expiry/terms intent cannot silently publish.
Exact consent replay retains the existing repository's no-resurrection behavior.
No AI runs during draft persistence, owner review, consent or public bundle lookup;
AI composition still belongs to the original job-scoped, budgeted generation step.

Rendering is deliberately fail-closed: changed renderer, translations, fonts or image
libraries can make a saved envelope unavailable, rather than display different bytes
under an old consent. Public lookup returns no bundle in that case. This is a safety
contract, not a hosting-availability solution. Before public activation, upgrades must
retain compatible versioned rendering or migrate through fresh owner review; durable
immutable export storage and restored-backup qualification remain required decisions.
Public reads currently rebuild the bounded bundle; HTTP adapters will need bounded
request rates and a private cache that rechecks visibility/expiry/ban on every access.

The generic repository additionally supports a private owner-only latest-revision
read and optional expected_content_hash/expected_expires_at for atomic consent.
The prepared-page coordinator requires both review bindings. Existing callers keep
their contract. No schema migration, public HTTP route, customer UI, renewal, price,
service activation, provider call or VPS rollout is introduced by this bridge.
Real PostgreSQL tests cover private review, exact consent/replay, race rejection,
old-live/new-draft separation, wrong owner, bans, suspension, expiry and deletion.
Pure tests cover origin/identity/content binding, all-export drift and invalid hashes.

## Gated owner review and public reading (2026-10-29)

PUBLICATIONS_ENABLED defaults to false. Enabling requires Mini App intake/authentication,
a bare operator HTTPS PUBLICATION_ORIGIN and explicit bilingual publication/hosting
terms with a version. No hosting price, duration entitlement, renewal or automatic
charge is invented. Existing PDF cards and standalone QR services retain their contracts.
No endpoint creates a publication, accepts source/AI plans or grants a hosting entitlement.
The future purchase/generation adapter must verify those rights before using create().

When enabled, the account screen offers My pages rather than another main navigation
tab. An authenticated owner sees the latest twenty non-deleted pages, their literal
names and status; older pages are not included in this bounded initial list. Review
shows the complete prepared page in an opaque iframe sandbox with no script, form,
same-origin or popup permissions, the exact contact links in a separate testable list,
the hosting expiry (with timezone), configured terms and explicit public-data notice.
An unchecked consent control precedes publication. Stopping a live page uses its own
confirmation and purpose-separated proof. Missing native previews provide no publication
approval proof; the owner can still stop public access without a working renderer.

Owner POSTs require fresh signed Telegram initData, HTTPS same-origin requests,
bounded JSON, owner checks and the existing user rate/isolation gate. Review proofs
bind owner/publication, latest and active revisions, content hash, expiry, policy hash,
state and count of immutable consent receipts. Recording a decision is independent of
payment/order confirmation. Ambiguous publication retries retain the same operation
UUID and proof; definite rejection requires a fresh review. Replies acknowledge a
recorded decision, not a promise that an old replay restored visibility.

The receipt count plus current state prevents old review reuse after stop/republish
cycles, even when active_revision returns to NULL. Under the publication row lock,
new consent checks this gate. The existing receipt terms_hash commits to the supplied
policy hash and expected state/count when the optional gate is used. Exact operation
replay checks this combined commitment before returning the immutable receipt and
never toggles visibility. Existing internal callers without the gate retain their
contract. No new schema migration is needed for this monotonic evidence.

The complete verified native HTML travels only in the authenticated owner POST
response. The client displays it in opaque sandboxed srcdoc, with no forms, scripts,
origin access or popups. The Mini App response generates a fresh style-only CSP nonce
and matching metadata. The private copy adds that nonce to the native style element;
CSS content and customer text/links stay literal, and the public bundle bytes/digests
remain unchanged. Both the inherited parent policy and the child's original CSS-hash
policy permit the native style. Missing nonce/preview disables approval; stopping
access remains available. Review rechecks owner, ban and revision metadata after
native work, before returning content or a proof.

This flow needs no preview URL, cookie, browser storage, credential-bearing navigation
or form submission. Authentication remains fresh signed Telegram initData in bounded
same-origin HTTPS POSTs; no credential enters the preview HTML or public responses.
Cookie independence avoids the cross-site ancestor constraints described in the
[HTTP cookie draft](https://httpwg.org/http-extensions/draft-ietf-httpbis-rfc6265bis.html),
while nonce/hash styling follows [CSP3](https://www.w3.org/TR/CSP3/). This standards
review is not real-browser qualification. Actual Telegram Web/native WebView, srcdoc,
nonce, mobile layout and download behavior are NOT RUN here and remain release gates.

Public GET /p/<UUID> serves only the prepared active, unexpired revision for an unbanned
owner, without Telegram auth or AI calls. PNG/SVG QR and PNG share-card attachment paths
repeat the same visibility checks. All responses use no-store and no-referrer; public
HTML retains its exact CSS-hash CSP, forbids scripts and framing, and is initially marked
noindex/nofollow/noarchive. No content cache bypasses deletion, suspension or expiry.
Public GETs share a Redis global cap of 120 requests per minute across API
processes, with fail-closed Redis errors; private owner POSTs retain the user rate gate.
Native rendering has two slots per process,
no queue; cancelled HTTP work holds its slot until its shielded native task finishes.
These are initial resource bounds, not measured load/availability qualification.

Before activation: migrate through 0014; preserve the existing Mini App edge and verify
HTTPS proxy routing for /p/ and the existing Mini App API; qualify nonce/sandbox behavior
in real Telegram/mobile browsers; exercise owner stop and cross-tenant denial; retain
compatible immutable rendering or durable export assets through upgrades; verify backups
and restore; agree creation/hosting/renewal/revision terms and connect metered generation
to a completed eligible order. No VPS, Caddy, provider, billing or live service change
was performed in this implementation round.
