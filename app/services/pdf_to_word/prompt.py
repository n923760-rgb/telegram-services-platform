PDF_TO_WORD = """Reconstruct the text extracted from the customer's PDF as a professional editable Word document.
Preserve every supplied name, date, number, factual statement and meaningful section. Do not invent facts.
Preserve numeric tokens and email/URL tokens verbatim, including signs, separators, leading zeros,
date notation, percent signs and occurrence counts across the title, headings, paragraphs and bullets.
Do not add numbered lists, duplicate a date/number in a title or normalize a contact address.
The injected [Page N] markers are navigation metadata, not source content: do not copy their numbers.
Numbers actually present in the extracted page content, including footers, must be retained.
Repair only obvious extraction artifacts such as broken line wrapping. Keep the original language.
Infer headings and bullet lists conservatively. This is conversion, not new document authoring.
The supplied extracted text is the complete input: sparse tables, isolated identifiers,
short notes and partial sentences are valid content to preserve as supplied. No additional
customer context is required. Do not infer absent names, units, values or explanations.
For table-only extraction, retain every supplied cell value as text in the supplied order.
Always return the editable document and keep missing_information=false. Unreadable/image-only
PDFs are handled before this planning step. Return only the requested schema."""
