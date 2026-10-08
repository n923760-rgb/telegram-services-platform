# PDF-to-Word mixed raster/text fidelity — 2026-10-08

## Authority and baseline

OWNER REQUEST: Merge PDF date PR #18 and continue output quality work.
FACT: #18 merged as `b3deb0136e50f79b17de13389b274caf7514201e`; main workflow
`37829349423`, job `113490326816`, passed 340 tests, lint/format, migrations/drift and
Compose configuration. Actual logs contain one existing ARQ deprecation warning.
No operator runtime was changed. This round proposes a bounded code PR, not deployment.

## Failure reproduced

FAIL: Four synthetic, real PDFs containing both selectable text and raster drawing content
were accepted by the old converter. Raster pixels are not present in its extracted text.
This allows an incomplete editable Word file to be delivered as successful even when
the raster contains a source note/identifier. Existing rejection only caught pages without
extractable text, so hybrid pages and scanned pages with a text/OCR layer bypassed it.

The baseline regression run produced four failures (ordinary image, inline image, image
inside nested PDF Forms, image on a later page) and one passing text-only Form case.

## Bounded correction

Inspect parsed drawing instructions before text extraction/AI. Detect inline images and
invoked image XObjects; follow invoked Form streams using their resource context. Reject
cycles, nesting beyond 16 and traversal beyond 100,000 instructions per page. These are
inspection traversal limits, not a universal PDF parsing/decompression safety guarantee.
Detect without calling image extraction APIs or decoding raster pixels. Text-only Forms
remain supported; an unused image resource does not cause rejection.

Use a distinct localized `pdf_image_content` failure and explain text-only scope during
intake. Conservatively reject any raster drawing instruction, including a logo or clipped/
hidden image; its significance cannot be determined by this service. No image preservation,
OCR, original layout, native tables, vector graphics or annotation reconstruction is added.
AI fidelity for accepted text-only content remains a separate qualification gate.

Version 2 records the narrower accepted-input behavior. Registry synchronization retains
administrator price and enablement. Unprepared old version-1 work is cancelled/released
by the existing runner; cached prepared delivery behavior is unchanged. No generic bot/core,
provider, dependency, database, ledger-policy or default enablement changes.

## Evidence

PASS: Locked install, lint/format and 24 focused helper/plugin/governance tests.
Ten new local cases cover four real hybrid types, text-only Forms, cyclic/deep Forms,
huge declared image dimensions without decoding, unused image resources and instruction limits.
All four previously failing cases pass; blocked inputs call no AI and write no output.
Full suite collects 355 tests (15 new cases including five hosted lifecycle cases).

NOT RUN locally: Full PostgreSQL/Redis suite. Added lifecycle cases prove release/notification
once, no provider/output, cleanup and old-version cancellation with retained admin settings;
inspect actual source-bound hosted logs before merging.
NOT RUN: Live provider/source-fidelity, Microsoft Word qualification and new server deployment.
The rejection change does not alter the Word renderer or claim new visual qualification.

Reference: [pypdf text extraction](https://pypdf.readthedocs.io/en/latest/user/extract-text.html)
and [image handling](https://pypdf.readthedocs.io/en/latest/user/extract-images.html); installed
6.19.0 source was inspected because the image-list API can decode inline images.
Use [service quality gates](../../docs/OUTPUT_QUALITY.md) for remaining acceptance.
