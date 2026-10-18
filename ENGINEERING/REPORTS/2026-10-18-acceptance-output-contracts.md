# Acceptance output contracts — 2026-10-18

## Baseline and scope

FACT: Official main 9fd8e67baba7a5564447e297c9b79bfea4440f8d includes #104.
Owner authorizes continued improvements and tested merges, with production deployment
deferred to one later batch. This bounded task strengthens the isolated synthetic
acceptance harness rather than adding another customer feature.

The former inspector accepted any nonempty PPTX and PDFs with at least the minimum page
count. It did not assert selected slide counts, exact page counts, page rotation flags or
required workbook sheets. Therefore these structural mistakes could pass that inspector.

## Change

Internal Case fields now optionally declare exact_pdf_pages, pdf_rotations, pptx_slides
and required_sheets. A mismatching inspected artifact raises acceptance_output_invalid.
Rotation tuples cover every page including length; required sheets allow optional extras.
PDF minimum-page policy remains for variable-layout exports such as CV. Existing source
token, formula/hyperlink, format, ownership and byte/hash reporting checks are unchanged.

The plan remains the exact 16-service public portfolio, now 29 cases. It adds only a
provider-free pdf_rotate case. Existing images_pdf uses an explicit reverse order with
exact two-page output; pptx selects three slides with exact-count inspection; minutes
omits the optional title; csv requires Data/Source/Review/Columns. No additional AI case,
call allowance, provider cap, price, activation, customer contract or plugin version change.

## Verification

PASS LOCALLY: 43 focused pure acceptance/output-contract tests, including positive and
negative PDF counts, rotation values/tuple length, PPTX counts, missing/optional workbook
sheets, preserved variable-layout minimum and validation of the full current fixture plan.
Architecture gates, global Ruff lint/format and diff whitespace PASS.

Added hosted DB flows run three selected native cases with the network provider forbidden,
verify report output metadata, zero provider usage/holds/reservations and three captures.
A deliberately missing required sheet must produce REVIEW_REQUIRED, no delivered artifact,
no capture and no stranded reservation. Full exact-head hosted CI including all existing
non-root network-disabled worker gates is required before merge; workflow is unchanged.

NOT RUN: live provider acceptance, production/server work or representative Telegram/mobile
visual acceptance. Local code tests and mocked hosted provider fixtures are not live acceptance.
Isolation, fresh-database and synthetic-owner guards remain mandatory and unchanged.

LIMITS: These declarations check artifacts of matching type, not every artifact filename or
semantic quality. They do not independently certify image order or contents of the Columns
sheet; dedicated native/service tests cover those. Readback is not visual certification.
