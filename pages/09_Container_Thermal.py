# -*- coding: utf-8 -*-
"""
09_Container_Thermal.py
배터리 컨테이너 내부 3D 열유동 시뮬레이션
Battery Container Internal 3D Thermal Flow Simulation
"""
import streamlit as st
try:
    st.set_page_config(page_title="BESS EPC Platform", layout="wide", initial_sidebar_state="expanded")
except Exception:
    pass

import numpy as np
import plotly.graph_objects as go
from utils.css_loader import apply_custom_css
from utils.lang_helper import t
from utils.auth_helper import require_auth, sidebar_user_info
from utils.theme import PALETTE
from utils.sim_physics import (
    heat2d_transient, stratification_profile,
    build_animation, fmt_time,
)

# Display grid for HVAC vent selector (columns × rows)
HVAC_NX, HVAC_NY = 10, 4

# Physical snapshot times for the heat-up transient animation [s]
SNAP_TIMES_S = list(range(0, 1801, 60))   # 0~30분, 60초 균일 31프레임(부드러운 재생/스크럽)


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
        bat_kw = st.number_input(
            t("p9_bat_heat"), min_value=1.0, max_value=5000.0,
            value=min(float(max(st.session_state.get('capacity_mw', 50.0), 1.0) * 50.0), 5000.0),
            step=10.0,
        )
        # 기본값 60 kW/MW — 발열 기본(50 kW/MW)을 상회하도록 (30이면 기본 조합이 항상 과열 판정)
        hvac_kw = st.number_input(
            t("p9_hvac_cap"), min_value=1.0, max_value=3000.0,
            value=min(float(max(st.session_state.get('capacity_mw', 50.0), 1.0) * 60.0), 3000.0),
            step=5.0,
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
                    colorbar=dict(title="°C", x=1.02),
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

            # 정지 상태에서는 run_every=None — 유휴 시 0.4초 무한 재렌더 루프 차단.
            # 재생 상태 전환은 st.rerun(scope="app")으로 전체 rerun하여 타이머를 재장전한다.
            _sl_every = 0.4 if st.session_state.get("sl_playing", False) else None

            @st.fragment(run_every=_sl_every)
            def _slice_anim():
                zi = int(st.session_state.get("sl_frame", 0)) % n_z
                playing = st.session_state.get("sl_playing", False)

                _t2_sc1, _t2_sc2 = st.columns([6, 2])
                with _t2_sc1:
                    _step = st.slider(
                        "높이 슬라이더 (m):" if not is_en else "Height Slider (m):",
                        0, n_z - 1, zi,
                        format="%d",
                        key="sl_step_slider",
                    )
                with _t2_sc2:
                    if st.button("▶ 시작" if not is_en else "▶ Start", key="sl_play_btn", type="primary", use_container_width=True):
                        st.session_state["sl_playing"] = True
                        st.session_state["sl_frame"] = 0
                        st.rerun(scope="app")
                    if st.button("⏸ 정지" if not is_en else "⏸ Pause", key="sl_pause_btn", type="secondary", use_container_width=True):
                        st.session_state["sl_playing"] = False
                        st.rerun(scope="app")
                if _step != zi and not playing:
                    zi = _step
                    st.session_state["sl_frame"] = zi

                z_val   = float(z_vals[zi])
                T_slice = T_3d[zi]
                surf = go.Surface(
                    x=x_c, y=y_c,
                    z=np.full_like(T_slice, z_val),
                    surfacecolor=T_slice,
                    customdata=T_slice,
                    colorscale="RdYlBu_r",
                    cmin=amb, cmax=max(peak, amb + 1),
                    showscale=True,
                    colorbar=dict(title="°C", x=1.02, thickness=12),
                    opacity=0.92,
                    hovertemplate=(
                        f"z={z_val:.2f}m | X: %{{x:.1f}}m | Y: %{{y:.1f}}m | "
                        f"<b>%{{customdata:.1f}}°C</b><extra></extra>"
                    ),
                )
                
                fig_s = go.Figure(data=[surf] + wire_data)
                fig_s.update_layout(
                    **dark_layout,
                    title=f"3D 수평 단면 온도 — {z_val:.2f}m" if not is_en
                          else f"3D Horizontal Temp Slice — {z_val:.2f}m",
                    scene=_scene_t2,
                )
                st.plotly_chart(fig_s, use_container_width=True, key="sl_chart")

                if playing:
                    if zi < n_z - 1:
                        st.session_state["sl_frame"] = zi + 1
                    else:
                        st.session_state["sl_playing"] = False
                        st.rerun(scope="app")   # 재생 종료 — 타이머 해제

            _slice_anim()
            st.caption(
                "▶ 재생으로 바닥→천장 단면 스캔 | 슬라이더로 높이 선택 | 청록 선 = HVAC 덕트" if not is_en
                else "▶ Play scans floor→ceiling | Slider selects height | Cyan = HVAC ducts"
            )
        # ── Tab 3: 3D Airflow — fragment-based particle animation ──────────────
        with tab3:
            U, V = vent_airflow_vectors(T_floor, sim_exhaust, sim_intake, NX, NY)

            N_FRAMES = 48
            N_COLS, N_ROWS = 8, 5
            N_P = N_COLS * N_ROWS
            TAIL_LEN = 6

            gx_arr = np.linspace(con_l * 0.07, con_l * 0.93, N_COLS)
            gy_arr = np.linspace(con_w * 0.10, con_w * 0.90, N_ROWS)
            G_X, G_Y = np.meshgrid(gx_arr, gy_arr)
            p0x = G_X.flatten()
            p0y = G_Y.flatten()

            base_z = np.array([
                con_h * (0.10 + 0.80 * (i / (N_P - 1))) for i in range(N_P)
            ])
            step_x = con_l * 0.07
            step_y = con_w * 0.07

            # Pre-compute trajectories once per simulation result
            # 캐시 키: id() 대신 결과 시그니처 — 재실행마다 세션에 쌓이는 누수·오매칭 방지
            _traj_sig = (round(float(T_floor.sum()), 3), tuple(sim_exhaust), tuple(sim_intake),
                         round(float(con_l), 3), round(float(con_w), 3))
            traj_key = "af_traj"
            if st.session_state.get("af_traj_sig") != _traj_sig:
                st.session_state.pop(traj_key, None)
                st.session_state["af_traj_sig"] = _traj_sig
            if traj_key not in st.session_state:
                traj_x_b = [p0x.copy()]
                traj_y_b = [p0y.copy()]
                px_c, py_c = p0x.copy(), p0y.copy()
                for _ in range(N_FRAMES - 1):
                    nx_a = np.empty_like(px_c)
                    ny_a = np.empty_like(py_c)
                    for i in range(N_P):
                        gxi = max(0, min(NX - 1, int(px_c[i] / dx)))
                        gyi = max(0, min(NY - 1, int(py_c[i] / dy)))
                        ux  = float(U[gyi, gxi])
                        vy_ = float(V[gyi, gxi])
                        mag = max(np.sqrt(ux ** 2 + vy_ ** 2), 1e-6)
                        nx_a[i] = (px_c[i] + ux  / mag * step_x) % con_l
                        ny_a[i] = (py_c[i] + vy_ / mag * step_y) % con_w
                    px_c, py_c = nx_a, ny_a
                    traj_x_b.append(px_c.copy())
                    traj_y_b.append(py_c.copy())
                st.session_state[traj_key] = (traj_x_b, traj_y_b)
            traj_x, traj_y = st.session_state[traj_key]

            # Speed stored in session state; fragment reads it on each run
            # 정지 상태에서는 run_every=None — 유휴 시 0.3초 무한 재렌더 루프 차단
            _af_iv = (st.session_state.get("af_interval", 0.3)
                      if st.session_state.get("af_playing", False) else None)

            _scene_c = dict(
                **_base_scene,
                zaxis=dict(title=t("p9_z_label"), range=[0, con_h], **_ax),
                aspectmode='manual',
                aspectratio=_ar_phys,
                camera=dict(eye=dict(x=1.6, y=-1.8, z=1.5)),
            )

            @st.fragment(run_every=_af_iv)
            def _airflow_anim():
                fi = int(st.session_state.get("af_frame", 0)) % N_FRAMES
                playing = st.session_state.get("af_playing", False)
                phase = fi / N_FRAMES * 2 * np.pi

                # Controls inside fragment — prevents full page rerun / tab reset
                _af_c1, _af_c2, _af_c3 = st.columns([3, 1, 1])
                with _af_c1:
                    _new_iv = st.select_slider(
                        "속도 (초/프레임)" if not is_en else "Speed (sec/frame)",
                        options=[0.1, 0.15, 0.2, 0.3, 0.5, 0.8, 1.0],
                        value=st.session_state.get("af_interval", 0.3),
                        key="af_speed_sel",
                    )
                    _iv_changed = st.session_state.get("af_interval") != _new_iv
                    st.session_state["af_interval"] = _new_iv
                    if _iv_changed and playing:
                        st.rerun(scope="app")   # 재생 중 속도 변경 — 새 간격으로 타이머 재장전
                with _af_c2:
                    if st.button("▶ 시작" if not is_en else "▶ Start", key="af_play_btn",
                                 type="primary", use_container_width=True):
                        st.session_state["af_playing"] = True
                        st.session_state["af_frame"] = 0
                        st.rerun(scope="app")   # 타이머 장전 (run_every 재평가)
                with _af_c3:
                    if st.button("⏸ 정지" if not is_en else "⏸ Pause", key="af_pause_btn",
                                 type="secondary", use_container_width=True):
                        st.session_state["af_playing"] = False
                        st.rerun(scope="app")   # 타이머 해제

                traces = []
                # Tail traces (fading)
                for tb in range(min(TAIL_LEN, fi), 0, -1):
                    alpha = (1.0 - tb / TAIL_LEN) * 0.45
                    fi_b = fi - tb
                    ph_b = fi_b / N_FRAMES * 2 * np.pi
                    tz = np.array([
                        base_z[i] + con_h * 0.04 * np.sin(ph_b + i * 0.42)
                        for i in range(N_P)
                    ])
                    traces.append(go.Scatter3d(
                        x=traj_x[fi_b], y=traj_y[fi_b], z=tz,
                        mode='markers',
                        marker=dict(size=3, color=f'rgba(0,180,216,{alpha:.2f})'),
                        showlegend=False, hoverinfo='skip',
                    ))

                # Current frame — bright particles coloured by height
                cur_z = np.array([
                    base_z[i] + con_h * 0.06 * np.sin(phase + i * 0.42)
                    for i in range(N_P)
                ])
                traces.append(go.Scatter3d(
                    x=traj_x[fi], y=traj_y[fi], z=cur_z,
                    mode='markers',
                    marker=dict(
                        size=6, color=cur_z, colorscale='Blues',
                        cmin=0, cmax=con_h, opacity=0.95,
                    ),
                    name="공기 파티클" if not is_en else "Air Particles",
                    hovertemplate="X=%{x:.1f}m Y=%{y:.1f}m Z=%{z:.2f}m<extra></extra>",
                ))

                # Floor temperature surface
                traces.append(go.Surface(
                    x=x_c, y=y_c, z=np.zeros_like(T_floor),
                    surfacecolor=T_floor,
                    colorscale="RdYlBu_r", cmin=amb, cmax=max(peak, amb + 1),
                    showscale=False, opacity=0.35,
                    name="Floor Temp", hoverinfo='skip',
                ))

                # Exhaust duct markers (cyan)
                if sim_exhaust:
                    traces.append(go.Scatter3d(
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
                # Intake duct markers (orange)
                if sim_intake:
                    traces.append(go.Scatter3d(
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

                fig_c = go.Figure(data=traces)
                fig_c.update_layout(
                    **dark_layout,
                    title=(
                        f"3D 공기 흐름 — {'▶ 재생 중' if playing else '⏸ 정지'} (프레임 {fi + 1}/{N_FRAMES})"
                        if not is_en else
                        f"3D Airflow — {'▶ Playing' if playing else '⏸ Paused'} (Frame {fi + 1}/{N_FRAMES})"
                    ),
                    scene=_scene_c,
                )
                st.plotly_chart(fig_c, use_container_width=True, key="af_chart")

                if playing:
                    st.session_state["af_frame"] = (fi + 1) % N_FRAMES

            _airflow_anim()
            st.caption(
                "파란 점 = 공기 파티클 | 💨(청록) = 배기 덕트 (공기 흡입) | 🔵(주황) = 흡기 덕트 (공기 공급) | ▶ 시작 / ⏸ 정지" if not is_en
                else "Blue dots = air particles | 💨(cyan) = Exhaust duct (air out) | 🔵(orange) = Intake duct (air in) | ▶ Start / ⏸ Pause"
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
                    "- **공기 흐름(탭 3):** 최근접 덕트 방향의 단순 운동학적 벡터장 — 모멘텀 해석 아님(시각화 보조)\n\n"
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
                    "- **Airflow (Tab 3):** kinematic nearest-duct vector field — NOT a momentum solution (visual aid only)\n\n"
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
