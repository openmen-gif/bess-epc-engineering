# -*- coding: utf-8 -*-
import json as _json
import streamlit as st
import utils.auth_helper as _auth_mod          # for _sidebar_shown reset
from utils.css_loader import apply_custom_css
from utils.lang_helper import t
from utils.auth_helper import (
    require_auth, sidebar_user_info, is_authenticated,
)
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="BESS EPC Unified Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_custom_css()

# ── Cookie-based session restore ─────────────────────────────────────────────
_COOKIE_KEY = "bess_auth_v1"
try:
    from streamlit_cookies_controller import CookieController as _CC
    _cc = _CC()
    if not is_authenticated():
        _raw = _cc.get(_COOKIE_KEY)
        if _raw:
            try:
                _sd = _json.loads(_raw)
                st.session_state["auth_user"] = _sd["u"]
                st.session_state["auth_role"] = _sd["r"]
                st.session_state["auth_name"] = _sd["n"]
            except Exception:
                _cc.remove(_COOKIE_KEY)
    if is_authenticated():
        _cc.set(_COOKIE_KEY, _json.dumps({
            "u": st.session_state["auth_user"],
            "r": st.session_state["auth_role"],
            "n": st.session_state["auth_name"],
        }), max_age=86400 * 7)   # 7일 유지
except Exception:
    _cc = None

# ── Reset per-run sidebar dedup flag ─────────────────────────────────────────
_auth_mod._sidebar_shown = False

# ── Language Toggle ───────────────────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state.lang = "KO"

st.sidebar.image(
    "https://img.icons8.com/color/144/000000/artificial-intelligence.png",
    width=100,
)
lang_choice = st.sidebar.radio(
    t("lang_label"),
    options=["🇰🇷 한국어", "🇺🇸 English"],
    index=0 if st.session_state.lang == "KO" else 1,
    horizontal=True,
)
st.session_state.lang = "KO" if "한국어" in lang_choice else "EN"

sidebar_user_info()  # rendered once; pages' calls are deduped

st.sidebar.title(t("hp_sidebar_title"))
st.sidebar.markdown("---")
st.sidebar.markdown(t("hp_sidebar_ver"))
st.sidebar.info(t("hp_sidebar_hint"))


# ── Helper functions ──────────────────────────────────────────────────────────

def _chk(session_key: str) -> str:
    return "✅" if st.session_state.get(session_key) else "⏳"


def workflow_items(step: int) -> str:
    rows = {
        1: [
            (_chk("capacity_mw"), t("hp_wi_sizing")),
            (_chk("proj_name"),   t("hp_wi_rfp")),
            ("⏳",                t("hp_wi_feasib")),
        ],
        2: [("🔄", t("hp_wi_arch")), ("🔄", t("hp_wi_sld")), ("⏳", t("hp_wi_pcs"))],
        3: [("🔄", t("hp_wi_cfd")), ("⏳", t("hp_wi_struct")), ("⏳", t("hp_wi_fds"))],
        4: [("⏳", t("hp_wi_tr")), ("⏳", t("hp_wi_cable")), ("⏳", t("hp_wi_gnd"))],
        5: [("⏳", t("hp_wi_pad")), ("⏳", t("hp_wi_hvac")), ("⏳", t("hp_wi_fire_prot"))],
        6: [("⏳", t("hp_wi_kpi")), ("⏳", t("hp_wi_deg"))],
    }
    return "  \n".join(f"{icon} {label}" for icon, label in rows.get(step, []))


def calc_progress() -> tuple[int, str]:
    keys = ["proj_name", "capacity_mw", "duration_h", "battery_type", "grid_voltage"]
    filled = sum(1 for k in keys if st.session_state.get(k))
    if filled == 0:
        return 5, "hp_phase_init"
    elif filled < len(keys):
        return max(10, 5 + filled * 3), "hp_phase_step1"
    else:
        return 35, "hp_phase_step2"


# ── Dashboard home page content ────────────────────────────────────────────────

def _home():
    require_auth()  # safety net for direct URL access

    st.title(t("hp_page_title"))
    st.markdown(t("hp_welcome"))
    st.markdown(t("hp_wf_title"))
    st.markdown(t("hp_wf_sub"))

    pct, phase_key = calc_progress()
    st.progress(pct, text=t("hp_progress", pct=pct, phase=t(phase_key)))
    st.markdown("<br>", unsafe_allow_html=True)

    w1, w2, w3, w4, w5, w6 = st.columns(6)
    with w1:
        with st.container(border=True):
            st.markdown(t("hp_w1_title"))
            st.markdown(workflow_items(1))
            st.page_link("pages/01_Project_Setup.py",      label=t("hp_w1_link"))
    with w2:
        with st.container(border=True):
            st.markdown(t("hp_w2_title"))
            st.markdown(workflow_items(2))
            st.page_link("pages/02_System_Engineering.py", label=t("hp_w2_link"))
    with w3:
        with st.container(border=True):
            st.markdown(t("hp_w3_title"))
            st.markdown(workflow_items(3))
            st.page_link("pages/03_3D_Simulation.py",      label=t("hp_w3_link"))
    with w4:
        with st.container(border=True):
            st.markdown(t("hp_w4_title"))
            st.markdown(workflow_items(4))
            st.page_link("pages/04_EBOP_Engineer.py",      label=t("hp_w4_link"))
    with w5:
        with st.container(border=True):
            st.markdown(t("hp_w5_title"))
            st.markdown(workflow_items(5))
            st.page_link("pages/05_CBOP_Engineer.py",      label=t("hp_w5_link"))
    with w6:
        with st.container(border=True):
            st.markdown(t("hp_w6_title"))
            st.markdown(workflow_items(6))
            st.page_link("pages/06_Data_Analyst.py",       label=t("hp_w6_link"))

    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label=t("hp_m1"), value="3",    delta="+1")
    with col2:
        st.metric(label=t("hp_m2"), value="124",  delta=t("hp_m2_delta"))
    with col3:
        st.metric(label=t("hp_m3"), value=f"{pct}%")
    with col4:
        st.metric(label=t("hp_m4"), value="5",    delta="-2", delta_color="inverse")

    st.markdown("---")

    st.markdown(t("hp_tools_title"))
    st.caption(t("hp_tools_sub"))
    ta, tb, tc, td, te = st.columns(5)
    with ta:
        with st.container(border=True):
            st.markdown(t("hp_ipo_title"))
            st.caption(t("hp_ipo_desc"))
            st.page_link("pages/07_IPO_Checklists.py",      label=t("hp_ipo_link"))
    with tb:
        with st.container(border=True):
            st.markdown(t("hp_launcher_title"))
            st.caption(t("hp_launcher_desc"))
            st.page_link("pages/08_Tool_Launcher.py",       label=t("hp_launcher_link"))
    with tc:
        with st.container(border=True):
            st.markdown(t("hp_thermal_title"))
            st.caption(t("hp_thermal_desc"))
            st.page_link("pages/09_Container_Thermal.py",   label=t("hp_thermal_link"))
    with td:
        with st.container(border=True):
            st.markdown(t("hp_fire_title"))
            st.caption(t("hp_fire_desc"))
            st.page_link("pages/10_Fire_Spread.py",         label=t("hp_fire_link"))
    with te:
        with st.container(border=True):
            st.markdown(t("hp_cyber_title"))
            st.caption(t("hp_cyber_desc"))
            st.page_link("pages/11_Cyber_Security.py",      label=t("hp_cyber_link"))

    st.markdown("---")

    st.subheader(t("hp_arch_title"))
    st.info(t("hp_arch_info"))

    x_col  = t("hp_chart_x")
    y_col  = t("hp_chart_y")
    phases = [t("hp_phase_design"), t("hp_phase_proc"), t("hp_phase_const"), t("hp_phase_comm")]
    data   = pd.DataFrame({x_col: phases, y_col: [95, 60, 20, 0]})
    fig = px.bar(
        data, x=x_col, y=y_col, color=x_col,
        title=t("hp_chart_title"),
        color_discrete_sequence=px.colors.sequential.Teal,
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#c9d1d9"),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


# ── Dynamic navigation based on role ─────────────────────────────────────────

_login_pg = st.Page("pages/00_Login.py",             title="Login / 계정관리",    icon="🔑")
_home_pg  = st.Page(_home,                            title="Dashboard",            icon="🏠")
_p01 = st.Page("pages/01_Project_Setup.py",           title="01 Project Setup",     icon="📋")
_p02 = st.Page("pages/02_System_Engineering.py",      title="02 System Engineering",icon="⚙️")
_p03 = st.Page("pages/03_3D_Simulation.py",           title="03 3D Simulation",     icon="🏗️")
_p04 = st.Page("pages/04_EBOP_Engineer.py",           title="04 EBOP Engineer",     icon="⚡")
_p05 = st.Page("pages/05_CBOP_Engineer.py",           title="05 CBOP Engineer",     icon="🏗️")
_p06 = st.Page("pages/06_Data_Analyst.py",            title="06 Data Analyst",      icon="📊")
_p07 = st.Page("pages/07_IPO_Checklists.py",          title="07 IPO Checklists",    icon="✅")
_p08 = st.Page("pages/08_Tool_Launcher.py",           title="08 Tool Launcher",     icon="🚀")
_p09 = st.Page("pages/09_Container_Thermal.py",       title="09 Container Thermal", icon="🌡️")
_p10 = st.Page("pages/10_Fire_Spread.py",             title="10 Fire Spread",       icon="🔥")
_p11 = st.Page("pages/11_Cyber_Security.py",          title="11 Cyber Security",    icon="🔒")

_viewer_pages   = [_p01, _p02, _p03, _p04, _p05, _p06]
_engineer_pages = [_p07, _p08, _p09, _p10, _p11]

role   = st.session_state.get("auth_role", "")
authed = is_authenticated()

if not authed:
    nav = st.navigation([_login_pg])
elif role == "admin":
    nav = st.navigation({
        "":               [_home_pg, _login_pg],
        "📋 Tools 01~06": _viewer_pages,
        "🔧 Tools 07~11": _engineer_pages,
    })
elif role == "engineer":
    nav = st.navigation({
        "":               [_home_pg],
        "📋 Tools 01~06": _viewer_pages,
        "🔧 Tools 07~11": _engineer_pages,
    })
else:  # viewer
    nav = st.navigation({
        "":               [_home_pg],
        "📋 Tools 01~06": _viewer_pages,
    })

nav.run()
