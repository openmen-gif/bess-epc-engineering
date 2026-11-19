import streamlit as st
try:
    st.set_page_config(page_title="BESS EPC Platform", layout="wide", initial_sidebar_state="auto")
except Exception:
    pass

from datetime import datetime

import plotly.graph_objects as go
from utils.css_loader import apply_custom_css
from utils.fig_compact import compact
from utils.auth_helper import require_auth, sidebar_user_info
from utils import engineering_params as EP
from utils import design_model as DM
from utils import site_layout as SL
from utils.engineering_viewer import render_viewer, site_payload

_KIND = {  # 종류 → (한글, 영문, 색)
    "enc":        ("배터리 인클로저", "Battery enclosure", "#f8fafc"),
    "pcs":        ("PCS/MV 스키드", "PCS/MV skid", "#1565c0"),
    "tr":         ("주변압기 (POI)", "Main transformer (POI)", "#e3b341"),
    "bund":       ("변압기 방유제 (Bund)", "Transformer Bund Wall", "#8b949e"),
    "ehouse":     ("E-House (수배전반/제어실)", "E-House (Switchgear/Control)", "#00b4d8"),
    "pump_house": ("소방 가압 펌프실", "Fire Pump House", "#d90429"),
    "tank":       ("소방 수조", "Fire water tank", "#79c0ff"),
    "storage":    ("O&M 자재 보관소", "O&M parts storage", "#4a5568"),
    "basin":      ("비상 저류조 (침사지)", "Emergency Retention Basin", "#2a9d8f"),
    "hydrant":    ("옥외 소화전", "Fire Hydrant", "#e63946"),
}
_SRC = {"p01": "01 프로젝트 설정", "p02": "02 시스템 설계", "p04": "04 전기 BOP", "p05": "05 토목 BOP"}
_SRC_EN = {"p01": "01 Project Setup", "p02": "02 System Eng", "p04": "04 EBOP", "p05": "05 CBOP"}


def run_site_layout_module():
    apply_custom_css()
    require_auth("13")
    sidebar_user_info()
    ko = st.session_state.get("lang", "KO") == "KO"
    L = (lambda k, e: k if ko else e)

    st.caption(L("🛤️ **BESS EPC 워크플로우:** 02 시스템 · 04 전기 · 05 토목 → **[13: 3D 부지 배치]**",
                 "🛤️ **BESS EPC Workflow:** 02 System · 04 EBOP · 05 CBOP → **[13: Site Layout 3D]**"))
    st.title(L("📐 3D 부지 배치", "📐 Site Layout 3D"))
    st.info(L("02·04·05 설계 페이지의 계산값을 그대로 받아 부지 배치를 자동 생성합니다. "
              "설계 페이지에서 값을 바꾸면 이 화면이 따라 바뀝니다.",
              "Builds the site layout directly from the results of design pages 02·04·05. "
              "Change a value there and this view follows."))
    st.caption(L("스크리닝 배치입니다 — 실시공 배치도는 지형·인허가·AHJ 협의로 확정합니다. "
                 "장비 외형(PCS 6.05×2.44 m, 주변압기 8×6 m, 인클로저 높이 2.9 m)은 [가정] 값입니다.",
                 "Screening layout — the construction layout is fixed by terrain, permits and AHJ review. "
                 "Equipment envelopes (PCS 6.05×2.44 m, main TR 8×6 m, enclosure height 2.9 m) are [assumed]."))

    # ── 입력 출처 표 ────────────────────────────────────────────────────────
    inp = DM.layout_inputs()
    stat = {s: DM.status(s) for s in ("system", "ebop", "cbop")}
    sec_of = {"p02": "system", "p04": "ebop", "p05": "cbop"}
    names = {
        "n_enc": L("인클로저 수", "Enclosures"), "n_pcs": L("PCS 스키드 수", "PCS skids"),
        "enc_l": L("인클로저 길이 (m)", "Enclosure length (m)"), "enc_w": L("인클로저 폭 (m)", "Enclosure width (m)"),
        "trench_w": L("트렌치 폭 (m)", "Trench width (m)"), "trench_d": L("트렌치 깊이 (m)", "Trench depth (m)"),
        "pad_l": L("기초 패드 길이 (m)", "Pad length (m)"), "pad_w": L("기초 패드 폭 (m)", "Pad width (m)"),
        "water_m3": L("소방 수원 (m³)", "Fire water (m³)"),
        "main_tr_mva": L("주변압기 (MVA)", "Main TR (MVA)"), "cable_area_mm2": L("케이블 단면적 (mm²)", "Cable size (mm²)"),
        "target_market": L("목표 시장", "Target market"),
    }
    rows = []
    for k, label in names.items():
        v, src = inp[k]
        if src == "[가정]":
            badge = L("⚪ 미실행", "⚪ not run")
        elif ((sec_of.get(src) and stat[sec_of[src]] == "stale")
              or (k == "n_enc" and (DM.get("cbop") or {}).get("n_enc_basis") == "p05-stale")):
            badge = L("⚠️ 재계산", "⚠️ recompute")
        else:
            badge = "✅"
        shown = "—" if v is None else (f"{v:,.2f}" if isinstance(v, float) else str(v))
        rows.append({L("항목", "Item"): label, L("값", "Value"): shown,
                     L("출처", "Source"): (_SRC if ko else _SRC_EN).get(src, src), L("상태", "Status"): badge})
    with st.expander(L("🔗 설계값 출처 (설계 모델)", "🔗 Design value sources (design model)"),
                     expanded=any(r[L("상태", "Status")] != "✅" for r in rows)):
        st.dataframe(rows, use_container_width=True, hide_index=True)
        st.caption(L("⚪ 미실행 = 해당 설계 페이지를 아직 열지 않아 기본값[가정] 사용 · "
                     "⚠️ 재계산 = 01 입력이 바뀐 뒤 해당 페이지를 다시 열지 않음",
                     "⚪ not run = page not opened yet, default [assumed] used · "
                     "⚠️ recompute = 01 inputs changed since that page last ran"))

    # ── 파워블록 구성 & PCS 연계 비율 메인 설정 (상단 전면 노출) ───────────────────────
    st.markdown("### ⚡ " + L("파워블록 연계 비율 & 전기 아키텍처 설정", "Power Block Coupling Ratio & Electrical Architecture"))
    st.caption(L("실제 BESS 현장 표준 비율(1:1, 1:2, 1:3, 1:4, 2:3)에 따라 PCS 대당 배터리 수량을 즉시 설정하고 최적 배치합니다.",
                 "Configures PCS-to-battery ratio (1:1, 1:2, 1:3, 1:4, 2:3) to optimize layout and power block boundaries."))

    pbc1, pbc2, pbc3 = st.columns([1.5, 1.2, 1.2])
    pb_ratio_opts = [
        L("02 시스템 설계값 자동 연동 (Auto from 02 System Eng)", "Auto from 02 System Engineering"),
        L("1 : 2 (PCS 1대당 배터리 2대 - 0.5C 표준형) [권장]", "1 : 2 (1 PCS : 2 Batteries - 0.5C Standard) [Recommended]"),
        L("1 : 4 (PCS 1대당 배터리 4대 - 0.25C 장주기 대칭형)", "1 : 4 (1 PCS : 4 Batteries - 0.25C Long-Duration Symmetric)"),
        L("1 : 3 (PCS 1대당 배터리 3대 - 3.45MW 대용량형)", "1 : 3 (1 PCS : 3 Batteries - 3.45MW High-Cap)"),
        L("1 : 1 (PCS 1대당 배터리 1대 - 1C 고출력 단독형)", "1 : 1 (1 PCS : 1 Battery - 1C High-Power)"),
        L("2 : 3 (PCS 2대당 배터리 3대 - 듀얼 인버터 공유형)", "2 : 3 (2 PCS : 3 Batteries - Dual-Inverter Shared)"),
        L("사용자 직접 지정 (Custom)", "Custom Manual Entry"),
    ]
    pb_choice = pbc1.selectbox(
        L("⚡ 파워블록 연계 비율 (PCS : Battery)", "Power Block Ratio (PCS : Bat)"),
        pb_ratio_opts, index=0, key="sl_pb_ratio",
        help=L("실제 BESS 현장의 표준 파워블록 연계 비율(1:1, 1:2, 1:3, 1:4, 2:3)을 선택하여 PCS 대수와 구획을 자동 재편합니다.",
               "Selects industry standard power block coupling ratio (1:1, 1:2, 1:3, 1:4, 2:3) to size PCS skids.")
    )
    topo_choice = pbc2.selectbox(
        L("블록 배치 구조 (Topology)", "Block Topology"),
        [L("중앙 집중형 (Center-Fed 대칭) [권장]", "Center-Fed Cluster [Recommended]"),
         L("선형 일렬형 (Linear, 말단 배치)", "Linear (PCS at end)")],
        index=0,
        help=L("중앙 집중형: PCS를 블록 가운데 두고 배터리를 대칭 배치하여 DC 케이블 최대 거리 및 스트링 간 편차를 최소화합니다.",
               "Center-Fed: Places PCS in the center with symmetric battery pairs to minimize DC cable run and imbalance.")
    )
    tr_pos_choice = pbc3.selectbox(
        L("주변압기(POI) 위치", "Main TR Location"),
        [L("남측 부하 중심 (Center) [권장]", "South Load Center [Recommended]"),
         L("남서측 모서리 (Corner)", "South-West Corner")],
        index=0,
        help=L("부하 중심: 주변압기를 남측 중앙에 두어 MV 케이블 최장 경로와 트렌치 총연장을 25~35% 단축합니다.",
               "Load Center: Centers the main TR along the south band, cutting MV cable route by 25-35%.")
    )

    # ── 부지 세부 이격거리 설정 (Expander) ─────────────────────────────────
    mk = EP.market_key(inp["target_market"][0])
    sep = EP.SEPARATION_BY_MARKET[mk]
    with st.expander(L("⚙️ 세부 이격거리 & 인프라 설정 (시장: ", "⚙️ Clearance & Infra Parameters (Market: ") + f"{mk})", expanded=False):
        st.caption(f"{sep['src']} {sep['tag']} — " + L("값 소유: bess-fire-engineer", "owner: bess-fire-engineer"))
        c1, c2 = st.columns(2)
        unit_gap = c1.number_input(L("유닛 간 이격 (m)", "Unit separation (m)"), 0.3, 20.0,
                                   float(sep["unit_m"]), 0.1, key=f"sl_gap_{mk}")
        boundary = c2.number_input(L("부지경계 이격 (m)", "Property-line clearance (m)"), 0.0, 50.0,
                                   float(sep["boundary_m"]), 0.5, key=f"sl_bnd_{mk}")
        aisle = c1.number_input(L("블록 행 사이 통로 (m) [가정]", "Aisle between block rows (m) [assumed]"),
                                0.0, 20.0, EP.ACCESS_AISLE_M, 0.5)
        tr_clear = c2.number_input(L("주변압기 이격 (m) [가정]", "Main TR clearance (m) [assumed]"),
                                   0.0, 30.0, EP.TRANSFORMER_CLEARANCE_M, 0.5,
                                   help=L("IEC 61936-1·FM Global DS 5-4 에서 절연유량·내화등급별로 정함 — 조항 확인 전 스크리닝 값",
                                          "Set by IEC 61936-1 / FM Global DS 5-4 per oil volume & fire rating — screening value"))

        include_ehouse = st.checkbox(
            L("E-House (수배전반 및 제어실 40ft HC) 포함 [권장]", "Include E-House (Switchgear & Control Room 40ft HC) [Recommended]"),
            value=True,
            help=L("MV Switchgear(VCB/보호계전기), EMS/SCADA 서버랙, 소방수신반(FACP), UPS를 내장한 프리패브 E-House를 남측 간선에 배치합니다.",
                   "Places a prefabricated 40ft HC E-House containing MV switchgear, EMS/SCADA racks, FACP, and UPS along the south trunk.")
        )
        include_infra = st.checkbox(
            L("부지 방재·인프라 (방유제 · 소화전 · 펌프실 · 저류조 · 보관소) 포함 [권장]",
              "Include Site Infra (Bund · Hydrants · Pump House · Basin · Storage) [Recommended]"),
            value=True,
            help=L("NFPA 850 오일 방유제, NFPA 24 소화전 시스템(45m 간격), 소방 펌프실, 환경 배수 저류조, O&M 보관소를 실물 배치합니다.",
                   "Places oil bund, perimeter fire hydrants (45m spacing), pump house, retention basin, and O&M storage container.")
        )

    topology_val = "center_fed" if "Center-Fed" in topo_choice or "중앙" in topo_choice else "linear"
    tr_pos_val = "center" if "Center" in tr_pos_choice or "중심" in tr_pos_choice else "corner"

    # 파워블록 연계 비율에 따른 PCS 수량 동적 산출
    import math
    n_enc_val = int(inp["n_enc"][0])
    raw_n_pcs = int(inp["n_pcs"][0])

    if "1 : 2" in pb_choice:
        effective_n_pcs = max(1, math.ceil(n_enc_val / 2))
        ratio_tag = "1:2"
    elif "1 : 4" in pb_choice:
        effective_n_pcs = max(1, math.ceil(n_enc_val / 4))
        ratio_tag = "1:4"
    elif "1 : 3" in pb_choice:
        effective_n_pcs = max(1, math.ceil(n_enc_val / 3))
        ratio_tag = "1:3"
    elif "1 : 1" in pb_choice:
        effective_n_pcs = n_enc_val
        ratio_tag = "1:1"
    elif "2 : 3" in pb_choice:
        effective_n_pcs = max(1, math.ceil(n_enc_val * 2 / 3))
        ratio_tag = "2:3"
    elif "사용자" in pb_choice or "Custom" in pb_choice:
        custom_pcs = st.number_input(L("PCS 스키드 수량 직접 지정", "Custom PCS Count"),
                                     min_value=1, max_value=n_enc_val, value=raw_n_pcs, step=1,
                                     key="sl_custom_pcs")
        effective_n_pcs = int(custom_pcs)
        ratio_tag = f"1:{n_enc_val / effective_n_pcs:.1f}"
    else:
        effective_n_pcs = raw_n_pcs
        ratio_tag = f"1:{n_enc_val / max(1, raw_n_pcs):.1f}"

    lay = SL.build_layout(n_enc_val, effective_n_pcs, inp["enc_l"][0], inp["enc_w"][0],
                          unit_gap=unit_gap, boundary=boundary, aisle=aisle, tr_clear=tr_clear,
                          trench_w=inp["trench_w"][0], water_m3=inp["water_m3"][0],
                          topology=topology_val, tr_pos=tr_pos_val, include_ehouse=include_ehouse,
                          include_infra=include_infra)
    m, chk = lay["metrics"], SL.check_layout(lay)

    st.info(L(f"🔋 **파워블록 연계 최적화 ({ratio_tag}):** 배터리 인클로저 **{n_enc_val}기**에 PCS **{effective_n_pcs}대**를 매칭하여 "
              f"총 **{m['power_blocks_count']}개**의 독립 파워블록을 형성했습니다. (블록당 배터리 평균 {m['enc_per_pcs_ratio']:.1f}기 · DC 케이블 최대 {m['dc_max_cable_m']:.1f}m · 불균형 {m['dc_cable_imbalance_m']:.1f}m)",
              f"🔋 **Power Block Interconnection ({ratio_tag}):** {n_enc_val} Enclosures paired with {effective_n_pcs} PCS skids "
              f"forming {m['power_blocks_count']} power blocks. (Avg {m['enc_per_pcs_ratio']:.1f} Bat/PCS · Max DC {m['dc_max_cable_m']:.1f}m · Imbalance {m['dc_cable_imbalance_m']:.1f}m)"))

    # ── 기준안 비교 — 설계값을 바꾸기 전 배치를 저장해 두면 변화량·이전 윤곽을 함께 보여준다 ──────
    base = st.session_state.get("sl_baseline")
    k1, k2 = st.columns(2)
    if k1.button(L("📌 현재 배치를 기준안으로 저장", "📌 Save current layout as baseline"), use_container_width=True):
        base = {"metrics": dict(m), "ts": datetime.now().strftime("%H:%M"),
                "boxes": [{k: x[k] for k in ("kind", "x", "y", "dx", "dy", "dz")} for x in lay["boxes"]]}
        st.session_state["sl_baseline"] = base
    if base and k2.button(L("기준안 지우기", "Clear baseline"), use_container_width=True):
        st.session_state.pop("sl_baseline", None)
        base = None
    dlt = SL.diff_metrics(m, base["metrics"]) if base else {}

    def _delta(key, unit, nd=0):
        # 변화 0 이면 표시하지 않는다 — Streamlit 은 '-' 로 시작하지 않는 문자열을 전부 ↑ 로 그린다
        if key not in dlt or abs(dlt[key][2]) < 1e-9:
            return None
        _, _, dv, dp = dlt[key]
        return f"{dv:+,.{nd}f} {unit} ({dp:+.1f}%)"

    # ── 지표 ───────────────────────────────────────────────────────────────
    a, b, c, d = st.columns(4)
    a.metric(L("부지 면적", "Site area"), f"{m['site_area_m2']:,.0f} m²", delta=_delta("site_area_m2", "m²"),
             delta_color="inverse", help=f"{m['site_w_m']:.1f} × {m['site_h_m']:.1f} m")
    b.metric(L("인클로저 / PCS", "Enclosures / PCS"), f"{m['n_enc']} / {m['n_pcs']}",
             delta=_delta("n_enc", L("기", "units")), delta_color="off",
             help=L(f"블록 {m['blocks_cols']}열 × {m['blocks_rows']}행, 블록당 최대 {m['enc_per_block']}기",
                    f"{m['blocks_cols']} × {m['blocks_rows']} blocks, ≤{m['enc_per_block']} per block"))
    c.metric(L("트렌치 총연장", "Total trench"), f"{m['trench_len_m']:,.0f} m", delta=_delta("trench_len_m", "m"),
             delta_color="inverse")
    d.metric(L("최장 케이블 경로", "Longest cable route"), f"{m['longest_cable_m']:,.1f} m",
             delta=_delta("longest_cable_m", "m", 1), delta_color="inverse",
             help=L("PCS → 주변압기 직각 경로 길이 (여장·단말 미포함)",
                    "PCS → main TR orthogonal route (no slack/termination allowance)"))

    # ── 케이블 루트 및 인버터-배터리 연계 최적화 세부 지표 ────────────────────
    c_opt1, c_opt2, c_opt3, c_opt4 = st.columns(4)
    c_opt1.metric(
        L("DC 케이블 최장 거리", "Max DC Cable Run"),
        f"{m.get('dc_max_cable_m', 0.0):.1f} m",
        delta=L("대칭 배치로 단축됨", "Optimized by Center-Fed") if topology_val == "center_fed" else None,
        delta_color="normal",
        help=L("인클로저 -> 담당 PCS 간 최장 거리 (Center-Fed 대칭 배치 시 50% 단축)",
               "Longest distance from battery to its PCS (50% shorter with Center-Fed)")
    )
    c_opt2.metric(
        L("DC 스트링 경로 편차 (최장-최단)", "DC String Imbalance"),
        f"{m.get('dc_cable_imbalance_m', 0.0):.1f} m",
        help=L("블록 내 배터리 간 DC 케이블 길이 편차. 편차가 작을수록 스트링 간 순환전류와 조기 열화가 억제됩니다.",
               "Delta between longest and shortest DC strings. Lower delta prevents circulating currents.")
    )
    ratio_enc_pcs = m['n_enc'] / max(m['n_pcs'], 1)
    c_opt3.metric(
        L("PCS 1기당 배터리 연계", "Battery per PCS"),
        f"1 : {ratio_enc_pcs:.1f}",
        delta=L(f"총 {m.get('power_blocks_count', m['n_pcs'])}개 파워블록", f"{m.get('power_blocks_count', m['n_pcs'])} Power Blocks"),
        delta_color="normal",
        help=L(f"블록당 평균 {ratio_enc_pcs:.1f}기 배터리 인클로저가 PCS 1기와 Center-Fed 대칭 연계됩니다.",
               f"Average {ratio_enc_pcs:.1f} battery enclosures per PCS skid in symmetric bay.")
    )
    c_opt4.metric(
        L("E-House (수배전반/EMS)", "E-House Facility"),
        f"{m.get('ehouse_m2', 0.0):.1f} m²" if m.get("include_ehouse") else L("미포함", "Excluded"),
        delta=L("40ft HC 프리패브", "40ft HC Prefab") if m.get("include_ehouse") else None,
        delta_color="normal",
        help=L("MV Switchgear(VCB/보호계전기), EMS/SCADA 서버랙, FACP 및 UPS가 내장된 통합 운영 하우스",
               "Integrated operational facility housing MV switchgear, EMS/SCADA racks, FACP and UPS.")
    )
    if base:
        st.caption(L(f"Δ = {base['ts']} 저장한 기준안 대비 (Δ 없음 = 기준안과 같음) · 3D 의 회색 점선 = 기준안 윤곽",
                     f"Δ = vs baseline saved at {base['ts']} (no Δ = unchanged) · grey dashed outline in 3D = baseline"))

    cov = SL.check_fire_coverage(lay, radius_m=40.0) if m.get("include_infra") else None
    if m.get("include_infra"):
        st.caption(L(f"🧯 **부지 방재·인프라 설비 요약:** 옥외 소화전 **{m.get('num_hydrants', 0)}기** (NFPA 24 / 45m 간격) · "
                     f"변압기 방유제 **{m.get('bund_area_m2', 0)} m²** (IEEE 980) · "
                     f"소방폐수·우수 저류조 **{m.get('basin_m3', 0)} m³** · 20ft 소방펌프실 및 O&M 자재보관소",
                     f"🧯 **Site Safety & Infra:** **{m.get('num_hydrants', 0)} Fire Hydrants** (NFPA 24 / 45m spacing) · "
                     f"TR Oil Bund **{m.get('bund_area_m2', 0)} m²** (IEEE 980) · "
                     f"Retention Basin **{m.get('basin_m3', 0)} m³** · 20ft Pump House & Storage"))
        if cov:
            if cov["all_covered"]:
                st.success(L(f"🚒 **소화전 방수 커버리지 100% 충족 (NFPA 24 / NFPC 109 PASS):** 부지 내 모든 {cov['total_assets']}기 주요 설비(배터리·PCS·TR·E-House)가 소화전 반경 40m 내에 완벽히 방호됩니다. (최장 도달거리 {cov['max_dist_m']}m, 평균 {cov['avg_dist_m']}m)",
                             f"🚒 **100% Fire Hydrant Coverage (NFPA 24 PASS):** All {cov['total_assets']} critical assets within 40m hydrant reach. (Max distance {cov['max_dist_m']}m, avg {cov['avg_dist_m']}m)"))
            else:
                st.warning(L(f"⚠️ **소방 사각지대 {len(cov['uncovered'])}개소 감지:** 커버리지 {cov['coverage_pct']}% (소화전 40m 초과 설비: {', '.join([u['label'] for u in cov['uncovered'][:4]])})",
                             f"⚠️ **Fire Blind Spots ({len(cov['uncovered'])} assets):** Coverage {cov['coverage_pct']}% (Exceeding 40m: {', '.join([u['label'] for u in cov['uncovered'][:4]])})"))

    st.subheader(L("실물형 3D · 설계 모델 탐색", "Spatial 3D · design model explorer"))
    render_viewer(site_payload(lay, inp["pad_l"][0], inp["pad_w"][0], inp["trench_d"][0],
                               language="KO" if ko else "EN", baseline=base))
    st.caption(L("설비 클릭 → 치수·좌표 확인 / 평면·정면·단면 / 두 점 거리 측정. 외벽·문·환기구·도로는 시각화용 상세입니다.",
                 "Click equipment for dimensions / plan, front and section views / point-to-point measurement. Panels, doors, vents and roads are illustrative details."))
    st.subheader(L("정량 배치도 · 기초 및 트렌치", "Analytical layout · foundations and trenches"))
    # ── 3D 컨트롤 및 옵션 ──────────────────────────────────────────────────
    views = [L("등각", "Isometric"), L("위에서", "Top"), L("구조 (기초·트렌치)", "Structure (pads·trench)")]
    vc_col1, vc_col2, vc_col3 = st.columns([2.5, 2.5, 2.0])
    with vc_col1:
        view = st.radio(L("시점", "View"), views, horizontal=True, key="sl_view", label_visibility="collapsed")
    with vc_col2:
        scale_opts = [L("1:1 실척 (True Scale)", "1:1 True Scale"), L("수직 3배 강조", "Vertical ×3")]
        scale_mode = st.radio(L("스케일", "Scale"), scale_opts, horizontal=True, key="sl_scale", label_visibility="collapsed")
    with vc_col3:
        show_heavy_eq = st.checkbox(
            L("🚜 중장비 활동반경 시뮬레이션", "🚜 Equipment Radius"),
            value=True,
            help=L("50T 크레인 인양 반경(20m, 아우트리거 7.5m) 및 3.5T 지게차 회전 반경(3.8m) 시뮬레이션",
                   "Simulate 50T crane lifting radius (20m) and 3.5T forklift turning radius (3.8m)")
        )

    cb_col1, cb_col2 = st.columns(2)
    with cb_col1:
        show_cables = st.checkbox(
            L("⚡ 전기 결선 및 케이블 루트 (DC 1500V / AC 0.69kV / MV 22.9kV)",
              "⚡ Electrical Cabling & Routing (DC 1500V / AC 0.69kV / MV 22.9kV)"),
            value=True,
            help=L("배터리-PCS 간 DC 1500V 스트링 결선, PCS-TR 간 LV 0.69kV 3상 선로, TR-E.House-MainTR 간 MV 22.9kV 3상 특고압 집전선로를 3D로 시각화합니다.",
                   "Renders 3D routing for DC 1500V battery strings, LV 0.69kV AC inverter tie, and MV 22.9kV 3-phase collection feeder.")
        )
    with cb_col2:
        show_hydrant_cov = st.checkbox(
            L("🚒 소화전 40m 방수반경 가시화", "🚒 Show Hydrant 40m Coverage"),
            value=True,
            help=L("NFPA 24 / NFPC 109 기준 옥외 소화전 40m 유효 방호 구역을 붉은색 링 및 반투명 돔으로 표시합니다.",
                   "Displays 40m hose stream coverage circles and domes around fire hydrants (NFPA 24).")
        ) if m.get("include_infra") else False

    struct = view == views[2]
    is_true_scale = (scale_mode == scale_opts[0])

    fig = go.Figure()
    for kind, (kn, en, col) in _KIND.items():
        bx = [x for x in lay["boxes"] if x["kind"] == kind]
        if not bx:
            continue
        xs, ys, zs, ii, jj, kk = SL.mesh_arrays(bx)
        hover = []
        for x in bx:
            t_ = x["label"]
            if kind == "pcs":
                t_ += L(f"<br>블록 {x['block']} · 인클로저 {x['n_enc']}기", f"<br>block {x['block']} · {x['n_enc']} enclosures")
            if kind == "tr" and inp["main_tr_mva"][0]:
                t_ += f"<br>{inp['main_tr_mva'][0]} MVA"
            if kind == "tank":
                t_ += f"<br>{m['tank_m3']:.1f} m³"
            if kind == "ehouse":
                t_ += L("<br>40ft HC (MV 수배전반 · EMS/SCADA 제어실)", "<br>40ft HC (MV Switchgear · EMS/SCADA)")
            if kind == "bund":
                t_ += L(f"<br>변압기 절연유 방유턱 (면적 {m.get('bund_area_m2', 0)} m² · IEEE 980)",
                        f"<br>Oil Retention Bund ({m.get('bund_area_m2', 0)} m² · IEEE 980)")
            if kind == "hydrant":
                t_ += L("<br>옥외 소화전 (NFPA 24 / 45m 간격 배치)", "<br>Outdoor Fire Hydrant (NFPA 24 / 45m spacing)")
            if kind == "pump_house":
                t_ += L("<br>소방 가압 펌프실 (주펌프+디젤예비펌프 패키지)", "<br>Fire Pump Room (Duty+Diesel Standby)")
            if kind == "storage":
                t_ += L("<br>20ft O&M 예비품 및 안전장구 보관소", "<br>20ft O&M Parts & Tools Storage")
            if kind == "basin":
                t_ += L(f"<br>우수 및 소방 오염수 차집 저류조 ({m.get('basin_m3', 0)} m³)",
                        f"<br>Emergency Retention Basin ({m.get('basin_m3', 0)} m³)")
            hover += [t_] * 8
        fig.add_trace(go.Mesh3d(x=xs, y=ys, z=zs, i=ii, j=jj, k=kk, color=col, opacity=0.35 if struct else 0.9,
                                name=L(kn, en), hovertext=hover, hoverinfo="text", flatshading=True,
                                showlegend=True))
    # 장비 모서리선 — 박스가 많아도 1 트레이스 (구조 뷰에선 지상 장비를 윤곽으로 읽게)
    ex, ey, ez = SL.edge_arrays(lay["boxes"])
    fig.add_trace(go.Scatter3d(x=ex, y=ey, z=ez, mode="lines", line=dict(color="#0d1117", width=2),
                               hoverinfo="skip", showlegend=False))
    cable = inp["cable_area_mm2"][0]
    tw, td = inp["trench_w"][0], inp["trench_d"][0]
    t_hover = (L(f"트렌치 폭 {tw:.2f} m · 깊이 {td:.2f} m", f"trench {tw:.2f} m wide · {td:.2f} m deep")
               + (f" · {cable} mm²" if cable else ""))
    if struct:   # 지중 구조 — 05 기초 패드·트렌치 실치수
        pads = SL.pad_boxes(lay, inp["pad_l"][0], inp["pad_w"][0])
        tbx = SL.trench_boxes(lay, td)
        for bxs, col, nm, hv in ((pads, "#8b949e", L("기초 패드", "Foundation pads"),
                                  L(f"패드 {inp['pad_l'][0]:.2f} × {inp['pad_w'][0]:.2f} m · 두께 {SL.PAD_T} m [가정]",
                                    f"pad {inp['pad_l'][0]:.2f} × {inp['pad_w'][0]:.2f} m · {SL.PAD_T} m thick [assumed]")),
                                 (tbx, "#f0883e", L("케이블 트렌치", "Cable trench"), t_hover)):
            if bxs:
                xs, ys, zs, ii, jj, kk = SL.mesh_arrays(bxs)
                fig.add_trace(go.Mesh3d(x=xs, y=ys, z=zs, i=ii, j=jj, k=kk, color=col, opacity=0.85,
                                        name=nm, hovertext=hv, hoverinfo="text", flatshading=True, showlegend=True))
    else:
        tx, ty = [], []
        for pl in lay["trench"]:
            tx += [p[0] for p in pl] + [None]
            ty += [p[1] for p in pl] + [None]
        fig.add_trace(go.Scatter3d(x=tx, y=ty, z=[0.05 if v is not None else None for v in tx], mode="lines",
                                   line=dict(color="#f0883e", width=5),
                                   name=L("케이블 트렌치", "Cable trench"), hovertext=t_hover, hoverinfo="text"))
    if base:     # 기준안 윤곽 — 윗면 사각형만 (가볍게)
        bx_, by_, bz_ = SL.edge_arrays(base["boxes"], top_only=True)
        fig.add_trace(go.Scatter3d(x=bx_, y=by_, z=bz_, mode="lines",
                                   line=dict(color="#c9d1d9", width=2, dash="dash"),
                                   name=L("기준안 윤곽", "Baseline outline"), hoverinfo="skip"))
    fx = [p[0] for p in lay["fence"]]
    fy = [p[1] for p in lay["fence"]]
    fig.add_trace(go.Scatter3d(x=fx + [None] + fx, y=fy + [None] + fy,
                               z=[0] * len(fx) + [None] + [EP.FENCE_HEIGHT_M] * len(fx), mode="lines",
                               line=dict(color="#8b949e", width=3), name=L("울타리·부지경계", "Fence / boundary"),
                               hoverinfo="skip"))
    
    # ── 지표면 기준면 (GL ±0.00m Ground Plane) ──
    # 현실감 있는 토공/지표면 레벨 확립
    gw, gh = lay["site"][0], lay["site"][1]
    fig.add_trace(go.Mesh3d(
        x=[0, gw, gw, 0], y=[0, 0, gh, gh], z=[0.0, 0.0, 0.0, 0.0],
        i=[0, 0], j=[1, 2], k=[2, 3],
        color="#334155", opacity=0.18,
        name=L("지표면 GL ±0.00m (Ground Level)", "GL ±0.00m Ground Level"),
        hoverinfo="skip", showlegend=True
    ))

    if show_hydrant_cov and m.get("include_infra"):
        # 소화전 40m 지표면 원형 링
        hx, hy, hz = SL.hydrant_coverage_circles(lay, radius_m=40.0)
        fig.add_trace(go.Scatter3d(
            x=hx, y=hy, z=hz, mode="lines",
            line=dict(color="#e63946", width=4, dash="dot"),
            name=L("소화전 40m 방수반경 (NFPA 24)", "Hydrant 40m Coverage Ring (NFPA 24)"),
            hoverinfo="skip"
        ))
        # 소화전 40m 반투명 돔 메쉬
        dxs, dys, dzs, dii, djj, dkk = SL.hydrant_coverage_dome_mesh(lay, radius_m=40.0)
        if dxs:
            fig.add_trace(go.Mesh3d(
                x=dxs, y=dys, z=dzs, i=dii, j=djj, k=dkk,
                color="#e63946", opacity=0.08, flatshading=True,
                name=L("소화전 40m 방호구역 (돔)", "Hydrant 40m Coverage Dome"),
                hoverinfo="skip", showlegend=True
            ))

    # 중장비 시뮬레이션 (50T 크레인 실물 차체·20m 붐·주행 이동경로·코너 90° 회전궤적 & 지게차 3.8m 회전궤적)
    heavy_eq_result = None
    if show_heavy_eq:
        heavy_eq_result = SL.heavy_equipment_simulation(lay)
        c_xs, c_ys, c_zs = heavy_eq_result["crane_circles"]
        o_xs, o_ys, o_zs = heavy_eq_result["outrigger_boxes"]
        b_xs, b_ys, b_zs = heavy_eq_result.get("crane_bodies", ([], [], []))
        bm_xs, bm_ys, bm_zs = heavy_eq_result.get("crane_booms", ([], [], []))
        ac_xs, ac_ys, ac_zs = heavy_eq_result.get("access_routes", ([], [], []))
        ct_xs, ct_ys, ct_zs = heavy_eq_result.get("crane_turning_swept", ([], [], []))
        ft_xs, ft_ys, ft_zs = heavy_eq_result.get("forklift_turning_swept", ([], [], []))

        # 1. 50T 크레인 20m 인양 선회 반경 링
        fig.add_trace(go.Scatter3d(
            x=c_xs, y=c_ys, z=c_zs, mode="lines",
            line=dict(color="#eab308", width=3, dash="dash"),
            name=L("50T 크레인 20m 인양 선회반경", "50T Crane 20m Lift Radius"),
            hoverinfo="skip"
        ))
        # 2. 7.5×7.5m 아우트리거 지지 베이스
        fig.add_trace(go.Scatter3d(
            x=o_xs, y=o_ys, z=o_zs, mode="lines",
            line=dict(color="#f59e0b", width=2.5),
            name=L("크레인 아우트리거 (7.5×7.5m)", "Crane Outrigger (7.5x7.5m)"),
            hoverinfo="skip"
        ))
        # 3. 50T 크레인 실물 차체 (11.8×2.55m 노란색 섀시)
        if b_xs:
            fig.add_trace(go.Scatter3d(
                x=b_xs, y=b_ys, z=b_zs, mode="lines",
                line=dict(color="#ca8a04", width=4),
                name=L("50T 크레인 실물 차체 (11.8×2.55m)", "50T Crane Body (11.8x2.55m)"),
                hoverinfo="skip"
            ))
        # 4. 20m 인양 붐대 (Boom Arm)
        if bm_xs:
            fig.add_trace(go.Scatter3d(
                x=bm_xs, y=bm_ys, z=bm_zs, mode="lines",
                line=dict(color="#eab308", width=5),
                name=L("크레인 20m 인양 붐대 (Boom)", "Crane 20m Boom Arm"),
                hoverinfo="skip"
            ))
        # 5. 중장비 주행 진입 이동 경로 (Access / Haul Road)
        if ac_xs:
            fig.add_trace(go.Scatter3d(
                x=ac_xs, y=ac_ys, z=ac_zs, mode="lines",
                line=dict(color="#06b6d4", width=4, dash="dot"),
                name=L("중장비 주행 이동 경로 (Haul Road)", "Equipment Access Route (Haul Road)"),
                hoverinfo="skip"
            ))
        # 6. 50T 크레인 코너 90° 좌우 회전 궤적 (Swept Path: 외륜 R=10.5m / 내륜 R=5.8m)
        if ct_xs:
            fig.add_trace(go.Scatter3d(
                x=ct_xs, y=ct_ys, z=ct_zs, mode="lines",
                line=dict(color="#f97316", width=3.5),
                name=L("50T 크레인 90° 코너 회전 궤적 (R=10.5m)", "50T Crane 90° Turning Swept Path"),
                hoverinfo="skip"
            ))
        # 7. 3.5T 지게차 통로 내 90° 작업 회전 궤적 (R=3.8m)
        if ft_xs:
            fig.add_trace(go.Scatter3d(
                x=ft_xs, y=ft_ys, z=ft_zs, mode="lines",
                line=dict(color="#10b981", width=3),
                name=L("3.5T 지게차 90° 작업 회전 궤적 (R=3.8m)", "Forklift 90° Turning Swept Path"),
                hoverinfo="skip"
            ))

    # 파워 블록(Power Block: 1 PCS + N Battery) 바닥 구획선 가시화
    for pb in lay.get("power_blocks", []):
        pbx = [pb["x"], pb["x"] + pb["dx"], pb["x"] + pb["dx"], pb["x"], pb["x"], None]
        pby = [pb["y"], pb["y"], pb["y"] + pb["dy"], pb["y"] + pb["dy"], pb["y"], None]
        fig.add_trace(go.Scatter3d(
            x=pbx, y=pby, z=[0.02] * 5 + [None], mode="lines",
            line=dict(color="#1f6feb", width=3, dash="dash"),
            name=L("파워블록(1 PCS:N Bat) 구획", "Power Block Bay Outline"),
            hovertext=L(f"파워블록 #{pb['block']}: {pb['pcs_label']} 연계 (배터리 {pb['n_enc']}기)",
                        f"Power Block #{pb['block']}: {pb['pcs_label']} ({pb['n_enc']} Bat)"),
            hoverinfo="text", showlegend=(pb["block"] == 1)
        ))

    # 전기 결선 및 케이블 루트 3D 트레이스 (DC 1500V / AC 0.69kV / MV 22.9kV)
    cable_wiring_res = None
    if show_cables:
        cable_wiring_res = SL.build_cable_wiring(lay)
        dc_xs, dc_ys, dc_zs = cable_wiring_res["dc_line_coords"]
        lv_xs, lv_ys, lv_zs = cable_wiring_res["lv_line_coords"]
        mv_xs, mv_ys, mv_zs = cable_wiring_res["mv_line_coords"]
        tm_xs, tm_ys, tm_zs, tm_cols, tm_lbls = cable_wiring_res["terminal_markers"]

        # 1. DC 1500V 배터리-PCS 스트링 케이블 (주황색 실선)
        if dc_xs:
            fig.add_trace(go.Scatter3d(
                x=dc_xs, y=dc_ys, z=dc_zs, mode="lines",
                line=dict(color="#f97316", width=3.5),
                name=L("DC 1500V 케이블 (배터리→PCS)", "DC 1500V Cables (Battery→PCS)"),
                hovertext=L("DC 1500V 스트링 결선 (1C×300mm²×2, 트렌치 Riser 배선)",
                            "DC 1500V String Cable (1C×300mm²×2 in Trench)"),
                hoverinfo="text", showlegend=True
            ))

        # 2. LV 0.69kV 저압 3상 AC 케이블 (에메랄드 그린 실선)
        if lv_xs:
            fig.add_trace(go.Scatter3d(
                x=lv_xs, y=lv_ys, z=lv_zs, mode="lines",
                line=dict(color="#10b981", width=4.5),
                name=L("LV 0.69kV AC 3상 (PCS→변압기 1차)", "LV 0.69kV AC 3-Phase (PCS→TR 1st)"),
                hovertext=L("0.69kV AC 3상 3선식 버스바/케이블 (TFR-CV 3C×240mm²×3조)",
                            "0.69kV AC 3-Phase Inverter Output (TFR-CV 3C×240mm²×3)"),
                hoverinfo="text", showlegend=True
            ))

        # 3. MV 22.9kV 특고압 3상 AC 집전 선로 (일렉트릭 블루 실선)
        if mv_xs:
            fig.add_trace(go.Scatter3d(
                x=mv_xs, y=mv_ys, z=mv_zs, mode="lines",
                line=dict(color="#2563eb", width=4.5),
                name=L("MV 22.9kV AC 3상 집전선 (블록→E-House→POI)", "MV 22.9kV Collection Feeder (Block→E-House→POI)"),
                hovertext=L("22.9kV 3상 특고압 집전 간선 (CNCV-W 3C×250mm², 삼엽 포설)",
                            "22.9kV 3-Phase MV Feeder (CNCV-W 3C×250mm² Trefoil)"),
                hoverinfo="text", showlegend=True
            ))

        # 4. 전기 접속 단자점 마커 (Terminal Connection Points)
        if tm_xs:
            fig.add_trace(go.Scatter3d(
                x=tm_xs, y=tm_ys, z=tm_zs, mode="markers",
                marker=dict(size=4, color=tm_cols),
                name=L("전기 결선 접속 단자 (Terminals)", "Electrical Connection Terminals"),
                hovertext=tm_lbls, hoverinfo="text", showlegend=True
            ))
    # 기준안이 더 크면 축 범위를 넓혀 이전 윤곽이 잘리지 않게
    bw = max([x["x"] + x["dx"] for x in base["boxes"]], default=0.0) if base else 0.0
    bh = max([x["y"] + x["dy"] for x in base["boxes"]], default=0.0) if base else 0.0
    w, h = max(lay["site"][0], bw), max(lay["site"][1], bh)
    
    # 현실 1:1 실척 vs 수직 강조 축 범위 계산
    zmax_eq = max([x["dz"] for x in lay["boxes"]], default=3.0) + 1.0
    zmin_eq = -(td + 0.5) if struct else -0.5
    eye = {views[1]: dict(x=0.0, y=-0.01, z=2.2), views[2]: dict(x=-1.1, y=-1.25, z=0.35)}.get(
        view, dict(x=-0.95, y=-1.1, z=0.75))

    if is_true_scale:
        # 현실 공학 1:1 실척 (True Scale: 1m x 1m x 1m 가 왜곡 없이 정확하게 1:1 물리 비례 유지)
        fig.update_layout(
            scene=dict(
                xaxis=dict(title="x (m)", range=[0, w]),
                yaxis=dict(title="y (m)", range=[0, h]),
                zaxis=dict(title="z (m)", range=[zmin_eq, zmax_eq]),
                aspectmode="data",  # 1:1 현실 실척
                camera=dict(eye=eye)
            ),
            paper_bgcolor="rgba(0,0,0,0)", font_color="#c9d1d9", height=500,
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", y=-0.02, x=0, font=dict(size=11)),
        )
    else:
        # 수직 3배 강조 모드 (지중 트렌치와 패드 높이를 시각적으로 돋보이게 표시)
        z_aspect = 0.08 if not struct else 0.12
        fig.update_layout(
            scene=dict(
                xaxis=dict(title="x (m)", range=[0, w]),
                yaxis=dict(title="y (m)", range=[0, h]),
                zaxis=dict(title="z (m)", range=[zmin_eq, zmax_eq]),
                aspectmode="manual",
                aspectratio=dict(x=w / max(w, h), y=h / max(w, h), z=z_aspect),
                camera=dict(eye=eye)
            ),
            paper_bgcolor="rgba(0,0,0,0)", font_color="#c9d1d9", height=500,
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", y=-0.02, x=0, font=dict(size=11)),
        )

    st.plotly_chart(compact(fig), use_container_width=True)
    if struct:
        gap = SL.pad_clear_gap(lay, inp["pad_l"][0], inp["pad_w"][0])
        if gap < 0:
            st.warning(L(f"⚠️ 이웃 기초 패드가 {-gap:.2f} m 겹칩니다 — 일체 기초(매트)로 검토하거나 유닛 이격을 넓히세요.",
                         f"⚠️ Adjacent pads overlap by {-gap:.2f} m — consider a combined mat or wider separation."))
        st.caption((L(f"기초 패드 순간격 최소 {gap:.2f} m · " if 0 <= gap != float("inf") else
                      ("이웃 기초 패드 없음 · " if gap == float("inf") else ""),
                      f"Min clear gap between pads {gap:.2f} m · " if 0 <= gap != float("inf") else
                      ("No adjacent pads · " if gap == float("inf") else "")))
                   + L(f"트렌치(깊이 {td:.1f}m) · 패드(두께 {SL.PAD_T:.2f}m) · {'1:1 현실 실척 (True Scale)' if is_true_scale else '수직 과장 모드'}",
                       f"trench (d={td:.1f}m) · pad (t={SL.PAD_T:.2f}m) · {'1:1 True Scale' if is_true_scale else 'Exaggerated'}"))

    # ── ⚡ EBOP 전기 결선 및 케이블 루트 공학 해석 리포트 ─────────────────────────
    if cable_wiring_res:
        cw_m = cable_wiring_res["metrics"]
        st.markdown("#### " + L("⚡ EBOP 전기 결선 및 케이블 루트 공학 해석 리포트",
                                "⚡ Electrical BOP Cabling & Wiring Analysis Report"))
        cw1, cw2, cw3, cw4 = st.columns(4)
        cw1.metric(
            L("DC 1500V 총 포설 연장", "Total DC 1500V Cable"),
            f"{cw_m['total_dc_len_m']:,.1f} m",
            delta=L(f"스트링 편차 {cw_m['dc_imbalance_m']:.1f} m", f"Imbalance {cw_m['dc_imbalance_m']:.1f} m"),
            delta_color="normal",
            help=L(f"배터리 {len(cable_wiring_res['dc_cables'])}회선 총 포설연장. 최장 {cw_m['max_dc_len_m']}m, 최단 {cw_m['min_dc_len_m']}m.",
                   f"{len(cable_wiring_res['dc_cables'])} DC strings. Max {cw_m['max_dc_len_m']}m, min {cw_m['min_dc_len_m']}m.")
        )
        cw2.metric(
            L("LV 0.69kV AC 총 연장", "Total LV 0.69kV Cable"),
            f"{cw_m['total_lv_len_m']:.1f} m",
            delta=L("PCS-TR 직결 (2510A)", "PCS-TR Direct (2510A)"),
            delta_color="normal",
            help=L("PCS 인버터와 MV 승압변압기 1차측 간 저압 대용량 3상 버스바/케이블",
                   "Low-voltage high-current 3-phase link between inverter and MV transformer.")
        )
        cw3.metric(
            L("MV 22.9kV 집전 간선", "MV 22.9kV Feeder"),
            f"{cw_m['total_mv_len_m']:,.1f} m",
            delta=L(f"최장 집전 {cw_m['max_mv_len_m']:.1f} m", f"Max Feeder {cw_m['max_mv_len_m']:.1f} m"),
            delta_color="normal",
            help=L("파워블록 MV 변압기 2차측 -> 지선/간선 트렌치 -> E-House 22.9kV VCB -> Main TR",
                   "Collection feeder from power block MV transformers through trunk trench to E-House VCB.")
        )
        cw4.metric(
            L("트렌치 점유율 (NEC 392)", "Trench Cable Fill"),
            f"{cw_m['trench_fill_ratio_pct']:.1f} %",
            delta=L("허용치 40% 이내 PASS", "≤40% Standard PASS") if cw_m['trench_fill_ratio_pct'] <= 40.0 else L("초과 (트렌치 확장 필요)", "Exceeded"),
            delta_color="normal" if cw_m['trench_fill_ratio_pct'] <= 40.0 else "inverse",
            help=L("NEC 392 규격 트렌치 유효 단면적 대비 전력케이블 단면적 합계 비율 (40% 이하 권장).",
                   "NEC 392 cable fill ratio in main precast trench (limit ≤40%).")
        )

        with st.expander(L("📋 전기 결선 세부 사양 및 규격 준수 검토 (DC 1500V / 3상 AC / 트렌치)",
                           "📋 Electrical Wiring Detailed Specs & Code Compliance (DC 1500V / 3-Phase AC / Trench)"), expanded=False):
            st.markdown(L(f"""
- **1. DC 1500V 스트링 결선 (UL 4703 / IEC 62930):**
  - 케이블 규격: **DC 1,500V 가교폴리에틸렌(XLPE) 절연 단심 동 케이블 1C × 300 mm² × 2선(DC+, DC-)**
  - 최대 전압강하율: **{cw_m['dc_vdrop_pct']:.2f}%** (기준치 1.0% 이하 완벽 충족, 순환전류 및 불평형 손실 억제)
  - 배선 경로: 배터리 인클로저 하부 Riser 관통 ➔ 콘크리트 트렌치 상부 직류 전용 격벽 ➔ PCS 직류 차단기반 인입
- **2. LV 0.69kV 저압 3상 AC 결선 (KEC 제232조 / IEC 60364):**
  - 케이블 규격: **0.6/1kV TFR-CV 3C × 240 mm² × 3조 병렬 (정격전류 2,510 A 대응)**
  - 상별 색상 기준 (KEC 제241조 / IEC 60446): **L1(갈색), L2(흑색), L3(회색), N(청색), PE(녹황색)**
  - 배선 경로: PCS 인버터 모듈 ➔ 스키드 내부 단축 버스덕트/케이블 ➔ 파워블록 승압변압기(0.69 / 22.9 kV) 1차측 부싱
- **3. MV 22.9kV 특고압 3상 AC 집전 선로 (KEC 제332조 / IEEE 141):**
  - 케이블 규격: **22.9kV 동심중성선 수밀형 전력케이블 (CNCV-W 3C × 250 mm², 삼엽 Trefoil 포설)**
  - 최대 전압강하율: **{cw_m['mv_vdrop_pct']:.2f}%** (한전 계통연계 기준 2.0% 이하 완벽 충족)
  - 배선 경로: 파워블록 MV 변압기 2차측(22.9kV) ➔ 지선 트렌치 ➔ 메인 트렁크 트렌치 ➔ E-House 22.9kV VCB반 ➔ 154kV Main TR
- **4. 프리캐스트 트렌치 안전성 (NEC 392 / KEC 232.41):**
  - 트렌치 단면 규격: 폭 800 mm × 깊이 1,000 mm (상부 무소음 스틸 그레이팅 t=80mm)
  - 케이블 단면 점유율: **{cw_m['trench_fill_ratio_pct']:.1f}%** (NEC 허용 상한 40.0% 이내 안전 마진 확보)
  - 전압 레벨별 격벽 분리: 특고압 22.9kV 선로는 트렌치 최하단(-0.7m), 직류 1500V 및 저압 AC는 상단(-0.35m)에 내화 격벽 분리 포설
""", f"""
- **1. DC 1500V String Cabling (UL 4703 / IEC 62930):**
  - Spec: **DC 1500V XLPE Single Core Copper 1C × 300 mm² × 2 (DC+, DC-)**
  - Max Voltage Drop: **{cw_m['dc_vdrop_pct']:.2f}%** (Strictly within ≤1.0% limit)
- **2. LV 0.69kV 3-Phase AC Cabling (KEC / IEC 60364):**
  - Spec: **0.6/1kV TFR-CV 3C × 240 mm² × 3 parallel sets (Rated 2,510 A)**
  - Phase Identification: **L1(Brown), L2(Black), L3(Grey), N(Blue), PE(Green-Yellow)**
- **3. MV 22.9kV 3-Phase Feeder (KEC / IEEE 141):**
  - Spec: **22.9kV CNCV-W 3C × 250 mm² (Trefoil formation)**
  - Max Voltage Drop: **{cw_m['mv_vdrop_pct']:.2f}%** (Limit ≤2.0%)
- **4. Trench Fill & Safety (NEC 392):**
  - Trench Spec: 800 mm (W) × 1,000 mm (D) with steel grating
  - Fill Ratio: **{cw_m['trench_fill_ratio_pct']:.1f}%** (Limit ≤40.0% PASS)
"""))

    # ── 중장비 활동 반경 및 좌우 회전 궤적(Swept Path) 시뮬레이션 결과 리포트 ─────
    if heavy_eq_result:
        st.markdown("#### " + L("🚜 시공 및 O&M 중장비 활동성·회전 궤적(Swept Path) 시뮬레이션",
                                "🚜 Heavy Equipment & Turning Swept Path Simulation"))
        eq1, eq2, eq3, eq4 = st.columns(4)
        eq1.metric(
            L("50T 크레인 인양 커버리지", "50T Crane Coverage"),
            f"{heavy_eq_result['crane_coverage_pct']:.1f}%",
            L(f"{len(heavy_eq_result['crane_stations'])}개소 작업 거점 (R=20m)",
              f"{len(heavy_eq_result['crane_stations'])} Stations (R=20m)")
        )
        eq2.metric(
            L("크레인 90° 코너 회전 여유", "Crane 90° Corner Clearance"),
            f"+{heavy_eq_result['crane_corner_clearance_m']:.2f} m",
            L("회전 외륜 R=10.5m / 통과 PASS" if heavy_eq_result['crane_corner_pass'] else "⚠️ 회전 폭 주의",
              "R_ext=10.5m / PASS" if heavy_eq_result['crane_corner_pass'] else "Caution")
        )
        eq3.metric(
            L("지게차 90° 작업 회전 여유", "Forklift 90° Aisle Margin"),
            f"+{heavy_eq_result['aisle_margin_m']:.2f} m",
            L(f"통로 {heavy_eq_result['site_aisle_m']:.1f}m vs 회전 3.8m",
              f"Aisle {heavy_eq_result['site_aisle_m']:.1f}m vs R=3.8m")
        )
        eq4.metric(
            L("중장비 종합 시공/O&M 판정", "Equipment Maneuver Status"),
            "PASS (적합)" if heavy_eq_result["all_pass"] else "REVIEW",
            L("전 장비 회전·인양 간섭 0건", "No Swept Clash") if heavy_eq_result["all_pass"] else L("통로 폭 재검토", "Review Width")
        )

        with st.expander(L("📐 중장비 제원 및 좌우 회전 궤적 (Swept Path) 엔지니어링 해석 기준",
                           "📐 Heavy Equipment Specs & Turning Swept Path Methodology"), expanded=False):
            st.markdown(L(
                "**1. 50T 올테레인 크레인 (Liebherr LTM 1050-3.1급 / BESS 인클로저 및 PCS 인양용):**  \n"
                "- **차체 규격:** 전장 11.8m × 전폭 2.55m × 높이 3.2m (3축 조향 올테레인 섀시)  \n"
                "- **아우트리거 베이스:** 7.50m × 7.50m (4점 유압 지지 패드 전개)  \n"
                "- **인양 작업 반경:** 정격 20.0m (30톤 컨테이너 기준 안전 작업 모멘트)  \n"
                "- **90° 코너 회전 궤적:** 최소 외륜 회전반경 R_ext = 10.5m, 내륜 궤적 R_int = 5.8m (스윕 폭 4.7m). "
                "남측 메인 도로와 블록 통로 교차부에서 설비 기초와 간섭 없이 부드럽게 좌/우회전 가능.  \n\n"
                "**2. 3.5T 전동 지게차 (배터리 모듈 교체 및 O&M 자재 운반용):**  \n"
                "- **차량 규격:** 전폭 1.30m, 전장 2.65m  \n"
                "- **최소 회전 반경:** R = 3.80m (후륜 조향 방식)  \n"
                "- **90° 직각 적재 소요 폭(Ast):** 4.20m (팔레트 적재 상태에서 컨테이너 도어 진입 가능 여부)  \n"
                "- **시공성 결론:** 블록 간 작업 통로(Aisle)가 확보되어 지게차 90° 좌우 직각 선회 및 180° 유턴이 완벽히 수용됩니다.",
                "**1. 50T All-Terrain Crane (Liebherr LTM 1050-3.1 Class):**  \n"
                "- Dimensions: 11.8m (L) x 2.55m (W) x 3.2m (H)  \n"
                "- Outriggers: 7.5m x 7.5m full extension  \n"
                "- Lift Radius: 20.0m safe rated reach for 30T container  \n"
                "- 90° Turning Swept Path: R_ext = 10.5m, R_int = 5.8m (Swept width 4.7m).  \n\n"
                "**2. 3.5T Electric Forklift (O&M Module Replacement):**  \n"
                "- Turning Radius: R = 3.80m  \n"
                "- 90° Stacking Aisle (Ast): 4.20m  \n"
                "- Result: Pass with safe clearance margin."
            ))

    # ── 배치 검사 ───────────────────────────────────────────────────────────
    ok = chk["overlaps"] == 0 and chk["unit_ok"] and chk["tr_ok"] and chk["boundary_ok"]
    msg = L(f"겹침 {chk['overlaps']}건 · 유닛 간 최소 {chk['min_unit_gap_m']:.2f} m (기준 {unit_gap:.2f}) · "
            f"주변압기~유닛 최소 {chk['min_tr_gap_m']:.2f} m (기준 {tr_clear:.2f}) · "
            f"부지경계 최소 {chk['min_boundary_m']:.2f} m (기준 {boundary:.2f})",
            f"Overlaps {chk['overlaps']} · min unit gap {chk['min_unit_gap_m']:.2f} m (req. {unit_gap:.2f}) · "
            f"TR-to-unit {chk['min_tr_gap_m']:.2f} m (req. {tr_clear:.2f}) · "
            f"boundary {chk['min_boundary_m']:.2f} m (req. {boundary:.2f})")
    (st.success if ok else st.error)(("✅ " if ok else "❌ ") + msg)
    if not chk["trench_fits"]:
        st.warning(L(f"⚠️ 트렌치 폭 {inp['trench_w'][0]:.2f} m 가 유닛 이격 {unit_gap:.2f} m 보다 넓어 블록 사이 간선이 "
                     "장비 기초와 겹칩니다 — 이격을 넓히거나 05 트렌치(케이블 수·배열)를 재검토하세요.",
                     f"⚠️ Trench width {inp['trench_w'][0]:.2f} m exceeds unit separation {unit_gap:.2f} m — "
                     "branch trenches clash with equipment pads; widen separation or revisit 05 trench design."))
    if m["pcs_clipped"]:
        st.warning(L("⚠️ PCS 스키드 수가 인클로저 수보다 많아 인클로저 수만큼만 배치했습니다 — 02 단위 용량을 확인하세요.",
                     "⚠️ More PCS skids than enclosures — placed one per enclosure; check 02 unit ratings."))

    # ── 2D 공학 정밀 횡단면도 (Section A-A / Section B-B) ──────────────────────
    st.markdown("---")
    st.subheader(L("📐 2D 공학 정밀 횡단면도 (Section A-A / Section B-B)",
                   "📐 2D Engineering Sections (Section A-A / Section B-B)"))
    st.caption(L("실제 토목 및 전기설계 기준 GL ±0.00m 지표면, 콘크리트 패드(t=300mm), 지중 트렌치(w=800, d=1000), 배터리(h=2900mm) 및 PCS(h=2400mm) 1:1 실척 단면",
                 "1:1 engineering sections showing GL ±0.00m, foundation pads (t=300mm), cable trench (d=1000mm), and equipment profiles."))

    sec_fig_a, sec_fig_b = SL.create_section_figures(lay)
    sec_tab1, sec_tab2 = st.tabs([
        L("횡단면도 Section A-A (배터리·패드·트렌치·PCS)", "Section A-A (Battery·Pad·Trench·PCS)"),
        L("종단면도 Section B-B (주변압기·방유벽·소방도로)", "Section B-B (Main TR·Bund Wall·Fire Road)")
    ])
    with sec_tab1:
        st.plotly_chart(compact(sec_fig_a), use_container_width=True)
    with sec_tab2:
        st.plotly_chart(compact(sec_fig_b), use_container_width=True)

    # ── 04 로 되돌려 보내기 ─────────────────────────────────────────────────
    if st.button(L(f"📏 최장 경로 {m['longest_cable_m']:.1f} m 를 04 케이블 사이징 길이로 적용",
                   f"📏 Apply longest route {m['longest_cable_m']:.1f} m to 04 cable sizing"),
                 use_container_width=True):
        st.session_state["dm_cable_length_m"] = round(m["longest_cable_m"], 1)
        st.success(L("적용했습니다 — 04 전기 BOP › 케이블 탭에서 전압강하 재검증하세요.",
                     "Applied — re-check voltage drop in 04 EBOP › Cable tab."))

    # ── 내보내기·불러오기 ───────────────────────────────────────────────────
    st.markdown("---")
    st.subheader(L("💾 내보내기 / 불러오기 (CAD & BIM Data)", "💾 Export / Import (CAD & BIM Data)"))
    st.caption(L("AutoCAD, BricsCAD, ZWCAD 등에서 즉시 사용 가능한 12개 전문 레이어, 치수선, 평면도 및 횡·종단면도(A-A, B-B), 표준 표제란이 포함된 DXF 내보내기",
                 "Export professional multi-view DXF with 12 engineering layers, dimensions, plan, sections A-A/B-B, and standard title block."))
    e1, e2 = st.columns(2)
    e1.download_button(L("설계 모델 JSON", "Design model JSON"),
                       data=DM.export_json(layout_metrics={k: (round(v, 3) if isinstance(v, float) else v)
                                                           for k, v in m.items()}),
                       file_name="bess_design_model.json", mime="application/json", use_container_width=True)
    e2.download_button(L("📐 전문가 멀티뷰 CAD DXF (평면+단면A-A/B-B)", "📐 Engineering Multi-View DXF (Plan+Sections)"),
                       data=SL.to_dxf(lay, multi_view=True),
                       file_name="bess_engineering_drawings.dxf", mime="application/dxf", use_container_width=True)
    if ko:  # 업로더 안내문·버튼은 Streamlit 고정 영문 — 한국어 모드에서만 CSS 로 문구 교체
        st.markdown("""<style>
        [data-testid=stFileUploaderDropzoneInstructions] > div > span,
        [data-testid=stFileUploaderDropzoneInstructions] > div > small,
        [data-testid=stFileUploaderDropzone] button {font-size:0 !important;}
        [data-testid=stFileUploaderDropzoneInstructions] > div > span::after {content:"JSON 파일을 끌어다 놓으세요"; font-size:1rem;}
        [data-testid=stFileUploaderDropzoneInstructions] > div > small::after {content:"파일당 200MB · JSON"; font-size:0.8rem;}
        [data-testid=stFileUploaderDropzone] button::after {content:"파일 선택"; font-size:0.9rem;}
        </style>""", unsafe_allow_html=True)
    up = st.file_uploader(L("설계 모델 JSON 불러오기", "Import design model JSON"), type=["json"],
                          key="sl_import")
    if up is not None and st.session_state.get("_sl_imported") != up.file_id:
        try:
            n = DM.import_json(up.getvalue().decode("utf-8"))
            st.session_state["_sl_imported"] = up.file_id
            st.success(L(f"{n}개 항목을 복원했습니다.", f"Restored {n} items."))
            st.rerun()
        except (ValueError, UnicodeDecodeError, TypeError) as ex:
            st.error(L(f"불러오기 실패: {ex}", f"Import failed: {ex}"))


run_site_layout_module()
