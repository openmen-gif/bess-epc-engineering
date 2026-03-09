import streamlit as st
try:
    st.set_page_config(page_title="BESS EPC Platform", layout="wide", initial_sidebar_state="expanded")
except Exception:
    pass

import pandas as pd
import numpy as np
from utils.css_loader import apply_custom_css
from utils.lang_helper import t
from utils.standards_helper import get_standards
from utils.auth_helper import require_auth, sidebar_user_info


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

        required_ac_energy   = energy_mwh * (1 + aux_loss)
        required_dc_nameplate = required_ac_energy / rte * (1 + epc_margin)

        st.metric(label=t("p2_duration"), value=f"{energy_mwh / power_mw:.2f} Hours")
        st.metric(label=t("p2_nameplate"), value=f"{required_dc_nameplate:.2f} MWh",
                  help=f"Includes {epc_margin*100}% Margin, {aux_loss*100}% Aux Loss, {(1-rte)*100:.1f}% RTE Derating.")

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
                import time
                time.sleep(1)
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
