import streamlit as st
try:
    st.set_page_config(page_title="BESS EPC Platform", layout="wide", initial_sidebar_state="auto")
except Exception:
    pass

import numpy as np
import plotly.express as px
from utils.css_loader import apply_custom_css
from utils.lang_helper import t
from utils.standards_helper import get_standards
from utils.auth_helper import require_auth, sidebar_user_info
from utils import engineering_params as EP
from utils import design_model as DM


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
            # 02 시스템 설계 결과(DoD·EOL SOH·편도효율 반영)가 현재 01 입력 기준일 때만 우선 — 두 페이지 수량 불일치 방지.
            # 01 이 바뀐 뒤 02 를 다시 열지 않았으면(stale) 옛 수량을 쓰지 않고 자체 식 + 경고
            _sys_state = DM.status("system")
            _n02 = st.session_state.get('num_containers') if _sys_state == "ok" else None
            if _n02:
                default_containers = int(_n02)

            num_enclosures = st.number_input(t("p5_num_enc"), min_value=1, value=default_containers, step=1)
            if _n02:
                st.caption("02 시스템 설계 산정값 적용" if st.session_state.get('lang', 'KO') == 'KO'
                           else "Using 02 System Engineering result")
            elif _sys_state == "stale":
                st.warning("⚠️ 01 입력이 바뀐 뒤 02 시스템 설계를 다시 열지 않아 05 간이식으로 산정했습니다 — "
                           "02 를 다시 열면 DoD·수명말 SOH 를 반영한 수량으로 맞춰집니다."
                           if st.session_state.get('lang', 'KO') == 'KO' else
                           "⚠️ 01 inputs changed since 02 last ran — using 05's simplified sizing. "
                           "Re-open 02 to sync the DoD/EOL-SOH based count.")
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
                                        value=float(bat_power * 0.03 * 1000),  # 3% 발열 (0.5C 스크리닝 대표값)
                                        step=10.0)
            pcs_heat  = st.number_input(t("p5_hvac_pcs_heat"), min_value=0.0,
                                        value=float(bat_power * 0.02 * 1000),  # 2% PCS heat
                                        step=5.0)
            amb_temp  = st.number_input(t("p5_hvac_amb"),    value=float(st.session_state.get('site_temp_max', 40.0)),
                                        min_value=-10.0, max_value=60.0, step=1.0)
            indoor_t  = st.number_input(t("p5_hvac_indoor"), value=25.0,
                                        min_value=15.0, max_value=35.0, step=1.0)
            # 기본 20% — bess-cbop-engineer "안전율 1.2~1.3" 하한
            safety    = st.slider(t("p5_hvac_safety"), 5, 30, 20, step=5)
            cop       = st.number_input(t("p5_hvac_cop"), min_value=2.0, max_value=5.0, value=3.0, step=0.1)
            unit_kw   = st.number_input(t("p5_hvac_unit_kw"), min_value=5.0, max_value=500.0, value=50.0, step=5.0)

        with hc2:
            import math
            dt = max(amb_temp - indoor_t, 0)
            base_load  = bat_heat + pcs_heat
            # 외피 취득열 = U·A·ΔT — 1기 UA 는 탭1 인클로저 치수로 산정, 플랜트 부하는 인클로저 수만큼 더한다
            ENV_UA_KW_PER_K = EP.enc_ua_kw_k(max(length, 0.5), max(width, 0.5))
            env_load   = dt * ENV_UA_KW_PER_K * num_enclosures
            # 안전율은 외피 포함 전체 부하에 곱한다 — bess-cbop-engineer "HVAC_capacity = Q_total × SF"
            total_load = (base_load + env_load) * (1 + safety / 100.0)
            hvac_units = math.ceil(total_load / unit_kw)
            hvac_power = total_load / cop

            st.metric(t("p5_hvac_total"),  f"{total_load:.1f} kW")
            st.metric(t("p5_hvac_units"),  f"{hvac_units} ea")
            st.metric(t("p5_hvac_power"),  f"{hvac_power:.1f} kW")
            st.caption(f"외피 취득열 {env_load:.1f} kW = {num_enclosures}기 × {ENV_UA_KW_PER_K:.3f} kW/K × ΔT {dt:.0f} K "
                       f"(U {EP.ENC_U_W_M2K} W/m²K [가정]) · 일사·환기 부하 미포함"
                       if st.session_state.get('lang', 'KO') == 'KO' else
                       f"Envelope gain {env_load:.1f} kW = {num_enclosures} × {ENV_UA_KW_PER_K:.3f} kW/K × ΔT {dt:.0f} K "
                       f"(U {EP.ENC_U_W_M2K} W/m²K [assumed]) · solar & ventilation not included")

            if total_load <= unit_kw * hvac_units * 0.85:
                st.success(t("p5_hvac_ok"))
            else:
                st.warning(t("p5_hvac_warn"))

    # ── Fire Suppression Design ──────────────────────────────────────
    with tab4:
        st.subheader(t("p5_fire_title"))
        st.caption(t("p5_fire_note"))
        is_ko = st.session_state.get('lang', 'KO') == 'KO'

        fc1, fc2 = st.columns(2)
        # 배터리 컨테이너 기본 = Water Mist(NFPA 750), 청정약제는 PCS실·EMS실용 — bess-fire-engineer "소화 시스템 비교"
        WATER_MIST = "Water Mist (NFPA 750)"
        agent_opts  = [WATER_MIST, "FM-200 (HFC-227ea)", "Novec 1230 (FK-5-1-12)", "CO₂ (고농도)", "질소 (N₂)"]
        # Design concentration by agent (%, as fraction of volume)
        agent_conc  = {"FM-200 (HFC-227ea)": 7.9, "Novec 1230 (FK-5-1-12)": 5.9,
                       "CO₂ (고농도)": 34.0, "질소 (N₂)": 40.6}
        # 증기 밀도 1/s @20°C (kg/m³) — NFPA 2001 비체적 s: FM-200 s=0.1269+0.0005151·t,
        # Novec(FK-5-1-12) s=0.0664+0.0002741·t → 20°C에서 각각 7.29 / 13.91 kg/m³
        agent_dens  = {"FM-200 (HFC-227ea)": 7.29, "Novec 1230 (FK-5-1-12)": 13.91,
                       "CO₂ (고농도)": 1.84, "질소 (N₂)": 1.165}
        # 불활성·CO₂는 고농도라 선형식 부적합 → NFPA 2001 로그식 적용 대상
        inert_agents = {"CO₂ (고농도)", "질소 (N₂)"}

        with fc1:
            room_opts = ["배터리셀실" if st.session_state.get('lang','KO')=='KO' else "Battery Cell Room",
                         "PCS/MV 패널실" if st.session_state.get('lang','KO')=='KO' else "PCS/MV Switchgear Room",
                         "제어실" if st.session_state.get('lang','KO')=='KO' else "Control Room",
                         "전체 컨테이너" if st.session_state.get('lang','KO')=='KO' else "Full Container"]
            room = st.selectbox(t("p5_fire_room"), room_opts)
            battery_room = room in (room_opts[0], room_opts[3])  # 배터리셀실·전체 컨테이너
            vol  = st.number_input(t("p5_fire_vol"),  min_value=1.0, max_value=5000.0, value=120.0, step=10.0)
            # 구역별 기본 약제: 배터리 구역 → Water Mist, PCS·제어실 → Novec 1230
            agent = st.selectbox(t("p5_fire_agent"), agent_opts, index=0 if battery_room else 2)
            if agent == WATER_MIST:
                lo, hi = EP.WATER_MIST_DENSITY_LPM_M3
                wm_dens = st.number_input("방출밀도 (L/min/m³)" if is_ko else "Discharge density (L/min/m³)",
                                          min_value=lo, max_value=hi, value=EP.WATER_MIST_DENSITY_DEFAULT, step=0.01)
                wm_dis  = st.number_input("방출 시간 (분)" if is_ko else "Discharge time (min)",
                                          min_value=EP.WATER_MIST_MIN_DISCHARGE_MIN, max_value=240.0,
                                          value=EP.WATER_MIST_BATTERY_DISCHARGE_MIN, step=5.0)
                wm_ext  = st.number_input("냉각 연장 시간 (분)" if is_ko else "Cooling extension (min)",
                                          min_value=0.0, max_value=240.0,
                                          value=EP.WATER_MIST_COOLING_EXT_MIN, step=10.0)
            else:
                conc  = st.number_input(t("p5_fire_conc"), min_value=1.0, max_value=50.0,
                                        value=agent_conc.get(agent, 7.9), step=0.1)

        with fc2:
          if agent == WATER_MIST:
            # NFPA 750: Q = 방출밀도 × 보호체적 × (방출 + 냉각 연장) — 실시험 인증값 우선
            flow_lpm = wm_dens * vol
            water_l  = flow_lpm * (wm_dis + wm_ext)
            st.metric("펌프 토출량 (L/min)" if is_ko else "Pump flow (L/min)", f"{flow_lpm:.1f}")
            st.metric("소요 수원 (L)" if is_ko else "Required water (L)", f"{water_l:,.0f}")
            st.success(
                "✅ 배터리 구역 권장 방식 — 냉각으로 열폭주 확산·재발화 억제 (NFPA 750). "
                "실제 펌프는 동시 작동 컨테이너 수 × 단위유량 + 안전율로 산정"
                if is_ko else
                "✅ Recommended for battery areas — cooling limits propagation and re-ignition (NFPA 750). "
                "Size the pump for simultaneous containers × unit flow + safety factor"
            )
          else:
            # NFPA 2001 소요량 — 할로카본(저농도): W = V·(C/(100−C))·(1/s)
            #                    불활성(고농도): V_agent = V·ln(100/(100−C)), W = V_agent·ρ
            density = agent_dens.get(agent, 7.29)
            if agent in inert_agents:
                qty_kg = vol * math.log(100.0 / (100.0 - conc)) * density
            else:
                qty_kg = vol * (conc / (100.0 - conc)) * density
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

            # 배터리 구역에 가스계 선택 시 — 냉각·재발화 억제 한계 경고
            if battery_room:
                st.warning(
                    "⚠️ 배터리 구역에 가스계 약제를 선택했습니다 — 청정약제는 PCS실·EMS실용이며 "
                    "열폭주 냉각·재발화 억제에 한계가 있습니다. 배터리 구역은 Water Mist(NFPA 750)가 기본입니다."
                    if is_ko else
                    "⚠️ Gaseous agent selected for a battery area — clean agents are meant for PCS/EMS rooms and "
                    "have limited cooling / re-ignition control. Battery areas default to Water Mist (NFPA 750)."
                )
            if agent.startswith("FM-200"):
                st.caption(f"FM-200 GWP = {EP.FM200_GWP:,} — 규제 강화 추세" if is_ko
                           else f"FM-200 GWP = {EP.FM200_GWP:,} — tightening regulation")

    _fire = dict(fire_agent=agent, fire_volume_m3=vol)
    if agent == WATER_MIST:
        _fire.update(water_l=water_l, pump_lpm=flow_lpm)
    else:
        _fire.update(agent_kg=qty_kg)
    # n_enc 산정 근거 — 02 결과 / 02 stale 이라 05 간이식 / 05 간이식(02 미실행). 13 표가 stale 을 ⚠️로 띄운다
    _basis = "p02" if _n02 else ("p05-stale" if _sys_state == "stale" else "p05")
    DM.record("cbop", dict(n_enc=int(num_enclosures), n_enc_basis=_basis, enc_l=length, enc_w=width, enc_weight_t=weight,
                           pad_l=pad_length, pad_w=pad_width, bearing_ratio=ratio,
                           trench_w=trench_width, trench_d=trench_depth,
                           bat_heat_kw=bat_heat, pcs_heat_kw=pcs_heat, hvac_load_kw=total_load,
                           hvac_units=hvac_units, hvac_installed_kw=hvac_units * unit_kw,
                           hvac_safety_pct=safety, hvac_dt_k=dt, env_ua_kw_k=ENV_UA_KW_PER_K, **_fire))

    st.markdown("---")
    st.subheader(t("regional_std"))
    lang = st.session_state.get('lang', 'KO')
    st.info(get_standards(st.session_state.get('target_market', 'US (ERCOT)'), lang, discipline="cbop"))



run_cbop_engineer_module()
