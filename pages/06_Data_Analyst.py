import streamlit as st
try:
    st.set_page_config(page_title="BESS EPC Platform", layout="wide", initial_sidebar_state="expanded")
except Exception:
    pass

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.css_loader import apply_custom_css
from utils.lang_helper import t
from utils.standards_helper import get_standards
from utils.auth_helper import require_auth, sidebar_user_info


def run_data_analyst_module():
    apply_custom_css()
    require_auth("06")
    sidebar_user_info()

    st.caption(t("p6_caption"))
    st.title(t("p6_title"))
    st.markdown("---")

    st.info(t("p6_info"))

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

        st.markdown(t("p6_monthly"))

        dates = pd.date_range(start='2026-02-01', periods=30, freq='D')
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
            file_name="BESS_monthly_profile.csv",
            mime="text/csv",
            key="dl_perf_csv",
        )

    # ── Battery Health ─────────────────────────────────────────────
    with tab2:
        st.subheader(t("p6_soh_title"))
        st.markdown(t("p6_soh_desc"))

        cycles      = np.linspace(0, 3000, 100)
        soh_linear  = 100 - (cycles * 0.002)
        soh_sqrt    = 100 - (np.sqrt(cycles) * 0.3)

        soh_lbl1 = "선형 열화 모델" if lang == "KO" else "Linear Degradation Model"
        soh_lbl2 = "루트 열화 모델" if lang == "KO" else "Root Degradation Model"

        fig_soh = go.Figure()
        fig_soh.add_trace(go.Scatter(x=cycles, y=soh_linear, name=soh_lbl1, line=dict(color='#58a6ff', dash='dash')))
        fig_soh.add_trace(go.Scatter(x=cycles, y=soh_sqrt,   name=soh_lbl2, line=dict(color='#3fb950')))
        fig_soh.add_hline(y=80, line_dash='dot', line_color='#f85149',
                          annotation_text="EoL = 80% SOH")
        x_axis = "등가 풀싸이클 (EFC)" if lang == "KO" else "Equivalent Full Cycles (EFC)"
        y_axis = "상태 건전성 SOH (%)"  if lang == "KO" else "State of Health SOH (%)"
        fig_soh.update_layout(
            xaxis_title=x_axis, yaxis_title=y_axis,
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font_color='#c9d1d9',
        )
        st.plotly_chart(fig_soh, use_container_width=True)

        # CSV download
        df_soh = pd.DataFrame({'EFC': cycles, 'SOH_Linear(%)': soh_linear, 'SOH_Root(%)': soh_sqrt})
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
