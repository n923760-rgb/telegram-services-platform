# Portfolio acceptance: complete deliverables and source order

Baseline: main `272c511d5c1b00cb7c4496ade0f2aeb398209710`, after merged PDF conversion/image clarification #120.

The prior acceptance checker required a nonempty package of individually valid files. It
did not guarantee that a CV or Word/PDF order actually included both files, that editing
included its change report and chat response, or that every other promised artifact existed.
The PDF merge fixture supplied the same PDF twice, making reversal unobservable. The image
PDF fixture checked page count but could accept wrong source pixels.

This round changes isolated synthetic qualification only:

- Declare the complete expected filename set for all 29 existing cases, covering all 16
  public services. Validate it before writing output files. Include chat text as response.txt
  only where the synthetic service contract requires it; previews are not chat results.
- Make the second merge source distinct and check known source literals on each page.
- Bind each selected images-to-PDF page to the corresponding generated source's decoded RGB
  dimensions and pixel signature. Reject missing/duplicate/reordered/changed embedded images.
- Keep case selection/count, whole-run call/cost budgets, test DB isolation, ledger handling,
  financial cleanup, production provider pause and source service versions unchanged.

Before-fix source execution reproduces acceptance of reversed distinct PDF pages and wrong
image pixels. Regression tests also reject missing native Word/PDF companions, required
text/change reports, unexpected outputs, duplicate/blank pages and even a one-pixel image
change. Correct native examples still pass.

Local: 68 acceptance/output/delivery checks pass, plus three architecture gates and global
lint/format/diff. Ten PostgreSQL acceptance cases are collected but cannot run locally;
source-bound hosted CI must check single capture on four correct native cases and one release
with no capture or outbound call for deliberately invalid package/image/PDF-order contracts.

No live provider, production deployment or human visual approval is implied. Embedded source
pixel retention does not prove the image was positioned visibly on the page. Page-local token
checks do not prove full PDF content/layout or reading order. Package completeness does not
prove text meaning, quality of prose, CV usefulness or accurate translation. Those remain the
per-service acceptance matrix and actual saved-file review on Office/mobile.

After the source and worker are updated, use the existing isolated `scripts/service-acceptance.sh`
procedure. Preserve its exact source SHA, report and generated files. Do not compare a new
ops checker against an older worker and label that the current product qualified.
