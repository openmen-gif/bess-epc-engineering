import streamlit as st
try:
    st.set_page_config(page_title="BESS EPC Platform", layout="wide", initial_sidebar_state="expanded")
except Exception:
    pass

import pandas as pd
from utils.css_loader import apply_custom_css
from utils.lang_helper import t
from utils.auth_helper import require_auth, sidebar_user_info
import time


def auto_fill_expert_samples():
    st.session_state['proj_name'] = "Texas Grid-Scale BESS Phase 2"
    st.session_state['target_market'] = "US (ERCOT)"
    st.session_state['capacity_mw'] = 200.0
    st.session_state['duration_h'] = 2.0
    st.session_state['battery_type'] = "LFP (Lithium Iron Phosphate)"
    st.session_state['site_temp_max'] = 45.0
    st.session_state['site_temp_min'] = -10.0
    st.session_state['grid_voltage'] = "138 kV"
    st.session_state['application'] = ["Frequency Response (FFR)", "Energy Arbitrage"]
    st.session_state['rte_percent'] = 89.5
    st.session_state['aux_loss_percent'] = 3.0
    st.session_state['epc_margin'] = 8.0


def reset_samples():
    for k in ['proj_name', 'target_market', 'capacity_mw', 'duration_h', 'battery_type',
              'site_temp_max', 'site_temp_min', 'grid_voltage', 'application',
              'rte_percent', 'aux_loss_percent', 'epc_margin']:
        if k in st.session_state:
            del st.session_state[k]


def run_project_setup_module():
    apply_custom_css()
    require_auth("01")
    sidebar_user_info()

    st.caption(t("p1_caption"))
    st.title(t("p1_title"))
    st.markdown("---")

    st.info(t("p1_guide"))

    btn_col1, btn_col2 = st.columns([1, 1])
    with btn_col1:
        if st.button(t("p1_autofill")):
            auto_fill_expert_samples()
            st.rerun()
    with btn_col2:
        if st.button(t("p1_reset")):
            reset_samples()
            st.rerun()

    if 'proj_name' not in st.session_state:
        st.session_state['proj_name'] = ""
    if 'capacity_mw' not in st.session_state:
        st.session_state['capacity_mw'] = 0.0
    if 'duration_h' not in st.session_state:
        st.session_state['duration_h'] = 0.0

    def sync_state(key):
        st.session_state[key] = st.session_state["widget_" + key]

    st.subheader(t("p1_s1"))
    col1, col2, col3 = st.columns(3)
    with col1:
        st.text_input(t("p1_proj_name"), value=st.session_state.get('proj_name', ""),
                      key="widget_proj_name", on_change=sync_state, args=("proj_name",))
    with col2:
        st.selectbox(t("p1_market"),
                     ["KR (한국)", "US (ERCOT)", "US (CAISO)", "AU (호주)", "UK (영국)", "JP (일본)", "EU (유럽)"],
                     index=1 if st.session_state.get('target_market') == "US (ERCOT)" else 0,
                     key="widget_target_market", on_change=sync_state, args=("target_market",))
    with col3:
        st.multiselect(t("p1_app"),
                       ["Energy Arbitrage", "Frequency Response (FFR)", "Capacity Market", "Microgrid/Island"],
                       default=st.session_state.get('application', []),
                       key="widget_application", on_change=sync_state, args=("application",))

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader(t("p1_s2"))
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.number_input(t("p1_power"), min_value=0.0, value=st.session_state.get('capacity_mw', 0.0),
                        step=10.0, key="widget_capacity_mw", on_change=sync_state, args=("capacity_mw",))
    with c2:
        st.number_input(t("p1_duration"), min_value=0.0, value=st.session_state.get('duration_h', 0.0),
                        step=0.5, key="widget_duration_h", on_change=sync_state, args=("duration_h",))
    with c3:
        st.selectbox(t("p1_chem"), ["LFP (Lithium Iron Phosphate)", "NMC", "Solid State", "Flow Battery"],
                     index=0, key="widget_battery_type", on_change=sync_state, args=("battery_type",))
    with c4:
        st.selectbox(t("p1_grid_v"), ["22.9 kV", "33 kV", "66 kV", "138 kV", "154 kV", "345 kV"],
                     index=3 if st.session_state.get('grid_voltage') == "138 kV" else 0,
                     key="widget_grid_voltage", on_change=sync_state, args=("grid_voltage",))

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader(t("p1_s3"))
    e1, e2 = st.columns(2)
    with e1:
        st.slider(t("p1_max_temp"), min_value=-20.0, max_value=60.0,
                  value=st.session_state.get('site_temp_max', 35.0),
                  key="widget_site_temp_max", on_change=sync_state, args=("site_temp_max",))
    with e2:
        st.slider(t("p1_min_temp"), min_value=-40.0, max_value=20.0,
                  value=st.session_state.get('site_temp_min', -5.0),
                  key="widget_site_temp_min", on_change=sync_state, args=("site_temp_min",))

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader(t("p1_s4"))
    l1, l2, l3 = st.columns(3)

    if 'rte_percent' not in st.session_state:    st.session_state['rte_percent'] = 88.0
    if 'aux_loss_percent' not in st.session_state: st.session_state['aux_loss_percent'] = 2.5
    if 'epc_margin' not in st.session_state:     st.session_state['epc_margin'] = 5.0

    with l1:
        st.number_input(t("p1_rte"), min_value=70.0, max_value=99.0,
                        value=st.session_state.get('rte_percent', 88.0), step=0.5,
                        key="widget_rte_percent", on_change=sync_state, args=("rte_percent",))
        st.caption(t("p1_rte_help"))
    with l2:
        st.number_input(t("p1_aux_loss"), min_value=0.5, max_value=10.0,
                        value=st.session_state.get('aux_loss_percent', 2.5), step=0.2,
                        key="widget_aux_loss_percent", on_change=sync_state, args=("aux_loss_percent",))
        st.caption(t("p1_aux_help"))
    with l3:
        st.number_input(t("p1_epc_margin"), min_value=0.0, max_value=20.0,
                        value=st.session_state.get('epc_margin', 5.0), step=1.0,
                        key="widget_epc_margin", on_change=sync_state, args=("epc_margin",))
        st.caption(t("p1_epc_help"))


run_project_setup_module()
