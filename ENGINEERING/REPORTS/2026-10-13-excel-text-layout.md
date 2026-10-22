# Excel proportional-font layout

## Authority and evidence

Owner accepted continuing development after the extended PDF-table trial.
Baseline main d188667. The supplied workbook preserves the complete telephone
and email strings, but the LibreOffice print preview wraps them in a 22-point
row: character-count column sizing underestimated the rendered DejaVu text.
This is a layout defect; no missing source data was observed.

## Change

- Shared Excel builder sets body/header font size explicitly to 11 points.
  Existing Pillow measures the installed DejaVu regular/bold font, using the
  longest explicit line instead of summed multiline lengths.
- Column sizing and row/title/header wrapping estimates use font measurements,
  a conservative margin and existing width/height bounds. Bold headings and
  the 18-point title use their own metrics.
- Only three font objects are cached; no customer text is cached. Missing fonts
  retain an approximate fallback for non-Docker callers. Production images
  already install DejaVu; no package/configuration/container change is required.
- Same cells, types, number formats, tables, references, ordering, formula
  protections, prices, gates and service versions. Previously saved artifacts
  retain their original formatting and are not regenerated.

## Checks

- PASS locally: 136 Excel/CSV/PDF-table/Arabic/architecture cases, global
  ruff lint/format and diff checks. Added proportional-glyph, bounded multiline,
  literal contact and missing-font compatibility regression coverage.
- PASS locally: rebuilt the actual supplied five-sheet extraction. Every
  worksheet's values match the supplied workbook exactly. LibreOffice PDF
  previews inspected for all five sheets; telephone/email now fit completely
  on one line in Data2 and Source2.
- Full exact-source PostgreSQL/Redis/native CI required before merge.
- Server deployment/repeated Telegram export NOT RUN for this change.

## Limits

Layout estimates depend on rendering/font substitution. Existing 60-column-unit
and 409-point limits remain; no universal native-Excel/mobile/print guarantee.
This does not expand Arabic mixed-cell recovery, reinterpret values or add
automatic calculations. Provider pause and historical uncertain cost exposure
remain unchanged.
