# Optional source-bound Word and PDF improvement

## Authority and baseline

Owner continuation authorizes improving existing services with AI where useful.
Baseline main `9f22e979338fb9ea23e6a54e496610f808908ff3` (#77). Operator output
confirms this deployment, CV v5, PPTX v3, healthy core containers, zero unfinished
orders before deployment and provider pause retained. Backup reported at
`/home/aidev/telegram-service-safety-1eNIYZCg`. No direct server access here.

## Implemented contract

- Word/PDF service v2 has an explicit optional direct/smart mode. Skip and omitted
  mode preserve literal text; existing programmatic direct callers remain compatible.
- Direct retains the same renderer/result path, 12,000-character intake, no AI/cost
  holds and optional title. Smart accepts 9,000 characters, 80 nonempty source lines,
  at most 4,000 characters per line. These limits are disclosed and checked before
  reservation; source is entered once, not repeated or translated.
- Smart source IDs must occur exactly once in original order across proposed sections.
  Numeric/email/URL occurrence counters must match within EACH ID. Supplied titles
  stay verbatim; generated titles/headings cannot add/repeat numeric/contact tokens.
  Output is bounded to 18,000 characters. Injected responses are revalidated before
  renderer/storage use. Blank-line layout is editable in smart mode, literal in direct.
- AI chooses three existing typed Word designs, density, section labels and ordered
  paragraph/bullet/lead blocks. No arbitrary code, HTML, fonts, images, coordinates,
  generated tables, free translation or invented claims are allowed by the contract.
- Shared bounded creation/content review, one repair, recorded usage, prepared visual
  approval, retry/replay and settlement controls are reused without service branches.
  Numeric/source-ID checks do not prove names, meaning, negation or factual association;
  semantic review and actual customer acceptance remain necessary.

## Generic Word correction

Visual inspection found long email identifiers overpowering the script-direction
heuristic in short Arabic prose. Shared Word formatting now excludes recognized
dates/ASCII email/URLs when selecting paragraph direction, splits inline identifiers
into LTR runs and adds portable LTR formatting marks in the existing professional
formatting path. Named-style bullets use the same prose direction. Literal character
content is retained (invisible formatting marks are not source edits). Internationalized
email and arbitrary mixed-script/URL edge cases are not universally certified.

## Evidence and remaining checks

- PASS LOCALLY: 89 focused service/source-policy/architecture/template/native-render
  cases; global lint, format and diff checks. No production DB tests run locally.
- PASS VISUAL: all six final one-page Word/PDF fixtures, Arabic/English in modern,
  classic and editorial. Rendered after the final inline-direction correction; dates,
  leading zeros, amount, phone/email and negative/conditional prose remain present.
  Fixtures are hand-authored model-shaped responses, NOT real AI/provider output.
- Added hosted lifecycle checks for reviewed usage, numeric repair/failure, paused-AI
  versus direct availability, visual approval, prepared delivery retry, invalid-source
  pre-admission and version upgrades retaining administrator prices/gates.
- Added a native non-root, network-disabled worker gate for all six smart designs.
  Full hosted CI qualification required before merge.

No prices, gates, migrations, dependencies, provider pause or historic unknown costs
changed. Live provider quality, mobile acceptance, new deployment and invoice
reconciliation are NOT RUN. This adds selective AI to one service, not a blanket toggle.
