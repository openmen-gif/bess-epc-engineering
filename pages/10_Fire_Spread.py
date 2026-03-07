# -*- coding: utf-8 -*-
"""
10_Fire_Spread.py
배터리 화재 확산 시뮬레이션 — 셀룰러 오토마타 + 3D 시각화
Battery Fire Spread Simulation — Cellular Automata + 3D Visualisation
"""
import streamlit as st
try:
    st.set_page_config(page_title="BESS EPC Platform", layout="wide", initial_sidebar_state="expanded")
except Exception:
    pass

import time
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils.css_loader import apply_custom_css
from utils.lang_helper import t
from utils.auth_helper import require_auth, sidebar_user_info

# ── Cell states ────────────────────────────────────────────────────────────────
NORMAL          = 0
HEATING         = 1
THERMAL_RUNAWAY = 2
FIRE            = 3
SUPPRESSED      = 4

STATE_COLORS = {
    NORMAL:          "#1f4e79",
    HEATING:         "#f4a234",
    THERMAL_RUNAWAY: "#e05c1a",
    FIRE:            "#c0392b",
    SUPPRESSED:      "#2ecc71",
}

CHEM_PARAMS = {
    "LFP": {"spread_prob": 0.30, "runaway_time": 8,  "label": "LFP (Lithium Iron Phosphate)"},
    "NMC": {"spread_prob": 0.55, "runaway_time": 5,  "label": "NMC (Nickel Manganese Cobalt)"},
    "NCA": {"spread_prob": 0.65, "runaway_time": 4,  "label": "NCA (Nickel Cobalt Aluminum)"},
    "LTO": {"spread_prob": 0.15, "runaway_time": 12, "label": "LTO (Lithium Titanate)"},
}

AGENT_PARAMS = {
    "None":       {"suppression_rate": 0.0,  "label_ko": "없음 (소화 없음)", "label_en": "None (No Suppression)"},
    "FM-200":     {"suppression_rate": 0.70, "label_ko": "FM-200 (HFC-227ea)", "label_en": "FM-200 (HFC-227ea)"},
    "Novec 1230": {"suppression_rate": 0.80, "label_ko": "Novec 1230 (FK-5-1-12)", "label_en": "Novec 1230 (FK-5-1-12)"},
    "Water Mist": {"suppression_rate": 0.50, "label_ko": "워터 미스트", "label_en": "Water Mist"},
}


# ── Simulation engine ─────────────────────────────────────────────────────────
def simulate_fire_spread(rows, cols, origin_r, origin_c,
                          chem, agent, response_sec, max_steps=60):
    params       = CHEM_PARAMS.get(chem, CHEM_PARAMS["LFP"])
    spread_prob  = params["spread_prob"]
    runaway_time = params["runaway_time"]
    supp_rate    = AGENT_PARAMS.get(agent, AGENT_PARAMS["None"])["suppression_rate"]

    grid   = np.zeros((rows, cols), dtype=int)
    heat_t = np.zeros((rows, cols), dtype=int)
    grid[origin_r, origin_c]   = FIRE
    heat_t[origin_r, origin_c] = runaway_time

    frames, fire_counts, supp_counts = [grid.copy()], [1], [0]

    for step in range(1, max_steps + 1):
        new_grid = grid.copy()
        supp_active = (step >= response_sec) and (supp_rate > 0)

        for r in range(rows):
            for c in range(cols):
                state = grid[r, c]
                if state == FIRE:
                    if supp_active and np.random.random() < supp_rate * 0.15:
                        new_grid[r, c] = SUPPRESSED
                        continue
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < rows and 0 <= nc < cols:
                            if grid[nr, nc] == NORMAL and np.random.random() < spread_prob:
                                new_grid[nr, nc] = HEATING
                            elif grid[nr, nc] == HEATING:
                                heat_t[nr, nc] += 1
                                if heat_t[nr, nc] >= runaway_time:
                                    new_grid[nr, nc] = THERMAL_RUNAWAY
                elif state == THERMAL_RUNAWAY:
                    new_grid[r, c] = FIRE
                elif state == HEATING:
                    heat_t[r, c] += 1
                    if heat_t[r, c] >= runaway_time:
                        new_grid[r, c] = THERMAL_RUNAWAY

        grid = new_grid
        fire_cnt = int(np.sum(grid == FIRE))
        supp_cnt = int(np.sum(grid == SUPPRESSED))
        frames.append(grid.copy())
        fire_counts.append(fire_cnt)
        supp_counts.append(supp_cnt)
        if fire_cnt == 0 and int(np.sum(grid == HEATING)) == 0 and int(np.sum(grid == THERMAL_RUNAWAY)) == 0:
            break

    return frames, fire_counts, supp_counts


# ── Build Plotly 3D rack grid figure ─────────────────────────────────────────
def _rack_height(state):
    """Map cell state to visual height for 3D bar."""
    return {NORMAL: 0.2, HEATING: 0.5, THERMAL_RUNAWAY: 0.8, FIRE: 1.0, SUPPRESSED: 0.3}.get(state, 0.2)


def build_3d_frame(grid, origin_r, origin_c, is_en):
    """Return a 3D bar-chart figure for one simulation timestep."""
    rows, cols = grid.shape
    x_pos, y_pos, z_base, heights, colors, labels = [], [], [], [], [], []
    state_names = {
        NORMAL:          "정상" if not is_en else "Normal",
        HEATING:         "가열 중" if not is_en else "Heating",
        THERMAL_RUNAWAY: "열폭주" if not is_en else "Thermal Runaway",
        FIRE:            "화재" if not is_en else "Fire",
        SUPPRESSED:      "소화됨" if not is_en else "Suppressed",
    }
    for r in range(rows):
        for c in range(cols):
            state = int(grid[r, c])
            x_pos.append(c)
            y_pos.append(r)
            z_base.append(0.0)
            heights.append(_rack_height(state))
            colors.append(STATE_COLORS[state])
            labels.append(state_names[state])

    fig = go.Figure()

    # One trace per state for legend
    for state_id, state_name in state_names.items():
        mask = [i for i, s in enumerate(labels) if s == state_name]
        if not mask:
            continue
        fig.add_trace(go.Scatter3d(
            x=[x_pos[i] for i in mask],
            y=[y_pos[i] for i in mask],
            z=[heights[i] for i in mask],
            mode='markers',
            marker=dict(
                size=14,
                color=STATE_COLORS[state_id],
                symbol='square',
                opacity=0.9,
            ),
            name=state_name,
            hovertemplate=(
                ("행: %{y} · 열: %{x}<br>상태: " if not is_en else "Row: %{y} · Col: %{x}<br>State: ")
                + state_name + "<extra></extra>"
            ),
        ))

    # Mark origin
    fig.add_trace(go.Scatter3d(
        x=[origin_c], y=[origin_r], z=[1.3],
        mode='markers+text',
        marker=dict(size=10, color='white', symbol='diamond', opacity=1.0),
        text=["🔥"],
        textfont=dict(size=14),
        textposition="top center",
        name="발원 지점" if not is_en else "Fire Origin",
        hovertemplate=("발원 지점<br>행: %{y} · 열: %{x}<extra></extra>" if not is_en
                       else "Fire Origin<br>Row: %{y} · Col: %{x}<extra></extra>"),
    ))

    fig.update_layout(
        scene=dict(
            xaxis=dict(title="열 (Col)" if not is_en else "Col", backgroundcolor="rgba(0,0,0,0)", gridcolor="#30363d",
                       tickmode='linear', tick0=0, dtick=1),
            yaxis=dict(title="행 (Row)" if not is_en else "Row", backgroundcolor="rgba(0,0,0,0)", gridcolor="#30363d",
                       tickmode='linear', tick0=0, dtick=1),
            zaxis=dict(title="강도" if not is_en else "Intensity", backgroundcolor="rgba(0,0,0,0)", gridcolor="#30363d",
                       range=[0, 1.5]),
            bgcolor="rgba(0,0,0,0)",
            camera=dict(eye=dict(x=1.6, y=-1.8, z=1.4)),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#c9d1d9",
        legend=dict(bgcolor="rgba(30,30,30,0.6)", bordercolor="#30363d", borderwidth=1),
        margin=dict(l=0, r=0, t=30, b=0),
        height=500,
    )
    return fig


# ── Main Module ───────────────────────────────────────────────────────────────
def run_fire_spread_module():
    apply_custom_css()
    require_auth("10")
    sidebar_user_info()
    lang  = st.session_state.get('lang', 'KO')
    is_en = (lang == 'EN')

    st.caption(t("p10_caption"))
    st.title(t("p10_title"))
    st.markdown("---")
    st.info(t("p10_info"))

    # ── 담당 부분 (Responsible Discipline) ───────────────────────────────────
    with st.expander("👷 " + ("담당 부분 지정" if not is_en else "Responsible Disciplines"), expanded=False):
        _disc_ko = ["소방 엔지니어", "안전 엔지니어", "시스템 엔지니어", "기계 엔지니어", "전기 엔지니어", "PM"]
        _disc_en = ["Fire Protection Engineer", "Safety Engineer", "System Engineer", "Mechanical Engineer", "Electrical Engineer", "PM"]
        _discs   = _disc_en if is_en else _disc_ko
        _ra, _rb = st.columns([3, 2])
        with _ra:
            st.multiselect(
                "담당 엔지니어링 분야" if not is_en else "Responsible Engineering Disciplines",
                _discs, default=_discs[:2], key="fire_responsible",
            )
        with _rb:
            st.text_input(
                "담당자 이름" if not is_en else "Assignee Name",
                value=st.session_state.get("fire_assignee", ""),
                key="fire_assignee",
            )

    # ── Parameters ────────────────────────────────────────────────────────────
    st.markdown(t("p10_params"))
    p1, p2, p3 = st.columns(3)
    chem_options = {k: v["label"] for k, v in CHEM_PARAMS.items()}

    with p1:
        chem_key = st.selectbox(t("p10_chem"), list(chem_options.keys()),
                                format_func=lambda k: chem_options[k])
        rows = int(st.number_input(t("p10_rows"), min_value=2, max_value=20, value=6, step=1))
        cols = int(st.number_input(t("p10_cols"), min_value=2, max_value=20, value=8, step=1))
    with p2:
        response_sec = int(st.number_input(t("p10_response"), min_value=1, max_value=60, value=10, step=1))
    with p3:
        agent_labels = {k: (v["label_ko"] if not is_en else v["label_en"]) for k, v in AGENT_PARAMS.items()}
        agent_key = st.selectbox(t("p10_agent"), list(agent_labels.keys()),
                                 format_func=lambda k: agent_labels[k])

    # ── 🔥 Fire Origin Button Grid ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 🔥 " + ("화재 발원 지점 선택" if not is_en else "Select Fire Origin"))
    st.caption(
        "셀 버튼을 클릭하면 화재 발원 지점이 지정됩니다. 🔥 = 현재 발원 지점" if not is_en
        else "Click a cell button to set the fire origin. 🔥 = current origin"
    )

    # Resolve current origin from session state (clamped to grid)
    origin_r = min(int(st.session_state.get("fire_origin_r", 0)), rows - 1)
    origin_c = min(int(st.session_state.get("fire_origin_c", 0)), cols - 1)

    # Column header row
    hdr = st.columns([1] + [1] * cols)
    hdr[0].caption("R\\C")
    for gc in range(cols):
        hdr[gc + 1].caption(str(gc))

    # Button grid
    for gr in range(rows):
        row_cols = st.columns([1] + [1] * cols)
        row_cols[0].caption(str(gr))
        for gc in range(cols):
            with row_cols[gc + 1]:
                is_origin = (gr == origin_r and gc == origin_c)
                if st.button(
                    "🔥" if is_origin else "▫️",
                    key=f"fire_orig_{gr}_{gc}",
                    use_container_width=True,
                    type="primary" if is_origin else "secondary",
                ):
                    st.session_state["fire_origin_r"] = gr
                    st.session_state["fire_origin_c"] = gc
                    st.rerun()

    st.info(
        "🔥 " + ("현재 발원 지점: " if not is_en else "Current fire origin: ") +
        f"**{'행' if not is_en else 'Row'} {origin_r + 1}** · "
        f"**{'열' if not is_en else 'Col'} {origin_c + 1}**"
    )

    # ── Run button ────────────────────────────────────────────────────────────
    st.markdown("---")
    run = st.button(t("p10_run"), type="primary")

    if run:
        with st.spinner("시뮬레이션 실행 중…" if not is_en else "Running fire spread simulation…"):
            np.random.seed(42)
            frames, fire_cnt, supp_cnt = simulate_fire_spread(
                rows, cols, origin_r, origin_c,
                chem_key, agent_key, response_sec,
            )
        st.session_state["fire_frames"] = frames
        st.session_state["fire_cnt"]    = fire_cnt
        st.session_state["fire_supp"]   = supp_cnt
        st.session_state["fire_sim_params"] = (rows, cols, origin_r, origin_c, chem_key, agent_key, response_sec)
        st.session_state["fire_3d_slider"] = 0  # reset animation

    if "fire_frames" not in st.session_state:
        st.info(
            "시나리오 파라미터를 설정하고 **화재 확산 시뮬레이션 실행** 버튼을 누르세요." if not is_en
            else "Set scenario parameters and click **Run Fire Spread Simulation**."
        )
        return

    frames   = st.session_state["fire_frames"]
    fire_cnt = st.session_state["fire_cnt"]
    supp_cnt = st.session_state["fire_supp"]
    sim_params = st.session_state.get("fire_sim_params",
                                      (rows, cols, origin_r, origin_c, chem_key, agent_key, response_sec))
    _, _, sim_or, sim_oc, sim_chem, sim_agent, sim_resp = sim_params
    n_steps  = len(frames)

    max_fire  = max(fire_cnt)
    max_supp  = supp_cnt[-1]

    km1, km2, km3 = st.columns(3)
    km1.metric(t("p10_total_t"),    f"{n_steps} sec")
    km2.metric(t("p10_max_racks"),  f"{max_fire} racks")
    km3.metric(t("p10_suppressed"), f"{max_supp} racks")

    st.markdown("---")

    # ── Animation state (hoisted outside tabs to avoid double-render on rerun) ──
    playing  = st.session_state.get("fire_playing", False)
    step_val = min(int(st.session_state.get("_fire_step_val", 0)), n_steps - 1)

    tab1, tab2, tab3 = st.tabs([
        "🔥 " + ("3D 확산 애니메이션"        if not is_en else "3D Spread Animation"),
        "📈 " + ("확산 면적 추이"             if not is_en else "Spread Area Over Time"),
        "⚖️ " + ("방화 시스템 비교"           if not is_en else "Suppression Comparison"),
    ])

    # ── Tab 1: 3D + 2D — Streamlit-native animation (single Play control) ──
    with tab1:
        fire_cs = [
            [0.00, STATE_COLORS[NORMAL]],
            [0.25, STATE_COLORS[HEATING]],
            [0.50, STATE_COLORS[THERMAL_RUNAWAY]],
            [0.75, STATE_COLORS[FIRE]],
            [1.00, STATE_COLORS[SUPPRESSED]],
        ]
        state_labels = [t("p10_state0"), t("p10_state1"), t("p10_state2"),
                        t("p10_state3"), t("p10_state4")]
        _dark = dict(
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#c9d1d9",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=10, t=40, b=40),
        )

        # ── Play / Pause controls ──────────────────────────────────────────
        bcol1, bcol2, _ = st.columns([1, 1, 10])
        with bcol1:
            if st.button("▶ " + ("재생" if not is_en else "Play"), key="fire_play_btn"):
                if step_val >= n_steps - 1:
                    st.session_state["_fire_step_val"] = 0
                    step_val = 0
                st.session_state["fire_playing"] = True
                st.rerun()
        with bcol2:
            if st.button("⏸", key="fire_pause_btn"):
                st.session_state["fire_playing"] = False
                playing = False

        # Time slider (keyless — driven by _fire_step_val session var)
        step = st.slider("t (sec)", 0, n_steps - 1, step_val)
        st.session_state["_fire_step_val"] = step

        # ── 3D + 2D static charts for current step ────────────────────────
        col3d, col2d = st.columns([6, 5])

        with col3d:
            st.markdown("**🔥 " + ("3D 화재 확산" if not is_en else "3D Fire Spread") + "**")

            def _3d_surf(grid: np.ndarray) -> go.Surface:
                r_n, c_n = grid.shape
                z_surf = [[_rack_height(int(grid[r, c])) for c in range(c_n)]
                          for r in range(r_n)]
                return go.Surface(
                    x=list(range(c_n)), y=list(range(r_n)), z=z_surf,
                    surfacecolor=grid.astype(float).tolist(),
                    colorscale=fire_cs, cmin=0, cmax=4,
                    showscale=False, opacity=0.92,
                    hovertemplate=("행: %{y} · 열: %{x}<extra></extra>" if not is_en
                                   else "Row: %{y} · Col: %{x}<extra></extra>"),
                )

            origin_marker = go.Scatter3d(
                x=[sim_oc], y=[sim_or], z=[1.35],
                mode='markers+text',
                marker=dict(size=10, color='white', symbol='diamond', opacity=1.0),
                text=["🔥"], textfont=dict(size=14),
                textposition="top center",
                name="발원 지점" if not is_en else "Fire Origin",
            )

            fig_3d = go.Figure(data=[_3d_surf(frames[step]), origin_marker])
            fig_3d.update_layout(
                **_dark, height=460,
                scene=dict(
                    xaxis=dict(title="열 (Col)" if not is_en else "Col",
                               backgroundcolor="rgba(0,0,0,0)", gridcolor="#30363d",
                               tickmode='linear', tick0=0, dtick=1),
                    yaxis=dict(title="행 (Row)" if not is_en else "Row",
                               backgroundcolor="rgba(0,0,0,0)", gridcolor="#30363d",
                               tickmode='linear', tick0=0, dtick=1),
                    zaxis=dict(title="강도" if not is_en else "Intensity",
                               backgroundcolor="rgba(0,0,0,0)", gridcolor="#30363d",
                               range=[0, 1.5]),
                    bgcolor="rgba(0,0,0,0)",
                    camera=dict(eye=dict(x=1.6, y=-1.8, z=1.4)),
                ),
                legend=dict(bgcolor="rgba(30,30,30,0.6)", bordercolor="#30363d", borderwidth=1),
            )
            st.plotly_chart(fig_3d, use_container_width=True)

        with col2d:
            st.markdown("**📋 " + ("2D 뷰" if not is_en else "2D View") + "**")

            def _2d_hmap(grid: np.ndarray) -> go.Heatmap:
                return go.Heatmap(
                    z=grid.astype(float),
                    colorscale=fire_cs, zmin=0, zmax=4, showscale=True,
                    colorbar=dict(tickvals=[0, 1, 2, 3, 4], ticktext=state_labels,
                                  title="상태" if not is_en else "State", x=1.02,
                                  thickness=12, len=0.8),
                    hovertemplate=("행: %{y} · 열: %{x}<extra></extra>" if not is_en
                                   else "Row: %{y} · Col: %{x}<extra></extra>"),
                )

            fig_2d = go.Figure(data=[_2d_hmap(frames[step])])
            fig_2d.update_layout(
                **_dark, height=460,
                xaxis=dict(title="열 (Col)" if not is_en else "Col",
                           tickmode='linear', tick0=0, dtick=1,
                           gridcolor='rgba(0,0,0,0)', zeroline=False),
                yaxis=dict(title="행 (Row)" if not is_en else "Row",
                           tickmode='linear', tick0=0, dtick=1,
                           gridcolor='rgba(0,0,0,0)', zeroline=False,
                           autorange='reversed'),
            )
            st.plotly_chart(fig_2d, use_container_width=True)

        st.caption(
            "3D: Surface 높이 = 화재 강도 | 2D: 격자 색상 = 상태 | ▶/⏸ + 슬라이더로 시간 제어 | ◆ = 발원 지점"
            if not is_en else
            "3D: Surface height = fire intensity | 2D: cell colour = state | ▶/⏸ + slider = time | ◆ = origin"
        )

        with st.expander("📊 " + ("최종 상태 요약" if not is_en else "Final State Summary"), expanded=False):
            cur_g = frames[-1]
            ca, cb, cc = st.columns(3)
            ca.metric("🔥 " + ("화재" if not is_en else "Fire"),  str(int(np.sum(cur_g == FIRE))))
            cb.metric("💨 " + ("소화" if not is_en else "Supp."), str(int(np.sum(cur_g == SUPPRESSED))))
            cc.metric("🌡️ " + ("가열" if not is_en else "Heat"),
                      str(int(np.sum(cur_g == HEATING)) + int(np.sum(cur_g == THERMAL_RUNAWAY))))

    # ── Tab 2: Area Over Time ─────────────────────────────────────────────────
    with tab2:
        times = list(range(len(fire_cnt)))
        fire_lbl = "화재 랙" if not is_en else "Fire Racks"
        supp_lbl = "소화됨"  if not is_en else "Suppressed Racks"

        df = pd.DataFrame({
            t("p10_time_ax"): times,
            fire_lbl: fire_cnt,
            supp_lbl: supp_cnt,
        })
        fig_area = px.line(
            df, x=t("p10_time_ax"), y=[fire_lbl, supp_lbl],
            title=t("p10_area_title"),
            color_discrete_map={fire_lbl: "#c0392b", supp_lbl: "#2ecc71"},
            markers=True,
        )
        if sim_resp < len(times):
            fig_area.add_vline(
                x=sim_resp, line_dash="dash", line_color="#3498db",
                annotation_text="소화 시스템 작동" if not is_en else "Suppression Activated",
            )
        fig_area.update_layout(
            xaxis_title=t("p10_time_ax"), yaxis_title=t("p10_area_ax"),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#c9d1d9", legend_title_text="",
        )
        st.plotly_chart(fig_area, use_container_width=True)
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 CSV 다운로드" if not is_en else "📥 Download CSV",
            data=csv_data, file_name="BESS_fire_spread.csv", mime="text/csv",
            key="dl_fire_csv",
        )

    # ── Tab 3: Suppression Comparison ─────────────────────────────────────────
    with tab3:
        st.markdown(
            "각 소화 시스템을 동일 조건에서 시뮬레이션하여 최대 확산 랙 수를 비교합니다." if not is_en
            else "Runs the same scenario with each suppression system and compares max racks affected."
        )
        cmp_results = []
        sys_lbl  = "소화 시스템" if not is_en else "System"
        rack_lbl = "최대 화재 랙 수" if not is_en else "Max Racks on Fire"
        for ag, ap in AGENT_PARAMS.items():
            np.random.seed(42)
            _, fc, _ = simulate_fire_spread(
                sim_params[0], sim_params[1], sim_or, sim_oc,
                sim_chem, ag, sim_resp,
            )
            cmp_results.append({
                sys_lbl:  ap["label_ko" if not is_en else "label_en"],
                rack_lbl: max(fc),
            })
        df_cmp = pd.DataFrame(cmp_results)
        fig_cmp = px.bar(
            df_cmp, x=sys_lbl, y=rack_lbl,
            title=t("p10_cmp_title"),
            color=rack_lbl, color_continuous_scale="RdYlGn_r", text_auto=True,
        )
        fig_cmp.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#c9d1d9", showlegend=False,
        )
        st.plotly_chart(fig_cmp, use_container_width=True)

    # ── Auto-advance animation (outside all tabs to prevent double-render) ────
    if playing:
        time.sleep(0.4)
        if step < n_steps - 1:
            st.session_state["_fire_step_val"] = step + 1
        else:
            st.session_state["fire_playing"] = False
        st.rerun()


run_fire_spread_module()
