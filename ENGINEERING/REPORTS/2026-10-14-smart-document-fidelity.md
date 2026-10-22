# Smart Word and Text PDF source fidelity

Baseline: b2a41b6, merged #79. Owner continuation authorizes existing service quality improvement and selective AI. Last operator-confirmed deployment is #78 (63d2587); #79 deployment remains UNKNOWN.

## FACT: bounded change

Office v7 smart Word and Text PDF v4 use request-local schemas capturing source numeric/contact occurrence counters. All visible document titles, headings, paragraphs and bullets are checked; Word section titles/subtitles/blocks/table captions/headers/cells are included. Renderer/style metadata and clarification questions are excluded. Invalid printable PDF-plan text is also rejected before output.

Numeric spelling is literal: signs, leading zeros, separators, dates, percentages and repetitions cannot be removed, invented or reformatted. Recognized ASCII email and HTTP(S)/www tokens are exact. Source-adjacent Arabic words do not become part of an email token. URLs use a conservative whitespace boundary; trailing URL punctuation must remain verbatim. Unicode mail addresses and arbitrary contact formats are not universally recognized; phone digit tokens are checked by the numeric rule.

The existing gateway receives the schema, allowing its bounded creation repair and semantic review. Returned injected model instances and stored continuations are checked again before file creation/storage. Missing information returns the existing safe error without an output. Missing provider returns provider_config; validation errors expose no source values.

Direct Word/PDF modes bypass AI validation and retain literal behavior. Excel v6 source provenance remains in Office v7. No new dependencies, migrations, service branches in core, price/gate changes, financial policy changes, cost reconciliation or provider unpause.

## PASS locally

103 focused service/source/template/architecture cases. Tests reject changed/removed/repeated values, invented values in every Word text location, altered contacts/dates/precision, injected results and continuations before storage. Request isolation, schema privacy, Unicode digits and missing-provider behavior covered. Existing fixtures now supply the numeric content they expect in output; mobile clarification metadata is separate from document source.

Hosted tests additionally exercise real gateway schema repair plus content review, billable cost recording, one capture/release, failed delivery notification, successful cached confirmation and unchanged direct/registry upgrade behavior against disposable PostgreSQL/Redis. These checks are NOT RUN locally; hosted evidence is recorded in the PR after completion.

The existing non-root, network-disabled native worker gate additionally validates both schemas, native Word/PDF output tokens and rejection of invented values. Renderers/layout were not changed; this round does not claim a new visual design or manual visual certification.

## LIMITS / UNKNOWN

Counter equality across the whole document does not prove names, meaning, negation, unit/cell association or source instruction-versus-fact distinction. Numeric instructions are conservatively retained by this contract; ambiguous requests require clarification rather than silent deletion. Existing semantic review remains necessary and is not a guarantee. No free-form numeric list numbering or duplicating numeric/contact body facts into titles/summaries.

Live provider/mobile acceptance, actual server deployment, corrected deployed provider-cap response and historical invoice reconciliation remain UNKNOWN. Provider pause and uncertain hold 94412106-50ae-4c30-9b9c-b8c9686cfd36 are untouched.
