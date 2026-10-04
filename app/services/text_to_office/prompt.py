WORD = """Turn the customer's supplied text into a structured Word document.
Preserve supplied names, dates, numbers and factual statements. Choose clear sections.
Do not invent facts. Set missing_information=true if essential source facts are absent;
empty placeholders are allowed only if the customer explicitly asks for a reusable template.
Set ambiguous=true only when materially different interpretations exist, propose a sensible
structure, and put a short Arabic clarification in question. Do not ask confirmation for
an ordinary clear request. Provide only the requested schema."""
EXCEL = """Turn the customer's supplied text into a rectangular table for Excel.
Preserve names, identifiers, leading zeros, dates, units and values. Use actual numbers only
when they are numbers, not phone numbers or identifiers. Never generate formulas, macros,
external links, unsupported totals or invented rows. Set missing_information=true if essential
source data is absent. Empty template cells are allowed only when explicitly requested.
Set ambiguous=true only for materially different interpretations; propose a structure and
put a short Arabic clarification in question. Otherwise fulfill directly."""
