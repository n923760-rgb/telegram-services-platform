PDF = """Turn the customer's supplied text into a professional PDF document.
Support Arabic and English. Preserve supplied names, dates, numbers and factual statements.
Choose clear sections and headings. Do not invent facts.
Preserve every numeric token and email/URL verbatim with the same occurrence count across
the complete visible document, including titles, headings, paragraphs, bullets and table cells.
Do not duplicate body values in headings or summaries; do not generate numeric list labels.
Keep signs, leading zeros, separators, date notation, percent signs and decimal precision.
Set missing_information=true only if essential source facts are absent and completing
the requested task would require inventing facts. Short notes, a few supplied records,
an omitted title or the absence of a requested introduction/conclusion are not missing
information. Format the supplied facts as a concise document without filling gaps.
Set ambiguous=true only when materially different interpretations exist; propose a sensible
structure and put a short Arabic clarification in question. Otherwise fulfill directly.
Provide only the requested schema."""
