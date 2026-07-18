# -*- coding: utf-8 -*-
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

import streamlit as st
import utils.auth_helper as _auth_mod          # for _sidebar_shown reset
from utils.css_loader import apply_custom_css
from utils.lang_helper import t
from utils.auth_helper import (
    require_auth, sidebar_user_info, is_authenticated, current_role,
)
import utils.market_data as _market_data
import utils.project_store as _ps
from utils.ui_components import (
    render_progress_bar, render_workflow_grid, render_kpi_metrics,
    render_tools_grid, render_phase_avg_chart
)
st.set_page_config(
    page_title="BESS EPC Unified Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_custom_css()

# ── Server-side session restore (fingerprint-based, no external components) ──
from utils.auth_helper import restore_session_by_fingerprint, save_session_fingerprint

if not is_authenticated():
    restore_session_by_fingerprint()

if is_authenticated():
    save_session_fingerprint()

# ── Reset per-run sidebar dedup flag ─────────────────────────────────────────
_auth_mod._sidebar_shown = False

# ── Language Toggle ───────────────────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "KO"

# 로고 — 외부 CDN(icons8) 의존 제거, 자체 인라인 SVG (토큰 색상)
st.sidebar.markdown(
    """
    <div style="display:flex;align-items:center;gap:10px;padding:6px 2px 10px;">
      <svg width="44" height="44" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect x="4" y="10" width="40" height="28" rx="6" fill="#161b22" stroke="#58a6ff" stroke-width="2"/>
        <path d="M25 15 L18 26 h5 l-2 8 8 -12 h-5 l2 -7 z" fill="#e3b341" stroke="#e3b341" stroke-linejoin="round"/>
        <rect x="10" y="16" width="4" height="16" rx="1.5" fill="#3fb950"/>
        <rect x="34" y="16" width="4" height="16" rx="1.5" fill="#3fb950"/>
      </svg>
      <div style="line-height:1.15;">
        <div style="font-weight:800;font-size:1.05rem;color:#e6edf3;">BESS EPC</div>
        <div style="font-size:0.72rem;color:#8b949e;letter-spacing:0.08em;">ENGINEERING PLATFORM</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
# 라벨은 언어 중립 고정 + key 고정 — 라벨이 언어를 따라 바뀌면 위젯 정체성이 리셋되어
# EN→KO 복귀가 불가능해지는 버그가 있었음 (클릭 값이 새 위젯 ID로 승계되지 않음)
lang_choice = st.sidebar.radio(
    "🌐 언어 / Language",
    options=["🇰🇷 한국어", "🇺🇸 English"],
    index=0 if st.session_state.lang == "KO" else 1,
    horizontal=True,
    key="lang_radio",
)
st.session_state.lang = "KO" if "한국어" in lang_choice else "EN"

sidebar_user_info()  # rendered once; pages' calls are deduped

st.sidebar.title(t("hp_sidebar_title"))
st.sidebar.markdown("---")
# Control Center 링크는 관리자(admin)에게만 노출
if is_authenticated() and current_role() == "admin":
    st.sidebar.link_button("⚡ BESS AI Control Center", "https://bess-ai-control.work", use_container_width=True)
    st.sidebar.markdown("---")
st.sidebar.markdown(t("hp_sidebar_ver"))
st.sidebar.info(t("hp_sidebar_hint"))


# ── UI Rendering functions moved to utils.ui_components ───────────────────────


# ── Dashboard home page content ────────────────────────────────────────────────

def _home():
    require_auth()  # safety net for direct URL access

    st.title(t("hp_page_title"))
    st.markdown(t("hp_welcome"))
    st.markdown(t("hp_wf_title"))
    st.markdown(t("hp_wf_sub"))

    render_progress_bar()

    render_workflow_grid()

    st.markdown("---")

    _kpi = _ps.get_kpi()
    render_kpi_metrics(_kpi)

    st.markdown("---")

    render_tools_grid()

    st.markdown("---")
    
    # ── Market Report Download Section ──────────────────────────────────────────
    st.subheader(t("hp_market_trends_title") if t("hp_market_trends_title") != "hp_market_trends_title" else "📈 Global BESS Market Trends")
    st.markdown("최신 글로벌 BESS 시장 동향 및 뉴스 리포트를 다운로드하세요.")
    
    col_dl1, col_dl2, col_empty = st.columns([2, 2, 6])
    
    try:
        import utils.report_generator as rg
        _rg_ok = True
    except Exception as _rg_err:
        _rg_ok = False

    with col_dl1:
        st.markdown("**Word (.docx)**")
        if not _rg_ok:
            st.warning("리포트 생성 모듈 로드 실패 (서버 패키지 설치 확인 필요)")
        elif st.button("📄 Word 리포트 생성 (Generate Report)", use_container_width=True, key="btn_prep_word"):
            with st.spinner("Word 보고서 생성 중..."):
                try:
                    import os
                    report_path = rg.generate_word_report()
                    with open(report_path, "rb") as f:
                        st.session_state["dl_word_bytes"] = f.read()
                    st.session_state["dl_word_name"] = os.path.basename(report_path)
                    st.success("✅ 생성 완료! 아래 버튼으로 다운로드하세요.")
                except Exception as e:
                    st.error(f"보고서 생성 실패: {e}")
        
        if st.session_state.get("dl_word_bytes"):
            st.download_button(
                label="⬇️ Word 다운로드",
                data=st.session_state["dl_word_bytes"],
                file_name=st.session_state.get("dl_word_name", "BESS_Report.docx"),
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
                key="dl_word_btn"
            )

    with col_dl2:
        st.markdown("**PDF (.pdf)**")
        import platform
        if platform.system() != "Windows":
            st.info("PDF 변환은 Windows 환경에서만 지원됩니다.\nWord 파일을 다운로드 후 PDF로 변환해주세요.")
        elif not _rg_ok:
            st.warning("리포트 생성 모듈 로드 실패")
        elif st.button("📄 PDF 리포트 생성 (Generate Report)", use_container_width=True, key="btn_prep_pdf"):
            with st.spinner("PDF 보고서 생성 중 (약 30~60초)..."):
                try:
                    import os
                    pdf_path = rg.generate_pdf_report()
                    if pdf_path:
                        with open(pdf_path, "rb") as f:
                            st.session_state["dl_pdf_bytes"] = f.read()
                        st.session_state["dl_pdf_name"] = os.path.basename(pdf_path)
                        st.success("✅ 생성 완료! 아래 버튼으로 다운로드하세요.")
                    else:
                        st.error("PDF 생성에 실패했습니다. Word 형식을 사용해주세요.")
                except Exception as e:
                    st.error(f"보고서 생성 실패: {e}")

        if st.session_state.get("dl_pdf_bytes"):
            st.download_button(
                label="⬇️ PDF 다운로드",
                data=st.session_state["dl_pdf_bytes"],
                file_name=st.session_state.get("dl_pdf_name", "BESS_Report.pdf"),
                mime="application/pdf",
                use_container_width=True,
                key="dl_pdf_btn"
            )

    st.markdown("---")

    render_phase_avg_chart(_kpi)


# ── Dynamic navigation based on role ─────────────────────────────────────────
# 메뉴 제목은 언어 선택(사이드바 라디오 — nav 구성보다 먼저 실행됨)을 따라간다.
# st.Page의 URL 경로는 파일명에서 파생되므로 title 변경은 링크를 깨지 않는다.

_ko = st.session_state.get("lang", "KO") == "KO"

def _pt(ko, en):
    return ko if _ko else en

_login_pg = st.Page("pages/00_Login.py",             title=_pt("로그인 / 계정관리", "Login / Account"),  icon="🔑")
_home_pg  = st.Page(_home,                            title=_pt("홈 대시보드", "Dashboard"),               icon="🏠")
_p01 = st.Page("pages/01_Project_Setup.py",           title=_pt("01 프로젝트 설정", "01 Project Setup"),      icon="📋")
_p02 = st.Page("pages/02_System_Engineering.py",      title=_pt("02 시스템 설계", "02 System Engineering"),   icon="⚙️")
_p03 = st.Page("pages/03_3D_Simulation.py",           title=_pt("03 3D 시뮬레이션", "03 3D Simulation"),      icon="🏗️")
_p04 = st.Page("pages/04_EBOP_Engineer.py",           title=_pt("04 전기 BOP 설계", "04 EBOP Engineer"),      icon="⚡")
_p05 = st.Page("pages/05_CBOP_Engineer.py",           title=_pt("05 토목 BOP 설계", "05 CBOP Engineer"),      icon="🏗️")
_p06 = st.Page("pages/06_Data_Analyst.py",            title=_pt("06 데이터 분석", "06 Data Analyst"),         icon="📊")
_p07 = st.Page("pages/07_IPO_Checklists.py",          title=_pt("07 IPO 체크리스트", "07 IPO Checklists"),    icon="✅")
_p08 = st.Page("pages/08_Tool_Launcher.py",           title=_pt("08 도구 런처", "08 Tool Launcher"),          icon="🚀")
_p09 = st.Page("pages/09_Container_Thermal.py",       title=_pt("09 컨테이너 열해석", "09 Container Thermal"),icon="🌡️")
_p10 = st.Page("pages/10_Fire_Spread.py",             title=_pt("10 화재 확산", "10 Fire Spread"),            icon="🔥")
_p11 = st.Page("pages/11_Cyber_Security.py",          title=_pt("11 사이버 보안", "11 Cyber Security"),       icon="🔒")
_p12 = st.Page("pages/12_Project_Schedule.py",        title=_pt("12 프로젝트 공정", "12 Project Schedule"),   icon="📅")
_p_market = st.Page("pages/00_Market_Dashboard.py",  title=_pt("마켓 대시보드", "Dashboard: Market"),        icon="📈")

_viewer_pages   = [_p01, _p02, _p03, _p04, _p05, _p06]
_engineer_pages = [_p07, _p08, _p09, _p10, _p11, _p12]
_sec_basic = _pt("📋 도구 01~06", "📋 Tools 01~06")
_sec_adv   = _pt("🔧 도구 07~12", "🔧 Tools 07~12")

role   = st.session_state.get("auth_role", "")
authed = is_authenticated()

if not authed:
    nav = st.navigation([_login_pg])
elif role == "admin":
    nav = st.navigation({
        "":         [_home_pg, _p_market, _login_pg],
        _sec_basic: _viewer_pages,
        _sec_adv:   _engineer_pages,
    })
elif role == "engineer":
    nav = st.navigation({
        "":         [_home_pg, _p_market],
        _sec_basic: _viewer_pages,
        _sec_adv:   _engineer_pages,
    })
elif role == "viewer":
    nav = st.navigation({
        "":         [_home_pg, _p_market],
        _sec_basic: _viewer_pages,
    })
else:
    nav = st.navigation([_home_pg, _p_market, _login_pg])

nav.run()

# ── 모바일 UX: 메뉴 선택 시 사이드바 자동 닫힘 ────────────────────────────────
# st.navigation은 모바일 오버레이 사이드바를 페이지 이동 후에도 열어둔다(실측).
# 지속형 iframe + MutationObserver로 내비 링크에 자동 닫힘 핸들러를 상시 바인딩.
import streamlit.components.v1 as _components

_components.html(
    """
    <script>
    // 부모 문서에 상주 스크립트 주입 — 이 iframe은 리런마다 소멸하므로
    // 타이머·리스너를 부모 렘(realm)에 두어야 페이지 전환 후에도 동작한다.
    (function () {
      const doc = window.parent.document;
      if (doc.getElementById("bess-nav-autoclose")) return;
      const s = doc.createElement("script");
      s.id = "bess-nav-autoclose";
      s.textContent = `(function () {
        if (window.__bessNavAC) return; window.__bessNavAC = 1;
        const close = () => {
          if (window.innerWidth > 768) return;
          const sb = document.querySelector('[data-testid="stSidebar"]');
          if (!sb || sb.getBoundingClientRect().width < 50) return;
          const btn = document.querySelector('[data-testid="stSidebarCollapseButton"] button')
                   || document.querySelector('[data-testid="stSidebarCollapseButton"]');
          if (btn) btn.click();
        };
        document.addEventListener("click", (e) => {
          const t = e.target;
          if (!t || !t.closest) return;
          if (!t.closest('[data-testid="stSidebarNavLink"]')) return;
          [300, 900, 1800, 3000].forEach((d) => setTimeout(close, d));
        }, true);
      })();`;
      doc.body.appendChild(s);
    })();
    </script>
    """,
    height=0,
)
