# -*- coding: utf-8 -*-
"""
10_Fire_Spread.py
배터리 화재 확산 시뮬레이션 — 결정론적 셀간 열폭주 전파 모델 + 3D 애니메이션
Battery Fire Spread Simulation — Deterministic cell-to-cell thermal-runaway
propagation (SFPE point-source radiation + lumped rack heating) + go.Frames
3D animation.

⚠ Reduced-order analytical model — NOT a substitute for FDS / UL 9540A
   large-scale fire testing.
"""
import streamlit as st
try:
    st.set_page_config(page_title="BESS EPC Platform", layout="wide", initial_sidebar_state="auto")
except Exception:
    pass

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils.css_loader import apply_custom_css
from utils.lang_helper import t
from utils.auth_helper import require_auth, sidebar_user_info
from utils.sim_physics import simulate_runaway, build_animation, fmt_time

# ── Cell states ────────────────────────────────────────────────────────────────
NORMAL          = 0
HEATING         = 1
THERMAL_RUNAWAY = 2
FIRE            = 3
SUPPRESSED      = 4   # extinguished by agent OR burned out (energy exhausted)

STATE_COLORS = {
    NORMAL:          "#1f4e79",
    HEATING:         "#f4a234",
    THERMAL_RUNAWAY: "#e05c1a",
    FIRE:            "#c0392b",
    SUPPRESSED:      "#2ecc71",
}

# Representative physics parameters per chemistry.
# HRR per rack & TR onset temperature: REPRESENTATIVE values for screening —
# project designs must use rack-specific UL 9540A test data.
CHEM_PARAMS = {
    "LFP": {"hrr_MW": 1.2, "onset_C": 230.0, "energy_MJ": 1200.0,
            "label": "LFP (Lithium Iron Phosphate)"},
    "NMC": {"hrr_MW": 2.5, "onset_C": 170.0, "energy_MJ": 2700.0,
            "label": "NMC (Nickel Manganese Cobalt)"},
    "NCA": {"hrr_MW": 3.0, "onset_C": 150.0, "energy_MJ": 2700.0,
            "label": "NCA (Nickel Cobalt Aluminum)"},
    "LTO": {"hrr_MW": 0.6, "onset_C": 280.0, "energy_MJ": 1500.0,
            "label": "LTO (Lithium Titanate)"},
}

# eta = open-flame HRR knockdown fraction; q_cool_W = direct cooling applied
# to exposed (non-burning) racks — only water-based agents cool surfaces.
AGENT_PARAMS = {
    "None":       {"eta": 0.0,  "q_cool_W": 0.0,
                   "label_ko": "없음 (소화 없음)", "label_en": "None (No Suppression)"},
    "FM-200":     {"eta": 0.70, "q_cool_W": 0.0,
                   "label_ko": "FM-200 (HFC-227ea)", "label_en": "FM-200 (HFC-227ea)"},
    "Novec 1230": {"eta": 0.80, "q_cool_W": 0.0,
                   "label_ko": "Novec 1230 (FK-5-1-12)", "label_en": "Novec 1230 (FK-5-1-12)"},
    "Water Mist": {"eta": 0.50, "q_cool_W": 20000.0,
                   "label_ko": "워터 미스트", "label_en": "Water Mist"},
}

NFPA855_SPACING_M = 0.914   # 3 ft separation per NFPA 855


# ── Simulation engine (deterministic — see utils/sim_physics.py) ─────────────
@st.cache_data(show_spinner=False)
def simulate_fire_spread(rows, cols, origin_r, origin_c,
                         chem, agent, spacing_m, response_sec, t_max_s):
    cp = CHEM_PARAMS.get(chem, CHEM_PARAMS["LFP"])
    ap = AGENT_PARAMS.get(agent, AGENT_PARAMS["None"])
    return simulate_runaway(
        rows, cols, (origin_r, origin_c),
        hrr_MW=cp["hrr_MW"], onset_C=cp["onset_C"], energy_MJ=cp["energy_MJ"],
        spacing_m=spacing_m, eta_supp=ap["eta"], q_cool_W=ap["q_cool_W"],
        response_s=response_sec, t_max_s=t_max_s, n_frames=80,
    )


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
    st.caption(
        "⚠️ 축소차수 해석 모델 (SFPE 점원 복사 + 집중질량 랙 가열) — FDS / UL 9540A 실증시험을 대체하지 않습니다." if not is_en
        else "⚠️ Reduced-order analytical model (SFPE point-source radiation + lumped rack heating) — not a substitute for FDS / UL 9540A testing."
    )

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
        chem_key = st.selectbox(t("p10_chem"), list(chem_options.keys()), index=1,
                                format_func=lambda k: chem_options[k])
        rows = int(st.number_input(t("p10_rows"), min_value=2, max_value=20, value=6, step=1))
        cols = int(st.number_input(t("p10_cols"), min_value=2, max_value=20, value=8, step=1))
    with p2:
        response_sec = int(st.number_input(t("p10_response"), min_value=1, max_value=300, value=10, step=1))
        max_min = int(st.number_input(
            "최대 시뮬레이션 시간 (분)" if not is_en else "Max Simulation Time (min)",
            min_value=5, max_value=120, value=45, step=5,
        ))
        t_max_s = max_min * 60.0
    with p3:
        agent_labels = {k: (v["label_ko"] if not is_en else v["label_en"]) for k, v in AGENT_PARAMS.items()}
        agent_key = st.selectbox(t("p10_agent"), list(agent_labels.keys()),
                                 format_func=lambda k: agent_labels[k])
        spacing_m = st.slider(
            "랙 간 이격거리 (m)" if not is_en else "Rack-to-Rack Clear Spacing (m)",
            min_value=0.1, max_value=3.0, value=0.3, step=0.05,
            help=("NFPA 855의 0.914 m (3 ft)는 '유닛·어레이 간' 이격 기준입니다. 컨테이너 내부 랙-랙 간격에는 "
                  "참고 지표로만 적용하세요 (내부 랙 배치는 UL 9540A 시험·AHJ 승인 사항). "
                  "복사 열유속 ∝ 1/d² 이므로 이격거리가 전파 여부를 지배합니다." if not is_en else
                  "NFPA 855's 0.914 m (3 ft) applies to unit/array separation. Treat it as a reference only for "
                  "intra-container rack spacing (governed by UL 9540A testing & AHJ approval). "
                  "Radiative flux ∝ 1/d², so spacing governs whether propagation occurs."),
        )
        if spacing_m >= NFPA855_SPACING_M:
            st.caption("✅ " + ("NFPA 855 이격기준(0.914 m) 충족" if not is_en
                                else "Meets NFPA 855 separation (0.914 m)"))
        else:
            st.caption("⚠️ " + (f"NFPA 855 기준(0.914 m) 미만 — {(NFPA855_SPACING_M - spacing_m)*100:.0f} cm 부족" if not is_en
                                else f"Below NFPA 855 separation (0.914 m) by {(NFPA855_SPACING_M - spacing_m)*100:.0f} cm"))

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
            res = simulate_fire_spread(
                rows, cols, origin_r, origin_c,
                chem_key, agent_key, float(spacing_m), response_sec, t_max_s,
            )
        st.session_state["fire_result"] = res
        st.session_state["fire_sim_cfg"] = dict(
            rows=rows, cols=cols, origin_r=origin_r, origin_c=origin_c,
            chem=chem_key, agent=agent_key, spacing=float(spacing_m),
            response=response_sec, t_max=t_max_s,
        )

    if "fire_result" not in st.session_state:
        st.info(
            "시나리오 파라미터를 설정하고 **화재 확산 시뮬레이션 실행** 버튼을 누르세요." if not is_en
            else "Set scenario parameters and click **Run Fire Spread Simulation**."
        )
        return

    res      = st.session_state["fire_result"]
    cfg      = st.session_state.get("fire_sim_cfg", dict(
        rows=rows, cols=cols, origin_r=origin_r, origin_c=origin_c,
        chem=chem_key, agent=agent_key, spacing=float(spacing_m),
        response=response_sec, t_max=t_max_s,
    ))
    times    = res["times"]
    T_frames = res["T_frames"]
    frames   = res["state_frames"]
    fire_cnt = res["fire_counts"]
    supp_cnt = res["supp_counts"]
    n_steps  = len(frames)
    onset_C  = CHEM_PARAMS[cfg["chem"]]["onset_C"]

    # racks that EVER ignited (cumulative spread extent)
    ever_fire = int(np.sum(np.maximum.reduce([(g == FIRE).astype(int) | (g == SUPPRESSED).astype(int)
                                              for g in frames])))
    max_supp  = supp_cnt[-1]

    km1, km2, km3 = st.columns(3)
    km1.metric(t("p10_total_t"),    fmt_time(times[-1]))
    km2.metric(t("p10_max_racks"),  f"{ever_fire} racks")
    km3.metric(t("p10_suppressed"), f"{max_supp} racks")

    # 결과 해석 배너 — "왜 이런 결과인지" 명시(전파 없음이 정상인지 설명, 고장 오해 방지)
    _chem = cfg["chem"]; _sp = float(cfg["spacing"])
    _met = _sp >= NFPA855_SPACING_M
    if ever_fire <= 1:
        st.success(
            (f"✅ **전파 차단** — 인접 랙으로 확산되지 않고 발원 랙 1개만 연소 후 소진되었습니다"
             f"(에너지 소진, 자연소화가 아님). 원인: **{_chem}** 화학의 전파저항"
             + (f" + NFPA 855 이격({_sp:.2f} m ≥ 0.914 m) 충족" if _met
                else f" + 이격 {_sp:.2f} m에서 복사 열유속이 인접 랙을 onset까지 못 올림")
             + ". 🔥 **전파를 보려면 화학 = NMC/NCA + 이격 0.3~0.5 m** 로 설정하세요." )
            if not is_en else
            (f"✅ **Propagation arrested** — fire stayed at the single origin rack and burned out "
             f"(energy-limited, not a magic self-extinguish). Cause: **{_chem}** propagation resistance"
             + (f" + NFPA 855 spacing ({_sp:.2f} m)" if _met else f" + insufficient radiative flux at {_sp:.2f} m")
             + ". To see propagation, set **chemistry = NMC/NCA and spacing 0.3–0.5 m**.")
        )
    elif max_supp >= ever_fire:
        st.warning(
            (f"🔥➡️🛡️ **부분 전파 후 억제** — 최대 **{ever_fire}개** 랙이 점화되었으나 방화 시스템/연소 소진으로 억제되었습니다."
             if not is_en else
             f"🔥➡️🛡️ **Partial spread, then contained** — up to **{ever_fire}** racks ignited but were suppressed / burned out.")
        )
    else:
        st.error(
            (f"🔥 **열폭주 전파 발생** — 최대 **{ever_fire}개** 랙으로 확산되었습니다. 이격 확대(≥0.914 m) 또는 방화 강화가 필요합니다."
             if not is_en else
             f"🔥 **Thermal-runaway propagation** — spread to up to **{ever_fire}** racks. Increase spacing (≥0.914 m) or strengthen suppression.")
        )

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs([
        "🔥 " + ("3D 확산 애니메이션"        if not is_en else "3D Spread Animation"),
        "📈 " + ("확산 면적 추이"             if not is_en else "Spread Area Over Time"),
        "⚖️ " + ("방화 시스템 비교"           if not is_en else "Suppression Comparison"),
    ])

    _fire_cs = [
        [0.00, STATE_COLORS[NORMAL]],
        [0.25, STATE_COLORS[HEATING]],
        [0.50, STATE_COLORS[THERMAL_RUNAWAY]],
        [0.75, STATE_COLORS[FIRE]],
        [1.00, STATE_COLORS[SUPPRESSED]],
    ]
    _state_labels = [t("p10_state0"), t("p10_state1"), t("p10_state2"),
                     t("p10_state3"), t("p10_state4")]
    _dark = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#c9d1d9",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    frame_names = [f"k{i}" for i in range(n_steps)]
    time_labels = [fmt_time(tt) for tt in times]

    # ── Tab 1: go.Frames animations — rack temperature (3D) + state map (2D) ──
    with tab1:
        col3d, col2d = st.columns([6, 5])

        with col3d:
            st.markdown("**🌡️ " + ("3D 랙 온도장 (높이 = 온도)" if not is_en
                                     else "3D Rack Temperature Field (height = temp)") + "**")

            def _T_surf(Tg):
                return go.Surface(
                    x=list(range(cfg["cols"])), y=list(range(cfg["rows"])), z=Tg,
                    colorscale="Inferno", cmin=25.0, cmax=700.0,
                    colorbar=dict(title="°C", thickness=12, x=1.02),
                    hovertemplate=("행: %{y} · 열: %{x}<br><b>T: %{z:.0f}°C</b><extra></extra>" if not is_en
                                   else "Row: %{y} · Col: %{x}<br><b>T: %{z:.0f}°C</b><extra></extra>"),
                )

            onset_plane = go.Surface(
                x=[0, cfg["cols"] - 1], y=[0, cfg["rows"] - 1],
                z=[[onset_C, onset_C], [onset_C, onset_C]],
                colorscale=[[0, "rgba(255,255,0,0.22)"], [1, "rgba(255,255,0,0.22)"]],
                showscale=False,
                name=(f"열폭주 개시 {onset_C:.0f}°C" if not is_en else f"TR onset {onset_C:.0f}°C"),
                hovertemplate=(f"열폭주 개시 온도 {onset_C:.0f}°C (UL 9540A 시험값 사용 권장)<extra></extra>" if not is_en
                               else f"TR onset {onset_C:.0f}°C (use UL 9540A test data)<extra></extra>"),
            )
            origin_marker = go.Scatter3d(
                x=[cfg["origin_c"]], y=[cfg["origin_r"]], z=[720],
                mode='markers+text',
                marker=dict(size=8, color='white', symbol='diamond', opacity=1.0),
                text=["🔥"], textfont=dict(size=13), textposition="top center",
                name="발원 지점" if not is_en else "Fire Origin",
                hovertemplate=("발원 지점<extra></extra>" if not is_en else "Fire Origin<extra></extra>"),
            )

            layout_3d = dict(
                **_dark, height=520,
                margin=dict(l=0, r=0, t=50, b=60),
                title=("랙 온도 진행 — 점원 복사 가열" if not is_en
                       else "Rack Temperature Evolution — Point-Source Radiative Heating"),
                scene=dict(
                    xaxis=dict(title="열 (Col)" if not is_en else "Col",
                               backgroundcolor="rgba(0,0,0,0)", gridcolor="#30363d",
                               tickmode='linear', tick0=0, dtick=1),
                    yaxis=dict(title="행 (Row)" if not is_en else "Row",
                               backgroundcolor="rgba(0,0,0,0)", gridcolor="#30363d",
                               tickmode='linear', tick0=0, dtick=1),
                    zaxis=dict(title="온도 (°C)" if not is_en else "Temp (°C)",
                               backgroundcolor="rgba(0,0,0,0)", gridcolor="#30363d",
                               range=[0, 780]),
                    bgcolor="rgba(0,0,0,0)",
                    camera=dict(eye=dict(x=1.6, y=-1.8, z=1.4)),
                ),
                legend=dict(bgcolor="rgba(30,30,30,0.6)", bordercolor="#30363d", borderwidth=1),
            )
            fig_3d = build_animation(
                base_traces=[_T_surf(T_frames[0]), onset_plane, origin_marker],
                frame_traces_list=[[_T_surf(Tg)] for Tg in T_frames],
                frame_names=frame_names, time_labels=time_labels,
                animated_trace_idx=[0], layout=layout_3d,
                duration_ms=120, prefix="t = ",
            )
            st.plotly_chart(fig_3d, use_container_width=True, key="fire_3d_anim")

        with col2d:
            st.markdown("**📋 " + ("2D 상태 맵" if not is_en else "2D State Map") + "**")

            def _2d_hmap(grid):
                return go.Heatmap(
                    z=grid.astype(float),
                    colorscale=_fire_cs, zmin=0, zmax=4, showscale=True,
                    colorbar=dict(tickvals=[0, 1, 2, 3, 4], ticktext=_state_labels,
                                  title="상태" if not is_en else "State", x=1.02,
                                  thickness=12, len=0.8),
                    hovertemplate=("행: %{y} · 열: %{x}<extra></extra>" if not is_en
                                   else "Row: %{y} · Col: %{x}<extra></extra>"),
                )

            layout_2d = dict(
                **_dark, height=520,
                margin=dict(l=0, r=10, t=50, b=60),
                title=("상태 전이 (정상→가열→열폭주→화재→소화/소진)" if not is_en
                       else "State Transitions (Normal→Heating→TR→Fire→Supp.)"),
                xaxis=dict(title="열 (Col)" if not is_en else "Col",
                           tickmode='linear', tick0=0, dtick=1,
                           gridcolor='rgba(0,0,0,0)', zeroline=False),
                yaxis=dict(title="행 (Row)" if not is_en else "Row",
                           tickmode='linear', tick0=0, dtick=1,
                           gridcolor='rgba(0,0,0,0)', zeroline=False,
                           autorange='reversed'),
            )
            fig_2d = build_animation(
                base_traces=[_2d_hmap(frames[0])],
                frame_traces_list=[[_2d_hmap(g)] for g in frames],
                frame_names=frame_names, time_labels=time_labels,
                animated_trace_idx=[0], layout=layout_2d,
                duration_ms=120, prefix="t = ",
            )
            st.plotly_chart(fig_2d, use_container_width=True, key="fire_2d_anim")

        st.caption(
            "3D: 높이·색상 = 랙 온도(°C), 노란 평면 = 열폭주 개시 온도 | 2D: 셀 색상 = 상태 | ▶ 재생 + 슬라이더 = 실제 경과 시간" if not is_en
            else "3D: height/colour = rack temp (°C), yellow plane = TR onset | 2D: cell colour = state | ▶ Play + slider = real elapsed time"
        )

        with st.expander("📊 " + ("최종 상태 요약" if not is_en else "Final State Summary"), expanded=False):
            cur_g = frames[-1]
            ca, cb, cc = st.columns(3)
            ca.metric("🔥 " + ("화재" if not is_en else "Fire"),  str(int(np.sum(cur_g == FIRE))))
            cb.metric("💨 " + ("소화/소진" if not is_en else "Supp./Burned"), str(int(np.sum(cur_g == SUPPRESSED))))
            cc.metric("🌡️ " + ("가열" if not is_en else "Heat"),
                      str(int(np.sum(cur_g == HEATING)) + int(np.sum(cur_g == THERMAL_RUNAWAY))))

    # ── Tab 2: Area Over Time ─────────────────────────────────────────────────
    with tab2:
        fire_lbl = "화재 랙" if not is_en else "Fire Racks"
        supp_lbl = "소화/소진 랙"  if not is_en else "Suppressed/Burned Racks"

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
        if cfg["response"] < times[-1]:
            fig_area.add_vline(
                x=cfg["response"], line_dash="dash", line_color="#3498db",
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

    # ── Tab 3: Suppression Comparison (deterministic, identical scenario) ────
    with tab3:
        st.markdown(
            "각 소화 시스템을 동일 조건에서 시뮬레이션하여 화재 영향 랙 수(누적)를 비교합니다 — 결정론적 모델이므로 차이는 순수하게 소화 성능에 기인합니다." if not is_en
            else "Runs the IDENTICAL scenario with each suppression system — the model is deterministic, so differences are attributable purely to suppression performance."
        )
        cmp_results = []
        sys_lbl  = "소화 시스템" if not is_en else "System"
        rack_lbl = "화재 영향 랙 수 (누적)" if not is_en else "Racks Ever Ignited"
        for ag, ap in AGENT_PARAMS.items():
            r2 = simulate_fire_spread(
                cfg["rows"], cfg["cols"], cfg["origin_r"], cfg["origin_c"],
                cfg["chem"], ag, cfg["spacing"], cfg["response"], cfg["t_max"],
            )
            ever2 = int(np.sum(np.maximum.reduce(
                [(g == FIRE).astype(int) | (g == SUPPRESSED).astype(int) for g in r2["state_frames"]])))
            cmp_results.append({
                sys_lbl:  ap["label_ko" if not is_en else "label_en"],
                rack_lbl: ever2,
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

    # ── Methodology & Assumptions ─────────────────────────────────────────────
    with st.expander("📐 " + ("해석 방법론 & 가정" if not is_en else "Methodology & Assumptions")):
        st.markdown(
            (
                "**셀간 열폭주 전파 모델 (결정론적 — 난수 없음):**\n\n"
                "- **복사 열유속 (SFPE 점원 모델):** q″ = χr·Q/(4π·d²), χr = 0.30, "
                "d = 이격거리 + 랙 폭 0.6 m (대각선 ×√2 → 유속 ½)\n"
                "- **인접 랙 가열 (집중질량):** m·c·dT/dt = q″·A_exp − h·A·(T − T_amb) − Q_cool,supp "
                "(m·c = 1.2 MJ/K, A_exp = 4 m², h·A = 60 W/K)\n"
                "- **열폭주 개시:** T ≥ T_onset (화학종별 대표값 — LFP 230 / NMC 170 / NCA 150 / LTO 280 °C). "
                "실제 설계에는 UL 9540A 셀/모듈/유닛 시험값 적용 필수\n"
                "- **연소 지속:** 랙 방출에너지(MJ)를 HRR로 나눈 시간 동안 연소 후 소진\n"
                "- **소화:** 반응시간 이후 화염 HRR을 (1−η)로 저감, η/90초 노출 후 진화 — 단 진화 후에도 "
                "15 % 잔여 발열(벤트가스 스몰더링) 유지. 가스계 소화제(FM-200/Novec)는 표면 냉각 없음, "
                "워터미스트는 피폭 랙에 20 kW 직접 냉각\n"
                "- **NFPA 855:** 유닛 간 0.914 m (3 ft) 이격 기준 — q″ ∝ 1/d² 이므로 기준 이상 이격 시 "
                "전파가 차단되는 효과를 본 모델에서 직접 확인 가능\n\n"
                "**한계:** 화염 충돌(직접 접염), 벤트가스 제트화염, 천장열기류 재복사, 배연 영향은 미반영. "
                "가스계 소화제는 개방 화염만 억제하며 셀 내부 연쇄 열폭주를 멈추지 못할 수 있습니다. "
                "성능 검증은 UL 9540A 유닛 시험 + FDS 해석이 필요합니다."
            ) if not is_en else (
                "**Cell-to-cell thermal-runaway propagation model (deterministic — no randomness):**\n\n"
                "- **Radiative flux (SFPE point-source model):** q″ = χr·Q/(4π·d²), χr = 0.30, "
                "d = clear spacing + 0.6 m rack width (diagonal ×√2 → half flux)\n"
                "- **Target rack heating (lumped):** m·c·dT/dt = q″·A_exp − h·A·(T − T_amb) − Q_cool,supp "
                "(m·c = 1.2 MJ/K, A_exp = 4 m², h·A = 60 W/K)\n"
                "- **TR onset:** T ≥ T_onset (representative per chemistry — LFP 230 / NMC 170 / NCA 150 / LTO 280 °C). "
                "Project designs MUST use UL 9540A cell/module/unit test data\n"
                "- **Burn duration:** releasable rack energy (MJ) divided by HRR; rack burns out when exhausted\n"
                "- **Suppression:** after response time, open-flame HRR knocked down by (1−η); extinguished after "
                "~90/η s exposure — but 15 % residual heat release (vent-gas smoldering) persists. Gaseous agents "
                "(FM-200/Novec) provide no surface cooling; water mist adds 20 kW direct cooling to exposed racks\n"
                "- **NFPA 855:** 0.914 m (3 ft) unit separation — since q″ ∝ 1/d², the model directly demonstrates "
                "propagation arrest at or above this spacing\n\n"
                "**Limitations:** direct flame impingement, vent-gas jet flames, ceiling-layer re-radiation and "
                "ventilation effects are not modelled. Gaseous agents suppress open flaming but may not arrest "
                "internal cell-to-cell runaway. Verify with UL 9540A unit-level testing + FDS."
            )
        )


run_fire_spread_module()
