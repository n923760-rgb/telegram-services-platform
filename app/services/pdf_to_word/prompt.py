PDF_TO_WORD = """Reconstruct the text extracted from the customer's PDF as a professional editable Word document.
Preserve every supplied name, date, number, factual statement and meaningful section. Do not invent facts.
Preserve numeric tokens and email/URL tokens verbatim, including signs, separators, leading zeros,
date notation, percent signs and occurrence counts across the title, headings, paragraphs and bullets.
Do not add numbered lists, duplicate a date/number in a title or normalize a contact address.
The injected [Page N] markers are navigation metadata, not source content: do not copy their numbers.
Numbers actually present in the extracted page content, including footers, must be retained.
Repair only obvious extraction artifacts such as broken line wrapping. Keep the original language.
Infer headings and bullet lists conservatively. If the source is too incomplete to reconstruct reliably,
set missing_information=true. Return only the requested schema."""
