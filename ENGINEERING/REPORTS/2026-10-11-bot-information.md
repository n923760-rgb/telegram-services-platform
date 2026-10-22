# Bot information and Stars navigation — 2026-10-11

Owner authorized AI-supported bot information and Stars checkout. The owner-set
prices/admin panel are preserved. Pending unrelated quality work is not overwritten.

## FACT: behavior

Localized descriptions explain supported outcomes without accuracy guarantees.
Only configured admins can invoke `/syncprofile`; startup never writes metadata.
Default Arabic plus ar/en descriptions/short descriptions need six idempotent API
calls. Failure may be partial; users see a safe retry message, not raw API bodies.

Stars-mode welcome/help and Payments page explain direct checkout per service.
No test balance query in this page, no conversion/top-up or payment activation.
Old menu callbacks/message labels remain valid; customer draft and admin button
are preserved. Test-credit mode remains available separately.

## Verification

PASS local: four pure cases for six description writes/limits, failed response,
payment label compatibility and distinct admin button. Added actual dispatcher
fixtures for Stars page/draft/help plus profile authorization/success/API failure.
Full hosted lifecycle/native gates required before merge. No real Telegram writes,
mobile/VPS/purchase/refund acceptance performed here.
