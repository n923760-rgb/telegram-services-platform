# Explicit Word content choice

Baseline: official main eeb33c1879dc5437a3d283974933c3a292f7fb9a, reverified against GitHub. Owner requests continued development in GitHub under the approved service-quality plan. Existing open governance adoption PR #21 is outside this change.

## Finding and change

FACT: Office v7 intake asked for text and then file type. Direct Word required a documented first-line phrase; otherwise it implicitly requested smart organization. This hid a meaningful content choice in customer prose.

Office v8 asks for file type first. Word then requires a localized choice: preserve text as written, or improve wording/organization with AI. Content comes last. Excel skips this Word-only question and retains its existing source-bound AI planning. Both Word options retain the same administrator-owned service price.

Explicit direct requests preserve every line, including text that happens to match the old directive. Explicit smart selection also overrides that phrase. The unchanged internal parser still understands legacy requests without a mode; the public v8 intake requires a choice. No new runtime mode inference is added.

## Compatibility and boundaries

The contract bump uses existing snapshot/version guards. Old drafts cannot silently submit a different contract; changed queued jobs follow the existing cancellation/release policy. Upgrade tests include v7 and retained administrator activation/prices. Stored completed results and historical financial data are not rewritten. Do not roll out with unfinished orders; operational deployment checks remain required.

No changes to bot/core policy, rendering, source fidelity checks, financial/provider safeguards, dependencies or migrations. No service merge, price/gate mutation, production deployment or unpause. This is a clearer intake, not a new document design or proof of semantic quality.

## Verification

PASS LOCALLY: 104 focused pure Office mode, complete source-fidelity, portfolio AI-policy and acceptance tests. Existing Office service tests, lint/format/diff and architecture checks are recorded in the PR. Checks verify required choices, conditional Excel intake, literal whitespace/blank lines/identifiers, explicit-choice precedence, legacy internal parsing and absence of direct AI calls.

Updated hosted flows exercise Arabic/English real dispatcher journeys, language switching, failed prompt recovery, direct no-provider/no-cost execution and exactly-once capture, provider-disabled admission, invalid mode rejection before reservation, and v7 snapshot upgrade/cancellation/release. Full hosted workflow is required before merge; local PostgreSQL is unavailable. New live provider/Telegram/mobile-output acceptance NOT RUN.

## Next

Build all relevant images and use normal paused/zero-unfinished-order deployment checks before a runtime upgrade. Test both Word choices and Excel in Telegram. Continue the separate live CV/provider matrix from #90. Broader Word/PDF entry consolidation still requires a clear price/contract transition; current service slugs remain independent.
