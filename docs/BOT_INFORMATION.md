# Customer bot information and Stars navigation

Welcome text and descriptions identify Yusr as digital services supported by AI
and specialized tools. They do not guarantee perfect accuracy or claim every
mechanical operation calls AI. Available services remain controlled by registry
and owner activation/prices.

Configured administrators can run `/syncprofile` after deployment to write the
Telegram bot description and short description for default Arabic, Arabic and
English. It is never executed automatically on startup. Six writes are needed;
Telegram offers no transaction for them. Failure may leave partial updates, and
retrying the command is idempotent. Errors show a safe localized message.

When STARS_ENABLED is already configured, menus show Payments instead of My balance.
The payment page explains direct Stars checkout per order, the invoice after price
review and /paysupport. It does not query/display SAR test credit in this mode.
Legacy menu callbacks and both old/new message labels remain recognized. Test
mode retains the independent credit interface. Administrator home button is kept.

No Stars activation, terms, prices, conversion, top-up wallet or payment-policy
changes are included. Existing docs/STARS_ACCEPTANCE.md prerequisites apply.
Real Telegram profile/mobile acceptance and production deployment are not established
by mocked Bot API sessions.
