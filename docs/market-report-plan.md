# Market report implementation plan

Approved 2026-11-13: HHIC Word format, genuinely refreshed reference data,
professional EPC analysis, acceptance tests and deployment to the existing Space.
Execute inline using executing-plans; independent loop-checker before deployment.
Budget: 60 minutes, at most 3 correction/review iterations.

Architecture: a provenance-bearing reference bundle feeds the UI and declarative
HHIC document. Fetch official monthly EIA inventory and dated FX on demand;
maintain reviewed publisher benchmarks separately from fresh retrieval timestamps.
Never promote a forecast to an actual on a calendar change. New publisher releases
are review candidates, not automatically trusted numerical facts.

- [ ] Add tests for monthly inventory discovery/parsing, future dates, missing
  capacity, HTTP failure, forecast persistence, publisher disagreement and metadata.
- [ ] Implement utils/market_evidence.py and data/market_references.json. Refresh
  official reference inputs per generation, collect dated publication signals,
  preserve units/scope/status, never substitute an old quote as a current quote.
- [ ] Vendor the existing HHIC builder and SHA-pinned donor. Implement
  utils/market_report.py: evidence bundle -> Mode A JSON -> official builder.
  Linux uses isolated LibreOffice rendering; Windows uses available renderer.
  Validate JSON/DOCX and render pages. Keep legacy generator callable explicitly.
- [ ] Wire market and dashboard Word/PDF downloads to the same generator, show
  freshness in the market UI; test offline and actual report download via AppTest.
- [ ] Independent review; tests and rendering clean; commit and push existing
  deployment workflow; verify workflow, HF commit and health. Record facts here.

Acceptance: explicit source URL, period, type and retrieval state for every report
metric; zero unlabeled fallbacks; forecast remains forecast in 2027; pinned donor
unchanged; HHIC style warnings 0; document evidence and open-items sections;
network failures produce review warnings; correct DOCX/PDF downloads; independent
PASS; deployed revision and HTTP health verified.

Review focus: upstream schema changes, stale/future publication dates, heterogeneous
market scope, multi-user output collisions, Linux rendering and missing fonts.
E1/E2/E3/E4 follow the installed HHIC definitions; public external benchmarks are
identified as external references, with applicability confirmation before bidding.

## Ledger

Original donor found in OneDrive canonical HHIC skill, SHA256 matches pin
4ec89b04f8c3a88b78aa6585a0c4164afa41dcba8a7133b13fa31c6afa4277b0.
Current checkout is within an Orca isolated workspace. Deployment authorized by
user; no additional approval required. Preserve existing engineering viewer.

Implementation and local validation: tests/ has 29 passing tests including actual
market button -> paired HHIC DOCX/PDF, forecast rollover, offline behavior,
missing EIA identity/scope fields, recent invalid workbook links and stale references.
Donor hash matches; writing-style warnings 0. Latest live sample has 13 pages,
0 missing headings, 0 blank pages; Pretendard embedded; native TOC page numbers
resolved with isolated LibreOffice UNO. Rendered DOCX parity passes.

Independent review iteration 1: NEEDS_WORK (stale UI warning, EIA required columns,
per-metric retrieval timestamps). All three corrected with regression coverage.
Official EIA 2026-09 workbook: 1128 operating generators, 55616.5 MW; missing
reported MWh prevents energy total. October link returned HTML, explicitly recorded
as unavailable. IEA/SEIA page access can fail; prior reviewed references stay labeled.
The reference catalogue has 7 reviewed metrics; no claim that all markets are live.
New official RSS releases are candidates for human validation, not trusted new facts.

Deployment gate: Docker runs scripts/check_market_build.py, exercising Linux
python3-uno and the same DOCX/PDF path before accepting the container image.

Independent review iteration 2: PASS. Independent full suite 29 passed in
108.62 seconds, exit 0; rendered document parity 239 items, missing 0; 13 pages
visually reviewed, no material clipping; writing warnings 0. Deployment pending.

Deployment correction: HF rejected ordinary Git push because the pinned DOCX
and OTF files require binary storage. Use official HfApi.upload_folder on a
git-archive snapshot instead. No force push or history rewriting. deployment.json
records the GitHub source SHA because the HF deployment commit is now distinct.
