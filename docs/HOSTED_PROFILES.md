# Hosted customer profiles: foundation proposal

Status: internal persistence foundation implemented; customer service and public routes not implemented.
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
