# Market report chart and A4 layout revision

Approved corrective scope: user reported dated charts and weak A4 placement,
then instructed continuation. Existing improvement/deployment authorization
applies. Budget: 40 minutes, at most two visual review iterations. Stop after
independent PASS and verified deployment, or on budget/repeated failure.

## Design

Keep HHIC donor, modern typography and 18 analysis topics. Use HHIC JSON page
breaks, paragraph keep rules, table widths and note styles; do not patch generated
document XML. An opt-in engine extension exposes paragraph/table keep rules and
compact table padding; defaults remain unchanged and the donor pin is preserved.
Reading units are kept together and related short sections may share a page.
All evidence dates/statuses remain.

Replace eight identical vertical bar plots with semantic charts: horizontal
comparisons, sensitivity lines and an actual subtractive cash waterfall.
Use HHIC purple, quiet grid lines, direct value labels and Pretendard fonts.
Figures are designed at 8.4 x 2.65 inches and exported at 240 DPI, then placed
at 165 mm wide. This reduces chart height from about 70 mm to 52 mm while
retaining legible labels. Footnotes remain outside the chart as Word text.

## Acceptance

- 18 analysis topics and eight figures preserved, no numerical input changes.
- At least three meaningful chart forms; waterfall subtracts operating expense.
- All A4 pages rendered and visually inspected; no clipped labels, overlaps,
  isolated chart captions or section introductions detached from their tables.
- Native TOC resolved, body parity missing 0, blank pages 0, style warnings 0.
- Data/reference state tested with offline and frozen live evidence.
- Full test suite and independent checker PASS before deployment; deployed
  source SHA and runtime SHA verified with HTTP 200 health/page responses.

## Initial evidence

v3 page 10 repeats large vertical bars and begins the next chapter before its
table. Page 17 shows negative bars downward and another cash-component bar
plot, then a section introduction separated from its table. Several source
metadata tables span pages. Prior visual QA only checked clipping; this
revision also evaluates reading sequence and whitespace.

Two new regression tests failed before changes: no A4 page boundaries and no
semantic chart renderer. Focused checks after implementation: 4 passed.

Initial visual draft: forced breaks produced 37 pages with detached concluding
paragraphs. Rejected. Replaced most fixed boundaries with Word keep chains:
heading + introduction + compact table + interpretation stay together, and
chart/caption/note stay together. Long watchlists start on a new page and remain
splittable. Added a failing-then-passing XML regression for the table/conclusion
chain. This is a reusable JSON option in the HHIC engine, not an ad hoc document
editing script. Local extension is documented in vendor PROVENANCE.md.

## Verification ledger

- Independent review 1: NEEDS_WORK, one detached FX caveat paragraph.
- Fixed bounded table/source/caveat chains. EIA error plus original-source link
  and publication title plus URL are also kept together. News references start
  on a new page to prevent a mostly empty continuation page.
- Added physical PDF layout gate: complete small tables, their consecutive notes,
  and figure captions/notes must share a page. This supplements text parity.
- Full final suite: 35 passed in 44.52 seconds, exit 0.
- Latest sample: BESS_MarketReport_v4_20261114_060438_e972c799f8, evidence collected
  2026-11-14 06:01 KST. 31 pages, 18 analysis topics, 8 figures, 609 content
  checks with 0 missing, 0 style warnings, 0 blank pages. Layout: 35 tables,
  32 table-note groups and 8 figure-note groups checked, 0 errors.
- Word donor remains the pinned original. Default renderer behavior is unchanged;
  compact/keep options are opt-in and documented in the vendor provenance/schema.
- Page count can vary with successful data retrieval and subsequent publications.
  Reading-unit whitespace is retained so a short section or table is not split.
- Independent review 2/2: PASS. Reviewer inspected all 31 pages plus enlarged
  pages 18/28/29 and independently ran 4 focused tests (2.84 s, exit 0).
  FX source/caveat and publication title/URL now remain together. Blockers: 0.
