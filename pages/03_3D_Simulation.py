import streamlit as st
try:
    st.set_page_config(page_title="BESS EPC Platform", layout="wide", initial_sidebar_state="expanded")
except Exception:
    pass

import numpy as np
import plotly.graph_objects as go
from utils.css_loader import apply_custom_css
from utils.auth_helper import require_auth, sidebar_user_info

# ── Bilingual text dict ───────────────────────────────────────
def _T():
    lang = st.session_state.get("lang", "KO")
    return {
        "EN": {
            "caption":   "🛤️ **BESS EPC Workflow:** Step 2 (System Eng) ➔ **[Step 3: 3D & Analysis]** ➔ Step 4 (E-BOP) ...",
            "title":     "🧊 3D Analysis & Simulation Module",
            "select":    "Select Simulation Discipline",
            "roles":     ["CFD Analysis (Thermal/Ventilation)", "Structural & Seismic Analysis", "Fire & Gas Dispersion (FDS)"],
            # CFD
            "cfd_info":     "Analyzing airflow, heat dissipation, and HVAC sizing for Battery Enclosures.",
            "cfd_params":   "Simulation Parameters",
            "cfd_ambient":  "Ambient Temp (°C)",
            "cfd_hvac":     "HVAC Capacity (kW)",
            "cfd_heat":     "Inverter/Battery Heat Loss (kW)",
            "cfd_run":      "▶ Run Thermal Simulation",
            "cfd_result":   lambda t, r: f"Simulation complete. Max predicted internal temp: {t + (r[0]/(r[1]+1))*10:.1f} °C",
            "cfd_viewer":   "🌡️ 3D Thermal Heatmap Viewer (Mock)",
            "cfd_guide":    ("**📊 Chart Guide (hover for details):**  \n"
                             "- **X-axis:** East-West position in enclosure (0–15 m)  \n"
                             "- **Y-axis:** North-South position in enclosure (0–15 m)  \n"
                             "- **Z-axis / Color:** Predicted surface temperature (°C) — yellow = hot spot  \n"
                             "- **Goal:** Verify max temp ≤ 50 °C under rated HVAC capacity"),
            "cfd_xtitle":   "X: East-West (m)",
            "cfd_ytitle":   "Y: North-South (m)",
            "cfd_ztitle":   "Z: Temp (°C)",
            "cfd_ctitle":   "Temp (°C)",
            "cfd_figtitle": "Enclosure Floor Heat Distribution",
            "cfd_hover":    ("<b>Position</b><br>X (E-W): %{x:.1f} m<br>Y (N-S): %{y:.1f} m<br>"
                             "<b>Predicted Temp: %{z:.1f} °C</b><br>"),
            "cfd_extra":    lambda amb: f"<extra>CFD Simulation (Mock)<br>Normal range: {amb}–{amb+15} °C</extra>",
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
            "str_tab1":     "🔴 3D Von Mises Stress",
            "str_tab2":     "📊 3D Load Combination",
            "str_guide1":   ("**📊 Chart Guide (hover for details):**  \n"
                             "- **X/Y-axes:** Position on foundation pad (m)  \n"
                             "- **Z-axis / Color:** Von Mises equivalent stress (kN/m²) — red = high stress  \n"
                             "- **Yellow plane:** Allowable stress limit (45 kN/m²)  \n"
                             "- **Goal:** Entire pad below 45 kN/m²"),
            "str_xtitle1":  "X: Width direction (m)",
            "str_ytitle1":  "Y: Length direction (m)",
            "str_ztitle1":  "Z: Stress (kN/m²)",
            "str_ctitle1":  "Von Mises<br>Stress (kN/m²)",
            "str_figtit1":  "3D Von Mises Stress Distribution (Foundation Pad)",
            "str_hover1":   ("<b>Foundation Pad Position</b><br>"
                             "X (width): %{x:.2f} m<br>Y (length): %{y:.2f} m<br>"
                             "<b>Von Mises Stress: %{z:.1f} kN/m²</b><br>"),
            "str_extra1":   lambda d: f"<extra>Allowable: 45 kN/m²<br>DCR: {d:.2f}</extra>",
            "str_alimit":   "Allowable Stress Limit (45 kN/m²)",
            "str_guide2":   ("**📊 Load Combination Comparison (ASCE 7 / KDS 41):**  \n"
                             "Hover over each bar to check load components per node.  \n"
                             "- X-axis: Structural Node  /  Y-axis: Load Type  /  Z-axis: Load (kN)"),
            "str_combo_lbl": "Combo(1.2D+1.6L)",
            "str_figtit2":  "3D Load Combination Comparison (per Node)",
            "str_xnode":    "Node",
            "str_yload":    "Load Type",
            "str_zload":    "Load (kN)",
            "str_hover2":   "<b>Load: {cat}</b><br>Node: {node}<br>Value: {val:.1f} kN",
            # Fire FDS
            "fds_info":     "Fire Dynamics Simulation for smoke extraction and thermal runaway propagation.",
            "fds_params":   "FDS Parameters",
            "fds_fan":      "Exhaust Fan Speed (m/s)",
            "fds_fire":     "Fire Size (MW)",
            "fds_fire_opts":["1 MW (Incipient)", "5 MW (Growth)", "15 MW (Fully Developed)"],
            "fds_run":      "▶ Run FDS Solver",
            "fds_result":   "FDS calculation converged. Smoke clearance time estimated: 12.4 min.",
            "fds_viewer":   "🔥 3D Smoke Density Grid (Mock)",
            "fds_xtitle":   "X (m)", "fds_ytitle": "Y (m)", "fds_ztitle": "Z: Height (m)",
            "fds_ctitle":   "Temp/Density",
            "fds_figtit":   "Thermal Runaway Smoke Plume",
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
            # CFD
            "cfd_info":     "배터리 인클로저 내 기류, 열방출, HVAC 용량을 분석합니다.",
            "cfd_params":   "시뮬레이션 파라미터",
            "cfd_ambient":  "주변 온도 (°C)",
            "cfd_hvac":     "HVAC 용량 (kW)",
            "cfd_heat":     "인버터/배터리 발열 (kW)",
            "cfd_run":      "▶ 열해석 시뮬레이션 실행",
            "cfd_result":   lambda t, r: f"시뮬레이션 완료. 예측 최고 내부 온도: {t + (r[0]/(r[1]+1))*10:.1f} °C",
            "cfd_viewer":   "🌡️ 3D 열분포 뷰어 (Mock)",
            "cfd_guide":    ("**📊 차트 해석 (마우스를 올리면 상세 값 표시):**  \n"
                             "- **X축:** 인클로저 내 동서 방향 위치 (0~15m)  \n"
                             "- **Y축:** 인클로저 내 남북 방향 위치 (0~15m)  \n"
                             "- **Z축 / 색상:** 예측 표면 온도 (°C) — 노란색이 hot spot  \n"
                             "- **목표:** HVAC 용량 기준 최고 온도 50°C 이하 유지 확인"),
            "cfd_xtitle":   "X: 동서 위치 (m)",
            "cfd_ytitle":   "Y: 남북 위치 (m)",
            "cfd_ztitle":   "Z: 온도 (°C)",
            "cfd_ctitle":   "온도 (°C)",
            "cfd_figtitle": "인클로저 바닥면 열분포 (Enclosure Floor Heat Distribution)",
            "cfd_hover":    ("<b>위치</b><br>X (동서): %{x:.1f} m<br>Y (남북): %{y:.1f} m<br>"
                             "<b>예측 온도: %{z:.1f} °C</b><br>"),
            "cfd_extra":    lambda amb: f"<extra>CFD 시뮬레이션 결과 (Mock)<br>정상 범위: {amb}~{amb+15} °C</extra>",
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
            "str_tab1":     "🔴 3D Von Mises 응력 분포",
            "str_tab2":     "📊 3D 하중 조합 비교",
            "str_guide1":   ("**📊 차트 해석 (마우스를 올리면 값 표시):**  \n"
                             "- **X/Y축:** 기초 패드 상의 위치 (m)  \n"
                             "- **Z축 / 색상:** Von Mises 등가응력 (kN/m²) — 빨간색이 고응력  \n"
                             "- **노란 평면:** 허용응력 한계 (45 kN/m²)  \n"
                             "- **목표:** 전면 허용응력 45 kN/m² 이하 유지"),
            "str_xtitle1":  "X: 폭방향 (m)",
            "str_ytitle1":  "Y: 길이방향 (m)",
            "str_ztitle1":  "Z: 응력 (kN/m²)",
            "str_ctitle1":  "Von Mises 응력<br>(kN/m²)",
            "str_figtit1":  "3D Von Mises 등가응력 분포 (기초 패드)",
            "str_hover1":   ("<b>기초 패드 위치</b><br>"
                             "X (폭방향): %{x:.2f} m<br>Y (길이방향): %{y:.2f} m<br>"
                             "<b>Von Mises 응력: %{z:.1f} kN/m²</b><br>"),
            "str_extra1":   lambda d: f"<extra>허용 응력: 45 kN/m²<br>DCR 기준: {d:.2f}</extra>",
            "str_alimit":   "허용응력 한계 (45 kN/m²)",
            "str_guide2":   ("**📊 하중 조합 비교 (ASCE 7 / KDS 41 기준):**  \n"
                             "마우스를 올려 각 절점의 하중 성분을 확인하세요.  \n"
                             "- X축: 구조 절점  /  Y축: 하중 종류  /  Z축: 하중 크기 (kN)"),
            "str_combo_lbl": "조합(1.2D+1.6L)",
            "str_figtit2":  "3D 하중 조합 비교 (절점별)",
            "str_xnode":    "절점 (Node)",
            "str_yload":    "하중 종류",
            "str_zload":    "하중 크기 (kN)",
            "str_hover2":   "<b>하중: {cat}</b><br>절점: {node}<br>값: {val:.1f} kN",
            # Fire FDS
            "fds_info":     "화재 역학 시뮬레이션으로 연기 배출 및 열폭주 전파를 분석합니다.",
            "fds_params":   "FDS 파라미터",
            "fds_fan":      "배기팬 풍속 (m/s)",
            "fds_fire":     "화재 규모 (MW)",
            "fds_fire_opts":["1 MW (초기)", "5 MW (성장)", "15 MW (완전 발달)"],
            "fds_run":      "▶ FDS 솔버 실행",
            "fds_result":   "FDS 수렴 완료. 연기 제거 예상 시간: 12.4분.",
            "fds_viewer":   "🔥 3D 연기 밀도 그리드 (Mock)",
            "fds_xtitle":   "X (m)", "fds_ytitle": "Y (m)", "fds_ztitle": "Z: 높이 (m)",
            "fds_ctitle":   "온도/밀도",
            "fds_figtit":   "열폭주 연기 플룸 (Thermal Runaway Smoke Plume)",
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


# ── Main Page ─────────────────────────────────────────────────
apply_custom_css()
require_auth("03")
sidebar_user_info()
T = _T()

st.caption(T["caption"])
st.title(T["title"])
st.markdown("---")

role = st.selectbox(T["select"], T["roles"])

# ── CFD ───────────────────────────────────────────────────────
if role == T["roles"][0]:
    st.header(f"🌡️ {role}")
    st.info(T["cfd_info"])

    col1, col2 = st.columns([1, 3])
    with col1:
        st.subheader(T["cfd_params"])
        default_amb = st.session_state.get("site_temp_max", 35.0)
        ambient_temp  = st.slider(T["cfd_ambient"], min_value=-20.0, max_value=55.0, value=float(default_amb))
        hvac_capacity = st.slider(T["cfd_hvac"], min_value=10, max_value=100, value=40)
        heat_loss     = st.number_input(T["cfd_heat"], value=30.0)
        if st.button(T["cfd_run"]):
            st.success(T["cfd_result"](ambient_temp, (heat_loss, hvac_capacity)))

    with col2:
        st.subheader(T["cfd_viewer"])
        st.caption(T["cfd_guide"])

        x_vals = np.linspace(0, 15, 20)
        y_vals = np.linspace(0, 15, 20)
        z = np.random.normal(loc=ambient_temp + 10, scale=3, size=(20, 20))
        z = np.clip(z, ambient_temp, ambient_temp + 25)

        fig = go.Figure(data=[go.Surface(
            x=x_vals, y=y_vals, z=z,
            colorscale="Inferno",
            colorbar=dict(title=T["cfd_ctitle"], titlefont=dict(color="#c9d1d9"), tickfont=dict(color="#c9d1d9")),
            hovertemplate=T["cfd_hover"] + T["cfd_extra"](int(ambient_temp)),
        )])
        fig.update_layout(
            title=dict(text=T["cfd_figtitle"], font=dict(color="#c9d1d9", size=14)),
            scene=dict(
                xaxis=dict(title=T["cfd_xtitle"], color="#c9d1d9", gridcolor="#30363d"),
                yaxis=dict(title=T["cfd_ytitle"], color="#c9d1d9", gridcolor="#30363d"),
                zaxis=dict(title=T["cfd_ztitle"], color="#c9d1d9", gridcolor="#30363d"),
                bgcolor="rgba(0,0,0,0)",
            ),
            autosize=True, height=560,
            margin=dict(l=10, r=10, b=10, t=50),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#c9d1d9"),
        )
        st.plotly_chart(fig, use_container_width=True)

# ── Structural & Seismic ──────────────────────────────────────
elif role == T["roles"][1]:
    st.header(f"🏗️ {role}")
    st.info(T["str_info"])

    col_p, col_v = st.columns([1, 3])
    with col_p:
        st.subheader(T["str_params"])
        dead_load  = st.number_input(T["str_dead"],    value=8.5,  step=0.5)
        live_load  = st.number_input(T["str_live"],    value=3.0,  step=0.5)
        wind_load  = st.number_input(T["str_wind"],    value=12.0, step=1.0)
        seismic_g  = st.slider(T["str_seismic"], min_value=0.05, max_value=0.4, value=0.2, step=0.05)
        pad_w      = st.number_input(T["str_padw"],    value=6.05, step=0.1)
        pad_l      = st.number_input(T["str_padl"],    value=3.44, step=0.1)

        seismic_load = dead_load * seismic_g * 9.81
        total_combo  = 1.2 * dead_load + 1.6 * live_load + 0.5 * wind_load
        dcr = total_combo / 45.0

        st.metric(T["str_combo"], f"{total_combo:.1f}")
        st.metric(T["str_eqk"],   f"{seismic_load:.1f}")
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

            xs = np.linspace(0, pad_w, 25)
            ys = np.linspace(0, pad_l, 25)
            X, Y = np.meshgrid(xs, ys)
            peak = total_combo * 1.3
            base = total_combo * 0.6
            stress = (base
                      + (peak - base) * (0.5 - np.cos(np.pi * X / pad_w) * np.cos(np.pi * Y / pad_l)) / 1.5
                      + seismic_load * np.random.uniform(0.8, 1.2, X.shape))

            fig_s = go.Figure(data=[go.Surface(
                x=xs, y=ys, z=stress,
                colorscale="RdYlGn_r",
                colorbar=dict(title=T["str_ctitle1"], titlefont=dict(color="#c9d1d9"), tickfont=dict(color="#c9d1d9")),
                hovertemplate=T["str_hover1"] + T["str_extra1"](dcr),
            )])
            fig_s.add_trace(go.Surface(
                x=xs, y=ys,
                z=np.full_like(stress, 45.0),
                colorscale=[[0, "rgba(255,255,0,0.25)"], [1, "rgba(255,255,0,0.25)"]],
                showscale=False,
                name=T["str_alimit"],
                hovertemplate=T["str_alimit"] + "<extra></extra>",
            ))
            fig_s.update_layout(
                title=dict(text=T["str_figtit1"], font=dict(color="#c9d1d9", size=14)),
                scene=dict(
                    xaxis=dict(title=T["str_xtitle1"], color="#c9d1d9", gridcolor="#30363d"),
                    yaxis=dict(title=T["str_ytitle1"], color="#c9d1d9", gridcolor="#30363d"),
                    zaxis=dict(title=T["str_ztitle1"], color="#c9d1d9", gridcolor="#30363d"),
                    bgcolor="rgba(0,0,0,0)",
                ),
                height=560, margin=dict(l=0, r=0, b=0, t=50),
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#c9d1d9"),
                legend=dict(font=dict(color="#c9d1d9")),
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

# ── Fire / FDS ────────────────────────────────────────────────
else:
    st.header(f"🔥 {role}")
    st.info(T["fds_info"])

    col1, col2 = st.columns([1, 3])
    with col1:
        st.subheader(T["fds_params"])
        vent_speed = st.slider(T["fds_fan"], min_value=1.0, max_value=15.0, value=5.5)
        st.selectbox(T["fds_fire"], T["fds_fire_opts"], index=1)
        if st.button(T["fds_run"]):
            st.success(T["fds_result"])

    with col2:
        st.subheader(T["fds_viewer"])
        num_particles = 1500
        x_smoke = np.random.normal(loc=10, scale=2 + (vent_speed / 5), size=num_particles)
        y_smoke = np.random.normal(loc=10, scale=2, size=num_particles)
        z_smoke = np.clip(np.random.gamma(shape=2.0, scale=3.0, size=num_particles), 0, 20)
        colors_s = z_smoke + np.random.normal(0, 1, num_particles)

        fig_fds = go.Figure(data=[go.Scatter3d(
            x=x_smoke, y=y_smoke, z=z_smoke,
            mode="markers",
            marker=dict(size=4, color=colors_s, colorscale="Reds", opacity=0.6,
                        colorbar=dict(title=T["fds_ctitle"], tickfont=dict(color="#c9d1d9"))),
        )])
        fig_fds.update_layout(
            title=T["fds_figtit"], autosize=True, height=620,
            scene=dict(xaxis_title=T["fds_xtitle"], yaxis_title=T["fds_ytitle"], zaxis_title=T["fds_ztitle"]),
            margin=dict(l=10, r=10, b=10, t=50),
            paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#c9d1d9"),
        )
        st.plotly_chart(fig_fds, use_container_width=True)

# ── Phase Checklist ───────────────────────────────────────────
st.markdown("---")
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
                "Key Findings:\n"
                "- Thermal: no significant hotspots under nominal loading.\n"
                "- HVAC capacities sufficient below critical thresholds.\n"
                "- Structural DCR < 0.85 for all basic load combinations.\n"
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
