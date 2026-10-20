# PowerPoint hierarchy and Arabic date display

Baseline: official main aa58e169af68a9dc8319dbc405b53d231ed6a4c2, verified against GitHub. Owner authorizes continued service improvement and reviewed merging. Unrelated governance PR #21 remains untouched.

## Changes and evidence

PPTX v4 uses a native dark navy cover with light title/subtitle text, a quiet paper background for content slides, restrained dark body text and explicit thin table-cell borders. It keeps the original measured textbox geometry, font sizes, density rejection, source slide count and native editable text/tables. No images or decorative generated assets are added.

FACT: The LibreOffice visual review of Arabic source fixtures showed dates such as 2026-10-02 displayed as 02-10-2026 within RTL prose, although the underlying date characters were correct. The serializer now surrounds ISO dates in RTL paragraphs with LTR direction marks. Stripping those invisible marks recovers the exact supplied text; source validation remains before rendering. English paragraphs are unchanged. This is a display correction, not date parsing/reformatting.

Eight AR/EN fixture slides were rendered and inspected: cover, short content, native data table and six-bullet dense content in each language. No clipping or overlap observed in these fixtures. Arabic cover/content were rendered again after the date correction; visible ISO component order now matches the source. Table identifiers, zeros and blanks remain editable and literal. This is LibreOffice inspection, not Microsoft PowerPoint/mobile or live-provider certification.

## Qualification and scope

Focused local tests cover contrast >=4.5 for all six foreground/background pairs, saved native backgrounds/borders, exact source content after display-mark removal, date direction and unchanged English, editability, bounds and the existing service contracts. Global lint/format/diff, three architecture checks and report links are recorded in the PR. Full hosted DB/lifecycle/native workflow required before merge; local PostgreSQL unavailable.

Version bump uses the existing snapshot policy. Upgrade regression includes v3 pending-job cancellation/release with administrator price/activation preserved. Existing prepared results remain reusable. No AI plan/schema/call change, price/gate mutation, retry/cap increase, dependencies, migrations, production deployment or unpause. Source token guards still do not prove semantic completeness; live dense customer decks need separate acceptance.
