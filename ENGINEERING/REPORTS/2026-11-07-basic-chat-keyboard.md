# Basic chat controls with Mini App services

- User decision: retain persistent basic chat buttons; keep service categories/intake in Mini App.
- Change: app-mode keyboard has orders, balance (payments in Stars mode), support and help; administrators also see their existing admin control.
- Welcome remains one message with an authenticated inline app launch and optional draft resume. Do not use simple reply-keyboard WebApp launches.
- Existing catalog callbacks still route to Mini App. Legacy navigation remains when Mini App intake is unavailable.
- PASS locally: 51 navigation/configuration tests, repository lint and formatting checks.
- NOT RUN locally: PostgreSQL-backed navigation journeys; hosted CI and real Telegram keyboard/mobile checks remain required before deployment.
- No runtime changes in this round. Preserve the production Mini App URL override during deployment.
