# -*- coding: utf-8 -*-
import streamlit as st
try:
    st.set_page_config(page_title="BESS EPC Platform", layout="wide", initial_sidebar_state="expanded")
except Exception:
    pass

import os
from pathlib import Path
from utils.css_loader import apply_custom_css
from utils.lang_helper import t
from utils.auth_helper import require_auth, sidebar_user_info
from utils.config import IS_API_MODE

EXEC_DIR = Path(r"c:\Users\openm\00_AI개발\01_BESS사업\output\10_tools\executables")

# GitHub Release URL for cloud mode
GH_RELEASE_TAG = "tools-v1.0"
GH_REPO = "openmen-gif/bess-epc-engineering"
GH_RELEASE_URL = f"https://github.com/{GH_REPO}/releases/tag/{GH_RELEASE_TAG}"
GH_DOWNLOAD_BASE = f"https://github.com/{GH_REPO}/releases/download/{GH_RELEASE_TAG}"

# ── Bilingual tool metadata ────────────────────────────────────────────────
# key = exact executable name stem matching GitHub Release asset filename
TOOL_META: dict[str, dict] = {
    # ─ Engineering Calculators ─
    "BESS_ThermalCalc_v1.0": {
        "category_en": "Engineering Calc", "category_ko": "엔지니어링 계산",
        "desc_en": "BESS thermal management & cooling load calculation tool.",
        "desc_ko": "BESS 열관리 및 냉방 부하 계산 도구.", "icon": "🌡️",
    },
    "BESS_CableSizing_v1.0": {
        "category_en": "Engineering Calc", "category_ko": "엔지니어링 계산",
        "desc_en": "MV/LV cable cross-section sizing (thermal + voltage drop).",
        "desc_ko": "MV/LV 케이블 단면 산정 (열용량 + 전압강하).", "icon": "🔌",
    },
    "BESS_VoltageDrop_v1.0": {
        "category_en": "Engineering Calc", "category_ko": "엔지니어링 계산",
        "desc_en": "Voltage drop calculation across battery & PCS circuits.",
        "desc_ko": "배터리·PCS 회로 전압강하 계산.", "icon": "⚡",
    },
    "BESS_Grounding_v1.0": {
        "category_en": "Engineering Calc", "category_ko": "엔지니어링 계산",
        "desc_en": "Substation grounding grid design per IEEE 80.",
        "desc_ko": "IEEE 80 기준 변전소 접지 그리드 설계.", "icon": "🌍",
    },
    "BESS_HarmonicFilter_v1.0": {
        "category_en": "Engineering Calc", "category_ko": "엔지니어링 계산",
        "desc_en": "Harmonic filter design and THD analysis for BESS inverters.",
        "desc_ko": "BESS 인버터 고조파 필터 설계 및 THD 분석.", "icon": "📊",
    },
    "BESS_LDCalc_v1.0": {
        "category_en": "Engineering Calc", "category_ko": "엔지니어링 계산",
        "desc_en": "Liquidated Damages (LD) exposure calculation tool.",
        "desc_ko": "지체상금(LD) 노출 위험 계산 도구.", "icon": "⚖️",
    },
    "BESS_Foundation_v1.0": {
        "category_en": "Engineering Calc", "category_ko": "엔지니어링 계산",
        "desc_en": "Equipment pad foundation sizing per ASCE 7 / KDS 41.",
        "desc_ko": "ASCE 7 / KDS 41 기준 장비 기초 패드 설계.", "icon": "🏗️",
    },
    "BESS_StructuralCalc_v1.0": {
        "category_en": "Engineering Calc", "category_ko": "엔지니어링 계산",
        "desc_en": "Structural load combination and DCR calculation for BESS frames.",
        "desc_ko": "BESS 구조물 하중 조합 및 DCR 계산.", "icon": "🔩",
    },
    "BESS_EMCAnalysis_v1.0": {
        "category_en": "Engineering Calc", "category_ko": "엔지니어링 계산",
        "desc_en": "Electromagnetic compatibility analysis for BESS systems.",
        "desc_ko": "BESS 시스템 전자기 적합성(EMC) 분석.", "icon": "📡",
    },
    "BESS_HVAC_v1.0": {
        "category_en": "Engineering Calc", "category_ko": "엔지니어링 계산",
        "desc_en": "HVAC load calculation for battery rooms and MV rooms.",
        "desc_ko": "배터리실·PCS실 HVAC 부하 계산.", "icon": "❄️",
    },
    "BESS_FinancialCalc_v1.0": {
        "category_en": "Engineering Calc", "category_ko": "엔지니어링 계산",
        "desc_en": "BESS project financial analysis (IRR, NPV, LCOE).",
        "desc_ko": "BESS 프로젝트 재무분석 (IRR, NPV, LCOE).", "icon": "💰",
    },
    "BESS_FireProtection_v1.0": {
        "category_en": "Engineering Calc", "category_ko": "엔지니어링 계산",
        "desc_en": "Fire protection system design and NFPA 855 compliance check.",
        "desc_ko": "소방설비 설계 및 NFPA 855 적합성 확인.", "icon": "🧯",
    },
    "BESS_ProtectionCoord_v1.0": {
        "category_en": "Engineering Calc", "category_ko": "엔지니어링 계산",
        "desc_en": "Protection relay coordination and time-current curve analysis.",
        "desc_ko": "보호 계전기 협조 및 시간-전류 곡선 분석.", "icon": "🛡️",
    },

    # ─ Simulation & Analysis ─
    "BESS_Simulator_v1.0": {
        "category_en": "Simulation", "category_ko": "시뮬레이션",
        "desc_en": "Full BESS cycle simulation engine (charge/discharge/degradation).",
        "desc_ko": "BESS 전체 충방전 사이클 시뮬레이션 엔진.", "icon": "🔬",
    },
    "BESS_BatteryAnalysis_v1.0": {
        "category_en": "Simulation", "category_ko": "시뮬레이션",
        "desc_en": "Battery cell-to-system performance analysis and EFC tracking.",
        "desc_ko": "배터리 셀~시스템 성능 분석 및 EFC 추적.", "icon": "🔋",
    },
    "BESS_VRTSim_v1.0": {
        "category_en": "Simulation", "category_ko": "시뮬레이션",
        "desc_en": "Voltage Ride-Through (VRT) simulation and grid code compliance.",
        "desc_ko": "전압 Ride-Through(VRT) 시뮬레이션 및 계통 적합성 확인.", "icon": "📈",
    },
    "BESS_PCSDesign_v1.0": {
        "category_en": "Simulation", "category_ko": "시뮬레이션",
        "desc_en": "PCS design parameter calculation and control mode verification.",
        "desc_ko": "PCS 설계 파라미터 계산 및 제어 모드 검증.", "icon": "⚙️",
    },
    "BESS_GridTest_v1.0": {
        "category_en": "Simulation", "category_ko": "시뮬레이션",
        "desc_en": "Grid interconnection test procedure generator and result checker.",
        "desc_ko": "계통 연계 시험 절차 생성 및 결과 확인.", "icon": "🔗",
    },
    "BESS_CrossValidator_v1.0": {
        "category_en": "Simulation", "category_ko": "시뮬레이션",
        "desc_en": "Cross-validation tool for design parameters across disciplines.",
        "desc_ko": "분야 간 설계 파라미터 교차 검증 도구.", "icon": "✅",
    },
    "BESS_ModbusSim_v1.0": {
        "category_en": "Simulation", "category_ko": "시뮬레이션",
        "desc_en": "Modbus/TCP PCS communication simulation and testing.",
        "desc_ko": "Modbus/TCP PCS 통신 시뮬레이션 및 테스트.", "icon": "📶",
    },

    # ─ Project Management ─
    "BESS_EVM_v1.0": {
        "category_en": "Project Mgmt", "category_ko": "프로젝트 관리",
        "desc_en": "Earned Value Management (EVM) calculation and reporting.",
        "desc_ko": "획득가치관리(EVM) 계산 및 보고.", "icon": "📐",
    },
    "BESS_GanttGen_v1.0": {
        "category_en": "Project Mgmt", "category_ko": "프로젝트 관리",
        "desc_en": "Gantt chart generator for BESS EPC project schedules.",
        "desc_ko": "BESS EPC 프로젝트 일정 Gantt 차트 생성.", "icon": "📅",
    },
    "BESS_RiskRegister_v1.0": {
        "category_en": "Project Mgmt", "category_ko": "프로젝트 관리",
        "desc_en": "Risk register management with probability-impact matrix.",
        "desc_ko": "확률-영향 매트릭스 기반 리스크 등록부 관리.", "icon": "⚠️",
    },
    "BESS_ClaimTracker_v1.0": {
        "category_en": "Project Mgmt", "category_ko": "프로젝트 관리",
        "desc_en": "Claim tracking and dispute management tool.",
        "desc_ko": "클레임 추적 및 분쟁 관리 도구.", "icon": "📋",
    },
    "BESS_MarketScheduler_v2.0": {
        "category_en": "Project Mgmt", "category_ko": "프로젝트 관리",
        "desc_en": "Market-based project scheduling and resource allocation.",
        "desc_ko": "시장 기반 프로젝트 일정 및 자원 배분.", "icon": "🗓️",
    },

    # ─ O&M / Reporting ─
    "BESS_MaintenancePlanner_v1.0": {
        "category_en": "O&M / Reporting", "category_ko": "O&M / 보고서",
        "desc_en": "Preventive maintenance schedule planner for BESS systems.",
        "desc_ko": "BESS 설비 예방정비 일정 계획 도구.", "icon": "🔧",
    },
    "BESS_QCTracker_v1.0": {
        "category_en": "O&M / Reporting", "category_ko": "O&M / 보고서",
        "desc_en": "Quality control inspection tracker and NCR management.",
        "desc_ko": "품질 검사 추적 및 부적합 보고서(NCR) 관리.", "icon": "🔍",
    },
    "BESS_MarketDashboard_v1.0": {
        "category_en": "O&M / Reporting", "category_ko": "O&M / 보고서",
        "desc_en": "BESS market intelligence dashboard and report export.",
        "desc_ko": "BESS 시장 인텔리전스 대시보드 및 보고서 내보내기.", "icon": "📊",
    },
    "BESS_Dashboard_v1.0": {
        "category_en": "O&M / Reporting", "category_ko": "O&M / 보고서",
        "desc_en": "BESS operational dashboard (standalone desktop version).",
        "desc_ko": "BESS 운영 대시보드 (독립 데스크톱 버전).", "icon": "🖥️",
    },
    "BESS_Daily_Brief_Generator": {
        "category_en": "O&M / Reporting", "category_ko": "O&M / 보고서",
        "desc_en": "Automated daily briefing report generator.",
        "desc_ko": "일일 브리핑 보고서 자동 생성기.", "icon": "📰",
    },

    # ─ Standards & Compliance ─
    "BESS_Standards_v1.0": {
        "category_en": "Standards", "category_ko": "규격/기준",
        "desc_en": "BESS standards reference (IEC, IEEE, NFPA, UL) lookup tool.",
        "desc_ko": "BESS 규격 참조 (IEC, IEEE, NFPA, UL) 조회 도구.", "icon": "📖",
    },
    "BESS_Environmental_v1.0": {
        "category_en": "Standards", "category_ko": "규격/기준",
        "desc_en": "Environmental impact assessment and compliance checker.",
        "desc_ko": "환경영향평가 및 규제 적합성 확인.", "icon": "🌿",
    },
    "BESS_CommChecker_v1.0": {
        "category_en": "Standards", "category_ko": "규격/기준",
        "desc_en": "Commissioning procedure compliance checker.",
        "desc_ko": "시운전 절차 적합성 확인 도구.", "icon": "🚦",
    },

    # ─ BOM / Procurement ─
    "BESS_BOMGen_v1.0": {
        "category_en": "Procurement", "category_ko": "조달",
        "desc_en": "Bill of Materials (BOM) generation and cost estimation.",
        "desc_ko": "자재 소요량(BOM) 생성 및 원가 산정.", "icon": "📦",
    },
    "BESS_OrgFinder_v1.0": {
        "category_en": "Procurement", "category_ko": "조달",
        "desc_en": "Organization and personnel finder for EPC project staffing.",
        "desc_ko": "EPC 프로젝트 인력 조직/인원 검색 도구.", "icon": "👥",
    },

    # ─ Analysis Workbooks (xlsx) ─
    "BESS_FluidAnalysis_v1.0": {
        "category_en": "Engineering Calc", "category_ko": "엔지니어링 계산",
        "desc_en": "Fluid dynamics and cooling system analysis workbook.",
        "desc_ko": "유체역학 및 냉각 시스템 분석 워크북.", "icon": "💧", "ext": "xlsx",
    },
    "BESS_StructuralAnalysis_v1.0": {
        "category_en": "Engineering Calc", "category_ko": "엔지니어링 계산",
        "desc_en": "Structural engineering analysis workbook.",
        "desc_ko": "구조 엔지니어링 분석 워크북.", "icon": "🏛️", "ext": "xlsx",
    },
    "BESS_PCS_Battery_Selector_v3.0": {
        "category_en": "Engineering Calc", "category_ko": "엔지니어링 계산",
        "desc_en": "PCS-Battery interface selection and configuration workbook v3.",
        "desc_ko": "PCS-배터리 인터페이스 선정 및 구성 워크북 v3.", "icon": "🔌", "ext": "xlsx",
    },
    "BESS_PowerSystem_Analysis_v2.0": {
        "category_en": "Simulation", "category_ko": "시뮬레이션",
        "desc_en": "Power system analysis workbook (load flow, short circuit) v2.",
        "desc_ko": "전력계통 해석 워크북 (조류계산, 단락전류) v2.", "icon": "⚡", "ext": "xlsx",
    },
}

CATEGORY_ORDER_EN = ["Engineering Calc", "Simulation", "Project Mgmt", "O&M / Reporting", "Standards", "Procurement"]
CATEGORY_ORDER_KO = ["엔지니어링 계산",  "시뮬레이션",    "프로젝트 관리",    "O&M / 보고서",    "규격/기준",  "조달"]


def _get_stem(name: str) -> str:
    """Remove file extension and return the stem."""
    for ext in ('.exe', '.EXE', '.xlsx', '.XLSX'):
        if name.endswith(ext):
            return name[:-len(ext)]
    return name


def _file_size_mb(path: Path) -> float:
    try:
        return path.stat().st_size / (1024 * 1024)
    except Exception:
        return 0.0


def run_tool_launcher_module():
    apply_custom_css()
    require_auth("08")
    sidebar_user_info()

    lang = st.session_state.get('lang', 'KO')
    is_en = (lang == 'EN')

    st.caption(t("p8_caption") if "p8_caption" in dir() else
               ("🔧 **BESS EPC Workflow:** [Tool Launcher — All Engineering Executables]" if is_en
                else "🔧 **BESS EPC 워크플로우:** [도구 런처 — 전체 엔지니어링 실행 파일]"))
    st.title("🔧 Tool Launcher" if is_en else "🔧 도구 런처")
    st.markdown("---")

    st.info(
        "Browse, search, and download all BESS EPC engineering executables. "
        "Click **Download** to save any tool locally." if is_en else
        "모든 BESS EPC 엔지니어링 실행 파일을 탐색, 검색, 다운로드하세요. "
        "**다운로드** 버튼을 눌러 로컬에 저장하세요."
    )

    # ── Mode detection ──────────────────────────────────────────────
    use_local = IS_API_MODE and EXEC_DIR.exists()

    if use_local:
        exe_files = sorted(
            [f for f in EXEC_DIR.iterdir() if f.suffix.lower() in ('.exe', '.xlsx') and f.name.startswith('BESS_')],
            key=lambda f: f.name.lower()
        )
    else:
        # Cloud mode: build virtual file list from TOOL_META
        exe_files = []
        st.info(
            f"☁️ Cloud mode — tools available for download from [GitHub Releases]({GH_RELEASE_URL})."
            if is_en else
            f"☁️ 클라우드 모드 — [GitHub Releases]({GH_RELEASE_URL})에서 도구를 다운로드할 수 있습니다."
        )

    # ── Summary metrics ──────────────────────────────────────────────
    tool_count = len(exe_files) if use_local else len(TOOL_META)
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("총 도구 수" if not is_en else "Total Tools",    str(tool_count))
    col_m2.metric("분류 수"   if not is_en else "Categories",      str(len(CATEGORY_ORDER_EN)))
    if use_local:
        total_mb = sum(_file_size_mb(f) for f in exe_files)
        col_m3.metric("전체 크기" if not is_en else "Total Size",  f"{total_mb:.1f} MB")
    else:
        col_m3.metric("배포 방식" if not is_en else "Source",      "GitHub Release")

    st.markdown("---")

    # ── Search & filter ──────────────────────────────────────────────
    col_search, col_filter = st.columns([3, 1])
    with col_search:
        search_q = st.text_input(
            "🔍 Search tool name..." if is_en else "🔍 도구 이름 검색...",
            key="tool_search",
            placeholder="e.g. Cable" if is_en else "예: 케이블",
        )
    with col_filter:
        cat_opts_display = CATEGORY_ORDER_EN if is_en else CATEGORY_ORDER_KO
        cat_filter = st.selectbox(
            "Category" if is_en else "분류 선택",
            ["All / 전체"] + cat_opts_display,
            key="cat_filter",
        )

    # ── Build tool info list ─────────────────────────────────────────
    def _get_meta(stem: str):
        meta = TOOL_META.get(stem, None)
        if meta is None:
            base = '_'.join(stem.split('_')[:-1]) if '_' in stem else stem
            meta = TOOL_META.get(base, {})
        return meta

    # ── Category grouping ────────────────────────────────────────────
    grouped: dict[str, list] = {}

    if use_local:
        for f in exe_files:
            stem = _get_stem(f.name)
            meta = _get_meta(stem)
            cat  = meta.get("category_en" if is_en else "category_ko",
                            "General Tools" if is_en else "일반 도구")
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append((f, stem, meta))
    else:
        # Cloud mode: use TOOL_META catalog
        for stem, meta in TOOL_META.items():
            cat = meta.get("category_en" if is_en else "category_ko",
                           "General Tools" if is_en else "일반 도구")
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append((None, stem, meta))

    category_order = CATEGORY_ORDER_EN if is_en else CATEGORY_ORDER_KO
    sorted_groups  = sorted(grouped.items(),
                            key=lambda x: category_order.index(x[0]) if x[0] in category_order else 99)

    # ── Render ───────────────────────────────────────────────────────
    shown = 0
    for cat_label, tools in sorted_groups:
        # Category filter
        if cat_filter != "All / 전체" and cat_filter != cat_label:
            continue

        # Search filter
        visible_tools = []
        for f, stem, meta in tools:
            if search_q.strip():
                haystack = (stem + meta.get("desc_en", "") + meta.get("desc_ko", "")).lower()
                if search_q.lower() not in haystack:
                    continue
            visible_tools.append((f, stem, meta))

        if not visible_tools:
            continue

        icon = visible_tools[0][2].get("icon", "🔧")
        st.markdown(f"### {icon} {cat_label}")

        for f, stem, meta in visible_tools:
            tool_icon = meta.get("icon", "🔧")
            desc = meta.get("desc_en" if is_en else "desc_ko",
                            f"{stem} — engineering tool" if is_en else f"{stem} — 엔지니어링 도구")

            c1, c2, c3, c4 = st.columns([0.4, 3, 1, 1])
            with c1:
                st.markdown(f"## {tool_icon}")
            with c2:
                st.markdown(f"**{stem}**")
                st.caption(desc)
            with c3:
                if use_local and f:
                    st.markdown(f"`{_file_size_mb(f):.1f} MB`")
                else:
                    ext_label = meta.get("ext", "exe").upper()
                    st.markdown(f"`{ext_label}`")
            with c4:
                if use_local and f:
                    try:
                        with open(f, "rb") as fh:
                            data = fh.read()
                        st.download_button(
                            label="📥 Download" if is_en else "📥 다운로드",
                            data=data,
                            file_name=f.name,
                            mime="application/octet-stream",
                            key=f"dl_{stem}",
                        )
                    except Exception:
                        st.button("⚠️ Error", key=f"err_{stem}", disabled=True)
                else:
                    # Cloud mode: link to GitHub Release asset
                    ext = meta.get("ext", "exe")
                    dl_url = f"{GH_DOWNLOAD_BASE}/{stem}.{ext}"
                    st.link_button(
                        label="📥 Download" if is_en else "📥 다운로드",
                        url=dl_url,
                        use_container_width=True,
                    )
            shown += 1

        st.markdown("---")

    if shown == 0:
        st.info("No tools match your search / filter." if is_en else
                "검색/필터 조건에 맞는 도구가 없습니다.")


run_tool_launcher_module()
