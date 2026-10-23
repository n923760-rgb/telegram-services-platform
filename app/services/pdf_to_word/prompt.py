PDF_TO_WORD = """Reconstruct the text extracted from the customer's PDF as a professional editable Word document.
Preserve every supplied name, date, number, factual statement and meaningful section. Do not invent facts.
Preserve numeric tokens and email/URL tokens verbatim, including signs, separators, leading zeros,
date notation, percent signs and occurrence counts across all visible text, including table captions,
column headings and cells. Every cell is literal text: retain leading zeros and decimal spelling.
Do not add numbered lists, duplicate a date/number in a title or normalize a contact address.
The injected [Page N] markers are navigation metadata, not source content: do not copy their numbers.
Numbers actually present in the extracted page content, including footers, must be retained.
Repair only obvious extraction artifacts such as broken line wrapping. Keep the original language.
Infer headings and bullet lists conservatively. This is conversion, not new document authoring.
The supplied extracted text is the complete input: sparse tables, isolated identifiers,
short notes and partial sentences are valid content to preserve as supplied. No additional
customer context is required. Do not infer absent names, units, values or explanations.
When the extracted content clearly identifies column headings and corresponding rows, reconstruct
it as an editable table using section.tables, not a bullet list. Preserve row order, column order,
cell associations and empty cells. Do not repeat table content in paragraphs or headings.
Use only supplied column headings; do not invent headers, captions, totals or missing cells.
Keep surrounding prose in separate sections in source order. Tables are bounded to 6 columns,
100 data rows, 240 characters per cell and 10 tables per document. If the extracted structure is
ambiguous or exceeds these bounds, preserve its complete text in paragraphs instead of guessing,
truncating or claiming to reproduce the original page layout. Scanned tables remain unsupported.
Always return the editable document and keep missing_information=false. Unreadable/image-only
PDFs are handled before this planning step. Return only the requested schema."""
