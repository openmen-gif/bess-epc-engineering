# Market report content restoration

User-approved corrective scope: preserve HHIC formatting and restore the
comprehensive analysis lost during the v2 migration. Execute within 45 minutes,
at most two independent review iterations. Stop on accepted result, exhausted
budget, or repeated identical failure. Deployment was already authorized.

## Acceptance and coverage

- 18 analysis topics: summary, seven regions, categories, visualization,
  growth, competitors, projects, FX/materials, scenarios, investment,
  power markets, operations, safety, technology, permitting, financing,
  EPC contracts, strategy. Four source/status appendices follow the body.
- Each substantive analysis chapter has a table and explanatory interpretation;
  not just headings or a short list of missing inputs.
- Eight chart types: published forecasts, legacy versus external forecasts,
  scenario sensitivity, CAPEX sensitivity, efficiency sensitivity, price
  sensitivity, operating cash flow, verified project energy capacities.
  These replace unsafe mixed-scope rankings and invented time series.
- Explicit forecast/reported/illustrative distinctions; no fabricated current
  project status, commodity prices, financial returns or regulatory compliance.
- Reproducible cash-flow arithmetic; same input values in tables and figures.
- HHIC donor unchanged, style warnings zero, rendered content parity passing,
  resolved native TOC, no blank pages or missing headings; visual inspection.
- Full tests and independent checker PASS before push. Verify GitHub workflow,
  HF source marker, running revision and HTTP health after deployment.

## New primary-source checks, 2026-11-14 KST

- Mortenson: Edwards & Sanborn storage 3,287 MWh. Legacy 3,287 MW / 13,148 MWh
  is invalid. Do not infer battery MW from the combined interconnection.
  https://www.mortenson.com/projects/edwards-sanborn-solar-plus-storage
- Harmony Energy, 2023-06-29 case study: Pillswood 98 MW / 196 MWh.
  These are historical announced capacities, not a current operating check.
  https://harmonyenergy.co.uk/pv-power-tech-how-we-delivered-the-98mw-196mwh-pillswood-bess-project/
- NREL ATB 2024: 85% round-trip efficiency is a model assumption; its fixed
  operating costs include augmentation. Our illustrative operating expense
  is separate and excludes augmentation, clearly disclosed.
  https://atb.nrel.gov/electricity/2024/2023/utility-scale_battery_storage
- UL Solutions: 9540A evaluates thermal runaway/fire propagation; a test report
  is not blanket site approval. Edition and jurisdiction remain project inputs.
  https://www.ul.com/services/ul-9540a-test-method

Official regional portal links are follow-up destinations, not evidence that
current rules have been reviewed. Legacy competitor classifications and 18
project names are explicitly unverified internal references. Their numeric
rankings, capacities, statuses and pipeline sum are not carried forward.

## Regression verification

The new coverage test failed against v2 with missing analysis headings before
implementation. Tests now check all 17 restored chapters, body depth, tables,
eight physical figures, computed annual cash, NPV direction, CAPEX/efficiency
sensitivity and absence of the erroneous 13,148 MWh value. Native TOC testing
locates the actual body start instead of hard-coding page 4.

Rendering and independent review results to be recorded after verification.

Verification on 2026-11-14 KST:
- Full suite: 31 passed in 70.54 seconds, exit 0.
- Live sample BESS_MarketReport_v3_20261114_004643_151caad0c6:
  30 pages, 18 analysis chapters + 4 source/status chapters, 8 figures;
  651 rendered parity items, 0 missing items, 0 blank pages, 0 style warnings.
- All 30 pages inspected in five contact sheets; enlarged chart pages checked.
- Live lookup: 5/7 reference metrics matched; IEA and SEIA access unavailable,
  explicitly labeled. EIA monthly inventory unavailable, not backfilled. FX
  reference date 2026-11-13. These are disclosed limits, not claims of live data.
- First test run caught an old v2 filename expectation and an incorrectly
  hand-calculated expected cash value. Both tests corrected from the actual
  specification/arithmetic; production calculation was already correct.
- Independent checker: PASS, iteration 1; independently ran 4 focused tests and
  inspected all 30 rendered pages. Deployment readiness accepted; remote runtime
  verification remains a separate final gate.
