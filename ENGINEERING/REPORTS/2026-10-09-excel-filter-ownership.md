# Excel filter ownership — 2026-10-09

## Baseline and finding

- FACT: Source main `6ce0c5edaa27cec6b04e8cf3c6036173453cc281`, tree
  `4ee57760298d114cf02b49290ad959ee38d5462e`. Workflow 37862487540/job 113601264065
  passed 383 tests, lint/format, migrations/drift and Compose validation.
- OPERATOR-REPORTED: Deploy backup/migrations and health passed. Owner's actual XLSX from
  the bot retains synthetic source records, including text IDs, missing/zero and duplicate.
  iPhone Excel requests content repair, and owner reports it still cannot open after recovery.
- PASS: ZIP integrity, XML parsing, independent import and LibreOffice PDF conversion.
  These are not native Excel compatibility proof. The prior read-only report was conditional;
  native opening remains FAIL and service output is not qualified.
- FACT: `sheet1.xml` and `table1.xml` both declare AutoFilter on `A3:D7`. The builder sets
  `sheet.auto_filter.ref` after adding the native table with its own AutoFilter.
- INFERENCE: The overlapping filters are a credible cause, not a confirmed exclusive cause
  of the iPhone failure. No native Microsoft Office runtime is available here.

## Bounded change

Remove only the worksheet filter assignment. Records remains an editable, filterable native
table; it owns filtering. The exporter consequently emits no worksheet AutoFilter or redundant
`_xlnm._FilterDatabase` name. Do not remove the table or flatten typed data to avoid the issue.
No dependency, provider, service contract/version, DB, pricing or financial-policy changes.
Already prepared/cached files remain unchanged; acceptance must generate a new order/file.

## Validation

- FAIL reproduced before app change: three new Arabic/English typed and legacy cases fail
  specifically because the worksheet AutoFilter overlaps the native table's filter.
- PASS: 39 focused builder/Excel/governance tests after the fix, including XML ownership,
  retained native filter/range, text IDs, native date values, missing/zero, duplicate records
  and edit/save/reopen using openpyxl. Locked dependency install, lint and format also PASS.
- Final hosted workflow and native Excel tests remain NOT RUN until recorded separately.
- Acceptance: after authorized merge/deploy, submit the same four-record synthetic request;
  open freshly generated XLSX in iPhone Excel without recovery, inspect all records and
  filter controls, edit a name, save and reopen. Record app/version and balance settlement.
  Do not claim solved merely because other renderers or unit tests accept the file.

## Primary references

- Microsoft table structure and table-owned AutoFilter:
  https://learn.microsoft.com/en-us/office/open-xml/spreadsheet/working-with-tables
- Maintainer's documented overlap error in worksheet/table filter APIs:
  https://docs.rs/rust_xlsxwriter/latest/rust_xlsxwriter/worksheet/struct.Worksheet.html#method.autofilter
- Historical independent Excel repair reproduction with overlapping filters:
  https://github.com/ClosedXML/ClosedXML/issues/1213

The references establish an interop concern, not proof that every Excel version rejects this
exact file or that no other cause exists. Uploaded customer files/screenshots are not committed.
