# PDF to Word header-derived title

FACT: operator acceptance on f9a3246 passed the English table case, but the
uploaded result adds a large "ID Amount Note" title above the identical headers.
Cells, leading zeros, amount spelling and settled accounting were preserved.

CHANGE: PDF-to-Word v9 suppresses the visible document title only when it exactly
joins one table's headers, the entire extracted source matches that table's
headers/cells in order after whitespace normalization, and no surrounding prose,
caption, heading, page break, alternate layout or protected title literal exists.
Keep the reviewed plan immutable and use the existing builder include_title option.
Source validation, AI review/repair bounds, cell content and price are unchanged.
Ambiguous input retains its title; this deliberately does not claim to solve all
unnecessary-heading cases or reconstruct source geometry.

PASS locally: 45 focused header-title, existing opening-title, service and governance
tests; repository lint and formatting. Include English/Arabic headers, exact native
editable cells, distinct/ambiguous source titles, protected literals and a service
regression using the acceptance PDF without another AI extraction call.
Full DB upgrade/lifecycle and built-worker hosted CI: pending.
Live v9 provider qualification and PowerPoint/Word mobile editing: NOT RUN.
Production rollout: NOT RUN. The existing v8 acceptance is not v9 evidence.
