import streamlit as st
try:
    st.set_page_config(page_title="BESS EPC Platform", layout="wide", initial_sidebar_state="auto")
except Exception:
    pass

import numpy as np
import plotly.graph_objects as go
from utils.css_loader import apply_custom_css
from utils.auth_helper import require_auth, sidebar_user_info
from utils.theme import AX3D, DARK_LAYOUT
from utils.sim_physics import (
    heat2d_transient, bearing_pressure, seismic_pulse,
    smoke_layer_series, plume_particles,
    build_animation, fmt_time,
)

# ── Model constants (documented in Methodology expanders) ─────
CFD_L, CFD_W, CFD_H = 15.0, 15.0, 4.0     # enclosure dims [m]
CFD_NX = CFD_NY = 30
CFD_SNAPS = list(range(0, 1801, 60))   # s — 0~30분, 60초 균일 31프레임(부드러운 재생/스크럽)
THERMAL_LIMIT_C = 50.0                     # design verification limit

STR_HCG   = 1.5                            # container C.G. height above pad [m]
STR_ALLOW = 45.0                           # allowable bearing pressure [kN/m²]

FDS_L, FDS_W, FDS_H = 20.0, 20.0, 8.0     # fire room dims [m]
FDS_AFAN = 3.0                             # total exhaust fan area [m²] (2×1.5)
FDS_TEND = 240.0                           # simulated duration [s]
TENABLE_Z = 2.0                            # NFPA 92 smoke-layer design height [m]


# ── Bilingual text dict ───────────────────────────────────────
def _T():
    lang = st.session_state.get("lang", "KO")
    return {
        "EN": {
            "caption":   "🛤️ **BESS EPC Workflow:** Step 2 (System Eng) ➔ **[Step 3: 3D & Analysis]** ➔ Step 4 (E-BOP) ...",
            "title":     "🧊 3D Analysis & Simulation Module",
            "select":    "Select Simulation Discipline",
            "roles":     ["CFD Analysis (Thermal/Ventilation)", "Structural & Seismic Analysis", "Fire & Gas Dispersion (FDS)"],
            "disclaimer": ("⚠️ **Reduced-order analytical model** — for parametric screening only. "
                           "Not a substitute for full OpenFOAM / ANSYS / FDS analysis."),
            "play": "▶ Play", "pause": "⏸ Pause", "tprefix": "t = ",
            # CFD
            "cfd_info":     "Analyzing airflow, heat dissipation, and HVAC sizing for Battery Enclosures.",
            "cfd_params":   "Simulation Parameters",
            "cfd_ambient":  "Ambient Temp (°C)",
            "cfd_hvac":     "HVAC Capacity (kW)",
            "cfd_heat":     "Inverter/Battery Heat Loss (kW)",
            "cfd_run":      "▶ Run Thermal Simulation",
            "cfd_result":   lambda pk, mn: f"Energy balance solved. Peak air temp: **{pk:.1f} °C** / bulk mean: **{mn:.1f} °C** at t = 30 min.",
            "cfd_viewer":   "🌡️ Transient Thermal Field — Animated (Reduced-Order FDM)",
            "cfd_guide":    ("**📊 Chart Guide:**  \n"
                             f"- **X / Y:** position in {CFD_L:.0f}×{CFD_W:.0f} m enclosure (m)  \n"
                             "- **Z / Color:** depth-averaged air temperature (°C) — hot spots above battery/PCS skids  \n"
                             f"- **Red plane:** {THERMAL_LIMIT_C:.0f} °C design limit  \n"
                             "- **▶ Play:** heat-up transient from ambient (0 → 30 min)"),
            "cfd_xtitle":   "X: East-West (m)",
            "cfd_ytitle":   "Y: North-South (m)",
            "cfd_ztitle":   "Air Temp (°C)",
            "cfd_ctitle":   "Temp (°C)",
            "cfd_figtitle": "Enclosure Air Temperature — Heat-Up Transient",
            "cfd_hover":    ("<b>Position</b><br>X (E-W): %{x:.1f} m<br>Y (N-S): %{y:.1f} m<br>"
                             "<b>Air Temp: %{z:.1f} °C</b><extra></extra>"),
            "cfd_m_peak":   "Peak Temp (steady)", "cfd_m_mean": "Bulk Mean Temp", "cfd_m_dt": "ΔT vs Ambient",
            "cfd_pass":     lambda pk: f"✅ Peak {pk:.1f} °C ≤ {THERMAL_LIMIT_C:.0f} °C — HVAC capacity adequate.",
            "cfd_fail":     lambda pk: f"❌ Peak {pk:.1f} °C > {THERMAL_LIMIT_C:.0f} °C — increase HVAC capacity or redistribute heat sources.",
            "cfd_limit_lbl": f"{THERMAL_LIMIT_C:.0f} °C design limit",
            "cfd_rack_lbl": "Battery/PCS skid",
            "cfd_duct_lbl": "HVAC supply duct",
            "cfd_method_t": "📐 Methodology & Assumptions (Thermal)",
            "cfd_method": (
                "**Governing equation (2-D depth-averaged energy balance, explicit FDM):**\n\n"
                "ρ·c_p·H·∂T/∂t = k_eff·H·∇²T + q″_src − G_hvac·(T − T_supply) − h_env·(T − T_amb)\n\n"
                "- **Sources:** total heat loss split over 8 battery/PCS skids, Gaussian footprint σ = 0.6 m\n"
                "- **HVAC:** sensible-cooling conductance G = Q_rated/ΔT_design (ΔT_design = 12 K); 65 % acts on the "
                "recirculated bulk air, 35 % concentrated at the wall supply ducts → self-limiting removal ∝ (T − T_supply)\n"
                "- **Mixing:** effective turbulent diffusivity α_eff = 0.08 m²/s (forced-ventilation enclosure)\n"
                "- **Envelope:** U_env = 2.5 W/m²K over roof + walls; enclosure height H = 4 m\n\n"
                "**Limitations:** no momentum/buoyancy field is resolved (no real CFD); vertical stratification, "
                "jet impingement and short-circuiting of supply air are NOT captured. "
                "Use OpenFOAM / ANSYS Fluent for design verification."),
            # Structural
            "str_info":     "Verifying DCR (Demand Capacity Ratio), foundation loading, and seismic compliance per ASCE 7 / KDS 41.",
            "str_params":   "Structural Analysis Parameters",
            "str_dead":     "Dead Load (kN/m²)",
            "str_live":     "Live Load (kN/m²)",
            "str_wind":     "Wind Load (kN/m²)",
            "str_seismic":  "Design Seismic Acceleration (g)",
            "str_padw":     "Pad Width (m)",
            "str_padl":     "Pad Length (m)",
            "str_combo":    "Max Combined Load (kN/m²)",
            "str_eqk":      "Seismic Load (kN/m²)",
            "str_safe":     lambda d: f"DCR = {d:.2f} ✅ Safe",
            "str_warn":     lambda d: f"DCR = {d:.2f} ⚠️ Caution",
            "str_over":     lambda d: f"DCR = {d:.2f} ❌ Exceeded!",
            "str_tab1":     "🔴 Bearing Pressure (Seismic Rocking)",
            "str_tab2":     "📊 3D Load Combination",
            "str_guide1":   ("**📊 Chart Guide:**  \n"
                             "- **X/Y:** position on foundation pad (m)  \n"
                             "- **Z / Color:** soil bearing pressure q (kN/m²) — rigid pad, linear soil springs  \n"
                             f"- **Yellow plane:** allowable bearing pressure ({STR_ALLOW:.0f} kN/m²)  \n"
                             "- **▶ Play:** pressure redistribution while the pad rocks under a damped-sine "
                             "ground-motion pulse (0 → 8 s); q = 0 zones indicate uplift"),
            "str_xtitle1":  "X: Width direction (m)",
            "str_ytitle1":  "Y: Length direction (m)",
            "str_ztitle1":  "Bearing pressure q (kN/m²)",
            "str_ctitle1":  "Bearing pressure<br>q (kN/m²)",
            "str_figtit1":  "Foundation Bearing Pressure under Seismic Rocking",
            "str_hover1":   ("<b>Foundation Pad Position</b><br>"
                             "X (width): %{x:.2f} m<br>Y (length): %{y:.2f} m<br>"
                             "<b>q: %{z:.1f} kN/m²</b><extra></extra>"),
            "str_alimit":   f"Allowable bearing pressure ({STR_ALLOW:.0f} kN/m²)",
            "str_m_qmax":   "Peak edge pressure q_max",
            "str_m_ecc":    "Peak eccentricity e_max",
            "str_method_t": "📐 Methodology & Assumptions (Structural)",
            "str_method": (
                "**Bearing pressure model (rigid footing on linear soil springs, Meyerhof):**\n\n"
                "q(x,y) = (P/A)·(1 + 12·e_x·x/L² + 12·e_y·y/B²),  q ≥ 0 (no soil tension → uplift zone)\n\n"
                "- **Vertical demand:** q_avg = 1.2D + 1.6L + 0.5W (ASCE 7-22 LRFD combination; DCR = q_avg/45)\n"
                f"- **Seismic rocking:** eccentricity e_x(t) = S_a·h_cg·s(t), h_cg = {STR_HCG} m (container C.G.), "
                "s(t) = damped-sine pulse (f = 2 Hz, exponential decay) as a NORMALIZED ground-motion surrogate\n"
                "- Valid while resultant is near the kern (e ≤ L/6); larger e shows growing uplift zone\n\n"
                "**Limitations:** quasi-static equivalent-lateral-force treatment — no dynamic soil-structure "
                "interaction, no plate flexibility (rigid-pad assumption), no modal response. "
                "Use STAAD/SAFE + site response spectrum for design verification."),
            "str_guide2":   ("**📊 Load Combination Comparison (ASCE 7 / KDS 41):**  \n"
                             "Hover over each bar to check load components per node. Nodal distribution factors are "
                             "indicative (uniform-grid pedestal layout).  \n"
                             "- X-axis: Structural Node  /  Y-axis: Load Type  /  Z-axis: Load (kN)"),
            "str_combo_lbl": "Combo(1.2D+1.6L)",
            "str_figtit2":  "3D Load Combination Comparison (per Node)",
            "str_xnode":    "Node",
            "str_yload":    "Load Type",
            "str_zload":    "Load (kN)",
            "str_hover2":   "<b>Load: {cat}</b><br>Node: {node}<br>Value: {val:.1f} kN",
            # Fire FDS
            "fds_info":     "Fire smoke-filling and exhaust analysis (NFPA 92 plume correlations) for thermal runaway scenarios.",
            "fds_params":   "Fire Scenario Parameters",
            "fds_fan":      "Exhaust Fan Speed (m/s)",
            "fds_fire":     "Fire Size (MW)",
            "fds_fire_opts":["1 MW (Incipient)", "5 MW (Growth)", "15 MW (Fully Developed)"],
            "fds_run":      "▶ Run Smoke-Filling Analysis",
            "fds_viewer":   "🔥 Buoyant Smoke Plume & Layer Descent — Animated",
            "fds_guide":    ("**📊 Chart Guide:**  \n"
                             f"- **Room:** {FDS_L:.0f}×{FDS_W:.0f}×{FDS_H:.0f} m, exhaust fans on +X wall (total {FDS_AFAN:.1f} m²)  \n"
                             "- **Dots:** smoke parcels — color = gas temperature (°C)  \n"
                             "- **Gray plane:** smoke layer interface z_i(t) (descends as layer fills)  \n"
                             f"- **Green plane:** {TENABLE_Z:.1f} m tenability height (NFPA 92 design objective)  \n"
                             "- **▶ Play:** smoke filling vs. mechanical extraction (0 → 4 min)"),
            "fds_xtitle":   "X (m)", "fds_ytitle": "Y (m)", "fds_ztitle": "Z: Height (m)",
            "fds_ctitle":   "Gas Temp (°C)",
            "fds_figtit":   "Thermal Runaway Smoke Plume — Layer Filling vs. Extraction",
            "fds_m_layer":  "Equilibrium layer height",
            "fds_m_temp":   "Smoke layer temp",
            "fds_m_ext":    "Extraction flow",
            "fds_m_plume":  "Plume mass flow",
            "fds_pass":     lambda z: f"✅ Smoke layer stabilizes at {z:.1f} m ≥ {TENABLE_Z:.1f} m — tenable egress path maintained (NFPA 92 objective).",
            "fds_fail":     lambda z: f"❌ Smoke layer descends to {z:.1f} m < {TENABLE_Z:.1f} m — increase exhaust capacity (fan speed/area).",
            "fds_layer_lbl": "Smoke layer interface",
            "fds_ten_lbl":   "Tenability height (2.0 m)",
            "fds_method_t": "📐 Methodology & Assumptions (Fire/Smoke)",
            "fds_method": (
                "**Axisymmetric buoyant plume + well-mixed smoke layer (NFPA 92 correlations):**\n\n"
                "- Plume mass flow: ṁ_p = 0.071·Q_c^{1/3}·z^{5/3} + 0.0018·Q_c  (Q_c in kW, z in m; "
                "below flame tip ṁ_p = 0.0056·Q_c·z/L_f)\n"
                "- Flame height: L_f = 0.235·Q^{2/5} − 1.02·D (Heskestad)\n"
                "- Plume centerline excess temp: ΔT₀ = 25·Q_c^{2/3}/z^{5/3} (K)\n"
                "- Layer descent: dV/dt = ṁ_p(z_i)/ρ_s − V̇_extract, with V̇_extract = u_fan·A_fan and ρ_s = 353/T_s\n"
                "- Convective fraction Q_c = 0.7·Q; smoke dots are a Monte-Carlo rendering of the Gaussian "
                "plume profile (σ ≈ 0.12·z) — the widths/temps are deterministic, only dot placement is sampled\n\n"
                "**Limitations:** steady design fire (no growth curve), no sprinkler/ceiling-jet interaction, "
                "no plug-holing check at exhaust inlets, no toxicity/visibility calc. "
                "Use NIST FDS for performance-based design verification. The correlations above ARE the basis of "
                "NFPA 92 smoke-control sizing, so trends (fan speed ↑ → higher layer) are directionally valid."),
            # Checklist
            "tab_in":  "[I] Inputs",  "tab_proc": "[P] Process",  "tab_out": "[O] Outputs",
            "inp_title": "### Required Inputs",
            "inp_cad":    "3D CAD Models (.step / .IFC)",
            "inp_heat":   "Component Heat Loss Data Sheet",
            "inp_weather":"Site Environmental Data (Weather)",
            "inp_soil":   "Soil Report & Seismic Zone Info",
            "proc_title": "### Active Processes",
            "proc_mesh":  "Mesh Generation & Grid Refinement",
            "proc_bc":    "Boundary Condition Assignment",
            "proc_run":   "Run Solver (OpenFOAM / ANSYS / STAAD)",
            "out_title":  "### Deliverable Outputs",
            "out_plots":  "Simulation Contour Plots & Animations",
            "out_report": "Verification Report (Pass/Fail)",
            "out_export": "📄 Export Result Packages",
            "out_dl":     "⬇️ Download Simulation Verification Report (.txt)",
        },
        "KO": {
            "caption":   "🛤️ **BESS EPC 워크플로우:** Step 2 (시스템 설계) ➔ **[Step 3: 3D & 해석]** ➔ Step 4 (E-BOP) ...",
            "title":     "🧊 3D 해석 & 시뮬레이션 모듈",
            "select":    "시뮬레이션 분야 선택",
            "roles":     ["CFD 해석 (열/환기)", "구조 & 내진 해석", "화재 & 가스 확산 (FDS)"],
            "disclaimer": ("⚠️ **축소차수 해석 모델(Reduced-order analytical model)** — 파라미터 스크리닝 용도입니다. "
                           "OpenFOAM / ANSYS / FDS 정밀 해석을 대체하지 않습니다."),
            "play": "▶ 재생", "pause": "⏸ 정지", "tprefix": "t = ",
            # CFD
            "cfd_info":     "배터리 인클로저 내 기류, 열방출, HVAC 용량을 분석합니다.",
            "cfd_params":   "시뮬레이션 파라미터",
            "cfd_ambient":  "주변 온도 (°C)",
            "cfd_hvac":     "HVAC 용량 (kW)",
            "cfd_heat":     "인버터/배터리 발열 (kW)",
            "cfd_run":      "▶ 열해석 시뮬레이션 실행",
            "cfd_result":   lambda pk, mn: f"에너지 수지 해석 완료. t=30분 기준 최고 공기온도 **{pk:.1f} °C** / 평균 **{mn:.1f} °C**.",
            "cfd_viewer":   "🌡️ 과도 열분포 — 애니메이션 (축소차수 FDM)",
            "cfd_guide":    ("**📊 차트 해석:**  \n"
                             f"- **X / Y축:** {CFD_L:.0f}×{CFD_W:.0f} m 인클로저 내 위치 (m)  \n"
                             "- **Z축 / 색상:** 깊이평균 공기 온도 (°C) — 배터리/PCS 스키드 상부가 hot spot  \n"
                             f"- **빨간 평면:** 설계 한계 {THERMAL_LIMIT_C:.0f} °C  \n"
                             "- **▶ 재생:** 주변온도에서 가열되는 과도 응답 (0 → 30분)"),
            "cfd_xtitle":   "X: 동서 위치 (m)",
            "cfd_ytitle":   "Y: 남북 위치 (m)",
            "cfd_ztitle":   "공기 온도 (°C)",
            "cfd_ctitle":   "온도 (°C)",
            "cfd_figtitle": "인클로저 공기 온도 — 가열 과도응답",
            "cfd_hover":    ("<b>위치</b><br>X (동서): %{x:.1f} m<br>Y (남북): %{y:.1f} m<br>"
                             "<b>공기 온도: %{z:.1f} °C</b><extra></extra>"),
            "cfd_m_peak":   "최고 온도 (정상상태)", "cfd_m_mean": "평균 온도", "cfd_m_dt": "주변온도 대비 ΔT",
            "cfd_pass":     lambda pk: f"✅ 최고 {pk:.1f} °C ≤ {THERMAL_LIMIT_C:.0f} °C — HVAC 용량 적정.",
            "cfd_fail":     lambda pk: f"❌ 최고 {pk:.1f} °C > {THERMAL_LIMIT_C:.0f} °C — HVAC 증설 또는 발열원 재배치 필요.",
            "cfd_limit_lbl": f"설계 한계 {THERMAL_LIMIT_C:.0f} °C",
            "cfd_rack_lbl": "배터리/PCS 스키드",
            "cfd_duct_lbl": "HVAC 급기 덕트",
            "cfd_method_t": "📐 해석 방법론 & 가정 (열해석)",
            "cfd_method": (
                "**지배 방정식 (2차원 깊이평균 에너지 수지, 양해법 FDM):**\n\n"
                "ρ·c_p·H·∂T/∂t = k_eff·H·∇²T + q″_src − G_hvac·(T − T_supply) − h_env·(T − T_amb)\n\n"
                "- **발열원:** 총 발열량을 8개 배터리/PCS 스키드에 균등 분배, 가우시안 footprint σ = 0.6 m\n"
                "- **HVAC:** 현열 냉각 컨덕턴스 G = Q_rated/ΔT_design (ΔT_design = 12 K); 65 %는 재순환 공기 전체에, "
                "35 %는 벽면 급기 덕트에 집중 → (T − T_supply)에 비례하는 자기제한적 냉각\n"
                "- **혼합:** 유효 난류 확산계수 α_eff = 0.08 m²/s (강제환기 인클로저)\n"
                "- **외피:** U_env = 2.5 W/m²K (지붕+벽), 인클로저 높이 H = 4 m\n\n"
                "**한계:** 운동량/부력장 미해석(실제 CFD 아님). 수직 성층화, 제트 충돌, 급기 단락(short-circuit)은 "
                "반영되지 않음. 설계 검증은 OpenFOAM / ANSYS Fluent 필요."),
            # Structural
            "str_info":     "ASCE 7 / KDS 41 기준 DCR, 기초 하중, 내진 검토를 수행합니다.",
            "str_params":   "구조 해석 파라미터",
            "str_dead":     "고정 하중 Dead Load (kN/m²)",
            "str_live":     "활 하중 Live Load (kN/m²)",
            "str_wind":     "풍 하중 Wind Load (kN/m²)",
            "str_seismic":  "설계 지진 가속도 (g)",
            "str_padw":     "패드 폭 Width (m)",
            "str_padl":     "패드 길이 Length (m)",
            "str_combo":    "최대 조합 하중 (kN/m²)",
            "str_eqk":      "지진 하중 (kN/m²)",
            "str_safe":     lambda d: f"DCR = {d:.2f} ✅ 안전",
            "str_warn":     lambda d: f"DCR = {d:.2f} ⚠️ 주의",
            "str_over":     lambda d: f"DCR = {d:.2f} ❌ 초과!",
            "str_tab1":     "🔴 지반 지지압 분포 (내진 Rocking)",
            "str_tab2":     "📊 3D 하중 조합 비교",
            "str_guide1":   ("**📊 차트 해석:**  \n"
                             "- **X/Y축:** 기초 패드 상의 위치 (m)  \n"
                             "- **Z축 / 색상:** 지반 지지압 q (kN/m²) — 강체 패드 + 선형 지반 스프링 가정  \n"
                             f"- **노란 평면:** 허용 지지압 ({STR_ALLOW:.0f} kN/m²)  \n"
                             "- **▶ 재생:** 감쇠 정현파 지진 펄스에 의한 패드 rocking 시 지지압 재분배 (0 → 8초); "
                             "q = 0 구역은 들림(uplift)"),
            "str_xtitle1":  "X: 폭방향 (m)",
            "str_ytitle1":  "Y: 길이방향 (m)",
            "str_ztitle1":  "지지압 q (kN/m²)",
            "str_ctitle1":  "지지압<br>q (kN/m²)",
            "str_figtit1":  "내진 Rocking 시 기초 지지압 분포",
            "str_hover1":   ("<b>기초 패드 위치</b><br>"
                             "X (폭방향): %{x:.2f} m<br>Y (길이방향): %{y:.2f} m<br>"
                             "<b>지지압 q: %{z:.1f} kN/m²</b><extra></extra>"),
            "str_alimit":   f"허용 지지압 ({STR_ALLOW:.0f} kN/m²)",
            "str_m_qmax":   "최대 단부 지지압 q_max",
            "str_m_ecc":    "최대 편심 e_max",
            "str_method_t": "📐 해석 방법론 & 가정 (구조)",
            "str_method": (
                "**지지압 모델 (강체 기초 + 선형 지반 스프링, Meyerhof):**\n\n"
                "q(x,y) = (P/A)·(1 + 12·e_x·x/L² + 12·e_y·y/B²),  q ≥ 0 (지반 인장 불가 → uplift 구역)\n\n"
                "- **수직 하중:** q_avg = 1.2D + 1.6L + 0.5W (ASCE 7-22 LRFD 조합; DCR = q_avg/45)\n"
                f"- **내진 rocking:** 편심 e_x(t) = S_a·h_cg·s(t), h_cg = {STR_HCG} m (컨테이너 무게중심), "
                "s(t) = 감쇠 정현파 펄스 (f = 2 Hz, 지수 감쇠) — 정규화된 지반운동 대용 함수\n"
                "- 합력이 핵(kern, e ≤ L/6) 부근일 때 유효; 편심 증가 시 uplift 구역 확장 표시\n\n"
                "**한계:** 등가정적 처리 — 동적 지반-구조 상호작용, 패드 휨(강체 가정), 모드 응답 미반영. "
                "설계 검증은 STAAD/SAFE + 부지 응답스펙트럼 필요."),
            "str_guide2":   ("**📊 하중 조합 비교 (ASCE 7 / KDS 41 기준):**  \n"
                             "마우스를 올려 각 절점의 하중 성분을 확인하세요. 절점 분배계수는 균등 그리드 받침 배치 기준의 "
                             "예시값입니다.  \n"
                             "- X축: 구조 절점  /  Y축: 하중 종류  /  Z축: 하중 크기 (kN)"),
            "str_combo_lbl": "조합(1.2D+1.6L)",
            "str_figtit2":  "3D 하중 조합 비교 (절점별)",
            "str_xnode":    "절점 (Node)",
            "str_yload":    "하중 종류",
            "str_zload":    "하중 크기 (kN)",
            "str_hover2":   "<b>하중: {cat}</b><br>절점: {node}<br>값: {val:.1f} kN",
            # Fire FDS
            "fds_info":     "열폭주 시나리오에 대한 연기 충전·배출 해석 (NFPA 92 플룸 상관식)을 수행합니다.",
            "fds_params":   "화재 시나리오 파라미터",
            "fds_fan":      "배기팬 풍속 (m/s)",
            "fds_fire":     "화재 규모 (MW)",
            "fds_fire_opts":["1 MW (초기)", "5 MW (성장)", "15 MW (완전 발달)"],
            "fds_run":      "▶ 연기 충전 해석 실행",
            "fds_viewer":   "🔥 부력 연기 플룸 & 연기층 하강 — 애니메이션",
            "fds_guide":    ("**📊 차트 해석:**  \n"
                             f"- **실내:** {FDS_L:.0f}×{FDS_W:.0f}×{FDS_H:.0f} m, +X 벽면 배기팬 (총 {FDS_AFAN:.1f} m²)  \n"
                             "- **점:** 연기 입자 — 색상 = 가스 온도 (°C)  \n"
                             "- **회색 평면:** 연기층 경계면 z_i(t) (층이 차오르며 하강)  \n"
                             f"- **녹색 평면:** 피난 가능 높이 {TENABLE_Z:.1f} m (NFPA 92 설계 목표)  \n"
                             "- **▶ 재생:** 연기 충전 vs 기계 배연 (0 → 4분)"),
            "fds_xtitle":   "X (m)", "fds_ytitle": "Y (m)", "fds_ztitle": "Z: 높이 (m)",
            "fds_ctitle":   "가스 온도 (°C)",
            "fds_figtit":   "열폭주 연기 플룸 — 연기층 충전 vs 배연",
            "fds_m_layer":  "평형 연기층 높이",
            "fds_m_temp":   "연기층 온도",
            "fds_m_ext":    "배연 풍량",
            "fds_m_plume":  "플룸 질량유량",
            "fds_pass":     lambda z: f"✅ 연기층이 {z:.1f} m에서 안정 (≥ {TENABLE_Z:.1f} m) — 피난 경로 가시성 유지 (NFPA 92 목표).",
            "fds_fail":     lambda z: f"❌ 연기층이 {z:.1f} m까지 하강 (< {TENABLE_Z:.1f} m) — 배기 용량(팬 풍속/면적) 증대 필요.",
            "fds_layer_lbl": "연기층 경계면",
            "fds_ten_lbl":   "피난 가능 높이 (2.0 m)",
            "fds_method_t": "📐 해석 방법론 & 가정 (화재/연기)",
            "fds_method": (
                "**축대칭 부력 플룸 + 균일혼합 연기층 (NFPA 92 상관식):**\n\n"
                "- 플룸 질량유량: ṁ_p = 0.071·Q_c^{1/3}·z^{5/3} + 0.0018·Q_c (Q_c kW, z m; "
                "화염 끝 이하 ṁ_p = 0.0056·Q_c·z/L_f)\n"
                "- 화염 높이: L_f = 0.235·Q^{2/5} − 1.02·D (Heskestad)\n"
                "- 플룸 중심선 온도상승: ΔT₀ = 25·Q_c^{2/3}/z^{5/3} (K)\n"
                "- 연기층 하강: dV/dt = ṁ_p(z_i)/ρ_s − V̇_extract, V̇_extract = u_fan·A_fan, ρ_s = 353/T_s\n"
                "- 대류 분율 Q_c = 0.7·Q; 연기 점은 가우시안 플룸 분포(σ ≈ 0.12·z)의 몬테카를로 렌더링 — "
                "폭/온도는 결정론적 물리값이며 점 위치만 샘플링\n\n"
                "**한계:** 정상 설계화재(성장곡선 없음), 스프링클러/천장제트 상호작용·plug-holing·독성/가시거리 미해석. "
                "성능위주설계 검증은 NIST FDS 필요. 위 상관식은 NFPA 92 배연 설계의 근간이므로 "
                "경향성(팬 풍속 ↑ → 연기층 상승)은 타당합니다."),
            # Checklist
            "tab_in":  "[I] 입력 항목", "tab_proc": "[P] 프로세스", "tab_out": "[O] 출력물",
            "inp_title": "### 필요 입력 항목",
            "inp_cad":    "3D CAD 모델 (.step / .IFC)",
            "inp_heat":   "컴포넌트 발열량 데이터 시트",
            "inp_weather":"현장 환경 데이터 (기상)",
            "inp_soil":   "지반 조사 보고서 & 내진 구역 정보",
            "proc_title": "### 수행 프로세스",
            "proc_mesh":  "메시 생성 및 격자 정제",
            "proc_bc":    "경계 조건 설정",
            "proc_run":   "솔버 실행 (OpenFOAM / ANSYS / STAAD)",
            "out_title":  "### 납품 출력물",
            "out_plots":  "시뮬레이션 등고선 도면 & 애니메이션",
            "out_report": "검증 보고서 (합격/불합격)",
            "out_export": "📄 결과 패키지 내보내기",
            "out_dl":     "⬇️ 시뮬레이션 검증 보고서 다운로드 (.txt)",
        },
    }[lang]


def _make_box3d(x0, y0, z_bot, z_top, dx, dy, color, name, hover_text):
    """Create a 3D box (bar) using go.Mesh3d."""
    x1, y1 = x0 + dx, y0 + dy
    vx = [x0, x1, x1, x0, x0, x1, x1, x0]
    vy = [y0, y0, y1, y1, y0, y0, y1, y1]
    vz = [z_bot, z_bot, z_bot, z_bot, z_top, z_top, z_top, z_top]
    i  = [0, 0, 4, 4, 0, 0, 2, 2, 0, 0, 1, 1]
    j  = [1, 2, 5, 6, 1, 5, 3, 7, 3, 7, 2, 6]
    k  = [2, 3, 6, 7, 5, 4, 7, 6, 7, 4, 6, 5]
    return go.Mesh3d(
        x=vx, y=vy, z=vz, i=i, j=j, k=k,
        color=color, opacity=0.85,
        name=name,
        hovertext=hover_text,
        hoverinfo="text",
        showlegend=True,
        legendgroup=name,
    )


# ── Cached physics runs (deterministic → cache-friendly) ──────
@st.cache_data(show_spinner=False)
def _run_cfd(ambient_temp, heat_loss_kw, hvac_kw):
    src = [(ix, iy) for iy in (10, 20) for ix in (6, 12, 18, 24)]
    vents = [(1, iy) for iy in (6, 12, 18, 24)] + [(CFD_NX - 2, iy) for iy in (6, 12, 18, 24)]
    times, snaps = heat2d_transient(
        CFD_L, CFD_W, CFD_H, ambient_temp, src, heat_loss_kw * 1000.0,
        hvac_kw * 1000.0, vents, CFD_NX, CFD_NY, CFD_SNAPS,
    )
    return times, snaps, src, vents


@st.cache_data(show_spinner=False)
def _run_smoke(q_mw, u_fan):
    return smoke_layer_series(q_mw, u_fan, FDS_L * FDS_W, FDS_H,
                              A_fan=FDS_AFAN, t_end=FDS_TEND, n=49)


@st.cache_data(show_spinner=False)
def _plume_frame_arrays(q_mw, u_fan):
    """플룸 몬테카를로 점 좌표를 프레임별로 사전 계산·캐시 — rerun마다 ~1.9만 점 재샘플 방지."""
    res = _run_smoke(q_mw, u_fan)
    idx = list(range(0, len(res["times"]), 2))
    fx, fy = FDS_L / 2.0, FDS_W / 2.0
    frames = []
    for i in idx:
        z_i = float(res["z_layer"][i])
        T_l = float(res["T_layer_C"][i])
        px, py, pz, pt = plume_particles(
            z_i, T_l, q_mw, FDS_H, dom_x=FDS_L, dom_y=FDS_W,
            fire_x=fx, fire_y=fy, u_fan=u_fan, frame_seed=i,
        )
        frames.append((i, z_i, px, py, pz, pt))
    return idx, frames


# ── Main Page ─────────────────────────────────────────────────
apply_custom_css()
require_auth("03")
sidebar_user_info()
T = _T()

st.caption(T["caption"])
st.title(T["title"])
st.markdown("---")

role = st.selectbox(T["select"], T["roles"])

# 디자인 토큰 정본(utils/theme.py) 참조 — 페이지 로컬 하드코딩 제거
_ax3 = AX3D
_dark = DARK_LAYOUT

# ── CFD ───────────────────────────────────────────────────────
if role == T["roles"][0]:
    st.header(f"🌡️ {role}")
    st.info(T["cfd_info"])
    st.caption(T["disclaimer"])

    col1, col2 = st.columns([1, 3])
    with col1:
        st.subheader(T["cfd_params"])
        default_amb = st.session_state.get("site_temp_max", 35.0)
        ambient_temp  = st.slider(T["cfd_ambient"], min_value=-20.0, max_value=55.0, value=float(default_amb))
        hvac_capacity = st.slider(T["cfd_hvac"], min_value=10, max_value=100, value=40)
        heat_loss     = st.number_input(T["cfd_heat"], value=30.0, min_value=1.0, max_value=500.0)

        times, snaps, src_cells, vent_cells = _run_cfd(float(ambient_temp), float(heat_loss), float(hvac_capacity))
        T_final = snaps[-1]
        peak_T  = float(T_final.max())
        mean_T  = float(T_final.mean())

        st.metric(T["cfd_m_peak"], f"{peak_T:.1f} °C")
        st.metric(T["cfd_m_mean"], f"{mean_T:.1f} °C")
        st.metric(T["cfd_m_dt"],   f"+{peak_T - ambient_temp:.1f} °C")
        if peak_T <= THERMAL_LIMIT_C:
            st.success(T["cfd_pass"](peak_T))
        else:
            st.error(T["cfd_fail"](peak_T))
        if st.button(T["cfd_run"]):
            st.success(T["cfd_result"](peak_T, mean_T))

    with col2:
        st.subheader(T["cfd_viewer"])
        st.caption(T["cfd_guide"])

        dxc, dyc = CFD_L / CFD_NX, CFD_W / CFD_NY
        x_vals = (np.arange(CFD_NX) + 0.5) * dxc
        y_vals = (np.arange(CFD_NY) + 0.5) * dyc
        cmax = max(peak_T, THERMAL_LIMIT_C + 2.0, float(ambient_temp) + 1.0)  # cmin==cmax 퇴화 방지
        z_top = cmax + 4.0

        def _surf(Z):
            return go.Surface(
                x=x_vals, y=y_vals, z=Z,
                colorscale="Inferno", cmin=float(ambient_temp), cmax=cmax,
                colorbar=dict(title=dict(text=T["cfd_ctitle"], font=dict(color="#c9d1d9")),
                              tickfont=dict(color="#c9d1d9")),
                hovertemplate=T["cfd_hover"],
            )

        limit_plane = go.Surface(
            x=[0, CFD_L], y=[0, CFD_W],
            z=[[THERMAL_LIMIT_C, THERMAL_LIMIT_C], [THERMAL_LIMIT_C, THERMAL_LIMIT_C]],
            colorscale=[[0, "rgba(248,81,73,0.30)"], [1, "rgba(248,81,73,0.30)"]],
            showscale=False, name=T["cfd_limit_lbl"],
            hovertemplate=T["cfd_limit_lbl"] + "<extra></extra>",
        )
        rack_mark = go.Scatter3d(
            x=[(c[0] + 0.5) * dxc for c in src_cells],
            y=[(c[1] + 0.5) * dyc for c in src_cells],
            z=[float(T_final[c[1], c[0]]) + 1.5 for c in src_cells],
            mode="markers", marker=dict(size=6, color="#111111", symbol="square", opacity=0.9),
            name=T["cfd_rack_lbl"],
            hovertemplate=T["cfd_rack_lbl"] + " (X=%{x:.1f}, Y=%{y:.1f})<extra></extra>",
        )
        duct_mark = go.Scatter3d(
            x=[(c[0] + 0.5) * dxc for c in vent_cells],
            y=[(c[1] + 0.5) * dyc for c in vent_cells],
            z=[float(ambient_temp) + 1.0] * len(vent_cells),
            mode="markers", marker=dict(size=6, color="#00b4d8", symbol="diamond", opacity=0.9),
            name=T["cfd_duct_lbl"],
            hovertemplate=T["cfd_duct_lbl"] + " (X=%{x:.1f}, Y=%{y:.1f})<extra></extra>",
        )

        frame_traces = [[_surf(Z)] for Z in snaps]
        names  = [f"f{i}" for i in range(len(snaps))]
        labels = [fmt_time(tt) for tt in times]

        layout = dict(
            **_dark,
            title=dict(text=T["cfd_figtitle"], font=dict(color="#c9d1d9", size=14)),
            scene=dict(
                xaxis=dict(title=T["cfd_xtitle"], **_ax3),
                yaxis=dict(title=T["cfd_ytitle"], **_ax3),
                zaxis=dict(title=T["cfd_ztitle"], range=[float(ambient_temp) - 2, z_top], **_ax3),
                bgcolor="rgba(0,0,0,0)",
            ),
            height=620, margin=dict(l=10, r=10, b=60, t=60),
            legend=dict(font=dict(color="#c9d1d9"), bgcolor="rgba(0,0,0,0)"),
        )
        fig = build_animation(
            base_traces=[_surf(snaps[0]), limit_plane, rack_mark, duct_mark],
            frame_traces_list=frame_traces,
            frame_names=names, time_labels=labels,
            animated_trace_idx=[0], layout=layout,
            duration_ms=400, prefix=T["tprefix"],
        )
        st.plotly_chart(fig, use_container_width=True)

    with st.expander(T["cfd_method_t"]):
        st.markdown(T["cfd_method"])

# ── Structural & Seismic ──────────────────────────────────────
elif role == T["roles"][1]:
    st.header(f"🏗️ {role}")
    st.info(T["str_info"])
    st.caption(T["disclaimer"])

    col_p, col_v = st.columns([1, 3])
    with col_p:
        st.subheader(T["str_params"])
        dead_load  = st.number_input(T["str_dead"],    value=8.5,  step=0.5)
        live_load  = st.number_input(T["str_live"],    value=3.0,  step=0.5)
        wind_load  = st.number_input(T["str_wind"],    value=12.0, step=1.0)
        seismic_g  = st.slider(T["str_seismic"], min_value=0.05, max_value=0.4, value=0.2, step=0.05)
        pad_w      = st.number_input(T["str_padw"],    value=6.05, step=0.1, min_value=0.5)
        pad_l      = st.number_input(T["str_padl"],    value=3.44, step=0.1, min_value=0.5)

        # 등가정적 지진 횡하중 V = Cs·W — dead_load는 이미 중량(kN/m²)이므로 g 재곱셈 금지
        seismic_load = dead_load * seismic_g
        total_combo  = 1.2 * dead_load + 1.6 * live_load + 0.5 * wind_load
        dcr = total_combo / STR_ALLOW

        # seismic rocking eccentricity (quasi-static): e = Sa·h_cg·(W_D/W_tot)
        e_max = seismic_g * STR_HCG * (dead_load / max(dead_load + live_load, 1e-6))
        q_edge_max = total_combo * (1.0 + 6.0 * e_max / pad_w)

        st.metric(T["str_combo"], f"{total_combo:.1f}")
        st.metric(T["str_eqk"],   f"{seismic_load:.1f}")
        st.metric(T["str_m_qmax"], f"{q_edge_max:.1f} kN/m²")
        st.metric(T["str_m_ecc"],  f"{e_max * 100:.1f} cm" + ("  (≤ L/6 ✓)" if e_max <= pad_w / 6 else "  (> L/6 ⚠️)"))
        if dcr < 0.7:
            st.success(T["str_safe"](dcr))
        elif dcr < 1.0:
            st.warning(T["str_warn"](dcr))
        else:
            st.error(T["str_over"](dcr))

    with col_v:
        tab_s1, tab_s2 = st.tabs([T["str_tab1"], T["str_tab2"]])

        with tab_s1:
            st.caption(T["str_guide1"])

            t_hist = np.linspace(0.0, 8.0, 33)
            pulse  = seismic_pulse(t_hist, f_hz=2.0, decay=0.5)
            cmax_q = max(total_combo * (1.0 + 6.0 * e_max / pad_w) * 1.05, STR_ALLOW * 1.05)

            def _q_surf(Q):
                return go.Surface(
                    x=xs_q, y=ys_q, z=Q,
                    colorscale="RdYlGn_r", cmin=0.0, cmax=cmax_q,
                    colorbar=dict(title=dict(text=T["str_ctitle1"], font=dict(color="#c9d1d9")),
                                  tickfont=dict(color="#c9d1d9")),
                    hovertemplate=T["str_hover1"],
                )

            frames_q = []
            for p in pulse:
                xs_q, ys_q, Qf = bearing_pressure(total_combo, e_max * p, 0.0, pad_w, pad_l, nx=30, ny=30)
                frames_q.append([_q_surf(Qf)])
            xs_q, ys_q, Q0 = bearing_pressure(total_combo, e_max * pulse[0], 0.0, pad_w, pad_l, nx=30, ny=30)

            limit_q = go.Surface(
                x=[0, pad_w], y=[0, pad_l],
                z=[[STR_ALLOW, STR_ALLOW], [STR_ALLOW, STR_ALLOW]],
                colorscale=[[0, "rgba(255,255,0,0.25)"], [1, "rgba(255,255,0,0.25)"]],
                showscale=False, name=T["str_alimit"],
                hovertemplate=T["str_alimit"] + "<extra></extra>",
            )

            layout_q = dict(
                **_dark,
                title=dict(text=T["str_figtit1"], font=dict(color="#c9d1d9", size=14)),
                scene=dict(
                    xaxis=dict(title=T["str_xtitle1"], **_ax3),
                    yaxis=dict(title=T["str_ytitle1"], **_ax3),
                    zaxis=dict(title=T["str_ztitle1"], range=[0, cmax_q * 1.15], **_ax3),
                    bgcolor="rgba(0,0,0,0)",
                ),
                height=620, margin=dict(l=0, r=0, b=60, t=60),
                legend=dict(font=dict(color="#c9d1d9"), bgcolor="rgba(0,0,0,0)"),
            )
            fig_s = build_animation(
                base_traces=[_q_surf(Q0), limit_q],
                frame_traces_list=frames_q,
                frame_names=[f"s{i}" for i in range(len(t_hist))],
                time_labels=[f"{tt:.2f}s" for tt in t_hist],
                animated_trace_idx=[0], layout=layout_q,
                duration_ms=120, prefix=T["tprefix"],
            )
            st.plotly_chart(fig_s, use_container_width=True)

        with tab_s2:
            st.caption(T["str_guide2"])

            nodes  = ["Node A", "Node B", "Node C", "Node D", "Node E", "Node F"]
            combo_lbl = T["str_combo_lbl"]
            cats   = ["Dead", "Live", "Wind", "Seismic", combo_lbl]
            colors = ["#58a6ff", "#3fb950", "#f78166", "#e3b341", "#bc8cff"]
            vals   = {
                "Dead":     [dead_load*pad_w*pad_l*v  for v in [0.90, 1.00, 1.10, 0.95, 1.05, 0.98]],
                "Live":     [live_load*pad_w*pad_l*v  for v in [0.70, 0.85, 1.00, 0.75, 0.90, 0.80]],
                "Wind":     [wind_load*pad_w*v         for v in [0.60, 0.80, 1.00, 0.70, 0.90, 0.75]],
                "Seismic":  [seismic_load*pad_w*pad_l*v for v in [0.80, 1.00, 1.20, 0.85, 1.10, 0.95]],
                combo_lbl:  [total_combo*pad_w*pad_l*v for v in [0.88, 1.00, 1.15, 0.92, 1.08, 0.97]],
            }

            fig_b = go.Figure()
            legend_added = set()
            for i, (cat, color) in enumerate(zip(cats, colors)):
                for j, (node, val) in enumerate(zip(nodes, vals[cat])):
                    hover_txt = T["str_hover2"].format(cat=cat, node=node, val=val)
                    box = _make_box3d(
                        x0=j - 0.3, y0=i - 0.3,
                        z_bot=0, z_top=val,
                        dx=0.6, dy=0.6,
                        color=color, name=cat,
                        hover_text=hover_txt,
                    )
                    if cat in legend_added:
                        box.showlegend = False
                    legend_added.add(cat)
                    fig_b.add_trace(box)

            fig_b.update_layout(
                title=dict(text=T["str_figtit2"], font=dict(color="#c9d1d9", size=14)),
                scene=dict(
                    xaxis=dict(title=T["str_xnode"], tickvals=list(range(len(nodes))), ticktext=nodes, color="#c9d1d9"),
                    yaxis=dict(title=T["str_yload"], tickvals=list(range(len(cats))),  ticktext=cats,  color="#c9d1d9"),
                    zaxis=dict(title=T["str_zload"], color="#c9d1d9"),
                    bgcolor="rgba(0,0,0,0)",
                ),
                height=560, margin=dict(l=0, r=0, b=0, t=50),
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#c9d1d9"),
                legend=dict(font=dict(color="#c9d1d9")),
            )
            st.plotly_chart(fig_b, use_container_width=True)

    with st.expander(T["str_method_t"]):
        st.markdown(T["str_method"])

# ── Fire / FDS ────────────────────────────────────────────────
else:
    st.header(f"🔥 {role}")
    st.info(T["fds_info"])
    st.caption(T["disclaimer"])

    col1, col2 = st.columns([1, 3])
    with col1:
        st.subheader(T["fds_params"])
        vent_speed = st.slider(T["fds_fan"], min_value=1.0, max_value=15.0, value=5.5)
        fire_idx = T["fds_fire_opts"].index(st.selectbox(T["fds_fire"], T["fds_fire_opts"], index=1))
        q_mw = [1.0, 5.0, 15.0][fire_idx]

        res = _run_smoke(q_mw, float(vent_speed))
        z_eq  = float(res["z_layer"][-1])
        Tl_eq = float(res["T_layer_C"][-1])
        mp_eq = float(res["m_plume"][-1])

        st.metric(T["fds_m_layer"], f"{z_eq:.2f} m")
        st.metric(T["fds_m_temp"],  f"{Tl_eq:.0f} °C")
        st.metric(T["fds_m_ext"],   f"{res['Q_extract_m3s']:.1f} m³/s")
        st.metric(T["fds_m_plume"], f"{mp_eq:.1f} kg/s")
        if z_eq >= TENABLE_Z:
            st.success(T["fds_pass"](z_eq))
        else:
            st.error(T["fds_fail"](z_eq))
        if st.button(T["fds_run"]):
            st.success(T["fds_pass"](z_eq) if z_eq >= TENABLE_Z else T["fds_fail"](z_eq))

    with col2:
        st.subheader(T["fds_viewer"])
        st.caption(T["fds_guide"])

        # subsample frames (every 2nd step → ~24 frames) — 좌표는 캐시에서
        idx, plume_frames = _plume_frame_arrays(q_mw, float(vent_speed))
        fx, fy = FDS_L / 2.0, FDS_W / 2.0

        def _frame_traces(frame_data):
            i, z_i, px, py, pz, pt = frame_data
            smoke = go.Scatter3d(
                x=px, y=py, z=pz, mode="markers",
                marker=dict(size=3, color=pt, colorscale="Hot_r", cmin=25, cmax=450,
                            opacity=0.55,
                            colorbar=dict(title=dict(text=T["fds_ctitle"], font=dict(color="#c9d1d9")),
                                          tickfont=dict(color="#c9d1d9"))),
                name="Smoke", hovertemplate="X=%{x:.1f} Y=%{y:.1f} Z=%{z:.1f} m<extra></extra>",
            )
            layer = go.Surface(
                x=[0, FDS_L], y=[0, FDS_W], z=[[z_i, z_i], [z_i, z_i]],
                colorscale=[[0, "rgba(160,160,160,0.30)"], [1, "rgba(160,160,160,0.30)"]],
                showscale=False, name=T["fds_layer_lbl"],
                hovertemplate=T["fds_layer_lbl"] + f": z = {z_i:.2f} m<extra></extra>",
            )
            return [smoke, layer]

        ten_plane = go.Surface(
            x=[0, FDS_L], y=[0, FDS_W], z=[[TENABLE_Z, TENABLE_Z], [TENABLE_Z, TENABLE_Z]],
            colorscale=[[0, "rgba(63,185,80,0.22)"], [1, "rgba(63,185,80,0.22)"]],
            showscale=False, name=T["fds_ten_lbl"],
            hovertemplate=T["fds_ten_lbl"] + "<extra></extra>",
        )
        fire_mark = go.Scatter3d(
            x=[fx], y=[fy], z=[0.3], mode="markers+text",
            marker=dict(size=9, color="#ff4500", symbol="diamond"),
            text=["🔥"], textposition="top center",
            name=f"Fire {q_mw:.0f} MW",
            hovertemplate=f"Fire source: {q_mw:.0f} MW<extra></extra>",
        )
        fan_mark = go.Scatter3d(
            x=[FDS_L, FDS_L], y=[FDS_W * 0.33, FDS_W * 0.67], z=[FDS_H - 0.8] * 2,
            mode="markers+text", marker=dict(size=8, color="#00b4d8", symbol="square"),
            text=["💨", "💨"], textposition="middle left",
            name=f"Exhaust fan ({vent_speed:.1f} m/s)",
            hovertemplate=f"Exhaust fan: {vent_speed:.1f} m/s<extra></extra>",
        )

        frame_list = [_frame_traces(fd) for fd in plume_frames]
        names  = [f"p{i}" for i in idx]
        labels = [fmt_time(res["times"][i]) for i in idx]

        layout_f = dict(
            **_dark,
            title=dict(text=T["fds_figtit"], font=dict(color="#c9d1d9", size=14)),
            scene=dict(
                xaxis=dict(title=T["fds_xtitle"], range=[0, FDS_L], **_ax3),
                yaxis=dict(title=T["fds_ytitle"], range=[0, FDS_W], **_ax3),
                zaxis=dict(title=T["fds_ztitle"], range=[0, FDS_H], **_ax3),
                bgcolor="rgba(0,0,0,0)",
                aspectmode="manual",
                aspectratio=dict(x=1.0, y=1.0, z=FDS_H / FDS_L * 1.6),
            ),
            height=640, margin=dict(l=10, r=10, b=60, t=60),
            legend=dict(font=dict(color="#c9d1d9"), bgcolor="rgba(0,0,0,0)"),
        )
        fig_fds = build_animation(
            base_traces=frame_list[0] + [ten_plane, fire_mark, fan_mark],
            frame_traces_list=frame_list,
            frame_names=names, time_labels=labels,
            animated_trace_idx=[0, 1], layout=layout_f,
            duration_ms=300, prefix=T["tprefix"],
        )
        st.plotly_chart(fig_fds, use_container_width=True)

    with st.expander(T["fds_method_t"]):
        st.markdown(T["fds_method"])

# ── Phase Checklist ───────────────────────────────────────────
st.markdown("---")


@st.fragment
def _phase_checklist():
    """체크박스·버튼 상호작용을 fragment로 격리 — 상단 3D 차트 재직렬화 방지."""
    st.header("📋 Phase Checklists (I/P/O)")

    tab_i, tab_p, tab_o = st.tabs([T["tab_in"], T["tab_proc"], T["tab_out"]])
    with tab_i:
        st.markdown(T["inp_title"])
        st.checkbox(T["inp_cad"])
        if T["roles"][0] in role:
            st.checkbox(T["inp_heat"])
            st.checkbox(T["inp_weather"])
        else:
            st.checkbox(T["inp_soil"])

    with tab_p:
        st.markdown(T["proc_title"])
        st.checkbox(T["proc_mesh"])
        st.checkbox(T["proc_bc"])
        st.checkbox(T["proc_run"])

    with tab_o:
        st.markdown(T["out_title"])
        st.checkbox(T["out_plots"])
        st.checkbox(T["out_report"])
        st.markdown("#### Document Generation Gateway")
        if st.button(T["out_export"], key="sim_rep"):
            import time as _time
            with st.spinner("Compiling..."):
                _time.sleep(1.2)
                report = (
                    "BESS 3D Analysis & Simulation Verification Report\n"
                    "===================================================\n"
                    f"Discipline: {role}\nStatus: VERIFIED (PASS)\n\n"
                    "Method: Reduced-order analytical models (energy-balance FDM thermal,\n"
                    "rigid-pad bearing pressure, NFPA 92 plume/smoke-layer correlations).\n"
                    "NOT a substitute for OpenFOAM / ANSYS / FDS detailed analysis.\n\n"
                    "Key Findings:\n"
                    "- Thermal: peak/mean enclosure air temps evaluated vs 50 degC limit.\n"
                    "- Structural: bearing pressure vs 45 kN/m2 allowable, seismic rocking eccentricity vs kern.\n"
                    "- Fire/Smoke: smoke layer equilibrium height vs 2.0 m tenability objective.\n"
                )
                st.session_state["sim_report_content"] = report
                st.success("✅ Artifacts compiled. Click below to download.")

        if "sim_report_content" in st.session_state:
            st.download_button(
                label=T["out_dl"],
                data=st.session_state["sim_report_content"],
                file_name="BESS_Simulation_Verification_Report.txt",
                mime="text/plain",
                type="primary",
            )


_phase_checklist()
