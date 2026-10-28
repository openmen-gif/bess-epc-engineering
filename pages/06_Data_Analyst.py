import streamlit as st
try:
    st.set_page_config(page_title="BESS EPC Platform", layout="wide", initial_sidebar_state="auto")
except Exception:
    pass

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.css_loader import apply_custom_css
from utils import theme  # bess_dark 템플릿 등록 — px 차트 다크·브랜드 colorway 자동 적용
from utils.lang_helper import t
from utils.standards_helper import get_standards
from utils.auth_helper import require_auth, sidebar_user_info
from utils import engineering_params as EP


def run_data_analyst_module():
    apply_custom_css()
    require_auth("06")
    sidebar_user_info()

    st.caption(t("p6_caption"))
    st.title(t("p6_title"))
    st.markdown("---")

    st.info(t("p6_info"))
    # 이 페이지의 KPI·프로파일·히트맵은 실측이 아니라 설정값 기반 합성/난수 데이터다 — 실측으로 오인 방지
    st.warning(
        "⚠️ **시연용 데이터** — 아래 KPI·충방전 프로파일·온도 히트맵은 실측이 아니라 "
        "프로젝트 설정값으로 만든 합성(난수 포함) 데이터입니다. 보고·의사결정에 인용하지 마세요."
        if st.session_state.get('lang', 'KO') == "KO" else
        "⚠️ **Demo data** — KPIs, charge/discharge profile and temperature heatmap below are "
        "synthetic (partly random) values derived from project settings, not measurements. "
        "Do not cite them in reports or decisions."
    )

    tab1, tab2, tab3 = st.tabs([t("p6_tab1"), t("p6_tab2"), t("p6_tab3")])

    # ── Performance Metrics ─────────────────────────────────────────
    with tab1:
        st.subheader(t("p6_kpi"))

        col1, col2, col3, col4 = st.columns(4)

        target_rte = st.session_state.get('rte_percent', 88.0)
        target_aux = st.session_state.get('aux_loss_percent', 2.5)
        power_mw   = st.session_state.get('capacity_mw', 100.0)

        col1.metric(t("p6_avail"), "98.4%", "0.2%")
        col2.metric(t("p6_rte"),   f"{target_rte - 0.5:.1f}%", f"-0.5%")
        col3.metric(t("p6_disch"), f"{power_mw * 2 * 0.95:.0f} MWh", "+12 MWh")
        col4.metric(t("p6_aux"),   f"{target_aux + 0.2:.1f}%", f"+0.2%", delta_color="inverse")
        st.caption(
            f"판정 기준 [가정 — 계약 성능보증 값 우선]: 가용률 ≥{EP.KPI_AVAILABILITY_MIN_PCT:.0f}%, "
            f"RTE LFP ≥{EP.KPI_RTE_MIN_PCT['LFP']:.0f}% / NMC ≥{EP.KPI_RTE_MIN_PCT['NMC']:.0f}% (bess-data-analyst)"
            if st.session_state.get('lang', 'KO') == "KO" else
            f"Thresholds [assumption — contract guarantees take precedence]: availability ≥{EP.KPI_AVAILABILITY_MIN_PCT:.0f}%, "
            f"RTE LFP ≥{EP.KPI_RTE_MIN_PCT['LFP']:.0f}% / NMC ≥{EP.KPI_RTE_MIN_PCT['NMC']:.0f}% (bess-data-analyst)"
        )

        st.markdown(t("p6_monthly"))

        # 직전 30일 = 오늘로부터 과거 30일까지 — 항상 "최근" 데이터로 보이도록 동적 생성
        dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=30, freq='D')
        _power = max(power_mw, 50.0)
        _dur   = max(st.session_state.get('duration_h', 2.0), 1.0)
        daily_energy = _power * _dur

        charge    = np.random.uniform(daily_energy * 0.85, daily_energy * 1.0, size=30)
        avg_rte   = (target_rte - 0.5) / 100.0
        discharge = charge * np.random.uniform(avg_rte - 0.02, avg_rte + 0.01, size=30)

        lang = st.session_state.get('lang', 'KO')
        charge_lbl    = "충전량 (MWh)" if lang == "KO" else "Charge (MWh)"
        discharge_lbl = "방전량 (MWh)" if lang == "KO" else "Discharge (MWh)"

        df_profile = pd.DataFrame({
            'Date': dates,
            charge_lbl: charge,
            discharge_lbl: discharge,
        })

        fig_profile = px.bar(df_profile, x='Date', y=[charge_lbl, discharge_lbl],
                             barmode='group',
                             color_discrete_map={charge_lbl: '#58a6ff', discharge_lbl: '#3fb950'})
        fig_profile.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                  font_color='#c9d1d9', legend_title_text='')
        st.plotly_chart(fig_profile, use_container_width=True)

        # CSV download
        csv_perf = df_profile.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 CSV 다운로드" if lang == "KO" else "📥 Download CSV",
            data=csv_perf,
            file_name="BESS_monthly_profile_DEMO.csv",
            mime="text/csv",
            key="dl_perf_csv",
        )

    # ── Battery Health ─────────────────────────────────────────────
    with tab2:
        st.subheader(t("p6_soh_title"))
        st.markdown(t("p6_soh_desc"))

        # 캘린더(Arrhenius) + 사이클(throughput) 선형 가산 — bess-battery-expert "열화·수명 모델" 앵커로 보정
        ko = lang == "KO"
        sc1, sc2, sc3, sc4 = st.columns(4)
        temp_c = sc1.slider("평균 셀 온도 (°C)" if ko else "Avg cell temp (°C)", 10.0, 45.0, 25.0, 1.0)
        cyc_d  = sc2.slider("일 사이클 수" if ko else "Cycles per day", 0.0, 3.0, 1.0, 0.1)
        dod    = sc3.slider("방전심도 DoD" if ko else "Depth of discharge", 0.5, 1.0, 0.8, 0.05)
        z_exp  = sc4.slider("사이클 지수 z [가정]" if ko else "Cycle exponent z [assumed]", 0.5, 1.0,
                            EP.CYC_EXP_DEFAULT, 0.05)

        years = np.linspace(0, 20, 201)
        cal   = np.array([EP.calendar_loss_pct(temp_c, y) for y in years])
        cyc   = np.array([EP.cycle_loss_pct(cyc_d * 365.0 * y * dod, z_exp) for y in years])
        soh   = 100.0 - cal - cyc
        unc   = EP.DEGRADATION_UNCERTAINTY_PCT

        fig_soh = go.Figure()
        fig_soh.add_trace(go.Scatter(x=years, y=soh + unc, line=dict(width=0), showlegend=False, hoverinfo='skip'))
        fig_soh.add_trace(go.Scatter(x=years, y=soh - unc, line=dict(width=0), fill='tonexty',
                                     fillcolor='rgba(88,166,255,0.15)', hoverinfo='skip',
                                     name=f"±{unc:.0f}%"))
        fig_soh.add_trace(go.Scatter(x=years, y=soh, name="SOH" , line=dict(color='#58a6ff', width=3)))
        fig_soh.add_trace(go.Scatter(x=years, y=100.0 - cal, name="캘린더만" if ko else "Calendar only",
                                     line=dict(color='#3fb950', dash='dash')))
        fig_soh.add_hline(y=EP.SOH_EOL_PCT, line_dash='dot', line_color='#f85149',
                          annotation_text=f"EoL = {EP.SOH_EOL_PCT:.0f}% SOH")
        fig_soh.update_layout(
            xaxis_title="운전 연수 (년)" if ko else "Years in operation",
            yaxis_title="상태 건전성 SOH (%)" if ko else "State of Health SOH (%)",
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font_color='#c9d1d9',
        )
        st.plotly_chart(fig_soh, use_container_width=True)

        m1, m2, m3, m4 = st.columns(4)
        for col, y in zip((m1, m2, m3), (10, 15, 20)):
            v = EP.soh_pct(temp_c, y, cyc_d, dod, z_exp)
            col.metric(f"{y}년 SOH" if ko else f"SOH @ {y} y", f"{v:.1f}%", f"±{unc:.0f}%", delta_color="off")
        below = years[soh < EP.SOH_EOL_PCT]
        m4.metric("EoL 도달" if ko else "Reaches EoL",
                  (f"{below[0]:.1f}년" if ko else f"{below[0]:.1f} y") if below.size else ("20년 초과" if ko else "> 20 y"))

        # 스킬 앵커(캘린더 10년 15% + 7,000사이클 앵커)를 그대로 쓰면 25°C·1회/일 10년 ≈72.7% 인데,
        # 같은 스킬의 '합산 예'는 10년 85~87% — 스킬 내부 모순이라 정본 정리 전까지 [요확인]
        st.warning(
            "[요확인] 스킬 앵커를 그대로 적용한 결과입니다. 같은 스킬의 '합산 예'(10년 잔존 85~87%)와 어긋나 "
            "정본 정리 전까지 보수적 스크리닝 값으로만 보세요. 보증·계약 수치는 셀 시험 데이터·벤더 보증 곡선을 쓰세요."
            if ko else
            "[To verify] Result of applying the skill anchors as-is. It disagrees with the same skill's combined example "
            "(85–87% after 10 y); treat it as a conservative screen until the skill is reconciled. "
            "Use cell test data / vendor warranty curves for contractual figures."
        )

        with st.expander("모델·가정 (스킬 근거)" if ko else "Model & assumptions (skill basis)"):
            st.markdown(
                f"- 총 열화 = 캘린더 + 사이클 (선형 가산) — `bess-battery-expert` 열화·수명 모델\n"
                f"- 캘린더: k(T)·t^{EP.CAL_TIME_EXP} , Arrhenius Ea = **{EP.CAL_EA_J_MOL/1000:.1f} kJ/mol** — "
                f"앵커 25°C 10년·45°C 5년 잔존 85% 두 점으로 역산 (시간 지수 0.5 는 [가정])\n"
                f"- 사이클: 20% × (EFC / {EP.CYC_ANCHOR_EFC:,.0f})^z — 앵커 LFP 80% DoD 7,000사이클 → EoL 80%\n"
                f"- EFC = 일 사이클 × 365 × 연수 × DoD, 불확실성 ±{unc:.0f}%\n"
                f"- 셀 시험 데이터·보증 곡선이 있으면 그 값이 우선이다."
                if ko else
                f"- Total fade = calendar + cycle (linear sum) — `bess-battery-expert` degradation model\n"
                f"- Calendar: k(T)·t^{EP.CAL_TIME_EXP}, Arrhenius Ea = **{EP.CAL_EA_J_MOL/1000:.1f} kJ/mol** fitted to "
                f"anchors 25°C/10 y and 45°C/5 y → 85% remaining (time exponent 0.5 assumed)\n"
                f"- Cycle: 20% × (EFC / {EP.CYC_ANCHOR_EFC:,.0f})^z — anchor LFP 80% DoD 7,000 cycles → 80% EoL\n"
                f"- EFC = cycles/day × 365 × years × DoD, uncertainty ±{unc:.0f}%\n"
                f"- Cell test data or warranty curves take precedence."
            )

        # CSV download
        df_soh = pd.DataFrame({'Year': years, 'SOH(%)': soh, 'Calendar_loss(%)': cal, 'Cycle_loss(%)': cyc})
        csv_soh = df_soh.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 SOH 데이터 CSV 다운로드" if lang == "KO" else "📥 Download SOH Data CSV",
            data=csv_soh,
            file_name="BESS_SOH_degradation.csv",
            mime="text/csv",
            key="dl_soh_csv",
        )

    # ── Anomaly Detection ──────────────────────────────────────────
    with tab3:
        st.subheader(t("p6_anomaly"))
        st.markdown(t("p6_hmap"))

        z_data = np.random.normal(25, 1.5, size=(10, 10))
        z_data[2:4, 7:9] += 8.0

        rack_lbl = "랙 번호"   if lang == "KO" else "Rack Number"
        mod_lbl  = "모듈 번호" if lang == "KO" else "Module Number"
        temp_lbl = "온도 (°C)" if lang == "KO" else "Temp (°C)"

        fig_heatmap = px.imshow(z_data,
                                labels=dict(x=rack_lbl, y=mod_lbl, color=temp_lbl),
                                x=[f"R{i+1}" for i in range(10)],
                                y=[f"M{i+1}" for i in range(10)],
                                color_continuous_scale="Inferno")
        fig_heatmap.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                  font_color='#c9d1d9')
        st.plotly_chart(fig_heatmap, use_container_width=True)

        if st.button(t("p6_detect")):
            with st.spinner("Analyzing..."):
                import time; time.sleep(1.5)
            st.error(t("p6_anomaly_err"))

    st.markdown("---")
    st.subheader(t("p6_std_title"))
    lang = st.session_state.get('lang', 'KO')
    st.info(get_standards(st.session_state.get('target_market', 'US (ERCOT)'), lang, discipline="data"))


run_data_analyst_module()
