# CV profiles and compact layout

## Authority and baseline
Owner requested integration of useful CV tools and researched customer-facing CV types.
Baseline main ad569b958287249ea63d640925176d86a9d82d90, clean before task.

## Research decision
- CareerOneStop distinguishes chronological, functional and combination formats, recommends clear single-column layouts and warns against omitting detailed work history: https://cloudfront.careeronestop.org/JobSearch/Resumes/ResumeGuide/formatting.aspx
- Oxford describes academic education/research/publication evidence: https://www.ox.ac.uk/careers/careers-guidance/job-search-and-applications/writing-applications/academic-applications
- These are guidance, not measured Saudi demand or ATS certification. Customer-purpose choices are our product mapping: general professional, student/graduate, career change and academic/research.
- Existing docxtpl 0.20.2/python-docx remain the integrated engines. Source-owned templates render escaped customer values; no downloaded template execution, new dependency or external customer-data upload.
- RenderCV/its agent skill reviewed as structured-data/design references; PDF-oriented documented output does not qualify our editable Word/Arabic pair. Not installed or represented as integrated. Arabic DOCX skill reviewed as RTL QA reference, not imported wholesale. Sources: https://github.com/rendercv/rendercv, https://github.com/rendercv/rendercv-skill, https://github.com/alahmadics/arabic-docx-skill, https://github.com/elapouya/python-docx-template
- Original implementation, no third-party copied source/assets in this change.

## Implemented bounded change
CV v2 adds an optional purpose choice (skip/absent = professional), single-line headline, optional projects/training/volunteering, languages, research and publications. Every supplied nonempty section remains present regardless of selected type. Each type changes section order; raw entries remain in source order, dates are not inferred or sorted, no rewriting/translation/invented claims.
The existing 9000 total-character and 100-line-per-field limits include new fields. At least education or experience remains required. Other optional fields can be skipped.
Generic WordDocument layout standard/resume selects compact readable name/headings/spacing with normal body size 11pt. Standard layout remains default for other services. Customer contact data stays in the body. Shared script/date handling, preview, saved pair retry, owner storage and financial behavior reused.
No bot/core slug branch, migration, prices, gates, provider pause or historical cost-hold mutation. Unprepared stale v1 orders follow existing contract-cancellation/release; cached artifacts stay reusable under generic recovery policy.

## Evidence
PASS: 45 focused pure CV/Word-PDF/architecture tests, 3 native CV cases excluded locally; lint/format/diff.
PASS: All eight sample documents (four types x Arabic/English) rendered through local native LibreOffice; every page visually inspected, one page each, no visible clipping/overlap. Exact original fields verified by tests, literal markup not evaluated.
Hosted full PostgreSQL/Redis/native CI required before merge. New server deployment/Telegram acceptance NOT RUN.

## Limits and next slices
No claim of universal ATS compatibility, Saudi popularity rankings, recruiter outcome or arbitrary fonts/mobile rendering. No automatic factual rewriting, semantic date sorting, structured repeated-job intake, bilingual translation, photo/creative template or unrestricted academic dossier. Existing generic preview only shows first page and reports page count. Long content can span pages; never force one page by truncation.
