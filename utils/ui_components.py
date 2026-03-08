import streamlit as st
import pandas as pd
import plotly.express as px
from utils.lang_helper import t

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

def render_progress_bar():
    pct, phase_key = calc_progress()
    st.progress(pct, text=t("hp_progress", pct=pct, phase=t(phase_key)))
    st.markdown("<br>", unsafe_allow_html=True)

def render_workflow_grid():
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

def render_kpi_metrics(_kpi):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label=t("hp_m1"), value=str(_kpi["active"]))
    with col2:
        st.metric(label=t("hp_m2"), value=str(_kpi["total"]))
    with col3:
        st.metric(label=t("hp_m3"), value=f"{_kpi['avg_progress']}%")
    with col4:
        st.metric(label=t("hp_m4"), value=str(_kpi["completed"]))

def render_tools_grid():
    from utils.auth_helper import has_access
    # Tools 07~11 require engineer role; hide from viewers to avoid page_link errors
    if not has_access("07"):
        return
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

def render_phase_avg_chart(_kpi):
    st.subheader(t("hp_arch_title"))
    st.info(t("hp_arch_info"))

    x_col  = t("hp_chart_x")
    y_col  = t("hp_chart_y")
    phases = [t("hp_phase_design"), t("hp_phase_proc"), t("hp_phase_const"), t("hp_phase_comm")]
    _pa    = _kpi["phase_avg"]
    data   = pd.DataFrame({x_col: phases, y_col: [
        _pa.get("설계", 0), _pa.get("조달", 0), _pa.get("시공", 0), _pa.get("시운전", 0)
    ]})
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
