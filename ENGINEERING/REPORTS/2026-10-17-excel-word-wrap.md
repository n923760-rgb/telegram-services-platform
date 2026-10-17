# Excel whole-word row sizing

Baseline: official main f056e92cb77d12d13badd784ef2a11ddace35396. Owner authorizes continued development, tested merging and deployment. Unrelated governance PR #21 remains untouched.

## Problem and change

The shared Excel renderer estimated wrapping as the ceiling of total text width divided by column width. Six words each wider than half a column require six native lines, although their summed width can predict fewer lines. Fixed row heights based on that estimate can hide text.

The measurement now places whole words before splitting overlong unbroken values and preserves explicit newline/blank-line counts. Per-call repeated-token measurements avoid repeated font work without retaining customer text in a process-wide cache. Existing font fallback, width bounds and 409-point height ceiling remain. No content, cell type, numeric precision, source quote, table filter or sorting change.

## Evidence and limits

41 focused pure/native-readback wrapping and source tests pass; global Ruff check and format check pass. Three architecture gates and diff checks pass. Regression fixtures include Arabic and English words that fit individually but cannot share a line, explicit blank lines, long unbroken identifiers, font fallback, exact text and capped extreme heights. Hosted full database/lifecycle/native worker checks are required before merge.

Native workbook XML/readback and measured geometry are not a visual review in Microsoft Excel, LibreOffice or a mobile app. Native applications can substitute fonts. Text exceeding the maximum row height remains stored in full and may still require expanding the formula bar. No new visual or live-provider certification is claimed.

No service contract/version, AI request, retry/cap, price/activation, financial, dependency or migration change. Existing prepared results remain reusable. Deployment requires the operator's existing Termius path; no direct server access is available in this session.
