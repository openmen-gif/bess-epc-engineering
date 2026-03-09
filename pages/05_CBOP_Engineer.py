import streamlit as st
try:
    st.set_page_config(page_title="BESS EPC Platform", layout="wide", initial_sidebar_state="expanded")
except Exception:
    pass

import numpy as np
import plotly.express as px
from utils.css_loader import apply_custom_css
from utils.lang_helper import t
from utils.standards_helper import get_standards
from utils.auth_helper import require_auth, sidebar_user_info


def run_cbop_engineer_module():
    apply_custom_css()
    require_auth("05")
    sidebar_user_info()

    st.caption(t("p5_caption"))
    st.title(t("p5_title"))
    st.markdown("---")

    st.info(t("p5_info"))

    tab1, tab2, tab3, tab4 = st.tabs([t("p5_tab1"), t("p5_tab2"), t("p5_tab3"), t("p5_tab4")])

    # ── Equipment Pad Sizing ────────────────────────────────────────
    with tab1:
        st.subheader(t("p5_pad_title"))
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(t("p5_inp_title"))

            rte        = st.session_state.get('rte_percent', 88.0) / 100.0
            aux_loss   = st.session_state.get('aux_loss_percent', 2.5) / 100.0
            epc_margin = st.session_state.get('epc_margin', 5.0) / 100.0
            default_power = max(st.session_state.get('capacity_mw', 0.0), 1.0)
            target_ac_energy = default_power * st.session_state.get('duration_h', 4.0)
            required_dc = (target_ac_energy * (1 + aux_loss)) / rte * (1 + epc_margin)
            _batt_unit = st.session_state.get('batt_unit_mwh', 5.015)
            default_containers = max(int(np.ceil(required_dc / _batt_unit)), 1)

            num_enclosures = st.number_input(t("p5_num_enc"), min_value=1, value=default_containers, step=1)
            soil_bearing   = st.slider(t("p5_soil"),  50, 300, 150)
            wind_speed     = st.number_input(t("p5_wind"), 20, 80, 45)

            st.markdown(t("p5_enc_dim"))
            length = st.number_input(t("p5_len"), value=6.05)
            width  = st.number_input(t("p5_wid"), value=2.44)
            weight = st.number_input(t("p5_wgt"), value=35.0)

        with col2:
            st.markdown(t("p5_out_title"))

            pad_length = length + 1.0
            pad_width  = width  + 1.0
            pad_area   = pad_length * pad_width
            total_area = pad_area * num_enclosures
            load       = (weight * 1000 * 9.81) / (pad_area * 1000)  # kPa
            ratio      = load / soil_bearing

            st.metric(t("p5_pad_l"), f"{pad_length:.2f} m")
            st.metric(t("p5_pad_w"), f"{pad_width:.2f} m")
            st.metric(t("p5_pad_a"), f"{pad_area:.2f} m²")
            st.metric(t("p5_tot_a"), f"{total_area:.1f} m²")
            st.metric(t("p5_brg"),   f"{ratio:.2f}")

            if ratio <= 0.5:
                st.success(t("p5_brg_ok"))
            elif ratio <= 0.8:
                st.warning(t("p5_brg_warn"))
            else:
                st.error(t("p5_brg_err"))

    # ── Trench & Duct Bank ──────────────────────────────────────────
    with tab2:
        st.subheader(t("p5_trench_title"))
        tc1, tc2 = st.columns(2)

        with tc1:
            num_cables  = st.number_input(t("p5_mv_n"),    1, 100, 24)
            cable_dia   = st.number_input(t("p5_cable_od"), 20, 100, 55)
            spacing     = st.slider(t("p5_spacing"), 1.0, 3.0, 2.0)

        with tc2:
            trench_width = num_cables * (cable_dia * spacing / 1000.0)
            trench_depth = 1.2
            st.metric(t("p5_tw"), f"{trench_width:.2f} m")
            st.metric(t("p5_td"), f"{trench_depth:.2f} m")
            if trench_width > 2.0:
                st.warning(t("p5_trench_warn"))

    # ── HVAC Cooling Load ────────────────────────────────────────────
    with tab3:
        st.subheader(t("p5_hvac_title"))
        hc1, hc2 = st.columns(2)

        with hc1:
            bat_power = max(st.session_state.get('capacity_mw', 50.0), 1.0)
            bat_heat  = st.number_input(t("p5_hvac_bat_heat"), min_value=0.0,
                                        value=float(bat_power * 0.05 * 1000),  # 5% heat loss → kW
                                        step=10.0)
            pcs_heat  = st.number_input(t("p5_hvac_pcs_heat"), min_value=0.0,
                                        value=float(bat_power * 0.02 * 1000),  # 2% PCS heat
                                        step=5.0)
            amb_temp  = st.number_input(t("p5_hvac_amb"),    value=float(st.session_state.get('site_temp_max', 40.0)),
                                        min_value=-10.0, max_value=60.0, step=1.0)
            indoor_t  = st.number_input(t("p5_hvac_indoor"), value=25.0,
                                        min_value=15.0, max_value=35.0, step=1.0)
            safety    = st.slider(t("p5_hvac_safety"), 5, 30, 15, step=5)
            cop       = st.number_input(t("p5_hvac_cop"), min_value=2.0, max_value=5.0, value=3.0, step=0.1)
            unit_kw   = st.number_input(t("p5_hvac_unit_kw"), min_value=5.0, max_value=500.0, value=50.0, step=5.0)

        with hc2:
            import math
            dt = max(amb_temp - indoor_t, 0)
            base_load  = bat_heat + pcs_heat
            total_load = base_load * (1 + safety / 100.0) + dt * 0.5  # simplified external gain
            hvac_units = math.ceil(total_load / unit_kw)
            hvac_power = total_load / cop

            st.metric(t("p5_hvac_total"),  f"{total_load:.1f} kW")
            st.metric(t("p5_hvac_units"),  f"{hvac_units} ea")
            st.metric(t("p5_hvac_power"),  f"{hvac_power:.1f} kW")

            if total_load <= unit_kw * hvac_units * 0.85:
                st.success(t("p5_hvac_ok"))
            else:
                st.warning(t("p5_hvac_warn"))

    # ── Fire Suppression Design ──────────────────────────────────────
    with tab4:
        st.subheader(t("p5_fire_title"))
        st.caption(t("p5_fire_note"))

        fc1, fc2 = st.columns(2)
        agent_opts  = ["FM-200 (HFC-227ea)", "Novec 1230 (FK-5-1-12)", "CO₂ (고농도)", "질소 (N₂)"]
        # Design concentration by agent (%, as fraction of volume)
        agent_conc  = {"FM-200 (HFC-227ea)": 7.9, "Novec 1230 (FK-5-1-12)": 5.9,
                       "CO₂ (고농도)": 34.0, "질소 (N₂)": 40.6}
        # Agent density (kg/m³ at design concentration)
        agent_dens  = {"FM-200 (HFC-227ea)": 7.28, "Novec 1230 (FK-5-1-12)": 8.35,
                       "CO₂ (고농도)": 1.88, "질소 (N₂)": 1.16}

        with fc1:
            room_opts = ["배터리셀실" if st.session_state.get('lang','KO')=='KO' else "Battery Cell Room",
                         "PCS/MV 패널실" if st.session_state.get('lang','KO')=='KO' else "PCS/MV Switchgear Room",
                         "제어실" if st.session_state.get('lang','KO')=='KO' else "Control Room",
                         "전체 컨테이너" if st.session_state.get('lang','KO')=='KO' else "Full Container"]
            room = st.selectbox(t("p5_fire_room"), room_opts)
            vol  = st.number_input(t("p5_fire_vol"),  min_value=1.0, max_value=5000.0, value=120.0, step=10.0)
            agent = st.selectbox(t("p5_fire_agent"), agent_opts)
            conc  = st.number_input(t("p5_fire_conc"), min_value=1.0, max_value=50.0,
                                    value=agent_conc.get(agent, 7.9), step=0.1)

        with fc2:
            # Simplified agent mass = Volume × (C/(100-C)) × agent_density
            c_frac  = conc / (100.0 - conc)
            density = agent_dens.get(agent, 7.28)
            qty_kg  = vol * c_frac * density
            cyls    = math.ceil(qty_kg / 50.0)

            st.metric(t("p5_fire_qty"), f"{qty_kg:.1f} kg")
            st.metric(t("p5_fire_cy"), f"{cyls} ea")
            st.metric(t("p5_fire_conc"), f"{conc:.1f} %")

            # Colour-coded risk level
            if conc < 8:
                st.success(f"✅ {agent} — 안전 농도 범위" if st.session_state.get('lang','KO')=='KO'
                           else f"✅ {agent} — Safe concentration range")
            elif conc < 35:
                st.warning(f"⚠️ {agent} — 산소 결핍 위험, 출입 통제 필수" if st.session_state.get('lang','KO')=='KO'
                           else f"⚠️ {agent} — Oxygen depletion risk, entry control required")
            else:
                st.error(f"🚨 {agent} — 고농도, 인명 위험 농도" if st.session_state.get('lang','KO')=='KO'
                         else f"🚨 {agent} — High concentration, fatal exposure risk")

    st.markdown("---")
    st.subheader(t("regional_std"))
    lang = st.session_state.get('lang', 'KO')
    st.info(get_standards(st.session_state.get('target_market', 'US (ERCOT)'), lang, discipline="cbop"))



run_cbop_engineer_module()
