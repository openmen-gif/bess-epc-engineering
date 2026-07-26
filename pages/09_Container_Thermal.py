# -*- coding: utf-8 -*-
"""
09_Container_Thermal.py
배터리 컨테이너 내부 3D 열유동 시뮬레이션
Battery Container Internal 3D Thermal Flow Simulation
"""
import streamlit as st
try:
    st.set_page_config(page_title="BESS EPC Platform", layout="wide", initial_sidebar_state="auto")
except Exception:
    pass

import numpy as np
import plotly.graph_objects as go
from utils.css_loader import apply_custom_css
from utils.lang_helper import t
from utils.auth_helper import require_auth, sidebar_user_info
from utils.theme import PALETTE, CBAR
from utils.sim_physics import (
    heat2d_transient, stratification_profile,
    airflow_trajectories, build_animation, fmt_time,
)

# Display grid for HVAC vent selector (columns × rows)
HVAC_NX, HVAC_NY = 10, 4

# Physical snapshot times for the heat-up transient animation [s]
SNAP_TIMES_S = list(range(0, 1801, 60))   # 0~30분, 60초 균일 31프레임(부드러운 재생/스크럽)

# 공기 흐름(Tab 3) — 랙 유동 장애물 반경 [m] ≈ 랙 폭 0.6~0.7 m의 절반
RACK_R_M = 0.35
# airflow_trajectories() 기본 u_ref와 동일 — 파티클 색상을 유속비 V/V∞로 정규화하는 기준
AF_U_REF = 0.55
# 하이퍼카 공기흐름 레퍼런스 범례(파랑→시안→녹→노랑→빨강)와 동일한 HSL 계열 색상축
AIRFLOW_HSL = [
    [0.00, "#2255ff"], [0.25, "#22ccdd"], [0.50, "#a8e05f"],
    [0.75, "#ffd23f"], [1.00, "#ff5a4e"],
]


# ── Solvers ───────────────────────────────────────────────────────────────────
from utils.config import IS_API_MODE, API_BASE_URL


@st.cache_data(show_spinner=False)
def _solve_local(nx, ny, dx, dy, ambient, heat_sources, hvac_kw, area_m2,
                 sim_vent_cells, bat_kw=50.0, con_h=2.59):
    """Local reduced-order FDM solver (physical time base).

    2-D depth-averaged energy balance:
      ρ·cp·H·∂T/∂t = k_eff·H·∇²T + q″_rack − G_hvac·(T − T_sup) − h_env·(T − T_amb)
    Rack heat enters as a SOURCE TERM (bat_kw split over racks) and HVAC as a
    sensible-cooling conductance G = Q_rated/ΔT_design — i.e. the steady mean
    temperature follows the enclosure energy balance instead of a prescribed
    rack temperature."""
    Lx, Ly = nx * dx, ny * dy
    src_cells  = [(int(s[0]), int(s[1])) for s in heat_sources]
    vent_cells = [(int(v[0]), int(v[1])) for v in sim_vent_cells]
    _, snaps = heat2d_transient(
        Lx, Ly, con_h, ambient, src_cells, bat_kw * 1000.0,
        hvac_kw * 1000.0, vent_cells, nx, ny, SNAP_TIMES_S,
        alpha_eff=0.08, U_env=2.5, dT_design=12.0, src_sigma_m=0.45,
    )
    return snaps


def _solve_via_api(nx, ny, dx, dy, ambient, heat_sources, hvac_kw, area_m2, sim_vent_cells):
    """Call FastAPI backend for FDM computation."""
    import requests
    response = requests.post(
        f"{API_BASE_URL}/simulation/thermal",
        json={
            "nx": nx, "ny": ny, "dx": dx, "dy": dy,
            "ambient": ambient, "heat_sources": heat_sources,
            "hvac_kw": hvac_kw, "area_m2": area_m2,
            "sim_vent_cells": [(int(c[0]), int(c[1])) for c in sim_vent_cells],
        },
        timeout=30,
    )
    response.raise_for_status()
    return [np.array(snap) for snap in response.json()["snapshots"]]


def solve_temperature_transient(nx, ny, dx, dy, ambient, heat_sources,
                                 hvac_kw, area_m2, sim_vent_cells,
                                 bat_kw=50.0, con_h=2.59):
    """Dual-mode: API mode tries backend first with local fallback; standalone runs locally."""
    if IS_API_MODE:
        try:
            return _solve_via_api(nx, ny, dx, dy, ambient, heat_sources,
                                  hvac_kw, area_m2, sim_vent_cells)
        except Exception:
            pass
    return _solve_local(nx, ny, dx, dy, ambient, heat_sources,
                        hvac_kw, area_m2, sim_vent_cells,
                        bat_kw=bat_kw, con_h=con_h)


def make_heat_sources(nx, ny, n_racks, T_rack):
    sources, count = [], 0
    cols_g = max(1, int(np.sqrt(n_racks)))
    rows_g = int(np.ceil(n_racks / cols_g))
    xs = np.linspace(2, nx - 3, cols_g, dtype=int)
    ys = np.linspace(2, ny - 3, rows_g, dtype=int)
    for iy in ys:
        for ix in xs:
            if count >= n_racks:
                break
            sources.append((int(ix), int(iy), T_rack))
            count += 1
    return sources


def build_3d_field(T_floor, ambient, con_h, nz=14):
    """Extrude the 2-D depth-averaged field with a linear stratification
    profile p(z): depth-average = 1.0, ceiling ≈ 2× floor excess temperature
    (buoyant hot air accumulates at the ceiling)."""
    z_vals  = np.linspace(0.0, con_h, nz)
    profile = stratification_profile(z_vals, con_h, ratio=2.0)
    T_3d    = ambient + np.einsum('z,yx->zyx', profile, T_floor - ambient)
    return T_3d, z_vals


def scale_vents_to_sim(hvac_vents, NX, NY):
    """Map display-grid vent coords to simulation-grid coords."""
    result = []
    for (vx, vy) in hvac_vents:
        sx = min(max(int(round(vx * NX / HVAC_NX)), 1), NX - 2)
        sy = min(max(int(round(vy * NY / HVAC_NY)), 1), NY - 2)
        result.append((sx, sy))
    return result


@st.cache_data(show_spinner=False)
def _airflow_traj_cached(T_floor, exhaust_xy, intake_xy, rack_xy, Lx, Ly, H, T_amb, wake_gain=1.0):
    """퍼텐셜 유동+랙 다이폴 회절/후류+부력 파티클 궤적 사전 계산 (동일 결과 재사용)."""
    return airflow_trajectories(T_floor, list(exhaust_xy), list(intake_xy),
                                Lx, Ly, H, rack_xy=list(rack_xy), rack_r=RACK_R_M,
                                wake_gain=wake_gain, n_particles=150, n_frames=60,
                                dt=0.35, T_amb=T_amb, u_ref=AF_U_REF)


@st.cache_data(show_spinner=False)
def vent_airflow_vectors(T_floor, sim_exhaust_cells, sim_intake_cells, NX, NY):
    """Return U, V arrays. Exhaust: flow toward duct. Intake: flow away from duct."""
    all_cells = list(sim_exhaust_cells) + list(sim_intake_cells)
    if not all_cells:
        gy, gx = np.gradient(T_floor)
        return -gx * 0.05, -gy * 0.05

    U = np.zeros((NY, NX))
    V = np.zeros((NY, NX))
    vx_all   = np.array([v[0] for v in all_cells], dtype=float)
    vy_all   = np.array([v[1] for v in all_cells], dtype=float)
    # +1 = exhaust (flow toward), -1 = intake (flow away)
    signs    = np.array([1.0] * len(sim_exhaust_cells) + [-1.0] * len(sim_intake_cells))

    for iy in range(NY):
        for ix in range(NX):
            dists   = (vx_all - ix) ** 2 + (vy_all - iy) ** 2
            nearest = int(np.argmin(dists))
            dvx = float(vx_all[nearest]) - ix
            dvy = float(vy_all[nearest]) - iy
            mag = max(np.sqrt(dvx ** 2 + dvy ** 2), 0.1)
            U[iy, ix] = signs[nearest] * dvx / mag * 0.05
            V[iy, ix] = signs[nearest] * dvy / mag * 0.05
    return U, V


# ── Main Module ───────────────────────────────────────────────────────────────
def run_container_thermal_module():
    apply_custom_css()
    require_auth("09")
    sidebar_user_info()
    lang  = st.session_state.get('lang', 'KO')
    is_en = (lang == 'EN')

    st.caption(t("p9_caption"))
    st.title(t("p9_title"))
    st.markdown("---")
    st.info(t("p9_info"))

    # ── 담당 부분 (Responsible Discipline) ───────────────────────────────────
    with st.expander("👷 " + ("담당 부분 지정" if not is_en else "Responsible Disciplines"), expanded=False):
        _disc_ko = ["HVAC 엔지니어", "열유동/소방 엔지니어", "안전 엔지니어", "기계 엔지니어", "전기 엔지니어", "PM"]
        _disc_en = ["HVAC Engineer", "Thermal/Fire Engineer", "Safety Engineer", "Mechanical Engineer", "Electrical Engineer", "PM"]
        _discs   = _disc_en if is_en else _disc_ko
        _ra, _rb = st.columns([3, 2])
        with _ra:
            st.multiselect(
                "담당 엔지니어링 분야" if not is_en else "Responsible Engineering Disciplines",
                _discs, default=_discs[:2], key="thermal_responsible",
            )
        with _rb:
            st.text_input(
                "담당자 이름" if not is_en else "Assignee Name",
                value=st.session_state.get("thermal_assignee", ""),
                key="thermal_assignee",
            )

    # ── Parameter Inputs ──────────────────────────────────────────────────────
    st.markdown(t("p9_params"))
    c1, c2, c3 = st.columns(3)

    with c1:
        amb = st.number_input(
            t("p9_amb"), min_value=-10.0, max_value=55.0,
            value=min(max(float(st.session_state.get('site_temp_max', 35.0)), -10.0), 55.0),
            step=1.0,
        )
        # 기본값은 '단일 컨테이너' 대표값 — 3.44 MWh급 0.5C 발열 ≈ 50 kW.
        # (기존 플랜트 총량 ×50 kW/MW 기본은 단일 컨테이너 형상에 2,500 kW를 넣어 항상 과열 판정)
        bat_kw = st.number_input(
            t("p9_bat_heat"), min_value=1.0, max_value=5000.0,
            value=50.0, step=10.0,
        )
        # HVAC 기본 60 kW — 발열 기본(50 kW)을 상회하는 적정 설계 출발점
        hvac_kw = st.number_input(
            t("p9_hvac_cap"), min_value=1.0, max_value=3000.0,
            value=60.0, step=5.0,
        )
    with c2:
        con_l = st.number_input(t("p9_con_l"), min_value=3.0,  max_value=30.0, value=12.19, step=0.5)
        con_w = st.number_input(t("p9_con_w"), min_value=1.5,  max_value=10.0, value=2.44,  step=0.1)
        con_h = st.number_input(t("p9_con_h"), min_value=1.5,  max_value=5.0,  value=2.59,  step=0.1)
    with c3:
        n_racks = int(st.number_input(t("p9_racks"), min_value=1, max_value=50, value=8, step=1))

    # ── HVAC Duct Position Selector ───────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        "#### 💨 " + ("HVAC 덕트 위치 설정" if not is_en else "HVAC Duct Positions")
    )
    st.caption(
        "셀 클릭 = 덕트 추가/제거 (파란 셀 = 덕트 위치) | 프리셋 버튼으로 빠르게 배치 가능" if not is_en
        else "Click a cell to add/remove a duct | Use preset buttons for quick layouts"
    )

    # Preset buttons
    pb1, pb2, pb3, pb4, _ = st.columns([1, 1, 1, 1, 3])
    with pb1:
        if st.button("⬛ " + ("양 끝" if not is_en else "End Walls"), key="hvac_p_ends"):
            _v = [(0, 1), (0, 2), (HVAC_NX - 1, 1), (HVAC_NX - 1, 2)]
            st.session_state["hvac_vents"] = _v
            st.session_state["hvac_vent_types"] = {(0, 1): "intake", (0, 2): "intake",
                                                    (HVAC_NX-1, 1): "exhaust", (HVAC_NX-1, 2): "exhaust"}
            st.rerun()
    with pb2:
        if st.button("⬛ " + ("중앙" if not is_en else "Center"), key="hvac_p_center"):
            mid = HVAC_NX // 2
            _v = [(mid - 1, 0), (mid, 0), (mid - 1, HVAC_NY - 1), (mid, HVAC_NY - 1)]
            st.session_state["hvac_vents"] = _v
            st.session_state["hvac_vent_types"] = {(mid-1, 0): "intake", (mid, 0): "intake",
                                                    (mid-1, HVAC_NY-1): "exhaust", (mid, HVAC_NY-1): "exhaust"}
            st.rerun()
    with pb3:
        if st.button("⬛ " + ("양 측면" if not is_en else "Side Walls"), key="hvac_p_sides"):
            _top = [(i, 0) for i in range(1, HVAC_NX - 1, 2)]
            _bot = [(i, HVAC_NY - 1) for i in range(1, HVAC_NX - 1, 2)]
            st.session_state["hvac_vents"] = _top + _bot
            st.session_state["hvac_vent_types"] = {v: "intake" for v in _top} | {v: "exhaust" for v in _bot}
            st.rerun()
    with pb4:
        if st.button("🗑 " + ("초기화" if not is_en else "Clear"), key="hvac_p_clear"):
            st.session_state["hvac_vents"] = []
            st.session_state["hvac_vent_types"] = {}
            st.rerun()

    # Default: end-wall vents (left=intake, right=exhaust)
    if "hvac_vents" not in st.session_state:
        st.session_state["hvac_vents"] = [(0, 1), (0, 2), (HVAC_NX - 1, 1), (HVAC_NX - 1, 2)]
    if "hvac_vent_types" not in st.session_state:
        st.session_state["hvac_vent_types"] = {
            (0, 1): "intake", (0, 2): "intake",
            (HVAC_NX - 1, 1): "exhaust", (HVAC_NX - 1, 2): "exhaust",
        }

    # Normalize to tuples (session state may contain lists after JSON round-trip)
    hvac_vents = [tuple(v) for v in st.session_state["hvac_vents"]]
    # Deduplicate while preserving order
    _seen: set = set()
    _dedup = []
    for _v in hvac_vents:
        if _v not in _seen:
            _seen.add(_v)
            _dedup.append(_v)
    if len(_dedup) != len(hvac_vents):
        st.session_state["hvac_vents"] = _dedup
        hvac_vents = _dedup

    # ── Button grid for duct toggle ────────────────────────────────────────
    hvac_vents_set = set(hvac_vents)
    hvac_vent_types = st.session_state.get("hvac_vent_types", {})

    # Column number header
    header_cols = st.columns([1] + [1] * HVAC_NX)
    header_cols[0].caption("Y/X")
    for gx in range(HVAC_NX):
        header_cols[gx + 1].caption(str(gx))

    for gy in range(HVAC_NY):
        row_cols = st.columns([1] + [1] * HVAC_NX)
        row_cols[0].caption(str(gy))
        for gx in range(HVAC_NX):
            with row_cols[gx + 1]:
                coord = (gx, gy)
                is_duct = coord in hvac_vents_set
                dtype = hvac_vent_types.get(coord, "exhaust") if is_duct else None
                label = ("🔵" if dtype == "intake" else "💨") if is_duct else "▫️"
                if st.button(
                    label,
                    key=f"hvac_{gx}_{gy}",
                    use_container_width=True,
                    type="primary" if is_duct else "secondary",
                ):
                    new_vents = [tuple(v) for v in st.session_state.get("hvac_vents", [])]
                    new_types = dict(st.session_state.get("hvac_vent_types", {}))
                    if coord not in new_vents:
                        new_vents.append(coord)
                        new_types[coord] = "exhaust"
                    elif new_types.get(coord) == "exhaust":
                        new_types[coord] = "intake"
                    else:
                        new_vents.remove(coord)
                        new_types.pop(coord, None)
                    st.session_state["hvac_vents"] = new_vents
                    st.session_state["hvac_vent_types"] = new_types
                    st.rerun()

    n_exhaust = sum(1 for v in hvac_vents if hvac_vent_types.get(v, "exhaust") == "exhaust")
    n_intake  = len(hvac_vents) - n_exhaust
    st.caption(
        f"💨 배기 덕트: {n_exhaust}개 | 🔵 흡기 덕트: {n_intake}개 | 클릭 순서: ▫️→💨(배기)→🔵(흡기)→제거" if not is_en
        else f"💨 Exhaust: {n_exhaust} | 🔵 Intake: {n_intake} | Click: ▫️→💨(exhaust)→🔵(intake)→remove"
    )

    # ── Run Button ────────────────────────────────────────────────────────────
    st.markdown("---")
    run = st.button(t("p9_run"), type="primary")

    if run or st.session_state.get("thermal_snapshots") is not None:
        NX, NY = 40, 20
        area   = con_l * con_w
        dx, dy = con_l / NX, con_w / NY

        # Indicative rack-surface temp (legacy API payload only — the local
        # solver injects bat_kw as a volumetric source term instead)
        cooling_eff = min(hvac_kw / max(bat_kw, 1.0), 2.0)
        dT    = max(5.0, 45.0 * max(0.05, 1.0 - 0.7 * min(cooling_eff, 1.0)))
        T_rack = amb + min(dT, 50.0)
        sources = make_heat_sources(NX, NY, n_racks, T_rack)

        # Scale HVAC vent positions to simulation grid (split by type)
        _vent_types   = st.session_state.get("hvac_vent_types", {})
        _exhaust_ui   = [v for v in hvac_vents if _vent_types.get(v, "exhaust") == "exhaust"]
        _intake_ui    = [v for v in hvac_vents if _vent_types.get(v, "exhaust") == "intake"]
        sim_exhaust   = scale_vents_to_sim(_exhaust_ui, NX, NY)
        sim_intake    = scale_vents_to_sim(_intake_ui,  NX, NY)
        sim_vents     = sim_exhaust + sim_intake  # all ducts for thermal simulation

        if run:
            with st.spinner("3D 시뮬레이션 계산 중…" if not is_en else "Running 3D simulation…"):
                snapshots = solve_temperature_transient(NX, NY, dx, dy, amb, sources,
                                                        hvac_kw, area, sim_vents,
                                                        bat_kw=bat_kw, con_h=con_h)
            snap_times = SNAP_TIMES_S[:len(snapshots)]
            st.session_state["thermal_snapshots"]   = snapshots
            st.session_state["thermal_times"]       = snap_times
            st.session_state["thermal_sources"]     = sources
            st.session_state["thermal_sim_vents"]   = sim_vents
            st.session_state["thermal_sim_exhaust"] = sim_exhaust
            st.session_state["thermal_sim_intake"]  = sim_intake
            st.session_state["thermal_params"]      = (NX, NY, dx, dy, amb, hvac_kw, area, con_l, con_w, con_h)
            st.session_state["thermal_snap_slider"] = 0
        else:
            snapshots   = st.session_state["thermal_snapshots"]
            snap_times  = st.session_state.get("thermal_times", SNAP_TIMES_S[:len(snapshots)])
            sources     = st.session_state.get("thermal_sources", sources)
            sim_vents   = st.session_state.get("thermal_sim_vents",   sim_vents)
            sim_exhaust = st.session_state.get("thermal_sim_exhaust", sim_vents)
            sim_intake  = st.session_state.get("thermal_sim_intake",  [])
            NX, NY, dx, dy, amb, hvac_kw, area, con_l, con_w, con_h = st.session_state["thermal_params"]

        T_floor = snapshots[-1]  # steady-state
        peak    = float(T_floor.max())
        avg     = float(T_floor.mean())
        hy, hx  = np.unravel_index(T_floor.argmax(), T_floor.shape)

        k1, k2, k3 = st.columns(3)
        k1.metric(t("p9_max_temp"), f"{peak:.1f} °C",  delta=f"{peak - amb:+.1f} °C vs ambient")
        k2.metric(t("p9_avg_temp"), f"{avg:.1f} °C")
        k3.metric(t("p9_hotspot"),  f"X={hx*dx:.1f}m, Y={hy*dy:.1f}m")

        if   peak <= 45: st.success(t("p9_hvac_ok"))
        elif peak <= 55: st.warning(t("p9_hvac_warn"))
        else:            st.error(t("p9_hvac_crit"))

        st.markdown("---")

        x_c = np.linspace(0, con_l, NX)
        y_c = np.linspace(0, con_w, NY)
        T_3d, z_vals = build_3d_field(T_floor, amb, con_h)
        NZ = len(z_vals)

        _ax = dict(backgroundcolor="rgba(0,0,0,0)", gridcolor=PALETTE["border"])
        dark_layout = dict(
            paper_bgcolor="rgba(0,0,0,0)",
            font_color=PALETTE["text2"],
            height=580,
            legend=dict(bgcolor="rgba(0,0,0,0)"),
        )
        _base_scene = dict(
            xaxis=dict(title=t("p9_x_label"), **_ax),
            yaxis=dict(title=t("p9_y_label"), **_ax),
            bgcolor="rgba(0,0,0,0)",
        )
        _ar_phys = dict(x=con_l / con_w, y=1.0, z=con_h / con_w)

        tab1, tab2, tab3 = st.tabs([
            "🧊 " + ("3D 온도 Surface"   if not is_en else "3D Temperature Surface"),
            "🏗️ " + ("수평 단면 슬라이스" if not is_en else "Horizontal Slice Views"),
            "💨 " + ("3D 공기 흐름 Cone" if not is_en else "3D Airflow Cones"),
        ])

        # ── Tab 1: 3D Surface — go.Frames time animation (physical seconds) ──
        with tab1:
            n_snaps = len(snapshots)
            cmax_all = max(float(np.max(s)) for s in snapshots)
            cmax_all = max(cmax_all, amb + 1.0)

            src_x     = [s[0] * dx for s in sources]
            src_y     = [s[1] * dy for s in sources]
            src_z_fin = [float(T_floor[min(max(s[1], 0), NY-1), min(max(s[0], 0), NX-1)]) for s in sources]
            vent_x    = [v[0] * dx for v in sim_vents]
            vent_y    = [v[1] * dy for v in sim_vents]
            vent_z_fin= [float(T_floor[min(max(v[1], 0), NY-1), min(max(v[0], 0), NX-1)]) for v in sim_vents]

            _scene_t1 = dict(
                **_base_scene,
                zaxis=dict(title="온도 (°C)" if not is_en else "Temperature (°C)",
                           range=[amb - 1.0, max(cmax_all, 56.0) + 3.0], **_ax),
                aspectmode='manual',
                aspectratio=dict(x=con_l / con_w, y=1.0, z=0.7),
                camera=dict(eye=dict(x=1.6, y=-1.9, z=1.3)),
            )

            def _t1_surf(T_snap):
                return go.Surface(
                    x=x_c, y=y_c, z=T_snap,
                    colorscale="RdYlBu_r",
                    cmin=amb, cmax=cmax_all,
                    colorbar=dict(title="°C", **CBAR),
                    hovertemplate="X: %{x:.1f}m | Y: %{y:.1f}m | <b>T: %{z:.1f}°C</b><extra></extra>",
                    name="Temp Field",
                )

            rack_trace = go.Scatter3d(
                x=src_x, y=src_y, z=[z + 0.15 for z in src_z_fin],
                mode='markers',
                marker=dict(size=7, color='#111', opacity=0.9, symbol='square'),
                name="배터리 랙" if not is_en else "Battery Rack",
                hovertemplate="Rack X=%{x:.1f}m Y=%{y:.1f}m<extra></extra>",
            )
            # 45 °C HVAC-adequacy reference plane (same limit as KPI banner)
            limit45 = go.Surface(
                x=[0.0, con_l], y=[0.0, con_w], z=[[45.0, 45.0], [45.0, 45.0]],
                colorscale=[[0, "rgba(248,81,73,0.25)"], [1, "rgba(248,81,73,0.25)"]],
                showscale=False,
                name="한계 45 °C" if not is_en else "45 °C limit",
                hovertemplate=("HVAC 적정성 한계 45 °C<extra></extra>" if not is_en
                               else "HVAC adequacy limit 45 °C<extra></extra>"),
            )
            base_data = [_t1_surf(snapshots[0]), limit45, rack_trace]
            if vent_x:
                base_data.append(go.Scatter3d(
                    x=vent_x, y=vent_y, z=[z + 0.2 for z in vent_z_fin],
                    mode='markers',
                    marker=dict(size=8, color='#00b4d8', opacity=0.9, symbol='diamond'),
                    name="HVAC 덕트" if not is_en else "HVAC Duct",
                    hovertemplate="Duct X=%{x:.1f}m Y=%{y:.1f}m<extra></extra>",
                ))

            _t1_layout = dict(
                **dark_layout,
                title=("3D 컨테이너 가열 과도응답 (0 → 30분)" if not is_en
                       else "3D Container Heat-Up Transient (0 → 30 min)"),
                scene=_scene_t1,
                margin=dict(l=0, r=0, t=60, b=60),
            )
            fig3d = build_animation(
                base_traces=base_data,
                frame_traces_list=[[_t1_surf(s)] for s in snapshots],
                frame_names=[f"t{i}" for i in range(n_snaps)],
                time_labels=[fmt_time(tt) for tt in snap_times[:n_snaps]],
                animated_trace_idx=[0],
                layout=_t1_layout,
                duration_ms=500,
                prefix="t = ",
            )
            st.plotly_chart(fig3d, use_container_width=True, key="th_chart")
            st.caption(
                "■ = 배터리 랙 | ◆ = HVAC 덕트 | 높이·색상 = 온도 | 빨간 평면 = 45 °C 한계 | ▶ 재생 = 실시간(초) 가열 진행 | 드래그로 회전" if not is_en
                else "■ = Battery racks | ◆ = HVAC ducts | red plane = 45 °C limit | ▶ Play = heat-up in physical seconds | Drag to rotate"
            )
        # ── Tab 2: Animated single horizontal slice (floor → ceiling) ──────────
        with tab2:
            xl, yw, zh = float(con_l), float(con_w), float(con_h)

            wire_data = []
            for ex, ey, ez in [
                ([0, xl, xl, 0, 0], [0, 0, yw, yw, 0], [0, 0, 0, 0, 0]),
                ([0, xl, xl, 0, 0], [0, 0, yw, yw, 0], [zh, zh, zh, zh, zh]),
                ([0, 0], [0, 0], [0, zh]), ([xl, xl], [0, 0], [0, zh]),
                ([xl, xl], [yw, yw], [0, zh]), ([0, 0], [yw, yw], [0, zh]),
            ]:
                wire_data.append(go.Scatter3d(
                    x=ex, y=ey, z=ez, mode='lines',
                    line=dict(color='#58a6ff', width=2),
                    showlegend=False, hoverinfo='skip',
                ))
            for (vx, vy) in sim_vents:
                wire_data.append(go.Scatter3d(
                    x=[float(vx)*dx, float(vx)*dx],
                    y=[float(vy)*dy, float(vy)*dy],
                    z=[0, zh], mode='lines',
                    line=dict(color='#00b4d8', width=3),
                    showlegend=False, hoverinfo='skip',
                ))

            n_z = NZ
            
            _scene_t2 = dict(
                **_base_scene,
                zaxis=dict(title=t("p9_z_label"), range=[0, con_h], **_ax),
                aspectmode='manual',
                aspectratio=_ar_phys,
                camera=dict(eye=dict(x=1.8, y=-1.6, z=1.5)),
            )

            # go.Frames 클라이언트 애니메이션 — 서버 폴링(fragment) 없이 브라우저에서
            # 부드럽게 재생. 바닥→천장 단면 스캔 (▶ 재생 / 슬라이더 스크럽)
            def _slice_surf(zi):
                z_val = float(z_vals[zi])
                T_slice = T_3d[zi]
                return go.Surface(
                    x=x_c, y=y_c,
                    z=np.full_like(T_slice, z_val),
                    surfacecolor=T_slice,
                    customdata=T_slice,
                    colorscale="RdYlBu_r",
                    cmin=amb, cmax=max(peak, amb + 1),
                    showscale=True,
                    colorbar=dict(title="°C", **CBAR),
                    opacity=0.92,
                    hovertemplate=(
                        f"z={z_val:.2f}m | X: %{{x:.1f}}m | Y: %{{y:.1f}}m | "
                        f"<b>%{{customdata:.1f}}°C</b><extra></extra>"
                    ),
                )

            _t2_layout = dict(
                **dark_layout,
                title=("3D 수평 단면 온도 — 바닥→천장 스캔" if not is_en
                       else "3D Horizontal Temp Slice — floor→ceiling scan"),
                scene=_scene_t2,
                margin=dict(l=0, r=0, t=60, b=60),
            )
            fig_s = build_animation(
                base_traces=[_slice_surf(0)] + wire_data,
                frame_traces_list=[[_slice_surf(zi)] for zi in range(n_z)],
                frame_names=[f"z{zi}" for zi in range(n_z)],
                time_labels=[f"{float(z_vals[zi]):.2f}m" for zi in range(n_z)],
                animated_trace_idx=[0],
                layout=_t2_layout,
                duration_ms=220,
                prefix="z = ",
            )
            st.plotly_chart(fig_s, use_container_width=True, key="sl_chart")
            st.caption(
                "▶ 재생으로 바닥→천장 단면 스캔 | 슬라이더로 높이 선택 | 청록 선 = HVAC 덕트" if not is_en
                else "▶ Play scans floor→ceiling | Slider selects height | Cyan = HVAC ducts"
            )
        # ── Tab 3: 3D Airflow — 다이폴 회절/후류+부력 파티클, go.Frames 클라이언트 재생 ──
        with tab3:
            # 물리 기반 유동장: 흡기=소스/배기=싱크 퍼텐셜 유동 + 랙=유동 장애물(다이폴 회절+후류) + 온도 부력 상승 + OU 난류
            wake_gain = st.slider(
                "💨 " + ("후류(박리) 강도" if not is_en else "Wake Intensity"),
                min_value=0.0, max_value=2.0, value=1.0, step=0.1,
                help=("랙 뒤편 재순환·와류 이탈 진동의 세기 — 하이퍼카 공기흐름 레퍼런스의 '후류 강도' 슬라이더와 동일 개념" if not is_en
                      else "Strength of the recirculation/vortex-shedding wake behind each rack"),
                key="af_wake_gain",
            )
            exhaust_xy = tuple((round(float(v[0]) * dx, 3), round(float(v[1]) * dy, 3)) for v in sim_exhaust)
            intake_xy  = tuple((round(float(v[0]) * dx, 3), round(float(v[1]) * dy, 3)) for v in sim_intake)
            rack_xy    = tuple((round(float(s[0]) * dx, 3), round(float(s[1]) * dy, 3)) for s in sources)
            traj = _airflow_traj_cached(T_floor, exhaust_xy, intake_xy, rack_xy,
                                        float(con_l), float(con_w), float(con_h), float(amb), wake_gain)
            N_FRAMES = traj["x"].shape[0]
            AF_DT = 0.35                      # airflow_trajectories dt와 동일 (라벨용)
            TAIL = 6

            _scene_c = dict(
                **_base_scene,
                zaxis=dict(title=t("p9_z_label"), range=[0, con_h], **_ax),
                aspectmode='manual',
                aspectratio=_ar_phys,
                camera=dict(eye=dict(x=1.6, y=-1.8, z=1.5)),
            )

            def _air_traces(k):
                # 잔상 트레일: 직전 TAIL 프레임의 연속 선분(레퍼런스의 파티클 유선 트레일과 동일한 표현)
                t0 = max(k - TAIL, 0)
                ratio_now = traj["speed"][k] / AF_U_REF     # 국소 유속비 V/V∞ (파티클별)
                if k > t0:
                    n_p = traj["x"].shape[1]
                    tx, ty, tz, tc = [], [], [], []
                    for p in range(n_p):
                        tx += list(traj["x"][t0:k + 1, p]) + [None]
                        ty += list(traj["y"][t0:k + 1, p]) + [None]
                        tz += list(traj["z"][t0:k + 1, p]) + [None]
                        tc += [float(ratio_now[p])] * (k + 1 - t0) + [0.0]
                else:
                    tx = ty = tz = tc = []
                tail = go.Scatter3d(
                    x=tx, y=ty, z=tz, mode='lines',
                    line=dict(color=tc, colorscale=AIRFLOW_HSL, cmin=0.3, cmax=1.6, width=3),
                    opacity=0.38, showlegend=False, hoverinfo='skip',
                )
                # 본체: 국소 유속비 V/V∞ 컬러 (레퍼런스 범례와 동일한 blue→cyan→green→yellow→red)
                main = go.Scatter3d(
                    x=traj["x"][k], y=traj["y"][k], z=traj["z"][k], mode='markers',
                    marker=dict(
                        size=4.5, color=ratio_now, colorscale=AIRFLOW_HSL,
                        cmin=0.3, cmax=1.6, opacity=0.9,
                        colorbar=dict(title=("유속비<br>V/V∞" if not is_en else "Speed ratio<br>V/V∞"),
                                      tickvals=[0.3, 0.75, 1.0, 1.3, 1.6], **CBAR),
                    ),
                    name="공기 파티클" if not is_en else "Air Particles",
                    hovertemplate="X=%{x:.1f}m Y=%{y:.1f}m Z=%{z:.2f}m<br>V/V∞=%{marker.color:.2f}<extra></extra>",
                )
                return [tail, main]

            static_traces = [go.Surface(
                x=x_c, y=y_c, z=np.zeros_like(T_floor),
                surfacecolor=T_floor,
                colorscale="RdYlBu_r", cmin=amb, cmax=max(peak, amb + 1),
                showscale=False, opacity=0.35,
                name="Floor Temp", hoverinfo='skip',
            )]
            if rack_xy:
                static_traces.append(go.Scatter3d(
                    x=[p[0] for p in rack_xy], y=[p[1] for p in rack_xy], z=[0.15] * len(rack_xy),
                    mode='markers',
                    marker=dict(size=7, color='#111111', symbol='square', opacity=0.9),
                    name="배터리 랙(유동 장애물)" if not is_en else "Battery Rack (flow obstacle)",
                    hovertemplate=("랙(장애물) X=%{x:.1f}m Y=%{y:.1f}m<extra></extra>" if not is_en
                                   else "Rack (obstacle) X=%{x:.1f}m Y=%{y:.1f}m<extra></extra>"),
                ))
            if sim_exhaust:
                static_traces.append(go.Scatter3d(
                    x=[float(v[0]) * dx for v in sim_exhaust],
                    y=[float(v[1]) * dy for v in sim_exhaust],
                    z=[con_h * 0.95] * len(sim_exhaust),
                    mode='markers+text',
                    marker=dict(size=6, color='#00b4d8', symbol='diamond', opacity=0.9),
                    text=["💨"] * len(sim_exhaust),
                    textposition="bottom center",
                    textfont=dict(size=9, color='#00b4d8'),
                    name="배기 덕트" if not is_en else "Exhaust Duct",
                    hovertemplate=("배기 X=%{x:.1f}m Y=%{y:.1f}m<extra></extra>" if not is_en
                                   else "Exhaust X=%{x:.1f}m Y=%{y:.1f}m<extra></extra>"),
                ))
            if sim_intake:
                static_traces.append(go.Scatter3d(
                    x=[float(v[0]) * dx for v in sim_intake],
                    y=[float(v[1]) * dy for v in sim_intake],
                    z=[con_h * 0.95] * len(sim_intake),
                    mode='markers+text',
                    marker=dict(size=6, color='#ff7f0e', symbol='diamond', opacity=0.9),
                    text=["🔵"] * len(sim_intake),
                    textposition="bottom center",
                    textfont=dict(size=9, color='#ff7f0e'),
                    name="흡기 덕트" if not is_en else "Intake Duct",
                    hovertemplate=("흡기 X=%{x:.1f}m Y=%{y:.1f}m<extra></extra>" if not is_en
                                   else "Intake X=%{x:.1f}m Y=%{y:.1f}m<extra></extra>"),
                ))

            _c_layout = dict(
                **dark_layout,
                title=("3D 공기 흐름 — 흡기→배기 순환 (퍼텐셜 유동 + 랙 회절·후류 + 부력)" if not is_en
                       else "3D Airflow — intake→exhaust circulation (potential flow + rack deflection/wake + buoyancy)"),
                scene=_scene_c,
                margin=dict(l=0, r=0, t=60, b=60),
            )
            fig_c = build_animation(
                base_traces=_air_traces(0) + static_traces,
                frame_traces_list=[_air_traces(k) for k in range(N_FRAMES)],
                frame_names=[f"a{k}" for k in range(N_FRAMES)],
                time_labels=[f"{k * AF_DT:.1f}s" for k in range(N_FRAMES)],
                animated_trace_idx=[0, 1],
                layout=_c_layout,
                duration_ms=80,               # 브라우저 클라이언트 재생 — 부드러운 12.5fps
                prefix="t = ",
            )
            st.plotly_chart(fig_c, use_container_width=True, key="af_chart")
            st.caption(
                "점 색·꼬리 색 = 국소 유속비 V/V∞(파랑→시안→녹→노랑→빨강) | ■ = 배터리 랙(유동 장애물 — 주변 유선이 휘어지고 뒤편에 후류 재순환 발생) | "
                "흐름: 🔵 흡기(급기, 하강·발산) → 랙 회절/후류 → 부력 상승 → 💨 배기(수렴·포집) | "
                "퍼텐셜 유동(다이폴 회절 포함) + 부력 + 난류 섭동의 운동학 모델 (모멘텀 CFD 아님)" if not is_en
                else "Dot/tail color = local speed ratio V/V∞ (blue→cyan→green→yellow→red) | ■ = Battery rack (flow obstacle — "
                     "streamlines bend around it, a recirculating wake forms downstream) | Flow: 🔵 intake (supply, descending·"
                     "diverging) → rack deflection/wake → buoyant rise → 💨 exhaust (converging·captured) | "
                     "Kinematic potential-flow (incl. dipole deflection) + buoyancy + turbulence model (not momentum CFD)"
            )

        with st.expander("📐 " + ("해석 방법론 & 가정" if not is_en else "Methodology & Assumptions")):
            st.markdown(
                (
                    "**지배 방정식 (2차원 깊이평균 에너지 수지, 양해법 FDM — 물리적 시간 기반):**\n\n"
                    "ρ·c_p·H·∂T/∂t = k_eff·H·∇²T + q″_rack − G_hvac·(T − T_supply) − h_env·(T − T_amb)\n\n"
                    "- **발열원:** 배터리 총 발열량(kW)을 랙 수로 균등 분배, 가우시안 footprint σ = 0.45 m (소스 항 — 랙 온도를 임의로 고정하지 않음)\n"
                    "- **HVAC:** 현열 냉각 컨덕턴스 G = Q_rated/ΔT_design (ΔT_design = 12 K). 65 %는 재순환 공기 전체(강제 혼합), "
                    "35 %는 선택한 덕트 셀에 집중 → 덕트 주변이 국부적으로 더 차가움. 냉각량은 (T − T_supply)에 비례(자기제한적)\n"
                    "- **혼합:** 유효 난류 확산계수 α_eff = 0.08 m²/s | **외피:** U_env = 2.5 W/m²K (지붕+벽)\n"
                    "- **수직 분포(탭 2):** 깊이평균 결과에 선형 성층 프로파일 적용 — 천장 초과온도 ≈ 바닥의 2배 (부력 성층 근사)\n"
                    "- **공기 흐름(탭 3):** 흡기=소스·배기=싱크 퍼텐셜 유동 중첩 + **배터리 랙=유동 장애물** "
                    "(국소 유동 방향에 정렬한 2D 다이폴 회절, k=0.52 — 하이퍼카 공기흐름 레퍼런스의 3D 타원체 다이폴 식을 랙 단면에 적용) "
                    "+ 랙 하류 후류 결손·와류 이탈 진동(후류 강도 슬라이더로 조절) + 바닥 온도 부력 상승류 + "
                    "OU(Ornstein–Uhlenbeck) 난류 섭동의 운동학 모델 — 유선 위상(흡기→배기 순환, 랙 주변 회절)은 물리적, 모멘텀 해석 아님. "
                    "색상은 국소 유속비 V/V∞로 정규화(레퍼런스와 동일한 blue→cyan→green→yellow→red 범례)\n\n"
                    "⚠️ **축소차수 해석 모델** — 파라미터 스크리닝/덕트 배치 비교 용도입니다. 운동량·부력장을 직접 풀지 않으므로 "
                    "제트 충돌, 급기 단락, 국부 재순환은 반영되지 않습니다. 설계 검증은 OpenFOAM / ANSYS Fluent CFD가 필요합니다."
                ) if not is_en else (
                    "**Governing equation (2-D depth-averaged energy balance, explicit FDM — physical time base):**\n\n"
                    "ρ·c_p·H·∂T/∂t = k_eff·H·∇²T + q″_rack − G_hvac·(T − T_supply) − h_env·(T − T_amb)\n\n"
                    "- **Sources:** total battery heat (kW) split evenly over racks, Gaussian footprint σ = 0.45 m "
                    "(true source term — rack temperature is NOT prescribed)\n"
                    "- **HVAC:** sensible-cooling conductance G = Q_rated/ΔT_design (ΔT_design = 12 K). 65 % acts on the "
                    "recirculated bulk air (forced mixing), 35 % concentrated at the selected duct cells → locally cooler "
                    "zones near ducts. Removal scales with (T − T_supply), i.e. self-limiting\n"
                    "- **Mixing:** effective turbulent diffusivity α_eff = 0.08 m²/s | **Envelope:** U_env = 2.5 W/m²K (roof + walls)\n"
                    "- **Vertical field (Tab 2):** linear stratification profile applied to the depth-averaged result — "
                    "ceiling excess temp ≈ 2× floor (buoyant stratification surrogate)\n"
                    "- **Airflow (Tab 3):** kinematic model — superposed potential flow (intakes as sources, exhausts as sinks) "
                    "+ **battery racks as flow obstacles** (2D dipole deflection aligned to the local flow direction, k=0.52 — "
                    "the same 3D ellipsoid-dipole formula from the hypercar airflow reference, applied to the rack cross-section) "
                    "+ a downstream wake deficit/vortex-shedding oscillation behind each rack (adjustable via the Wake Intensity "
                    "slider) + floor-temperature buoyant updraft + OU turbulence perturbation. Streamline topology (intake→exhaust "
                    "circulation, deflection around racks) is physical; NOT a momentum solution. Color is normalized as the local "
                    "speed ratio V/V∞ (same blue→cyan→green→yellow→red legend as the reference)\n\n"
                    "⚠️ **Reduced-order analytical model** — for parametric screening and duct-layout comparison. "
                    "Momentum/buoyancy fields are not resolved, so jet impingement, supply short-circuiting and local "
                    "recirculation are not captured. Use OpenFOAM / ANSYS Fluent CFD for design verification."
                )
            )

    else:
        st.info(
            "파라미터와 HVAC 덕트 위치를 설정하고 **시뮬레이션 실행** 버튼을 누르세요." if not is_en
            else "Set parameters & HVAC duct positions, then click **Run Thermal Simulation**."
        )


run_container_thermal_module()
