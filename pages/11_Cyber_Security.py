# -*- coding: utf-8 -*-
"""
11_Cyber_Security.py
BESS 사이버보안 & 시스템 검토 체크리스트
BESS Cybersecurity & System Review Checklist
"""
import streamlit as st
try:
    st.set_page_config(page_title="BESS EPC Platform", layout="wide", initial_sidebar_state="expanded")
except Exception:
    pass

from utils.css_loader import apply_custom_css
from utils.lang_helper import t
from utils.auth_helper import require_auth, sidebar_user_info


# ── Checklist data ─────────────────────────────────────────────────────────────
_IEC62443 = {
    "SL-1 기본 보안 (Basic Cyber Hygiene)": [
        ("네트워크 구성도 및 자산 목록 작성",                     "Asset inventory & network diagram documented"),
        ("기본 방화벽 규칙 적용",                                  "Basic firewall rules applied"),
        ("디폴트 패스워드 변경",                                   "Default passwords changed on all devices"),
        ("불필요한 서비스/포트 비활성화",                          "Unnecessary services/ports disabled"),
        ("안티바이러스 및 악성코드 방지 솔루션 설치",             "Antivirus/anti-malware solution installed"),
        ("정기 백업 및 복구 절차 수립",                            "Regular backup & recovery procedures established"),
    ],
    "SL-2 의도적 침해 방어 (Defense Against Intentional Violation)": [
        ("역할 기반 접근 제어(RBAC) 구현",                         "Role-Based Access Control (RBAC) implemented"),
        ("다중 인증(MFA) 적용 — 원격 접속 포함",                  "Multi-Factor Authentication (MFA) applied incl. remote"),
        ("네트워크 구역 분리 (DMZ / OT / IT)",                    "Network zone segmentation (DMZ / OT / IT)"),
        ("IDS/IPS 침입 탐지 및 방지 시스템 배포",                 "IDS/IPS deployed"),
        ("이벤트 로그 수집 및 SIEM 연동",                          "Event logs collected & SIEM integration"),
        ("취약점 스캔 분기별 수행",                                "Quarterly vulnerability scanning"),
        ("패치 관리 프로세스 문서화",                              "Patch management process documented"),
    ],
    "SL-3 고도화 공격 저항 (Resistance to Sophisticated Attacks)": [
        ("침투 테스트(Pen-Test) 연 1회 이상 수행",                "Annual penetration testing"),
        ("공급망 보안 위험 평가",                                  "Supply chain security risk assessment"),
        ("사이버 사고 대응 계획(IRP) 수립 및 훈련",               "Cyber Incident Response Plan (IRP) established & drilled"),
        ("암호화 통신 (TLS 1.2 이상)",                            "Encrypted communications (TLS 1.2+)"),
        ("엔드포인트 탐지 및 대응(EDR) 솔루션",                   "EDR endpoint detection & response solution"),
        ("사이버보안 운영 센터(SOC) 또는 관제 위탁",              "SOC or managed security service"),
    ],
}

_NERC_CIP = {
    "CIP-002: BES 사이버 시스템 분류": [
        ("High / Medium / Low 임팩트 자산 식별 완료",             "High / Medium / Low impact assets identified"),
        ("BES 사이버 시스템 목록 최신화",                          "BES Cyber System inventory up to date"),
    ],
    "CIP-003: 보안 관리 통제": [
        ("사이버보안 정책 승인 및 배포",                           "Cybersecurity policy approved & distributed"),
        ("고위 관리자 사이버보안 책임자 지정",                     "Senior manager cybersecurity accountability assigned"),
    ],
    "CIP-004: 인력 & 교육": [
        ("배경 조사(Background Check) 완료",                      "Background checks completed"),
        ("사이버보안 인식 교육 연 1회 이상",                       "Annual cybersecurity awareness training"),
        ("접근 권한 분기별 검토",                                  "Quarterly access privilege review"),
    ],
    "CIP-005: 전자 보안 경계(ESP)": [
        ("ESP 정의 및 문서화",                                     "Electronic Security Perimeter defined & documented"),
        ("인터랙티브 원격 접속(IRA) 제어 구현",                   "Interactive Remote Access controls implemented"),
        ("비인가 포트 모니터링",                                   "Unauthorized port monitoring active"),
    ],
    "CIP-006: 물리적 보안": [
        ("물리적 보안 경계 정의",                                  "Physical security perimeters defined"),
        ("출입 로그 및 CCTV 설치",                                 "Access logs & CCTV installed"),
        ("방문자 통제 절차 수립",                                  "Visitor control procedures established"),
    ],
    "CIP-007: 시스템 보안 관리": [
        ("포트 및 서비스 관리 (불필요 서비스 차단)",               "Port & service management (unnecessary blocked)"),
        ("보안 패치 35일 이내 평가 & 적용",                        "Security patches assessed & applied within 35 days"),
        ("악성코드 방지 솔루션 운영",                              "Malware prevention solution active"),
    ],
    "CIP-008: 사고 보고 & 대응": [
        ("사이버 사고 대응 계획 문서화",                           "Cyber incident response plan documented"),
        ("NERC 규정 사고 보고 절차 준수",                          "NERC-required incident reporting procedure in place"),
    ],
    "CIP-010: 구성 변경 관리": [
        ("기준선 구성(Baseline) 문서화",                           "Baseline configuration documented"),
        ("변경 제어 프로세스 운영",                                "Change control process operational"),
        ("취약점 모니터링 35일 주기",                              "35-day vulnerability monitoring cycle"),
    ],
}

_NETWORK_SEC = [
    ("방화벽 정책 검토 (연 1회 이상)",                            "Firewall policy review (annual minimum)"),
    ("네트워크 세그멘테이션: IT / OT / DMZ 분리",                 "Network segmentation: IT / OT / DMZ isolated"),
    ("VPN 원격 접속 MFA 적용",                                    "VPN remote access with MFA"),
    ("VLAN 설정 및 스위치 보안 포트",                              "VLAN configuration & switch port security"),
    ("DNS 보안 (DNSSEC) 또는 내부 DNS 전용 운영",                 "DNS security (DNSSEC) or internal-only DNS"),
    ("Wi-Fi 보안: WPA3 또는 분리 네트워크",                       "Wi-Fi security: WPA3 or isolated network"),
    ("NTP 시간 동기화 보안 설정",                                  "NTP time synchronization secured"),
    ("SNMP v3 이상 사용 (v1/v2 차단)",                            "SNMP v3+ (v1/v2 blocked)"),
    ("원격 데스크톱(RDP) 기본 포트 변경 또는 차단",               "RDP default port changed or blocked"),
    ("IDS/IPS 경보 임계값 검토",                                   "IDS/IPS alert threshold reviewed"),
]

_ACCESS_CTRL = [
    ("최소 권한 원칙(PoLP) 적용",                                 "Principle of Least Privilege (PoLP) applied"),
    ("계정 생명주기 관리 (생성 / 변경 / 삭제)",                   "Account lifecycle management (create / modify / delete)"),
    ("특권 계정(Admin/Root) 별도 관리",                            "Privileged account (Admin/Root) separately managed"),
    ("패스워드 정책: 길이 12+, 복잡도, 90일 교체",                "Password policy: 12+ chars, complexity, 90-day rotation"),
    ("유휴 세션 자동 잠금 (15분)",                                 "Idle session auto-lock (15 min)"),
    ("접근 감사 로그 90일 이상 보관",                              "Access audit logs retained 90+ days"),
    ("퇴직/이직자 접근 24시간 내 회수",                           "Access revoked within 24h of departure"),
    ("공유 계정 사용 금지 정책",                                   "Shared account prohibition policy"),
]

_SYS_REVIEW = [
    ("BESS BMS 펌웨어 최신 버전 확인",                            "BESS BMS firmware on latest version"),
    ("PCS/EMS 소프트웨어 패치 적용 현황",                         "PCS/EMS software patch status reviewed"),
    ("원격 모니터링 시스템 접근 제어 검토",                        "Remote monitoring system access control reviewed"),
    ("SCADA/DCS 취약점 평가 수행",                                 "SCADA/DCS vulnerability assessment performed"),
    ("엣지 디바이스 (RTU, IED) 보안 설정 점검",                   "Edge device (RTU, IED) security configuration checked"),
    ("사이버보안 위험 평가 (CSRA) 최신화",                        "Cyber Security Risk Assessment (CSRA) up to date"),
    ("제3자 공급업체 보안 계약 조항 확인",                         "Third-party vendor security contract clauses verified"),
    ("재해 복구 계획 (DRP) 최신화 및 훈련",                       "Disaster Recovery Plan (DRP) updated & drilled"),
    ("보안 정책 및 절차 문서 최신화",                              "Security policies & procedures documentation current"),
    ("사이버 보험 커버리지 적합성 검토",                           "Cyber insurance coverage adequacy reviewed"),
]


# ── Helper ─────────────────────────────────────────────────────────────────────
def _checklist_section(items: list, key_prefix: str, is_en: bool) -> tuple[int, int]:
    """Render a list of (ko, en) checkbox items. Returns (checked, total)."""
    checked = 0
    for idx, (ko, en) in enumerate(items):
        label = en if is_en else ko
        val   = st.checkbox(label, key=f"{key_prefix}_{idx}")
        if val:
            checked += 1
    return checked, len(items)


def _progress_bar(checked: int, total: int, is_en: bool) -> None:
    pct = int(checked / total * 100) if total else 0
    label = f"{'완료' if not is_en else 'Completed'}: {checked}/{total}  ({pct}%)"
    st.progress(pct / 100, text=label)
    if pct == 100:
        st.success("✅ " + ("모든 항목 완료!" if not is_en else "All items completed!"))
    elif pct >= 70:
        st.info("🔵 " + ("대부분 완료 — 나머지 항목 점검 필요" if not is_en else "Mostly complete — review remaining items"))
    else:
        st.warning("⚠️ " + ("미완료 항목 다수 — 즉시 조치 권고" if not is_en else "Many items pending — immediate action recommended"))


# ── Main ───────────────────────────────────────────────────────────────────────
def run_cyber_security_module():
    apply_custom_css()
    require_auth("11")
    sidebar_user_info()
    lang  = st.session_state.get("lang", "KO")
    is_en = (lang == "EN")

    caption_ko = "🔐 사이버보안 & 시스템 검토 체크리스트 — IEC 62443 · NERC CIP · 네트워크 보안 · 접근 제어"
    caption_en = "🔐 Cybersecurity & System Review Checklist — IEC 62443 · NERC CIP · Network Security · Access Control"
    title_ko   = "🔐 사이버보안 & 시스템 검토 전문가 체크리스트"
    title_en   = "🔐 Cybersecurity & System Review Expert Checklist"
    info_ko    = ("BESS 사이버보안 취약점 점검 및 시스템 검토 체크리스트입니다. "
                  "IEC 62443 (OT 보안), NERC CIP (북미 전력 표준), 네트워크 보안, 접근 제어 4개 영역을 포함합니다. "
                  "체크 완료 항목은 자동으로 진행률에 반영됩니다.")
    info_en    = ("BESS cybersecurity vulnerability assessment and system review checklist. "
                  "Covers 4 domains: IEC 62443 (OT Security), NERC CIP (North American Grid Standard), "
                  "Network Security, and Access Control. Checked items are reflected in progress automatically.")

    st.caption(caption_en if is_en else caption_ko)
    st.title(title_en if is_en else title_ko)
    st.markdown("---")
    st.info(info_en if is_en else info_ko)

    # ── 담당 부분 ────────────────────────────────────────────────────────────
    with st.expander("👷 " + ("담당 부분 지정" if not is_en else "Responsible Disciplines"), expanded=False):
        _disc_ko = ["사이버보안 엔지니어", "IT 관리자", "OT 엔지니어", "안전 엔지니어", "PM", "감리"]
        _disc_en = ["Cybersecurity Engineer", "IT Manager", "OT Engineer", "Safety Engineer", "PM", "Inspector"]
        _discs   = _disc_en if is_en else _disc_ko
        _ra, _rb = st.columns([3, 2])
        with _ra:
            st.multiselect(
                "담당 엔지니어링 분야" if not is_en else "Responsible Disciplines",
                _discs, default=_discs[:2], key="cyber_responsible",
            )
        with _rb:
            st.text_input(
                "담당자 이름" if not is_en else "Assignee Name",
                value=st.session_state.get("cyber_assignee", ""),
                key="cyber_assignee",
            )

    st.markdown("---")

    # ── Tabs ─────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🛡️ IEC 62443",
        "⚡ NERC CIP",
        "🌐 " + ("네트워크 보안" if not is_en else "Network Security"),
        "🔑 " + ("접근 제어"   if not is_en else "Access Control"),
        "⚙️ " + ("시스템 검토" if not is_en else "System Review"),
    ])

    # ── Tab 1: IEC 62443 ─────────────────────────────────────────────────────
    with tab1:
        hdr_ko = "IEC 62443 — OT / BESS 사이버보안 표준"
        hdr_en = "IEC 62443 — OT / BESS Cybersecurity Standard"
        st.subheader(hdr_en if is_en else hdr_ko)
        desc_ko = ("IEC 62443은 산업용 자동화 및 제어 시스템(IACS) 보안 국제 표준입니다. "
                   "BESS EMS/BMS 및 PCS 제어 시스템에 적용됩니다.")
        desc_en = ("IEC 62443 is the international standard for Industrial Automation & Control System "
                   "(IACS) security. Applies to BESS EMS/BMS and PCS control systems.")
        st.markdown(desc_en if is_en else desc_ko)

        total_all, checked_all = 0, 0
        for section, items in _IEC62443.items():
            with st.expander(f"📋 {section}", expanded=True):
                c, t_ = _checklist_section(items, f"iec_{section[:8]}", is_en)
                checked_all += c
                total_all   += t_
        st.markdown("---")
        _progress_bar(checked_all, total_all, is_en)

    # ── Tab 2: NERC CIP ──────────────────────────────────────────────────────
    with tab2:
        hdr_ko = "NERC CIP — 북미 전력망 사이버보안 표준"
        hdr_en = "NERC CIP — North American Electric Grid Cybersecurity Standard"
        st.subheader(hdr_en if is_en else hdr_ko)
        desc_ko = ("NERC CIP (Critical Infrastructure Protection) 표준은 북미 전력 계통 사이버 보안의 핵심 요구사항입니다. "
                   "미국·캐나다에 BESS를 설치할 경우 의무 준수 사항입니다.")
        desc_en = ("NERC CIP (Critical Infrastructure Protection) is the mandatory cybersecurity standard "
                   "for North American bulk electric systems. Required for BESS installations in the US/Canada.")
        st.markdown(desc_en if is_en else desc_ko)

        total_all, checked_all = 0, 0
        for section, items in _NERC_CIP.items():
            with st.expander(f"📋 {section}", expanded=False):
                c, t_ = _checklist_section(items, f"nerc_{section[:10]}", is_en)
                checked_all += c
                total_all   += t_
        st.markdown("---")
        _progress_bar(checked_all, total_all, is_en)

    # ── Tab 3: Network Security ───────────────────────────────────────────────
    with tab3:
        hdr_ko = "네트워크 보안 체크리스트"
        hdr_en = "Network Security Checklist"
        st.subheader(hdr_en if is_en else hdr_ko)
        desc_ko = "BESS 사이트 통신 네트워크의 주요 보안 항목을 점검합니다."
        desc_en = "Review key network security items for the BESS site communication network."
        st.markdown(desc_en if is_en else desc_ko)
        st.markdown("---")
        c, t_ = _checklist_section(_NETWORK_SEC, "netsec", is_en)
        st.markdown("---")
        _progress_bar(c, t_, is_en)

    # ── Tab 4: Access Control ─────────────────────────────────────────────────
    with tab4:
        hdr_ko = "접근 제어 & 계정 관리 체크리스트"
        hdr_en = "Access Control & Account Management Checklist"
        st.subheader(hdr_en if is_en else hdr_ko)
        desc_ko = "BESS 운영 시스템 및 원격 접속에 대한 사용자 접근 제어를 검토합니다."
        desc_en = "Review user access control for BESS operational systems and remote access."
        st.markdown(desc_en if is_en else desc_ko)
        st.markdown("---")
        c, t_ = _checklist_section(_ACCESS_CTRL, "access", is_en)
        st.markdown("---")
        _progress_bar(c, t_, is_en)

    # ── Tab 5: System Review ──────────────────────────────────────────────────
    with tab5:
        hdr_ko = "BESS 시스템 기술 검토 체크리스트"
        hdr_en = "BESS System Technical Review Checklist"
        st.subheader(hdr_en if is_en else hdr_ko)
        desc_ko = "하드웨어·소프트웨어·운영 절차 전반의 보안 기술 검토 항목입니다."
        desc_en = "Security technical review items covering hardware, software, and operational procedures."
        st.markdown(desc_en if is_en else desc_ko)
        st.markdown("---")
        c, t_ = _checklist_section(_SYS_REVIEW, "sysrev", is_en)
        st.markdown("---")
        _progress_bar(c, t_, is_en)

    # ── Overall summary ───────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📊 " + ("전체 체크리스트 완료 현황" if not is_en else "Overall Checklist Summary"))
    _all_keys = []
    for s, items in _IEC62443.items():
        _all_keys += [f"iec_{s[:8]}_{i}" for i in range(len(items))]
    for s, items in _NERC_CIP.items():
        _all_keys += [f"nerc_{s[:10]}_{i}" for i in range(len(items))]
    _all_keys += [f"netsec_{i}"  for i in range(len(_NETWORK_SEC))]
    _all_keys += [f"access_{i}"  for i in range(len(_ACCESS_CTRL))]
    _all_keys += [f"sysrev_{i}"  for i in range(len(_SYS_REVIEW))]

    total_items   = (sum(len(v) for v in _IEC62443.values()) +
                     sum(len(v) for v in _NERC_CIP.values()) +
                     len(_NETWORK_SEC) + len(_ACCESS_CTRL) + len(_SYS_REVIEW))
    checked_items = sum(1 for k in _all_keys if st.session_state.get(k, False))

    domain_labels = ["IEC 62443", "NERC CIP", "Network" if is_en else "네트워크",
                     "Access" if is_en else "접근 제어", "System" if is_en else "시스템 검토"]
    domain_totals = [
        sum(len(v) for v in _IEC62443.values()),
        sum(len(v) for v in _NERC_CIP.values()),
        len(_NETWORK_SEC),
        len(_ACCESS_CTRL),
        len(_SYS_REVIEW),
    ]
    domain_checked = [
        sum(1 for s, items in _IEC62443.items() for i in range(len(items))
            if st.session_state.get(f"iec_{s[:8]}_{i}", False)),
        sum(1 for s, items in _NERC_CIP.items() for i in range(len(items))
            if st.session_state.get(f"nerc_{s[:10]}_{i}", False)),
        sum(1 for i in range(len(_NETWORK_SEC)) if st.session_state.get(f"netsec_{i}", False)),
        sum(1 for i in range(len(_ACCESS_CTRL))  if st.session_state.get(f"access_{i}", False)),
        sum(1 for i in range(len(_SYS_REVIEW))   if st.session_state.get(f"sysrev_{i}", False)),
    ]

    cols = st.columns(len(domain_labels))
    for col, lbl, chk, tot in zip(cols, domain_labels, domain_checked, domain_totals):
        pct = int(chk / tot * 100) if tot else 0
        col.metric(lbl, f"{chk}/{tot}", delta=f"{pct}%")

    st.markdown("")
    _progress_bar(checked_items, total_items, is_en)

    # Export summary button
    lines = [
        f"{'BESS Cybersecurity & System Review Report' if is_en else 'BESS 사이버보안 & 시스템 검토 보고서'}",
        "=" * 60,
        f"{'Total Progress' if is_en else '전체 진행률'}: {checked_items}/{total_items} "
        f"({int(checked_items/total_items*100) if total_items else 0}%)",
        "",
    ]
    for lbl, chk, tot in zip(domain_labels, domain_checked, domain_totals):
        pct = int(chk / tot * 100) if tot else 0
        lines.append(f"  {lbl}: {chk}/{tot} ({pct}%)")
    report_txt = "\n".join(lines)
    st.download_button(
        "📥 " + ("체크리스트 보고서 다운로드 (.txt)" if not is_en else "Download Checklist Report (.txt)"),
        data=report_txt.encode("utf-8"),
        file_name="BESS_CyberSecurity_Checklist.txt",
        mime="text/plain",
        key="dl_cyber_report",
    )


run_cyber_security_module()
