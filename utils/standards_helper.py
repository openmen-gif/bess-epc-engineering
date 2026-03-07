"""
utils/standards_helper.py
Bilingual Regional Engineering Standards helper.
Usage:
    from utils.standards_helper import get_standards
    st.info(get_standards(target_market, lang, discipline="system"))
"""

import streamlit as st


def get_lang() -> str:
    return st.session_state.get("lang", "KO")


# ---------------------------------------------------------------------------
# Standards dictionary  key=(market_key, discipline, lang)
# market_key: one of "KR", "US", "JP", "AU", "EU"
# discipline: "system" | "ebop" | "cbop" | "data"
# ---------------------------------------------------------------------------

_STD: dict[tuple, str] = {
    # ── System Engineering ──────────────────────────────────────────────────
    ("KR", "system", "EN"): (
        "**South Korea (KR) System Standards:**\n"
        "* **KEC Art.241:** ESS facility regs (battery/PCS installation)\n"
        "* **Grid Interconnection Tech. Criteria:** FRT (LVRT/HVRT) & anti-islanding\n"
        "* **MOFA Fire Safety Code:** Rack-level thermal camera, fire compartment (2-hr), sprinkler mandatory\n"
        "* **Certification:** KS C IEC 62619 (battery safety), KC mark (PCS)"
    ),
    ("KR", "system", "KO"): (
        "**South Korea (KR) 시스템 적용 표준:**\n"
        "* **KEC 제241조:** ESS 시설 규정 (배터리/PCS 설치 기준)\n"
        "* **계통연계기술기준:** FRT(LVRT/HVRT) 및 단독운전 방지\n"
        "* **소방청 화재안전기준:** 랙 단위 열화상 카메라, 방화구획 (내화 2시간), 스프링클러 의무\n"
        "* **인증:** KS C IEC 62619 (배터리 안전), KC 인증 (PCS)"
    ),
    ("US", "system", "EN"): (
        "**United States (US) System Standards:**\n"
        "* **IEEE 1547-2018:** DER grid interconnection & power quality (Ride-Through Category II/III)\n"
        "* **NFPA 855 / NEC Article 706:** Large-scale ESS fire safety & separation distances (UL 9540A burn test recommended)\n"
        "* **NERC CIP:** Control network cybersecurity (Medium Impact BES assets)\n"
        "* **ISO/RTO Rules:** AGC response speed (≤ 4 s) & DNP3/ICCP integration"
    ),
    ("US", "system", "KO"): (
        "**United States (US) 시스템 적용 표준:**\n"
        "* **IEEE 1547-2018:** 분산전원 계통 연계 및 전력품질 특성 (Ride-Through Category II/III)\n"
        "* **NFPA 855 / NEC Article 706:** 대규모 ESS 화재 안전 및 이격 거리 기준 (UL 9540A 방염 시험 권장)\n"
        "* **NERC CIP:** 제어망 사이버보안 통제 (Medium Impact BES 자산 해당 시)\n"
        "* **ISO/RTO Rules:** AGC 제어 응답속도 (≤ 4초) 및 DNP3/ICCP 연동"
    ),
    ("JP", "system", "EN"): (
        "**Japan (JP) System Standards:**\n"
        "* **JEAC 9701-2020:** Grid interconnection requirements (voltage/frequency relay settings & FRT)\n"
        "* **電気事業法 (Electricity Business Act):** Security regulation establishment & construction plan approval\n"
        "* **JIS C 8715-2:** Industrial Li-ion battery safety (equivalent to IEC 62619)\n"
        "* **消防法 (Fire Services Act):** Battery room non-combustible zoning & electrolyte designated quantity filing"
    ),
    ("JP", "system", "KO"): (
        "**Japan (JP) 시스템 적용 표준:**\n"
        "* **JEAC 9701-2020:** 계통연계기술요건 (전압/주파수 보호계전기 정정 및 FRT 규정)\n"
        "* **電気事業法 (電事法):** 보안규정 수립 및 공사계획 인가/신고\n"
        "* **JIS C 8715-2:** 산업용 리튬이온 배터리 안전 (IEC 62619 동등)\n"
        "* **消防法:** 축전지실 불연구획 및 전해액 지정수량 신고"
    ),
    ("AU", "system", "EN"): (
        "**Australia (AU) System Standards:**\n"
        "* **AS/NZS 4777.2:2020:** Inverter grid connection requirements\n"
        "* **NER Schedule 5.2:** AEMO Generator Performance Standards (GPS)\n"
        "* **AS/NZS 5139:** Battery system safe installation\n"
        "* **FCAS Market:** Fast Frequency Response (FFR) metering capability mandatory"
    ),
    ("AU", "system", "KO"): (
        "**Australia (AU) 시스템 적용 표준:**\n"
        "* **AS/NZS 4777.2:2020:** 인버터 계통 연계 요건\n"
        "* **NER Schedule 5.2:** AEMO 발전기 성능 기준 (GPS)\n"
        "* **AS/NZS 5139:** 배터리 시스템 안전 설치\n"
        "* **FCAS 시장:** 초고속 주파수 응답(FFR) 계측기능 필수"
    ),
    ("EU", "system", "EN"): (
        "**Europe / UK System Standards:**\n"
        "* **ENTSO-E RfG 2016/631 (EU) / G99 (UK):** Power Park Module interconnection (FRT & reactive power injection)\n"
        "* **BS EN 62933:** Energy storage system integration & safety\n"
        "* **CE Marking / LVD / EMC Directive:** Mandatory conformity certification for EU distribution/installation\n"
        "* **IEC 61850:** Substation automation & SCADA control standard protocol"
    ),
    ("EU", "system", "KO"): (
        "**Europe / UK 시스템 적용 표준:**\n"
        "* **ENTSO-E RfG 2016/631 (EU) / G99 (UK):** 파워파크 모듈 계통 연계 (FRT 및 무효전력 주입)\n"
        "* **BS EN 62933:** 에너지 저장 시스템 통합 및 안전 규격\n"
        "* **CE 마킹 / LVD / EMC 지침:** 유럽 내 유통 및 설치를 위한 필수 적합성 인증\n"
        "* **IEC 61850:** 변전소 자동화 및 SCADA 제어 표준 프로토콜"
    ),

    # ── E-BOP ───────────────────────────────────────────────────────────────
    ("KR", "ebop", "EN"): (
        "**South Korea (KR) E-BOP Standards:**\n"
        "* **KEC Art.351 & Art.362:** HV substation & LV wiring standards\n"
        "* **Grid Interconnection Tech. Criteria:** Transformer protection relay settings (154 kV OVR/UVR etc.)\n"
        "* **Certification:** KESCO pre-use inspection & periodic inspection mandatory"
    ),
    ("KR", "ebop", "KO"): (
        "**South Korea (KR) E-BOP 적용 표준:**\n"
        "* **KEC 제351조 & 제362조:** 특고압 수전설비 및 저압 배선 기준\n"
        "* **계통연계기술기준:** 변압기 보호계전기 정정 (154kV OVR/UVR 등)\n"
        "* **인증:** KESCO(한국전기안전공사) 사용 전 검사 및 정기 검사 필수"
    ),
    ("US", "ebop", "EN"): (
        "**United States (US) E-BOP Standards:**\n"
        "* **NEC (NFPA 70) Article 706:** Energy storage system wiring & circuit breaker installation\n"
        "* **UL 1741 SA:** Advanced grid-interactive inverter specification (frequency/voltage response)\n"
        "* **IEEE 80:** Substation grounding grid design standard"
    ),
    ("US", "ebop", "KO"): (
        "**United States (US) E-BOP 적용 표준:**\n"
        "* **NEC (NFPA 70) Article 706:** 에너지 저장 시스템 배선 및 차단기 설치 기준\n"
        "* **UL 1741 SA:** 계통 연계 고급 주파수/전압 응답 인버터 규격\n"
        "* **IEEE 80:** 변전소 접지망 설계 기준 (Substation Grounding)"
    ),
    ("JP", "ebop", "EN"): (
        "**Japan (JP) E-BOP Standards:**\n"
        "* **電気設備技術基準 (Technical Standards):** Art.11 grounding resistance & Art.13 insulation resistance\n"
        "* **JEAC 9701:** Distribution/transmission relay settings by voltage level (6.6 kV/22 kV/66 kV)\n"
        "* **JIS C 8962:** Power conditioner (PCS) performance & safety (PSE mark required)"
    ),
    ("JP", "ebop", "KO"): (
        "**Japan (JP) E-BOP 적용 표준:**\n"
        "* **電気設備技術基準 (技術기준):** 제11조 접지 저항 및 제13조 절연 저항 기준\n"
        "* **JEAC 9701:** 배전/송전 연계 전압별(6.6kV, 22kV, 66kV) 계전기 정정 및 시험 기준\n"
        "* **JIS C 8962:** 파워컨디셔너(PCS) 성능 및 안전 규격 (PSE 마크)"
    ),
    ("AU", "ebop", "EN"): (
        "**Australia (AU) E-BOP Standards:**\n"
        "* **AS/NZS 3000:** Wiring Rules (national wiring regulations)\n"
        "* **AS/NZS 5033 / 5139:** Solar DER & BESS electrical installation safety\n"
        "* **AEMO GPS:** Reactive power (Q) supply capability & overvoltage protection criteria"
    ),
    ("AU", "ebop", "KO"): (
        "**Australia (AU) E-BOP 적용 표준:**\n"
        "* **AS/NZS 3000:** Wiring Rules (국가 배선 규정)\n"
        "* **AS/NZS 5033 / 5139:** 태양광 분산전원 및 BESS 전기적 설치 안전\n"
        "* **AEMO GPS:** 무효전력(Q) 공급 능력 및 과전압 보호 기준"
    ),
    ("EU", "ebop", "EN"): (
        "**Europe / UK E-BOP Standards:**\n"
        "* **IEC 60364 series:** Building & LV electrical installation international standard\n"
        "* **IEC 60076:** Power transformer design specification\n"
        "* **G99 (UK):** Loss of Mains (LOM) protection & ROCOF relay setting criteria"
    ),
    ("EU", "ebop", "KO"): (
        "**Europe / UK E-BOP 적용 표준:**\n"
        "* **IEC 60364 시리즈:** 건물 및 저압 전기설비 국제 표준\n"
        "* **IEC 60076:** 주요 변압기(Power Transformers) 설계 규격\n"
        "* **G99 (UK):** Loss of Mains (LOM) 보호 및 ROCOF 계전기 세팅 기준"
    ),

    # ── C-BOP ───────────────────────────────────────────────────────────────
    ("KR", "cbop", "EN"): (
        "**South Korea (KR) C-BOP Standards:**\n"
        "* **Building Act & KDS:** Structural foundation seismic design & snow/wind load standards\n"
        "* **MOFA Fire Safety Code:** Separation ≥ 6 m from general buildings (from outer wall)\n"
        "* **Environmental Conservation Act:** Dust & drainage control during civil works\n"
        "* **National Land Planning Act:** Development permit (floor area ratio by zoning district)"
    ),
    ("KR", "cbop", "KO"): (
        "**South Korea (KR) C-BOP 적용 표준:**\n"
        "* **건축법 및 KDS (국가건설기준):** 구조물 기초 내진 설계 및 적설/풍하중 기준\n"
        "* **소방청 화재안전기준:** 옥외 ESS 시설과 일반 건축물 간 이격 거리 (외벽 기준 6m 이상)\n"
        "* **환경보전법:** 토목 공사 시 비산 먼지 및 배수 처리 규정\n"
        "* **국토계획법:** 개발행위허가 (용도지역별 건폐율/용적률 검토)"
    ),
    ("US", "cbop", "EN"): (
        "**United States (US) C-BOP Standards:**\n"
        "* **IBC (International Building Code):** Equipment pad structural design requirements\n"
        "* **ASCE 7:** Minimum Design Loads (Wind, Seismic, Snow)\n"
        "* **NFPA 855:** Separation distances (10 ft from lot lines, 10 ft between units unless UL 9540A tested)\n"
        "* **EPA / Local Ordinances:** Stormwater Pollution Prevention Plan (SWPPP)"
    ),
    ("US", "cbop", "KO"): (
        "**United States (US) C-BOP 적용 표준:**\n"
        "* **IBC (국제건축기준):** 기기 패드 구조 설계 요건\n"
        "* **ASCE 7:** 최소 설계 하중 (풍하중, 지진, 적설)\n"
        "* **NFPA 855:** 이격 거리 (부지 경계선 10ft, 유닛 간 10ft — UL 9540A 미시험 시)\n"
        "* **EPA / 지방 조례:** 우수 오염 방지 계획 (SWPPP)"
    ),
    ("JP", "cbop", "EN"): (
        "**Japan (JP) C-BOP Standards:**\n"
        "* **Building Standards Act (建築基準法):** Strict seismic foundation design & load calculations in earthquake-prone areas\n"
        "* **Fire Services Act (消防法):** ESS ↔ Building ≥ 3 m, ESS ↔ ESS ≥ 1.5 m separation\n"
        "* **Environmental Impact Assessment Act:** Prior assessment for large-scale civil works"
    ),
    ("JP", "cbop", "KO"): (
        "**Japan (JP) C-BOP 적용 표준:**\n"
        "* **建築基準法 (건축기준법):** 지진 다발 지역 엄격한 내진 기초 설계 및 하중 계산\n"
        "* **消防法:** ESS ↔ 건축물 간 3m 이상, ESS ↔ ESS 간 1.5m 이상 이격\n"
        "* **環境影響評価法:** 대규모 토목 공사 시 사전 환경 평가"
    ),
    ("AU", "cbop", "EN"): (
        "**Australia (AU) C-BOP Standards:**\n"
        "* **NCC (National Construction Code):** Structural and drainage design\n"
        "* **AS 1170:** Structural Design Actions (Wind and Seismic loads)\n"
        "* **AS/NZS 5139:** Battery installation safety clearances and restrictions near habitable structures"
    ),
    ("AU", "cbop", "KO"): (
        "**Australia (AU) C-BOP 적용 표준:**\n"
        "* **NCC (국가건설기준):** 구조 및 배수 설계\n"
        "* **AS 1170:** 구조 설계 하중 (풍하중 및 지진)\n"
        "* **AS/NZS 5139:** 배터리 설치 안전 이격 거리 및 거주 건물 인접 제한"
    ),
    ("EU", "cbop", "EN"): (
        "**Europe / UK C-BOP Standards:**\n"
        "* **Eurocodes (EN 1990 – EN 1999):** Structural, concrete (EN 1992) & geotechnical design (EN 1997)\n"
        "* **CDM Regulations (UK):** Construction (Design and Management) health and safety\n"
        "* **Local Environmental Regulations:** Noise attenuation barriers and visual screening requirements"
    ),
    ("EU", "cbop", "KO"): (
        "**Europe / UK C-BOP 적용 표준:**\n"
        "* **Eurocodes (EN 1990 ~ EN 1999):** 구조, 콘크리트(EN 1992), 지반공학(EN 1997) 설계\n"
        "* **CDM Regulations (UK):** 건설, 설계, 관리 안전보건 규정\n"
        "* **지방 환경 규정:** 소음 저감 방벽 및 시각 차폐 요건"
    ),

    # ── Data Analyst ────────────────────────────────────────────────────────
    ("KR", "data", "EN"): (
        "**South Korea (KR) Data & O&M Standards:**\n"
        "* **KEC Art.241 / KEPCO Grid Code:** ESS performance monitoring & reporting requirements\n"
        "* **LFP Thermal Safety:** Rack-level SOC/SOH tracking per KS C IEC 62619\n"
        "* **SCADA / EMS:** DNP3 or IEC 61850 metering & event logging to KEPCO"
    ),
    ("KR", "data", "KO"): (
        "**South Korea (KR) 데이터 & 운영 표준:**\n"
        "* **KEC 제241조 / 한전 계통연계기준:** ESS 성능 모니터링 및 보고 요건\n"
        "* **LFP 열 안전:** KS C IEC 62619 기준 랙별 SOC/SOH 추적\n"
        "* **SCADA / EMS:** DNP3 또는 IEC 61850 계측 및 이벤트 로그 → 한전 보고"
    ),
    ("US", "data", "EN"): (
        "**United States (US) Data & O&M Standards:**\n"
        "* **NERC FAC-002 / FAC-003:** Facility ratings & interconnection performance data\n"
        "* **FERC Order 841:** BESS market participation data & telemetry requirements\n"
        "* **IEEE 1679 / SAE J2929:** Battery performance & safety monitoring guidelines"
    ),
    ("US", "data", "KO"): (
        "**United States (US) 데이터 & 운영 표준:**\n"
        "* **NERC FAC-002 / FAC-003:** 설비 정격 및 계통 연계 성능 데이터\n"
        "* **FERC Order 841:** BESS 시장 참여 데이터 및 원격 계측 요건\n"
        "* **IEEE 1679 / SAE J2929:** 배터리 성능 및 안전 모니터링 가이드라인"
    ),
    ("JP", "data", "EN"): (
        "**Japan (JP) Data & O&M Standards:**\n"
        "* **電気事業法 (Electricity Business Act):** Operational security regulations & performance records\n"
        "* **JEAC 9701:** Grid connection monitoring data format & sampling rate requirements\n"
        "* **JIS Q 45001:** Operational safety management data recording"
    ),
    ("JP", "data", "KO"): (
        "**Japan (JP) 데이터 & 운영 표준:**\n"
        "* **電気事業法:** 운영 보안 규정 및 성능 기록 유지\n"
        "* **JEAC 9701:** 계통 연결 모니터링 데이터 형식 및 샘플링 레이트\n"
        "* **JIS Q 45001:** 운영 안전 관리 데이터 기록"
    ),
    ("AU", "data", "EN"): (
        "**Australia (AU) Data & O&M Standards:**\n"
        "* **AEMO SEMS:** Storage Element Management System data reporting\n"
        "* **AS/NZS 5139:** Battery system health monitoring & maintenance requirements\n"
        "* **FCAS Telemetry:** 4-second metering & dispatch compliance logging"
    ),
    ("AU", "data", "KO"): (
        "**Australia (AU) 데이터 & 운영 표준:**\n"
        "* **AEMO SEMS:** 저장 요소 관리 시스템 데이터 보고\n"
        "* **AS/NZS 5139:** 배터리 시스템 건전성 모니터링 및 유지보수 요건\n"
        "* **FCAS 원격 계측:** 4초 계측 및 디스패치 이행 로그"
    ),
    ("EU", "data", "EN"): (
        "**Europe / UK Data & O&M Standards:**\n"
        "* **ENTSO-E Transparency Regulation:** Energy storage operational data reporting\n"
        "* **IEC 61850-2 / IEC 62351:** Substation data exchange & cybersecurity for O&M\n"
        "* **Battery Passport (EU 2023/1542):** Lifecycle performance data tracking requirements"
    ),
    ("EU", "data", "KO"): (
        "**Europe / UK 데이터 & 운영 표준:**\n"
        "* **ENTSO-E 투명성 규정:** 에너지 저장 운영 데이터 보고\n"
        "* **IEC 61850-2 / IEC 62351:** 변전소 데이터 교환 및 운영 사이버보안\n"
        "* **배터리 패스포트 (EU 2023/1542):** 생애주기 성능 데이터 추적 요건"
    ),
}

_DEFAULT: dict[tuple, str] = {
    ("_", "system", "EN"): "**Global Default — System Standards:**\n* IEC 62933: BESS System Integration & Safety\n* IEC 62619: Industrial Battery Safety\n* Grid Code: Subject to local utility review.",
    ("_", "system", "KO"): "**글로벌 기본 — 시스템 표준:**\n* IEC 62933: BESS 시스템 통합 및 안전\n* IEC 62619: 산업용 배터리 안전\n* 계통규정: 현지 계통운영사 검토 기준.",
    ("_", "ebop", "EN"): "**Global Default — E-BOP Standards:**\n* IEC 60364: Electrical Installations\n* IEEE 80: Substation Grounding\n* IEC 61439: LV switchgear assemblies.",
    ("_", "ebop", "KO"): "**글로벌 기본 — E-BOP 표준:**\n* IEC 60364: 전기설비\n* IEEE 80: 변전소 접지\n* IEC 61439: 저압 수배전반.",
    ("_", "cbop", "EN"): "**Global Default — C-BOP Standards:**\n* ASCE 7 / Eurocode 8: Seismic and wind load design\n* NFPA 855 / IEC 62933: Minimum fire separation distances.",
    ("_", "cbop", "KO"): "**글로벌 기본 — C-BOP 표준:**\n* ASCE 7 / Eurocode 8: 내진 및 풍하중 설계\n* NFPA 855 / IEC 62933: 최소 화재 이격 거리.",
    ("_", "data", "EN"): "**Global Default — Data & O&M Standards:**\n* IEC 61850: Substation automation & SCADA\n* IEEE 1679: Battery performance characterization\n* IEC 62933-5-2: BESS grid integration performance.",
    ("_", "data", "KO"): "**글로벌 기본 — 데이터 & 운영 표준:**\n* IEC 61850: 변전소 자동화 및 SCADA\n* IEEE 1679: 배터리 성능 특성\n* IEC 62933-5-2: BESS 계통 통합 성능.",
}


def _market_key(target_market: str) -> str:
    m = target_market.upper()
    if "KR" in m or "한국" in m or "KOREA" in m:  return "KR"
    if "US" in m or "ERCOT" in m or "PJM" in m:   return "US"
    if "JP" in m or "JAPAN" in m or "일본" in m:   return "JP"
    if "AU" in m or "AEMO" in m or "AUSTRALIA" in m: return "AU"
    if "UK" in m or "EU" in m or "RO" in m or "EUROPE" in m: return "EU"
    return "_"


def get_standards(target_market: str, lang: str, discipline: str = "system") -> str:
    """
    Return bilingual engineering standards string.

    Args:
        target_market: session_state['target_market'] value
        lang: 'EN' or 'KO'
        discipline: 'system' | 'ebop' | 'cbop' | 'data'
    """
    lang = lang.upper() if lang else "KO"
    if lang not in ("EN", "KO"):
        lang = "KO"
    mkey = _market_key(target_market)
    key = (mkey, discipline, lang)
    if key in _STD:
        return _STD[key]
    # Fallback
    return _DEFAULT.get(("_", discipline, lang), "Standards information unavailable.")
