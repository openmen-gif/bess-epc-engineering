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

EXEC_DIR = Path(r"c:\Users\openm\00_AI개발\01_BESS사업\output\10_tools\executables")

# ── Bilingual tool metadata ────────────────────────────────────────────────
# key = exact executable name stem (with version, e.g. BESS_ThermalCalc_v1.0)
TOOL_META: dict[str, dict] = {
    # ─ Engineering Calculators ─
    "BESS_ThermalCalc_v1.0": {
        "category_en": "Engineering Calc", "category_ko": "엔지니어링 계산",
        "desc_en": "BESS thermal management & cooling load calculation tool.",
        "desc_ko": "BESS 열관리 및 냉방 부하 계산 도구.",
        "icon": "🌡️",
    },
    "BESS_CableSizing_v1.0": {
        "category_en": "Engineering Calc", "category_ko": "엔지니어링 계산",
        "desc_en": "MV/LV cable cross-section sizing (thermal + voltage drop).",
        "desc_ko": "MV/LV 케이블 단면 산정 (열용량 + 전압강하).",
        "icon": "🔌",
    },
    "BESS_VoltageDrop_v1.0": {
        "category_en": "Engineering Calc", "category_ko": "엔지니어링 계산",
        "desc_en": "Voltage drop calculation across battery & PCS circuits.",
        "desc_ko": "배터리·PCS 회로 전압강하 계산.",
        "icon": "⚡",
    },
    "BESS_Grounding_v1.0": {
        "category_en": "Engineering Calc", "category_ko": "엔지니어링 계산",
        "desc_en": "Substation grounding grid design per IEEE 80.",
        "desc_ko": "IEEE 80 기준 변전소 접지 그리드 설계.",
        "icon": "🌍",
    },
    "BESS_HarmonicFilter_v1.0": {
        "category_en": "Engineering Calc", "category_ko": "엔지니어링 계산",
        "desc_en": "Harmonic filter design and THD analysis for BESS inverters.",
        "desc_ko": "BESS 인버터 고조파 필터 설계 및 THD 분석.",
        "icon": "📊",
    },
    "BESS_LDCalc_v1.0": {
        "category_en": "Engineering Calc", "category_ko": "엔지니어링 계산",
        "desc_en": "Liquidated Damages (LD) exposure calculation tool.",
        "desc_ko": "지체상금(LD) 노출 위험 계산 도구.",
        "icon": "⚖️",
    },
    "BESS_Foundation_v1.0": {
        "category_en": "Engineering Calc", "category_ko": "엔지니어링 계산",
        "desc_en": "Equipment pad foundation sizing per ASCE 7 / KDS 41.",
        "desc_ko": "ASCE 7 / KDS 41 기준 장비 기초 패드 설계.",
        "icon": "🏗️",
    },
    "BESS_StructuralCalc_v1.0": {
        "category_en": "Engineering Calc", "category_ko": "엔지니어링 계산",
        "desc_en": "Structural load combination and DCR calculation for BESS frames.",
        "desc_ko": "BESS 구조물 하중 조합 및 DCR 계산.",
        "icon": "🔩",
    },
    "BESS_EMCAnalysis_v1.0": {
        "category_en": "Engineering Calc", "category_ko": "엔지니어링 계산",
        "desc_en": "Electromagnetic compatibility analysis for BESS systems.",
        "desc_ko": "BESS 시스템 전자기 적합성(EMC) 분석.",
        "icon": "📡",
    },
    "BESS_HVAC_v1.0": {
        "category_en": "Engineering Calc", "category_ko": "엔지니어링 계산",
        "desc_en": "HVAC load calculation for battery rooms and MV rooms.",
        "desc_ko": "배터리실·PCS실 HVAC 부하 계산.",
        "icon": "❄️",
    },

    # ─ Simulation & Analysis ─
    "BESS_Simulator_v1.0": {
        "category_en": "Simulation", "category_ko": "시뮬레이션",
        "desc_en": "Full BESS cycle simulation engine (charge/discharge/degradation).",
        "desc_ko": "BESS 전체 충방전 사이클 시뮬레이션 엔진.",
        "icon": "🔬",
    },
    "BESS_BatteryAnalysis_v1.0": {
        "category_en": "Simulation", "category_ko": "시뮬레이션",
        "desc_en": "Battery cell-to-system performance analysis and EFC tracking.",
        "desc_ko": "배터리 셀~시스템 성능 분석 및 EFC 추적.",
        "icon": "🔋",
    },
    "BESS_VRTSim_v1.0": {
        "category_en": "Simulation", "category_ko": "시뮬레이션",
        "desc_en": "Voltage Ride-Through (VRT) simulation and grid code compliance check.",
        "desc_ko": "전압 Ride-Through(VRT) 시뮬레이션 및 계통 적합성 확인.",
        "icon": "📈",
    },
    "BESS_PCSDesign_v1.0": {
        "category_en": "Simulation", "category_ko": "시뮬레이션",
        "desc_en": "PCS design parameter calculation and control mode verification.",
        "desc_ko": "PCS 설계 파라미터 계산 및 제어 모드 검증.",
        "icon": "⚙️",
    },
    "BESS_GridTest_v1.0": {
        "category_en": "Simulation", "category_ko": "시뮬레이션",
        "desc_en": "Grid interconnection test procedure generator and result checker.",
        "desc_ko": "계통 연계 시험 절차 생성 및 결과 확인.",
        "icon": "🔗",
    },
    "BESS_CrossValidator_v1.0": {
        "category_en": "Simulation", "category_ko": "시뮬레이션",
        "desc_en": "Cross-validation tool for design parameters across disciplines.",
        "desc_ko": "분야 간 설계 파라미터 교차 검증 도구.",
        "icon": "✅",
    },
    "BESS_ModbusSim_v1.0": {
        "category_en": "Simulation", "category_ko": "시뮬레이션",
        "desc_en": "Modbus/TCP PCS communication simulation and testing.",
        "desc_ko": "Modbus/TCP PCS 통신 시뮬레이션 및 테스트.",
        "icon": "📶",
    },
    "BESS_ThermalRunaway_v1.0": {
        "category_en": "Simulation", "category_ko": "시뮬레이션",
        "desc_en": "Thermal Runaway propagation and fire spread simulation.",
        "desc_ko": "열폭주 전파 및 화재 확산 시뮬레이션.",
        "icon": "🔥",
    },

    # ─ O&M / Reporting ─
    "BESS_ReportGen_v1.0": {
        "category_en": "O&M / Reporting", "category_ko": "O&M / 보고서",
        "desc_en": "Automated EPC deliverables report generator (PDF/Word).",
        "desc_ko": "EPC 납품 문서 자동 보고서 생성기 (PDF/Word).",
        "icon": "📄",
    },
    "BESS_KPIDashboard_v1.0": {
        "category_en": "O&M / Reporting", "category_ko": "O&M / 보고서",
        "desc_en": "BESS operational KPI dashboard export tool.",
        "desc_ko": "BESS 운영 KPI 대시보드 내보내기 도구.",
        "icon": "📊",
    },
    "BESS_MaintenancePlanner_v1.0": {
        "category_en": "O&M / Reporting", "category_ko": "O&M / 보고서",
        "desc_en": "Preventive maintenance schedule planner for BESS systems.",
        "desc_ko": "BESS 설비 예방정비 일정 계획 도구.",
        "icon": "🗓️",
    },
    "BESS_WarrantyTracker_v1.0": {
        "category_en": "O&M / Reporting", "category_ko": "O&M / 보고서",
        "desc_en": "Equipment warranty period tracking and alert tool.",
        "desc_ko": "장비 보증 기간 추적 및 알림 도구.",
        "icon": "🏷️",
    },

    # ─ Procurement / Logistics ─
    "BESS_BOMManager_v1.0": {
        "category_en": "Procurement", "category_ko": "조달",
        "desc_en": "Bill of Materials (BOM) management and cost estimation.",
        "desc_ko": "자재 소요량(BOM) 관리 및 원가 산정 도구.",
        "icon": "📦",
    },
    "BESS_VendorEval_v1.0": {
        "category_en": "Procurement", "category_ko": "조달",
        "desc_en": "Vendor evaluation and technical bid comparison tool.",
        "desc_ko": "공급업체 평가 및 기술 입찰 비교 도구.",
        "icon": "🤝",
    },
    "BESS_ShippingCalc_v1.0": {
        "category_en": "Procurement", "category_ko": "조달",
        "desc_en": "Heavy equipment shipping & logistics cost calculator.",
        "desc_ko": "중장비 운송 및 물류 비용 계산 도구.",
        "icon": "🚢",
    },

    # ─ Commissioning ─
    "BESS_CommissioningPlan_v1.0": {
        "category_en": "Commissioning", "category_ko": "시운전",
        "desc_en": "Step-by-step commissioning checklist and test plan generator.",
        "desc_ko": "단계별 시운전 체크리스트 및 시험절차 생성 도구.",
        "icon": "🚦",
    },
    "BESS_ProtectionTest_v1.0": {
        "category_en": "Commissioning", "category_ko": "시운전",
        "desc_en": "Protection relay test result recorder and pass/fail evaluator.",
        "desc_ko": "보호 계전기 시험 결과 기록 및 합불 평가 도구.",
        "icon": "🛡️",
    },
    "BESS_CapacityTest_v1.0": {
        "category_en": "Commissioning", "category_ko": "시운전",
        "desc_en": "Capacity test data analysis and acceptance compliance checker.",
        "desc_ko": "용량 시험 데이터 분석 및 인수 적합성 확인 도구.",
        "icon": "🔋",
    },
}

CATEGORY_ORDER_EN = ["Engineering Calc", "Simulation", "O&M / Reporting", "Procurement", "Commissioning"]
CATEGORY_ORDER_KO = ["엔지니어링 계산",  "시뮬레이션",    "O&M / 보고서",     "조달",          "시운전"]


def _get_stem(name: str) -> str:
    """Remove .exe suffix and return the stem."""
    return name.removesuffix('.exe').removesuffix('.EXE')


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

    # ── Directory check ──────────────────────────────────────────────
    if not EXEC_DIR.exists():
        st.warning(
            f"Executables folder not found: `{EXEC_DIR}`" if is_en else
            f"실행 파일 폴더를 찾을 수 없습니다: `{EXEC_DIR}`"
        )
        exe_files = []
    else:
        exe_files = sorted(
            [f for f in EXEC_DIR.iterdir() if f.suffix.lower() == '.exe'],
            key=lambda f: f.name.lower()
        )

    # ── Summary metrics ──────────────────────────────────────────────
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("총 도구 수" if not is_en else "Total Tools",    str(len(exe_files)))
    col_m2.metric("분류 수"   if not is_en else "Categories",      str(len(CATEGORY_ORDER_EN)))
    total_mb = sum(_file_size_mb(f) for f in exe_files)
    col_m3.metric("전체 크기" if not is_en else "Total Size",      f"{total_mb:.1f} MB")

    st.markdown("---")

    if not exe_files:
        st.info(
            "No executable (.exe) files found in the folder. "
            "Place your BESS tools in the executables directory." if is_en else
            "실행 파일(.exe)이 없습니다. executables 폴더에 BESS 도구를 배치하세요."
        )
        return

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
    for f in exe_files:
        stem = _get_stem(f.name)
        meta = _get_meta(stem)
        cat  = meta.get("category_en" if is_en else "category_ko",
                        "General Tools" if is_en else "일반 도구")
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append((f, stem, meta))

    category_order = CATEGORY_ORDER_EN if is_en else CATEGORY_ORDER_KO
    sorted_groups  = sorted(grouped.items(),
                            key=lambda x: category_order.index(x[0]) if x[0] in category_order else 99)

    # ── Render ───────────────────────────────────────────────────────
    shown = 0
    for cat_label, tools in sorted_groups:
        # Category filter
        if cat_filter != "All / 전체":
            if is_en and cat_filter != cat_label:
                continue
            if not is_en and cat_filter != cat_label:
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
            size_mb  = _file_size_mb(f)
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
                st.markdown(f"`{size_mb:.1f} MB`")
            with c4:
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
            shown += 1

        st.markdown("---")

    if shown == 0:
        st.info("No tools match your search / filter." if is_en else
                "검색/필터 조건에 맞는 도구가 없습니다.")


run_tool_launcher_module()
