import streamlit as st
try:
    st.set_page_config(page_title="BESS EPC Platform", layout="wide", initial_sidebar_state="auto")
except Exception:
    pass

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from utils.css_loader import apply_custom_css
from utils.lang_helper import t
from utils.standards_helper import get_standards
from utils.auth_helper import require_auth, sidebar_user_info
from utils import design_model as DM
from utils import engineering_params as EP


def run_system_engineering_module():
    apply_custom_css()
    require_auth("02")
    sidebar_user_info()

    st.caption(t("p2_caption"))
    st.title(t("p2_title"))
    st.markdown("---")

    st.header(t("p2_arch"))
    st.info(t("p2_agent"))

    col1, col2 = st.columns(2)
    with col1:
        st.subheader(t("p2_key_in"))

        default_power = st.session_state.get('capacity_mw', 100.0)
        default_power = default_power if default_power > 0 else 100.0
        default_duration = st.session_state.get('duration_h', 4.0)
        default_duration = default_duration if default_duration > 0 else 4.0
        default_energy = default_power * default_duration

        power_mw  = st.number_input(t("p2_pow"),  min_value=1.0, value=float(default_power),  step=1.0)
        energy_mwh = st.number_input(t("p2_ene"), min_value=1.0, value=float(default_energy), step=1.0)

        c_rate_str = "1C"
        if power_mw > 0 and energy_mwh > 0:
            v = power_mw / energy_mwh
            if v <= 0.25: c_rate_str = "0.25C"
            elif v <= 0.5: c_rate_str = "0.5C"
            elif v <= 1.0: c_rate_str = "1C"
            else: c_rate_str = "2C"
        c_rate_opts = ["0.25C", "0.5C", "1C", "2C"]
        c_rate = st.selectbox(t("p2_crate"), c_rate_opts,
                              index=c_rate_opts.index(c_rate_str) if c_rate_str in c_rate_opts else 0)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**단위 용량설정 (Unit Sizing)**" if st.session_state.get('lang', 'KO') == 'KO' else "**Unit Capacity Settings**")
        pcs_unit_mw = st.number_input(
            "PCS 스키드 단위 용량 (MW)" if st.session_state.get('lang', 'KO') == 'KO' else "PCS Skid Rating (MW/MVA)",
            min_value=0.1, value=st.session_state.get('pcs_unit_mw', 4.2), step=0.1
        )
        batt_unit_mwh = st.number_input(
            "배터리 인클로저 단위 용량 (MWh)" if st.session_state.get('lang', 'KO') == 'KO' else "Battery Enclosure Rating (MWh)",
            min_value=0.1, value=st.session_state.get('batt_unit_mwh', 5.015), step=0.001,
            format="%.3f"
        )

    with col2:
        st.subheader(t("p2_sizing"))

        rte        = st.session_state.get('rte_percent', 88.0) / 100.0
        aux_loss   = st.session_state.get('aux_loss_percent', 2.5) / 100.0
        epc_margin = st.session_state.get('epc_margin', 5.0) / 100.0

        _ko = st.session_state.get('lang', 'KO') == 'KO'
        dod = st.number_input(
            "설계 방전심도 DoD (%)" if _ko else "Design DoD (%)",
            min_value=80.0, max_value=100.0, value=95.0, step=1.0,
        ) / 100.0
        soh_eol = st.number_input(
            "수명말 보증 SOH (%)" if _ko else "End-of-Life SOH (%)",
            min_value=60.0, max_value=100.0, value=80.0, step=1.0,
            help=("BOL 일괄 오버사이징 기준. 증설(augmentation) 전략이면 100%로 두고 별도 증설 계획 수립."
                  if _ko else "BOL oversizing basis. For augmentation strategy set 100% and plan separate additions."),
        ) / 100.0

        # 방전 경로는 편도 효율 √RTE 적용 (RTE는 왕복) + DoD·수명말 SOH 반영
        eta_discharge = float(np.sqrt(rte))
        required_ac_energy   = energy_mwh * (1 + aux_loss)
        required_dc_nameplate = required_ac_energy / (eta_discharge * dod * soh_eol) * (1 + epc_margin)

        st.metric(label=t("p2_duration"), value=f"{energy_mwh / power_mw:.2f} Hours")
        st.metric(label=t("p2_nameplate"), value=f"{required_dc_nameplate:.2f} MWh",
                  help=(f"{epc_margin*100:.0f}% Margin, {aux_loss*100:.1f}% Aux, "
                        f"편도효율 √RTE={eta_discharge*100:.1f}%, DoD {dod*100:.0f}%, EOL SOH {soh_eol*100:.0f}% 반영"))

        num_containers = np.ceil(required_dc_nameplate / batt_unit_mwh)
        st.metric(label=t("p2_enclosure"), value=f"{int(num_containers)} Units", help=f"Capacity per unit: {batt_unit_mwh} MWh")

        required_pcs_mw = power_mw * (1 + aux_loss)
        num_pcs = np.ceil(required_pcs_mw / pcs_unit_mw)
        st.metric(label=t("p2_pcs"), value=f"{int(num_pcs)} Skids", help=f"Rating per unit: {pcs_unit_mw} MW")

        # ── Persist sizing results to session_state for downstream pages ──
        st.session_state['pcs_unit_mw'] = pcs_unit_mw
        st.session_state['batt_unit_mwh'] = batt_unit_mwh
        st.session_state['num_containers'] = int(num_containers)
        st.session_state['num_pcs'] = int(num_pcs)
        st.session_state['required_dc_nameplate'] = required_dc_nameplate
        st.session_state['energy_mwh'] = energy_mwh
        DM.record("system", dict(num_containers=int(num_containers), num_pcs=int(num_pcs),
                                 pcs_unit_mw=pcs_unit_mw, batt_unit_mwh=batt_unit_mwh,
                                 required_dc_mwh=required_dc_nameplate, power_mw=power_mw,
                                 energy_mwh=energy_mwh))

    # ── 배터리 수명 열화 및 증설(Augmentation) 최적화 시뮬레이터 ─────────────
    st.markdown("---")
    st.header("🔋 배터리 수명 열화 & 증설(Augmentation) 전략 비교" if _ko
              else "🔋 Battery Degradation & Augmentation Strategy")
    st.caption("초기 100% 일괄 오버사이징(전략 A) 대비, 5~7년차 부분 증설(전략 B)을 통해 "
               "초기 CAPEX 및 총 생애주기 투자비(NPV)를 절감하는 엔지니어링 분석입니다." if _ko
               else "Compares Day-1 full oversizing (Strategy A) with mid-life augmentation (Strategy B) "
                    "to cut upfront CAPEX and lifecycle NPV.")

    with st.expander("⚙️ 열화 및 증설 시뮬레이션 파라미터" if _ko else "⚙️ Simulation Parameters", expanded=False):
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            sim_years = st.slider("운영 기간 (년)" if _ko else "Project Life (Years)", 10, 25, 15, step=1)
            sim_temp = st.slider("배터리 팩 평균 운전온도 (°C)" if _ko else "Average Operating Temp (°C)", 15.0, 40.0, 25.0, step=1.0)
        with sc2:
            sim_cycles = st.number_input("일일 충방전 횟수 (Cycles/day)" if _ko else "Daily Cycles", 0.5, 3.0, 1.0, step=0.1)
            sim_cell_cost = st.number_input("배터리 셀 초기단가 ($/kWh)" if _ko else "Initial Cell Cost ($/kWh)", 50.0, 200.0, 85.0, step=5.0)
        with sc3:
            sim_cost_decline = st.slider("연간 배터리 단가 하락율 (%)" if _ko else "Annual Cost Decline (%)", 0.0, 10.0, 4.0, step=0.5)
            sim_discount_rate = st.slider("할인율 (%)" if _ko else "Discount Rate (%)", 2.0, 12.0, 6.0, step=0.5)

    # 시뮬레이션 계산 실행
    aug_res = EP.simulate_battery_augmentation(
        project_years=sim_years,
        temp_c=sim_temp,
        cycles_per_day=sim_cycles,
        dod=dod,
        required_ac_mwh=required_ac_energy,
        eta_discharge=eta_discharge,
        soh_eol_target=soh_eol,
        cell_cost_per_kwh_usd=sim_cell_cost,
        annual_cost_decline_pct=sim_cost_decline,
        discount_rate_pct=sim_discount_rate,
    )

    # 핵심 KPI 메트릭 카드 3종
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    with kpi_col1:
        st.metric("초기 CAPEX 절감액" if _ko else "Upfront CAPEX Saved",
                  f"${aug_res['initial_savings_usd']:,.0f}",
                  delta=f"-{aug_res['initial_savings_pct']:.1f}%")
    with kpi_col2:
        st.metric("생애주기 투자비(NPV) 절감" if _ko else "Lifecycle NPV Saved",
                  f"${aug_res['npv_savings_usd']:,.0f}",
                  delta=f"-{aug_res['npv_savings_pct']:.1f}%")
    with kpi_col3:
        st.metric("최적 증설 시점" if _ko else "Recommended Augmentation",
                  f"Year {aug_res['strat_b_aug_year']}",
                  help=f"Year {aug_res['strat_b_aug_year']}에 {aug_res['strat_b_aug_mwh']:.1f} MWh 증설 권장")
    with kpi_col4:
        st.metric(f"{sim_years}년차 잔존 SOH" if _ko else f"Year {sim_years} SOH",
                  f"{aug_res['soh_curve'][-1]:.1f}%",
                  help="Arrhenius 캘린더 열화 + 사이클 처리량 열화 복합 반영")

    # Plotly 시각화 차트: 연도별 공급 가능 유효 용량 추이
    fig_aug = go.Figure()
    fig_aug.add_trace(go.Scatter(
        x=aug_res["years"],
        y=aug_res["strat_a_capacities"],
        mode="lines+markers",
        name="[전략 A] Day-1 올인원 용량" if _ko else "[Strategy A] Day-1 All-in-one",
        line=dict(color="#f85149", width=2.5, dash="dash"),
    ))
    fig_aug.add_trace(go.Scatter(
        x=aug_res["years"],
        y=aug_res["strat_b_capacities"],
        mode="lines+markers",
        name=f"[전략 B] Year {aug_res['strat_b_aug_year']} 증설 전략" if _ko else f"[Strategy B] Augmentation @ Y{aug_res['strat_b_aug_year']}",
        line=dict(color="#3fb950", width=3),
    ))
    fig_aug.add_hline(
        y=aug_res["base_target_dc_mwh"],
        line_dash="dot",
        line_color="#58a6ff",
        annotation_text="계약 보증 최소 필요 용량" if _ko else "Guaranteed Min DC Capacity",
        annotation_position="bottom right",
    )
    fig_aug.update_layout(
        title="연도별 BESS 유효 공급 가능 용량 추이 (MWh)" if _ko else "Yearly Available DC Capacity (MWh)",
        xaxis_title="운영 경과 연수 (Years)" if _ko else "Operating Years",
        yaxis_title="유효 방전 용량 (MWh)" if _ko else "Effective Capacity (MWh)",
        template="plotly_dark",
        height=380,
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_aug, use_container_width=True)

    st.markdown("---")
    st.subheader(t("regional_std"))
    target_market = st.session_state.get('target_market', 'US (ERCOT)')
    lang = st.session_state.get('lang', 'KO')
    st.info(get_standards(target_market, lang, discipline="system"))

    st.markdown("---")
    st.header("📋 Phase Checklists (I/P/O)")

    tab1, tab2, tab3 = st.tabs([t("phase_tab_i"), t("phase_tab_p"), t("phase_tab_o")])

    with tab1:
        st.markdown(t("req_inputs"))
        st.checkbox(t("p2_inp_cb1"))
        st.checkbox(t("p2_inp_cb2"))
        st.checkbox(t("p2_inp_cb3"))

    with tab2:
        st.markdown(t("active_procs"))
        st.checkbox(t("p2_proc_cb1"))
        st.checkbox(t("p2_proc_cb2"))
        st.checkbox(t("p2_proc_cb3"))

    with tab3:
        st.markdown(t("deliverables"))
        st.checkbox(t("p2_out_cb1"))
        st.checkbox(t("p2_out_cb2"))

        st.markdown(t("doc_gateway"))
        if st.button(t("p2_gen_rep"), key="sys_rep"):
            with st.spinner("Compiling..."):
                report_content = (
                    f"BESS System Architecture Conceptual Report\n"
                    f"=============================================\n"
                    f"* Auto-generated by Antigravity BESS Agent\n\n"
                    f"1. Target Capacity\n"
                    f"- Power: {power_mw} MW\n"
                    f"- Energy: {energy_mwh} MWh\n"
                    f"- C-Rate: {c_rate} (Duration: {energy_mwh/power_mw:.2f} Hours)\n\n"
                    f"2. Equipment Sizing\n"
                    f"- Battery Enclosures: {int(num_containers)} Units\n"
                    f"- PCS Skids: {int(num_pcs)} Units\n"
                )
                st.session_state['sys_report_content'] = report_content
                st.success("✅ Report compiled. Click below to download.")

        if 'sys_report_content' in st.session_state:
            st.download_button(
                label=t("p2_dl_rep"),
                data=st.session_state['sys_report_content'],
                file_name=f"BESS_Architecture_Report_{int(power_mw)}MW.txt",
                mime="text/plain",
                type="primary",
            )


run_system_engineering_module()
