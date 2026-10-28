import streamlit as st
try:
    st.set_page_config(page_title="BESS EPC Platform", layout="wide", initial_sidebar_state="auto")
except Exception:
    pass

import numpy as np
from utils.css_loader import apply_custom_css
from utils.lang_helper import t
from utils.standards_helper import get_standards
from utils.auth_helper import require_auth, sidebar_user_info
from utils import engineering_params as EP


# ── Market → Voltage mapping ─────────────────────────────────────────────────
_MARKET_VOLTAGE_MAP = {
    "KR": {
        "hv":  ["22.9kV", "66kV", "154kV", "345kV"],
        "lv":  {"22.9kV": "0.69kV / 1.1kV", "66kV": "22.9kV / 0.69kV",
                "154kV": "22.9kV", "345kV": "22.9kV"},
    },
    "US": {
        "hv":  ["34.5kV", "69kV", "115kV", "138kV", "230kV", "345kV"],
        "lv":  {"34.5kV": "0.69kV", "69kV": "12.47kV / 0.69kV",
                "115kV": "34.5kV", "138kV": "34.5kV",
                "230kV": "34.5kV", "345kV": "138kV / 34.5kV"},
    },
    "AU": {
        "hv":  ["11kV", "33kV", "66kV", "132kV", "220kV"],
        "lv":  {"11kV": "0.415kV", "33kV": "11kV / 0.415kV",
                "66kV": "11kV", "132kV": "33kV", "220kV": "66kV"},
    },
    "UK": {
        "hv":  ["11kV", "33kV", "66kV", "132kV", "275kV", "400kV"],
        "lv":  {"11kV": "0.4kV", "33kV": "11kV / 0.4kV",
                "66kV": "11kV", "132kV": "33kV",
                "275kV": "132kV", "400kV": "132kV"},
    },
    "JP": {
        "hv":  ["22kV", "33kV", "66kV", "77kV", "154kV", "275kV"],
        "lv":  {"22kV": "6.6kV / 0.415kV", "33kV": "6.6kV",
                "66kV": "22kV", "77kV": "22kV",
                "154kV": "66kV", "275kV": "66kV"},
    },
    "EU": {
        "hv":  ["20kV", "35kV", "110kV", "150kV", "220kV", "380kV"],
        "lv":  {"20kV": "0.4kV", "35kV": "10kV / 0.4kV",
                "110kV": "20kV", "150kV": "20kV",
                "220kV": "110kV", "380kV": "110kV"},
    },
}

def _market_key(target_market: str) -> str:
    """Extract 2-letter region key from target_market string."""
    m = target_market.upper()
    if m.startswith("KR"): return "KR"
    if m.startswith("US"): return "US"
    if m.startswith("AU"): return "AU"
    if m.startswith("UK"): return "UK"
    if m.startswith("JP"): return "JP"
    if m.startswith("EU"): return "EU"
    return "KR"  # default

def _parse_kv(s: str) -> float:
    """Parse '22.9kV' → 22900.0  (volts)."""
    try:
        return float(s.lower().replace("kv", "").strip()) * 1000.0
    except ValueError:
        return 22900.0


def run_ebop_engineer_module():
    apply_custom_css()
    require_auth("04")
    sidebar_user_info()

    st.caption(t("p4_caption"))
    st.title(t("p4_title"))
    st.markdown("---")

    st.info(t("p4_info"))

    # ── Resolve market → voltage lists ──────────────────────────────────
    raw_market  = st.session_state.get("target_market", "KR (한국)")
    mkey        = _market_key(raw_market)
    mv          = _MARKET_VOLTAGE_MAP[mkey]
    hv_options  = mv["hv"]
    lv_opts     = mv["lv"]

    # Try to pre-select HV that matches session_state grid_voltage
    gv_raw = str(st.session_state.get("grid_voltage", "")).replace(" ", "")  # e.g. "22.9kV"
    hv_default_idx = 0
    for i, h in enumerate(hv_options):
        if h.lower() == gv_raw.lower():
            hv_default_idx = i
            break

    tab1, tab2, tab3 = st.tabs([t("p4_tab1"), t("p4_tab2"), t("p4_tab3")])

    # ── Transformer Sizing ──────────────────────────────────────────
    with tab1:
        st.subheader(t("p4_tr_title"))
        col1, col2 = st.columns(2)

        with col1:
            default_power = max(st.session_state.get('capacity_mw', 50.0), 1.0)
            power_mw  = st.number_input(t("p4_tr_pow"), min_value=1.0, value=float(default_power), step=1.0)
            aux_loss  = st.session_state.get('aux_loss_percent', 2.5)
            aux_power = st.number_input(t("p4_aux_loss"), min_value=0.5, max_value=10.0, value=float(aux_loss), step=0.1)
            pf        = st.number_input(t("p4_tr_pf"), min_value=0.8, max_value=1.0, value=0.95, step=0.01)
            margin    = st.slider(t("p2_epc_margin"), 0, 25, 10, step=5)

        with col2:
            gross_mw   = power_mw * (1 + aux_power / 100.0)
            base_mva   = gross_mw / pf
            target_mva = base_mva * (1 + margin / 100.0)
            std_sizes  = [1, 2, 2.5, 5, 10, 15, 20, 25, 30, 40, 50, 60, 63, 75, 80, 100, 120, 150, 200]
            selected   = next((s for s in std_sizes if s >= target_mva), "Custom (>200)")

            st.metric(t("p4_base_mva"), f"{base_mva:.2f} MVA")
            st.metric(t("p4_target_mva").format(margin=margin), f"{target_mva:.2f} MVA")

            st.success(f"**{t('p4_tr_rec')}:** {selected} MVA")
            st.divider()
            st.caption(f"🌐 Market: **{raw_market}**")
            hv = st.selectbox(t("p4_tr_volt"), hv_options, index=hv_default_idx)
            st.info(f"LV side: **{lv_opts.get(hv, '0.69kV')}**")

    # ── Cable Sizing ────────────────────────────────────────────────
    with tab2:
        st.subheader(t("p4_cable_title"))
        col1, col2 = st.columns(2)

        # 케이블 사이징 3중 검증: ①허용전류 ②전압강하 ③단락 열적강도 — 하나라도 Fail 이면 상위 단면적
        # (bess-ebop-engineer 핵심 규칙, 판정값은 소유 도메인 bess-cable-engineer)
        is_ko = st.session_state.get('lang', 'KO') == 'KO'
        circuit_opts = [hv] + [s.strip() for s in lv_opts.get(hv, "0.69kV").split("/")]
        with col1:
            circuit_v   = st.selectbox("회로 선간전압" if is_ko else "Circuit line voltage",
                                       circuit_opts, index=len(circuit_opts) - 1)
            V_line      = _parse_kv(circuit_v)
            v_class     = EP.voltage_class(V_line / 1000.0)
            current     = st.number_input(t("p4_cable_i"), min_value=1.0, value=200.0, step=10.0)
            length      = st.number_input(t("p4_cable_l"), min_value=1.0, value=100.0, step=10.0)
            voltage_drop = st.slider(t("p4_cable_drop"), 1.0, 10.0, EP.VDROP_LIMIT_PCT[v_class], 0.5,
                                     key=f"vdrop_{v_class}")
            material    = st.selectbox(t("p4_cable_mat"), [t("p4_cable_cu"), t("p4_cable_al")])
            is_cu = "Cu" in material or "동" in material
            rho = 1.72e-8 if is_cu else 2.82e-8
            st.markdown("**" + ("단락 열적강도" if is_ko else "Short-circuit withstand") + "**")
            i_sc  = st.number_input("단락전류 I_sc (kA)" if is_ko else "Fault current I_sc (kA)",
                                    min_value=0.1, max_value=100.0, value=25.0, step=0.5)
            t_clr = st.number_input("차단 시간 t (s)" if is_ko else "Clearing time t (s)",
                                    min_value=0.02, max_value=3.0, value=0.5, step=0.05)
            k_key = "XLPE-Cu" if is_cu else "XLPE-Al"
            st.markdown("**" + ("허용전류 (선정 단면적의 공인 테이블 값)" if is_ko
                                else "Ampacity (tabulated value for the selected size)") + "**")
            i_base = st.number_input("기준 허용전류 I_base (A) — IEC 60502/60287·NEC 310.16 표" if is_ko
                                     else "Base ampacity I_base (A) — IEC 60502/60287 · NEC 310.16 table",
                                     min_value=0.0, value=None, step=5.0, placeholder="—")
            k_der = st.number_input("디레이팅 ∏k (온도·그룹·토양·깊이, ≤1)" if is_ko
                                    else "Derating ∏k (temp·group·soil·depth, ≤1)",
                                    min_value=0.1, max_value=1.0, value=0.8, step=0.05)

        with col2:
            V_drop   = V_line * (voltage_drop / 100.0)
            # 3상 전압강하 ΔV(L-L) = √3·I·L·R′ — 왕복 계수 2는 DC/단상용이라 √3으로 교정
            # (리액턴스 X 무시 — 저항 지배 가정의 스크리닝 값)
            vd_area  = (rho * np.sqrt(3.0) * length * current) / V_drop * 1e6
            sc_area  = EP.sc_min_area_mm2(i_sc, t_clr, EP.SC_K[k_key])
            min_area = max(vd_area, sc_area)
            std_areas = [16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300, 400, 500, 630, 800, 1000]
            rec_area  = next((a for a in std_areas if a >= min_area), None)
            st.caption(f"{circuit_v} → **{v_class}** · " +
                       (f"전압강하 기준 {EP.VDROP_LIMIT_PCT[v_class]:.0f}% (bess-cable-engineer)" if is_ko
                        else f"voltage-drop limit {EP.VDROP_LIMIT_PCT[v_class]:.0f}% (bess-cable-engineer)"))
            st.metric(("② 전압강하 최소 단면적" if is_ko else "② Min area — voltage drop"), f"{vd_area:.1f} mm²")
            st.metric(("③ 단락 열적강도 최소 단면적" if is_ko else "③ Min area — short-circuit"),
                      f"{sc_area:.1f} mm²", help=f"S = I·√t / k, k = {EP.SC_K[k_key]:.0f} ({k_key}, IEC 60364-4-43)")
            if rec_area is None:
                st.error("단일 케이블 표준 단면적(1,000 mm²) 초과 — 병렬 케이블 검토 필요" if is_ko
                         else "Exceeds 1,000 mm² single-core size — consider parallel cables")
            else:
                st.success(f"**{t('p4_cable_std')}:** {rec_area} mm² "
                           + ("(②·③ 중 큰 값)" if is_ko else "(max of ② and ③)"))
            # ① 허용전류 — U = I_load / (I_base·∏k) ≤ 1/1.25 (설계여유 1.25배)
            if i_base:
                u = current / (i_base * k_der)
                st.metric("① 이용률 U" if is_ko else "① Utilisation U", f"{u:.2f}",
                          help=f"U = I_load / (I_base × ∏k), 설계여유 {EP.AMPACITY_DESIGN_MARGIN}배 → U ≤ {1/EP.AMPACITY_DESIGN_MARGIN:.2f}")
                if u <= 1.0 / EP.AMPACITY_DESIGN_MARGIN:
                    st.success("① 허용전류 Pass" if is_ko else "① Ampacity Pass")
                elif u <= 1.0:
                    st.warning("① 허용전류 여유 부족 (U > 0.8) — 상위 단면적 권고" if is_ko
                               else "① Ampacity margin short (U > 0.8) — upsize recommended")
                else:
                    st.error("① 허용전류 Fail (U > 1.0) — 상위 단면적 재선정" if is_ko
                             else "① Ampacity Fail (U > 1.0) — upsize")
            else:
                st.info("① 허용전류: 위 권장 단면적의 공인 테이블 I_base 를 입력하면 판정합니다 "
                        "(앱은 테이블 값을 추정하지 않음)" if is_ko else
                        "① Ampacity: enter the tabulated I_base for the recommended size to get a verdict "
                        "(the app does not estimate table values)")

    # ── Grounding ───────────────────────────────────────────────────
    with tab3:
        st.subheader(t("p4_gnd_title"))
        st.markdown(t("p4_gnd_desc"))
        rho   = st.slider(t("p4_gnd_rho"), 10, 1000, 100, 10)
        area  = st.number_input(t("p4_gnd_area"), 100, 100000, 2500, 100)
        length = st.number_input(t("p4_gnd_len"), 100, 10000, 1000, 100)
        # Laurent 단순식 Rg = ρ/(4r) + ρ/L, r = 등가 원판 반경 √(A/π)
        # (기존 √A 사용은 첫 항을 √π≈1.77배 과소평가 — 비보수적 오류)
        r_eq = np.sqrt(area / np.pi)
        rg = rho / (4 * r_eq) + rho / length
        st.metric(t("p4_gnd_rg"), f"{rg:.3f} Ω")
        if rg <= 1.0:
            st.success(t("p4_gnd_ok"))
        elif rg <= 10.0:
            st.warning(t("p4_gnd_warn"))
        else:
            st.error(t("p4_gnd_err"))

    st.markdown("---")
    st.subheader(t("regional_std"))
    lang = st.session_state.get('lang', 'KO')
    st.info(get_standards(st.session_state.get('target_market', 'US (ERCOT)'), lang, discipline="ebop"))


run_ebop_engineer_module()
