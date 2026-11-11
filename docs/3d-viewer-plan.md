# EPC engineering 3D implementation plan

Approved scope: site layout, thermal/airflow, smoke/fire spread and structural result visualization; deploy to the existing HF Space. User reference: AutoCAD/Revit/Unreal-like spatial inspection, not a replacement CAD authoring engine.

Budget: 60 minutes from execution start; at most 3 implementation/review iterations. Stop on completed criteria, budget, iteration limit, or identical failure twice. Independent loop-checker judges PASS/NEEDS_WORK before deployment.

Architecture: retain existing numerical solvers, Plotly analysis/export and design model. Add an offline bundled Three.js viewer embedded through Streamlit components.html. Python adapters serialize exact geometry/results; front end renders materials, lighting, engineering layers, selections, orthographic views and deterministic result playback. Decorative geometry is explicitly illustrative.

- [ ] Task 1: add pure adapters in utils/engineering_viewer.py and tests/test_engineering_viewer.py. Verify design geometry/counts unchanged; finite SI values; thermal frame/time/grid mapping; fire state and temperature pairing; safe JSON serialization.
- [ ] Task 2: implement frontend/engineering-viewer.js and HTML/CSS template, vendor bundled Three.js with license. Test browser rendering, all layer/view controls, selection, measurement, playback, responsive layout and WebGL fallback.
- [ ] Task 3: integrate pages 03, 09, 10 and 13 without deleting existing analysis. Verify regression suite and KO/EN page rendering.
- [ ] Task 4: independent review, fix material defects, commit and deploy via existing HF destination without force-pushing history. Verify revision and site health; record outcome.

Acceptance: 4 pages integrated; 0 new Python/JS errors; geometry and temperatures match existing models within serialization rounding (0.001); selectable equipment dimensions in m; 3 camera presets; engineering layer toggles; linked playback with seconds and units; no CDN dependency; independent PASS and HF running revision verified.

Review focus: large arrays; hidden WebGL frames; iframe script escaping; frozen/playing time behavior; stale simulation input labels. Structural deformation is not inferred from pressure: display pressure and resultant eccentricity only. No fabricated physical airflow or suppression effect.

## Verification ledger

Tasks 1–3 complete. Local validation: 10 adapter/result-bearing page tests, 88 regression checks, 58 browser checks, 0 JavaScript exceptions. Browser cases include 301 equipment items, KO/EN, actual selection and measured geometry within 0.02 m, 390 px panel access, result playback/reset. Screenshots and logs: ignored output_reports/.

Independent loop-checker: iteration 1 NEEDS_WORK (airflow reset and mobile panel access); iteration 2 PASS after deterministic frame stepping with separate airflow clock and mobile panel toggle. Independent 10-test run passed; 6 fixtures generated 0 external HTTP requests and 0 JS exceptions. Deployment remains to be verified.

Ruling: retain pressure/eccentricity rather than inventing structural displacement. Correct the existing 2 Hz seismic animation sampling from 0.25 s (zero crossings only) to 0.125 s. Local HF token absent; use existing GitHub deployment credentials. Remove force-push from deployment because both repositories share the same starting commit and a fast-forward is sufficient.
