# EPC spatial viewer

The committed bundle is self-contained; the HF runtime needs only the existing Python requirements. No CDN, external fonts, network textures or Node server are required. Three.js is MIT licensed (THREE-LICENSE.txt).

Rebuild from the dashboard repository root:

```powershell
npm ci --prefix frontend
npm run build --prefix frontend
.venv/Scripts/python.exe -m pytest tests/test_engineering_viewer.py tests/test_engineering_pages.py -q
.venv/Scripts/python.exe tests/viewer_fixtures.py
node tests/verify_viewer.cjs
.venv/Scripts/python.exe tests/verify_dashboard.py
```

Browser tests default to installed Windows Chrome; set CHROME_PATH for another Chromium executable. Output screenshots/fixtures live in ignored output_reports/viewer. Production assets: engineering-viewer.html and engineering-viewer.bundle.js; source: engineering-viewer.js; adapter: utils/engineering_viewer.py.

Numerical conventions: Python x east/y north/z up map to Three x/z negative/y up. Lengths are metres. Thermal color maps show depth-averaged air temperature, not cell temperature. Airflow is the existing kinematic model at the final thermal field and has its own displayed clock. Fire states follow the solver (4 = flame knockdown with internal TR ongoing, 5 = burned out). Structural overlays show pressure and eccentricity, not solved displacement. Decorative doors, corrugation and road surfaces are illustrative.
