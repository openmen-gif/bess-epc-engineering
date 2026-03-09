# -*- coding: utf-8 -*-
"""
12_Project_Schedule.py
BESS EPC 프로젝트 공정 등록 및 관리
"""
import streamlit as st
try:
    st.set_page_config(page_title="BESS EPC Platform", layout="wide", initial_sidebar_state="expanded")
except Exception:
    pass

import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime
from utils.css_loader import apply_custom_css
from utils.auth_helper import require_auth, sidebar_user_info
from utils.project_store import (
    load_projects, save_projects, add_project, update_project, delete_project,
    get_kpi, new_project_template,
    STATUS_OPTIONS, STATUS_OPTIONS_EN, PHASE_STATUS, DEFAULT_PHASES,
)

apply_custom_css()
require_auth("12")
sidebar_user_info()

lang  = st.session_state.get("lang", "KO")
is_en = (lang == "EN")

# ── 상수 ──────────────────────────────────────────────────────────────────────
REGIONS = ["한국", "미국", "호주", "영국", "EU", "일본", "중동", "기타"]
REGIONS_EN = ["Korea", "USA", "Australia", "UK", "EU", "Japan", "Middle East", "Other"]
STATUS_COLORS = {"계획중": "#58a6ff", "진행중": "#3fb950", "완료": "#a5d6ff", "보류": "#e3b341"}
STATUS_COLORS_EN = {"Planned": "#58a6ff", "In Progress": "#3fb950", "Completed": "#a5d6ff", "On Hold": "#e3b341"}
PHASE_COLOR = {"대기": "#555", "진행중": "#3fb950", "완료": "#58a6ff"}


def _status_opts():
    return STATUS_OPTIONS_EN if is_en else STATUS_OPTIONS

def _region_opts():
    return REGIONS_EN if is_en else REGIONS

def _phase_status_opts():
    return ["Pending", "In Progress", "Completed"] if is_en else PHASE_STATUS


# ── 헤더 ──────────────────────────────────────────────────────────────────────
st.caption("🛤️ **BESS EPC Workflow:** ... → **[12: Project Schedule]**")
st.title("📅 " + ("Project Schedule Manager" if is_en else "프로젝트 공정 관리"))
st.markdown("---")

# ── 탭 구성 ───────────────────────────────────────────────────────────────────
tab_list, tab_reg, tab_detail, tab_gantt = st.tabs([
    "📋 " + ("Project List"     if is_en else "프로젝트 목록"),
    "➕ " + ("Register"         if is_en else "프로젝트 등록"),
    "✏️ " + ("Edit / Progress"  if is_en else "수정 / 공정 입력"),
    "📊 " + ("Gantt / Charts"   if is_en else "간트 / 차트"),
])

projects = load_projects()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: 프로젝트 목록
# ══════════════════════════════════════════════════════════════════════════════
with tab_list:
    if not projects:
        st.info("등록된 프로젝트가 없습니다. '프로젝트 등록' 탭에서 추가하세요." if not is_en
                else "No projects registered. Add one in the 'Register' tab.")
    else:
        kpi = get_kpi(projects)
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("전체 프로젝트" if not is_en else "Total Projects", kpi["total"])
        k2.metric("진행중" if not is_en else "Active", kpi["active"],
                  delta=f"+{kpi['active']}" if kpi["active"] else None)
        k3.metric("완료" if not is_en else "Completed", kpi["completed"])
        k4.metric("평균 공정률" if not is_en else "Avg Progress",
                  f"{kpi['avg_progress']}%")
        st.markdown("---")

        # 필터
        f1, f2, _ = st.columns([2, 2, 6])
        with f1:
            filt_status = st.selectbox(
                "상태 필터" if not is_en else "Status Filter",
                ["전체"] + _status_opts(), key="ps_filt_status"
            )
        with f2:
            filt_region = st.selectbox(
                "지역 필터" if not is_en else "Region Filter",
                ["전체"] + _region_opts(), key="ps_filt_region"
            )

        filtered = projects
        if filt_status != "전체":
            def _match_status(p):
                s = p.get("status", "계획중")
                if s == filt_status:
                    return True
                try:
                    return is_en and s in STATUS_OPTIONS and STATUS_OPTIONS_EN[STATUS_OPTIONS.index(s)] == filt_status
                except (ValueError, IndexError):
                    return False
            filtered = [p for p in filtered if _match_status(p)]
        if filt_region != "전체":
            def _match_region(p):
                r = p.get("region", "기타")
                if r == filt_region:
                    return True
                try:
                    return is_en and r in REGIONS and REGIONS_EN[REGIONS.index(r)] == filt_region
                except (ValueError, IndexError):
                    return False
            filtered = [p for p in filtered if _match_region(p)]

        for proj in filtered:
            phases = proj.get("phases", [])
            total_prog = round(sum(ph.get("progress", 0) for ph in phases) / max(len(phases), 1))
            status = proj.get("status", "계획중")
            color  = STATUS_COLORS.get(status, "#888")

            with st.container(border=True):
                c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 2, 1])
                with c1:
                    st.markdown(f"**{proj.get('name', 'N/A')}**")
                    st.caption(f"{proj.get('region','')} | {proj.get('capacity_mw',0):.1f} MW / {proj.get('capacity_mwh',0):.1f} MWh | {proj.get('client','')}")
                with c2:
                    st.markdown(f"<span style='color:{color};font-weight:bold'>{status}</span>",
                                unsafe_allow_html=True)
                with c3:
                    st.progress(total_prog / 100, text=f"{total_prog}%")
                with c4:
                    # 단계별 미니 진행바
                    for ph in phases:
                        p_val = ph.get("progress", 0)
                        ph_color = PHASE_COLOR.get(ph.get("status", "대기"), "#555")
                        st.markdown(
                            f"<div style='font-size:11px;color:#aaa'>{ph['name']} "
                            f"<span style='color:{ph_color}'>{p_val}%</span></div>",
                            unsafe_allow_html=True
                        )
                with c5:
                    if st.button("✏️", key=f"edit_{proj['id']}", help="수정", use_container_width=True):
                        st.session_state["ps_edit_id"] = proj["id"]
                        st.rerun()
                    if st.button("🗑", key=f"del_{proj['id']}", help="삭제", use_container_width=True):
                        st.session_state["ps_confirm_del"] = proj["id"]

        # 삭제 확인
        if st.session_state.get("ps_confirm_del"):
            del_id = st.session_state["ps_confirm_del"]
            del_proj = next((p for p in projects if p["id"] == del_id), None)
            if del_proj:
                st.warning(f"정말 삭제하시겠습니까? **{del_proj['name']}**")
                cc1, cc2 = st.columns(2)
                if cc1.button("✅ 확인 삭제", type="primary"):
                    delete_project(del_id)
                    st.session_state.pop("ps_confirm_del", None)
                    st.rerun()
                if cc2.button("❌ 취소"):
                    st.session_state.pop("ps_confirm_del", None)
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: 프로젝트 등록
# ══════════════════════════════════════════════════════════════════════════════
with tab_reg:
    st.subheader("➕ " + ("New Project Registration" if is_en else "신규 프로젝트 등록"))

    with st.form("reg_form", clear_on_submit=True):
        r1, r2 = st.columns(2)
        with r1:
            name    = st.text_input("프로젝트명 (KO)" if not is_en else "Project Name (KO)", placeholder="예: 신안 태양광+ESS")
            name_en = st.text_input("Project Name (EN)", placeholder="e.g. Sinan Solar+ESS")
            client  = st.text_input("발주처 / Client")
            region  = st.selectbox("지역 / Region", _region_opts())
        with r2:
            cap_mw  = st.number_input("용량 (MW)", min_value=0.0, value=0.0, step=1.0)
            cap_mwh = st.number_input("용량 (MWh)", min_value=0.0, value=0.0, step=1.0)
            status  = st.selectbox("초기 상태", _status_opts())
            s_date  = st.date_input("착공 예정일", value=date.today())
            e_date  = st.date_input("준공 예정일", value=date.today())

        notes = st.text_area("비고 / Notes", height=80)

        st.markdown("**공정 단계 초기 설정**" if not is_en else "**Phase Initial Settings**")
        ph_cols = st.columns(4)
        init_phases = []
        for i, ph in enumerate(DEFAULT_PHASES):
            with ph_cols[i]:
                st.markdown(f"**{ph['name_en'] if is_en else ph['name']}**")
                prog = st.slider("진행률 %" if not is_en else "Progress %", 0, 100, 0, key=f"reg_ph_{i}")
                ph_status = st.selectbox("상태" if not is_en else "Status", _phase_status_opts(), key=f"reg_ps_{i}")
                ph_s = st.date_input("시작일" if not is_en else "Start", value=s_date, key=f"reg_phs_{i}")
                ph_e = st.date_input("종료일" if not is_en else "End", value=e_date, key=f"reg_phe_{i}")
                init_phases.append({
                    "name": ph["name"], "name_en": ph["name_en"],
                    "progress": prog, "status": ph_status,
                    "start_date": str(ph_s), "end_date": str(ph_e),
                })

        submitted = st.form_submit_button("✅ " + ("Register" if is_en else "등록"), type="primary")

    if submitted:
        if not name.strip():
            st.error("프로젝트명을 입력하세요.")
        else:
            proj = new_project_template()
            proj.update({
                "name": name.strip(), "name_en": name_en.strip(),
                "client": client.strip(), "region": region,
                "capacity_mw": cap_mw, "capacity_mwh": cap_mwh,
                "status": status if not is_en else (STATUS_OPTIONS[STATUS_OPTIONS_EN.index(status)] if status in STATUS_OPTIONS_EN else status),
                "start_date": str(s_date), "end_date": str(e_date),
                "notes": notes.strip(), "phases": init_phases,
            })
            add_project(proj)
            st.success(f"✅ '{name}' 프로젝트가 등록되었습니다.")
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: 수정 / 공정 입력
# ══════════════════════════════════════════════════════════════════════════════
with tab_detail:
    if not projects:
        st.info("등록된 프로젝트가 없습니다." if not is_en else "No projects registered.")
    else:
        proj_names = [f"{p['name']} ({p.get('status','?')})" for p in projects]
        default_idx = 0
        edit_id = st.session_state.get("ps_edit_id")
        if edit_id:
            ids = [p["id"] for p in projects]
            if edit_id in ids:
                default_idx = ids.index(edit_id)

        sel_idx = st.selectbox(
            "수정할 프로젝트 선택" if not is_en else "Select Project to Edit",
            range(len(proj_names)),
            format_func=lambda i: proj_names[i],
            index=default_idx,
            key="ps_sel_edit",
        )
        proj = projects[sel_idx]

        st.markdown(f"### ✏️ {proj['name']}")
        st.caption(f"ID: {proj['id']} | 등록일: {proj.get('created_at','')[:10]}")

        with st.form("edit_form"):
            e1, e2 = st.columns(2)
            with e1:
                new_name    = st.text_input("프로젝트명", value=proj.get("name",""))
                new_name_en = st.text_input("Project Name (EN)", value=proj.get("name_en",""))
                new_client  = st.text_input("발주처", value=proj.get("client",""))
                _reg = proj.get("region", "기타")
                _reg_idx = REGIONS.index(_reg) if _reg in REGIONS else 0
                new_region  = st.selectbox("지역", _region_opts(), index=_reg_idx)
            with e2:
                new_mw  = st.number_input("용량 (MW)",  value=float(proj.get("capacity_mw", 0)), step=1.0)
                new_mwh = st.number_input("용량 (MWh)", value=float(proj.get("capacity_mwh", 0)), step=1.0)
                cur_status = proj.get("status", "계획중")
                _st_idx = STATUS_OPTIONS.index(cur_status) if cur_status in STATUS_OPTIONS else 0
                new_status = st.selectbox("상태", _status_opts(), index=_st_idx)
                new_s = st.date_input("착공일", value=date.fromisoformat(proj["start_date"]) if proj.get("start_date") else date.today())
                new_e = st.date_input("준공일", value=date.fromisoformat(proj["end_date"]) if proj.get("end_date") else date.today())

            new_notes = st.text_area("비고", value=proj.get("notes",""), height=68)

            st.markdown("---")
            st.markdown("**공정 단계별 진행률 / 일정 업데이트**" if not is_en else "**Phase Progress & Schedule Update**")
            phases = proj.get("phases", [dict(ph) for ph in DEFAULT_PHASES])
            ph_cols2 = st.columns(len(phases))
            new_phases = []
            for i, ph in enumerate(phases):
                with ph_cols2[i]:
                    st.markdown(f"**{ph.get('name_en', ph['name']) if is_en else ph['name']}**")
                    np_ = st.slider("진행률 %" if not is_en else "Progress %", 0, 100, ph.get("progress", 0), key=f"ep_{proj['id']}_{i}")
                    _ph_st = ph.get("status", "대기")
                    _ph_idx = PHASE_STATUS.index(_ph_st) if _ph_st in PHASE_STATUS else 0
                    ns_ = st.selectbox("상태" if not is_en else "Status", _phase_status_opts(),
                                       index=_ph_idx, key=f"es_{proj['id']}_{i}")
                    _phs = ph.get("start_date", "")
                    _phe = ph.get("end_date", "")
                    phs_ = st.date_input("시작일" if not is_en else "Start",
                                         value=date.fromisoformat(_phs) if _phs else date.today(),
                                         key=f"ephs_{proj['id']}_{i}")
                    phe_ = st.date_input("종료일" if not is_en else "End",
                                         value=date.fromisoformat(_phe) if _phe else date.today(),
                                         key=f"ephe_{proj['id']}_{i}")
                    new_phases.append({**ph, "progress": np_, "status": ns_,
                                       "start_date": str(phs_), "end_date": str(phe_)})

            save_btn = st.form_submit_button("💾 " + ("Save" if is_en else "저장"), type="primary")

        if save_btn:
            update_project(proj["id"], {
                "name": new_name, "name_en": new_name_en,
                "client": new_client, "region": new_region,
                "capacity_mw": new_mw, "capacity_mwh": new_mwh,
                "status": new_status if not is_en else (STATUS_OPTIONS[STATUS_OPTIONS_EN.index(new_status)] if new_status in STATUS_OPTIONS_EN else new_status),
                "start_date": str(new_s), "end_date": str(new_e),
                "notes": new_notes, "phases": new_phases,
            })
            st.session_state.pop("ps_edit_id", None)
            st.success("✅ 저장 완료")
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4: 간트 차트 / 분석
# ══════════════════════════════════════════════════════════════════════════════
with tab_gantt:
    if not projects:
        st.info("등록된 프로젝트가 없습니다." if not is_en else "No projects registered.")
    else:
        kpi = get_kpi(projects)

        # ── 상태별 파이 차트 ──────────────────────────────────────────────
        ch1, ch2 = st.columns(2)
        with ch1:
            status_counts = {}
            for p in projects:
                s = p.get("status", "계획중")
                status_counts[s] = status_counts.get(s, 0) + 1
            fig_pie = go.Figure(go.Pie(
                labels=list(status_counts.keys()),
                values=list(status_counts.values()),
                marker_colors=[STATUS_COLORS.get(k, "#888") for k in status_counts],
                hole=0.4,
            ))
            fig_pie.update_layout(
                title="프로젝트 상태 분포" if not is_en else "Project Status Distribution",
                paper_bgcolor="rgba(0,0,0,0)", font_color="#c9d1d9", height=300,
                margin=dict(l=10, r=10, t=40, b=10),
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with ch2:
            # ── 단계별 평균 진행률 막대 ──────────────────────────────────
            phase_names = ["설계", "조달", "시공", "시운전"]
            phase_vals  = [kpi["phase_avg"].get(pn, 0) for pn in phase_names]
            if is_en:
                phase_names = ["Design", "Procurement", "Construction", "Commissioning"]
            fig_bar = go.Figure(go.Bar(
                x=phase_names, y=phase_vals,
                marker_color=["#58a6ff", "#3fb950", "#f78166", "#e3b341"],
                text=[f"{v}%" for v in phase_vals], textposition="outside",
            ))
            fig_bar.update_layout(
                title="단계별 평균 진행률" if not is_en else "Average Phase Progress",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#c9d1d9", height=300, yaxis_range=[0, 110],
                margin=dict(l=10, r=10, t=40, b=10),
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("---")

        # ── 간트 차트 ─────────────────────────────────────────────────────
        st.subheader("📅 " + ("Project Gantt Chart" if is_en else "프로젝트 간트 차트"))

        _PHASE_COLORS = {"설계": "#58a6ff", "조달": "#3fb950", "시공": "#f78166", "시운전": "#e3b341"}

        from datetime import timedelta

        def _safe_dates(s_str, e_str):
            """Ensure valid date range with minimum 7-day width for visibility."""
            s = date.fromisoformat(s_str) if s_str else date.today()
            e = date.fromisoformat(e_str) if e_str else date.today()
            if e <= s:
                e = s + timedelta(days=7)
            return str(s), str(e)

        gantt_rows = []
        for proj in projects:
            raw_s = proj.get("start_date") or str(date.today())
            raw_e = proj.get("end_date") or str(date.today())
            s, e = _safe_dates(raw_s, raw_e)
            total_prog = round(sum(ph.get('progress',0) for ph in proj.get('phases',[]))/max(len(proj.get('phases',[])),1))
            gantt_rows.append(dict(
                Task=proj["name"],
                Start=s, Finish=e,
                Phase="전체" if not is_en else "Overall",
                Progress=f"{total_prog}%",
                Color=STATUS_COLORS.get(proj.get("status","계획중"), "#888"),
            ))
            for ph in proj.get("phases", []):
                ph_s, ph_e = _safe_dates(ph.get("start_date") or raw_s, ph.get("end_date") or raw_e)
                ph_label = ph.get("name_en", ph["name"]) if is_en else ph["name"]
                gantt_rows.append(dict(
                    Task=f"  ↳ {ph_label}",
                    Start=ph_s, Finish=ph_e,
                    Phase=ph_label,
                    Progress=f"{ph.get('progress',0)}%",
                    Color=_PHASE_COLORS.get(ph["name"], "#888"),
                ))

        if gantt_rows:
            df_g = pd.DataFrame(gantt_rows)
            fig_g = go.Figure()
            for _, row in df_g.iterrows():
                t_start = pd.Timestamp(row["Start"])
                t_finish = pd.Timestamp(row["Finish"])
                fig_g.add_trace(go.Bar(
                    x=[t_finish - t_start],
                    y=[row["Task"]],
                    base=[t_start],
                    orientation="h",
                    marker_color=row["Color"],
                    text=row["Progress"],
                    textposition="inside",
                    insidetextanchor="middle",
                    hovertemplate=f"{row['Task']}<br>{row['Start']} ~ {row['Finish']}<br>{row['Progress']}<extra></extra>",
                    showlegend=False,
                ))
            fig_g.update_yaxes(autorange="reversed")
            fig_g.update_xaxes(type="date", dtick="M1", tickformat="%Y-%m")
            fig_g.update_layout(
                title="프로젝트 일정 현황" if not is_en else "Project Schedule Overview",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#c9d1d9", height=max(400, 45 * len(gantt_rows)),
                margin=dict(l=200, r=20, t=40, b=40),
                barmode="overlay",
                bargap=0.3,
            )
            st.plotly_chart(fig_g, use_container_width=True)

        # ── 프로젝트별 공정률 히트맵 ──────────────────────────────────────
        st.markdown("---")
        st.subheader("🗂️ " + ("Phase Progress Heatmap" if is_en else "공정 진행률 히트맵"))
        phase_kos = ["설계", "조달", "시공", "시운전"]
        hm_data, hm_labels = [], []
        for proj in projects:
            row = []
            for pn in phase_kos:
                ph_list = proj.get("phases", [])
                val = next((ph.get("progress", 0) for ph in ph_list if ph.get("name") == pn), 0)
                row.append(val)
            hm_data.append(row)
            hm_labels.append(proj["name"])

        if hm_data:
            ph_display = ["Design","Procurement","Construction","Commissioning"] if is_en else phase_kos
            fig_hm = go.Figure(go.Heatmap(
                z=hm_data, x=ph_display, y=hm_labels,
                colorscale="Blues", zmin=0, zmax=100,
                text=[[f"{v}%" for v in row] for row in hm_data],
                texttemplate="%{text}",
                colorbar=dict(title="%"),
            ))
            fig_hm.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", font_color="#c9d1d9",
                height=max(200, 50 * len(hm_labels)),
                margin=dict(l=10, r=10, t=10, b=10),
            )
            st.plotly_chart(fig_hm, use_container_width=True)
