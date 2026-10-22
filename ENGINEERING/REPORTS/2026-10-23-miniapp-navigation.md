# Mini App navigation and review follow-up

## Verified source and authority

Owner continuation request follows the approved Mini App roadmap and service
quality priority. Read live AGENTS.md, project source map and canonical roadmap.
Verified main d905c7e and PR #138 head 1a9972d before this bounded follow-up.
PR #21 governance adoption is separate and is not changed.

## Findings and behavior

FACT: Service cards previously rendered detail directly without state. There was
no in-app back control, language changes discarded detail, and details omitted
price/pause hints. The language control did nothing before overview succeeded,
leaving error/outside notices and navigation labels in Arabic.

CHANGE: Represent selected service as view state. Retain detail on AR/EN change,
show price and pause hints and provide an explicit localized back button. Bind
Telegram BackButton once, show it only in detail, and restore selected category
and keyboard focus on return. Clear detail on bottom-tab navigation. Render
localized chrome/notices before data is available and expose filter selection
through aria-pressed. Keep customer text assigned through textContent.

## Validation

PASS: 24 existing Mini App authentication, assets and optional-launch checks using
a DB-free copied-test harness with the same source, locked dependencies and
pytest --asyncio-mode=auto. No PostgreSQL-backed integration claim.

PASS: Executable jsdom 26.1.0 DOM harness with a synthetic overview and mocked
Telegram WebApp: category selection, detail retention across language change,
both back controls, restored focus/category, price and AI-pause hints, tab reset,
chat close, localized failed-auth/outside notices and unchanged API call count.
jsdom was installed only into a temporary verification directory; no project
dependency or lock changed.

PASS: node --check app/miniapp/app.js, global uv run ruff check .,
uv run ruff format --check . and git diff --check.

BLOCKED: Real browser smoke/visual test: runtime Chromium was absent and browser
download returned invalid archives. DOM tests do not prove layout or actual
Telegram SDK behavior.

FACT: Existing exact-head workflow 39780251917 for 1a9972d was cancelled during
pytest, after lint/format/migration steps passed; drift/Compose/native-worker
checks were skipped. Do not describe that run as passed. A new complete hosted
run is required for the updated PR source.

NOT RUN: Full PostgreSQL suite, real iOS/Android Telegram, screenshots/visual
acceptance, real provider calls, production rollout or financial acceptance.

## Remaining release gates

Output quality issue #124 remains P0. Uploaded summary-only sample is already
reviewed on main and does not requalify all summaries or other services. Formal
Arabic rewriting still needs its isolated real-provider rerun and content review.
Mini App remains a draft, read-only interface pending hosted and mobile checks.
No server, checkout, upload, balance, price, credential or deployment changed.

## Authorized merge preparation and CI correction

Owner explicitly authorizes merging and publishing pending project work on
2026-10-23. Hosted run 39856052973 failed four tests, with 2964 passing:
Mini App serialization accessed nonexistent Service.description_en (two cases),
and an older keyboard test's SimpleNamespace omitted the new miniapp_url (two).
Use the persisted Arabic description as the English-view fallback; translated
service names and interface labels remain available. No column/migration is
introduced. Update the test configuration fixture and add a DB-free regression
that serializes a real mapped Service in both payment modes. Require the
existing owner-scope integration cases and complete hosted checks before merge.

Deployment authorization does not prove server access. This workspace has no
connected VPS installation or SSH configuration; operator execution of the
source-pinned deployment commands remains required. No deployment is claimed.
