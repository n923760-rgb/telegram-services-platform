# Commercial service expansion

Status: implementation specification, not an implemented/qualified service.
Owner requested Saudi e-invoicing and useful everyday business documents.
Research checked official ZATCA material on 2026-10-26. No merchant wave,
VAT registration or authority-to-issue evidence is available for a customer yet.

## Prioritized customer outcomes

| Order | Outcome | Proposed output | Deterministic behavior and boundary |
| --- | --- | --- | --- |
| 1 | Quotation | Arabic/English PDF and editable Word | Seller/customer, dated validity, line quantities/prices, exact Decimal totals; no invented goods or commitments. Clearly a quotation, not a tax invoice. |
| 2 | Pro forma invoice | PDF/Word | Explicit pro forma status; preserve merchant/customer data and terms. Never claim tax issuance or payment confirmation. |
| 3 | Receipt/payment voucher | PDF/Word | Record user-supplied payment evidence/reference and partial/balance amounts; document generation is not bank payment verification. |
| 4 | Account statement | Excel/PDF | Imported opening balance and dated debit/credit entries; reconcile every row and closing balance; never read platform wallet as merchant books. |
| 5 | Delivery note/purchase order | PDF/Word | Ordered/delivered quantities and optional signature area; no fabricated signatures or confirmation of actual receipt. |
| 6 | Saudi tax invoicing | Structured invoice plus readable copy | Separate merchant issuance system with compliance and integration gates below. |

Priorities are an engineering recommendation from reuse and risk, not verified
market-demand research. Reuse trusted builders and plugin discovery, default off;
retain administrator-owned pricing and avoid service-specific wallet/core branches.
Do not use AI for tax totals, identifiers, payment proof or compliance decisions.
AI may assist optional descriptive text only after explicit source review.

## Saudi invoicing requirements and architecture

Official sources:
- https://zatca.gov.sa/ar/E-Invoicing/Pages/default.aspx
- https://zatca.gov.sa/en/E-Invoicing/Introduction/Guidelines/Documents/E-Invoicing_Detailed__Guideline.pdf
- https://zatca.gov.sa/ar/E-Invoicing/Introduction/Guidelines/Documents/E-Invoicing%20Simplified%20Guideline.pdf

The detailed guide distinguishes Phase 1 generation by a compliant solution from
Phase 2 integration. Phase 1 does not prescribe XML/PDF-A3 as the sole format;
therefore format alone establishes neither compliance nor noncompliance. Phase 2
uses structured XML and prescribed security/integration processes. Standard tax
invoices normally require clearance before sharing; simplified invoices require
reporting within 24 hours. Exceptions/outages require their own reviewed handling.
The precise current XML/security/data dictionary releases must be pinned and
validated at implementation, not inferred from this high-level specification.

Required work packages before any compliant-service claim:
1. Merchant account and role isolation: VAT status, seller/address details,
   applicable phase/type and authorization to issue for that merchant. Telegram
   identity alone is not tax identity or proof of authority to issue invoices.
2. Exact calculations: Decimal units, quantities, discounts, tax categories,
   rounding and inclusive/exclusive prices with independently reconciled totals;
   do not assume all supplies are taxable at one rate or all customers VAT registered.
3. Persistent invoice model: atomic merchant-scoped numbering, immutable issued
   document/evidence, idempotent issuance, separate draft/issued/cleared/reported
   states, linked credit/debit notes instead of editing/deleting issued invoices.
4. Retention architecture: regulatory archive and restore/access audit independent
   of ordinary TTL deletion of service files and order content. The current file
   lifecycle cannot silently become the legal invoice record store. Determine
   applicable legal retention/location requirements before implementing storage.
5. Phase 2: authorized device/unit onboarding and CSID/private key lifecycle,
   prescribed XML/schema/business-rule validation, cryptographic stamp/hash/QR,
   clearance/reporting integration with durable retries and unknown-outcome
   reconciliation. Never resend a newly numbered invoice for an ambiguous response.
6. Qualification: official validation tooling and sandbox cases; standard/simplified,
   notes, concurrent numbering, totals/rounding, duplicate requests, timeouts,
   expired credentials, tenant crossing, restore and archive immutability. Follow
   applicable ZATCA production onboarding and verify merchant-specific readiness.

A third-party compliant invoicing provider is a valid architectural option subject
to connector capability, merchant authorization and data/retention review; do not
pick a vendor or claim certification before evaluating those requirements.

## Scope and commercial activation

Separate customer checkout for buying a bot service from merchant invoicing for
that customer's business. Platform Stars/test-credit ledgers remain unchanged.
No tax feature, price or customer menu is activated by this specification. Start
commercial documents as bounded plugins only with clear input contracts, visual
fixtures and normal failure-release tests. Tax invoice issuance needs the generic
merchant/archive foundation; propose and review that foundation rather than placing
one-off database/network policy into a document service.
