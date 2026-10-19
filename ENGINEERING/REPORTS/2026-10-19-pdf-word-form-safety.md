# PDF-to-Word: reject unsupported form/signature declarations

## Baseline and reproduced finding

- FACT: Official main `ababfbdb25591d9a4bc49d1d7c2b63aa553c3e44` contains #108;
  qualified tree `5729b099f7e1174d0e517b8b4c7d5d63fbde56d4`.
- FACT: PDF-to-Word v4 rejects images/scans and validates extracted source tokens,
  but does not inspect interactive field values or signature declarations.
- FAIL REPRODUCED: A real ReportLab text field contains `Account 00999` in `/V`,
  absent from pypdf page text. The original service accepts conversion without that
  value. A new rejection test fails with DID NOT RAISE; the source fixture check passes.

## Bounded implementation

- PDF-to-Word v5 rejects catalog `/AcroForm` or `/Perms` declarations (including an
  empty declaration), and page `/Widget` annotations even without a catalog form.
  Checks run before AI generation and builder/storage output; malformed inspected
  annotation structures use the existing `file_invalid` safe failure.
- Arabic/English intake and `pdf_word_form` explain unsupported fields/signatures,
  request a static text-based copy, and make no signature-authenticity promise.
- Classify the new `pdf_word_form` rejection as customer input in the existing circuit
  exclusion list. It must not pause the service or trigger failure alerts; this does
  not change classification of any existing error or genuine provider failure.
- Ordinary PDF links and reusable text-only Form XObjects remain supported. A Form
  XObject is a drawing resource, distinct from an AcroForm interactive field.
- No new service, dependency, AI stage, schema fields, migration, financial policy,
  price/activation change or production configuration. Same byte/page/text limits,
  image guards, source-token validation and native editable Word builder.
- Existing upgrade guards release/cancel unprepared older work; already-prepared
  historical v3/v4 output replays without regeneration. Administrator prices remain.

## Verification

- PASS LOCALLY: 68 focused tests: 15 new fixture/rejection/link/malformed/i18n cases
  and 53 existing PDF service/extraction/image/source-fidelity regressions. The latter
  pure modules use `--noconftest` locally because PostgreSQL is unavailable; hosted
  full-suite database fixtures remain unchanged.
- New native fixtures exercise catalog forms, direct/indirect-subtype orphan widgets, permission/signature
  declarations and empty forms, on first/later pages. Permission fixtures are synthetic
  declarations, not cryptographically valid signed documents.
- PASS LOCALLY: Three architecture gates, global Ruff lint/format/diff, workflow YAML
  parsing and embedded worker Python compilation.
- Hosted DB tests add five zero-provider-cost rejection flows: single release, no
  capture or CostUsage, one error notification and file cleanup. Extend v4 pending
  upgrade/admin overrides and v3/v4 cached retry with Word regeneration forbidden.
- Extend the existing circuit regression with six synthetic form-input failures and
  assert no circuit opening or failure alert. Retain genuine-failure circuit tests.
- A local adversarial review after publication also reproduced an orphan Widget whose
  Subtype is an indirect PDF name reference bypassing `.get()` comparison. Resolve
  Subtype through pypdf dictionary indexing instead; add first/later-page regressions,
  hosted settlement and native worker coverage. Qualify the corrected head, not the
  earlier publication, before merge.
- Offline non-root worker adds actual injected service rejection of five PDF fixtures,
  verifying no provider call or new artifact. Full exact-head hosted tests, migrations,
  drift, Compose and worker image checks are required before merge.

## Limits and deployment

- This is conservative rejection, not form flattening, field reconstruction or digital
  signature verification. Empty form declarations are intentionally unsupported.
- Other annotations, links, outlines, original layout and arbitrary PDF semantics are
  not reconstructed or newly certified. Previously prepared output is not rewritten.
- NOT RUN: Real provider, Telegram/mobile/Word visual acceptance or server deployment.
  Owner requests one later production deployment after improvements; no server action.
