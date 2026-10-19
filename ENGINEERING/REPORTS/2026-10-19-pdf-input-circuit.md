# PDF input rejections must not pause a healthy service

## Finding and scope

- FACT: Official main `25de614df94f3163de362cd1267938c1b0e72cc9` contains #109,
  qualified by 2408 tests and 30 non-root offline worker checks. Its tree is
  `355692f33c789fdfb53f4837086ea1d7d5d6fbd6`.
- FACT FROM SOURCE: Circuit evaluation excludes a small explicit set of input errors,
  including the new PDF-to-Word form rejection. Six other explicit PDF input errors
  enter its failed-job samples: `pdf_image_content`, `pdf_text_unreadable`,
  `pdf_text_too_long`, `pdf_tools_form`, `pdf_tools_limit`, `pdf_page_selection`.
- INFERENCE: Enough such rejected uploads/selections can pause an otherwise healthy
  service, cancel queued work and emit failure alerts. No production incident or
  baseline PostgreSQL reproduction is claimed; PostgreSQL is unavailable locally.

## Change

- Add only those six codes to the existing circuit input exclusion list. The SQL
  predicate still filters before the sample-window limit, preserving older genuine
  failure samples when newer unsupported inputs arrive.
- Keep generic `file_invalid` counted because its existing producers can include
  ambiguous processing/storage failures. Keep unknown errors, `service_failed` and
  `provider_invalid` counted. No broad prefix or service-name exclusion.
- No plugin contract/version, output format, input schema, price, activation, AI
  allowance, dependency, migration, configuration or ledger mechanics change.
- Disabled services are not re-enabled. Provider pause and circuit reset/threshold
  settings retain their existing meaning. No server action; deployment remains deferred.

## Verification

- PASS LOCALLY: Three architecture gates, global Ruff lint/format and diff whitespace.
  Collection succeeds for all 55 tests in the touched operational/PDF flow modules.
  Collection is not database test execution.
- Hosted PostgreSQL coverage extends the existing six-rejection/no-alert regression
  to all six new keys. Also assert that the service remains enabled, rejected orders
  have no reserved funds, and a healthy queued order retains its reservation/status.
- Three new mixed-window cases use genuine `service_failed`, `provider_invalid` and
  ambiguous `file_invalid` failures, followed by six newer excluded PDF rejections.
  A five-sample window must still open the circuit, alert and cancel/release queued work.
- Existing actual PDF utilities failure flows for forms and missing pages additionally
  evaluate the circuit with one-sample/one-alert thresholds. They must preserve service
  availability and produce no circuit/failure notification, alongside existing release,
  single customer error, zero-provider and cleanup assertions.
- NOT RUN LOCALLY: PostgreSQL/Redis execution, migrations, Docker worker image.
  Full workflow and offline non-root worker qualification are required before merge.

## Limits

- This corrects six explicit input codes, not all file failures or all services' error
  taxonomy. Runtime activity, actual provider quality and mobile output acceptance are
  separate from this source change. Historical audit rows are not rewritten.
