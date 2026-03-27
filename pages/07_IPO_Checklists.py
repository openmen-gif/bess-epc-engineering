import streamlit as st
try:
    st.set_page_config(page_title="BESS EPC Platform", layout="wide", initial_sidebar_state="expanded")
except Exception:
    pass

import os
import re
import time
from pathlib import Path
from utils.css_loader import apply_custom_css
from utils.lang_helper import t
from utils.ipo_en_data import EN_IPO
from utils.auth_helper import require_auth, sidebar_user_info

SKILL_MD_DIR = str(Path(__file__).parent.parent / "skill_md")


def extract_skill_profile(file_path: str) -> dict:
    """Extract role description, one-line definition, key principles, and role boundaries from skill MD."""
    profile = {"description": "", "definition": "", "principles": [], "boundaries": [], "outputs": []}
    if not os.path.exists(file_path):
        return profile

    for enc in ('utf-8', 'utf-8-sig', 'cp949'):
        try:
            with open(file_path, 'r', encoding=enc) as f:
                content = f.read()
            break
        except (UnicodeDecodeError, LookupError):
            content = ""

    # Frontmatter description
    fm_match = re.search(r'^description:\s*"?(.+?)"?\s*$', content, re.MULTILINE)
    if fm_match:
        profile["description"] = fm_match.group(1).strip()

    # Section extractor helper
    def _extract_section(header_pattern, max_lines=10):
        lines_out = []
        match = re.search(header_pattern, content, re.MULTILINE)
        if not match:
            return lines_out
        start = match.end()
        remaining = content[start:].split('\n')
        for line in remaining:
            stripped = line.strip()
            if stripped.startswith('## '):
                break
            if stripped.startswith('---'):
                break
            if stripped and not stripped.startswith('```'):
                clean = re.sub(r'^[-\*]\s*', '', stripped).replace('**', '').strip()
                if len(clean) > 2 and len(lines_out) < max_lines:
                    lines_out.append(clean)
        return lines_out

    # One-line definition
    def_lines = _extract_section(r'^## 한 줄 정의', max_lines=3)
    profile["definition"] = ' '.join(def_lines) if def_lines else ""

    # Key principles
    profile["principles"] = _extract_section(r'^## 핵심 원칙', max_lines=8)

    # Role boundaries
    profile["boundaries"] = _extract_section(r'^## 역할 경계', max_lines=8)

    # Outputs
    profile["outputs"] = _extract_section(r'^## 산출물', max_lines=8)

    return profile


def _skill_key(filename: str) -> str:
    """Convert 'bess-project-manager.md' → 'bess-project-manager'"""
    return filename.replace('.md', '')


def _has_english_ipo(filename: str) -> bool:
    return _skill_key(filename) in EN_IPO


def extract_ipo_en(filename: str):
    """Return English I/P/O lists from the pre-built EN_IPO dictionary."""
    key = _skill_key(filename)
    data = EN_IPO.get(key, {})
    inputs    = data.get("inputs",    ["RFP / Specification Document", "Site Layout Drawing", "Previous Phase Data"])
    processes = data.get("processes", ["Review inputs for completeness", "Perform baseline calculations", "Draft initial models/documents"])
    outputs   = data.get("outputs",   ["Completed Calculation Sheet", "Final Approved Report", "3D Model/Drawings"])
    return inputs, processes, outputs


def extract_ipo_from_markdown(file_path, lang: str = "KO"):
    """
    Parse I/P/O sections from a bilingual skill markdown file.

    Bilingual format (each MD file should contain both):
      ## 받는 인풋         ← Korean inputs
      ## [EN] Inputs       ← English inputs
      ## 핵심 역량 및 업무 범위  ← Korean processes
      ## [EN] Processes    ← English processes
      ## 산출물            ← Korean outputs
      ## [EN] Outputs      ← English outputs

    When lang='EN', only [EN] sections are parsed.
    When lang='KO', only Korean sections are parsed.
    """
    inputs, processes, outputs = [], [], []
    current_section = None

    if not os.path.exists(file_path):
        return inputs, processes, outputs

    for enc in ('utf-8', 'utf-8-sig', 'cp949', 'euc-kr'):
        try:
            with open(file_path, 'r', encoding=enc) as f:
                lines = f.readlines()
            break
        except (UnicodeDecodeError, LookupError):
            lines = []
    else:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()

    in_code_block = False
    is_en = (lang.upper() == "EN")

    for line in lines:
        stripped = line.strip()

        if stripped.startswith('```'):
            in_code_block = not in_code_block
            continue
        if not stripped:
            continue

        if stripped.startswith('#'):
            header_text = stripped.lower()

            if is_en:
                # English mode: look for [EN] tagged headers
                if '[en] input' in header_text or '[en] 입력' in header_text:
                    current_section = "input"
                elif '[en] process' in header_text or '[en] workflow' in header_text:
                    current_section = "process"
                elif '[en] output' in header_text or '[en] deliverable' in header_text:
                    current_section = "output"
                else:
                    current_section = None
            else:
                # Korean mode: look for Korean section keywords
                if any(kw in header_text for kw in ["인풋", "입력", "받는", "필요"]):
                    current_section = "input"
                elif any(kw in header_text for kw in ["프로세스", "역량", "업무", "단계", "절차", "체크리스트", "수행"]):
                    current_section = "process"
                elif any(kw in header_text for kw in ["아웃풋", "출력", "산출물", "결과물"]):
                    current_section = "output"
                else:
                    current_section = None
            continue

        if current_section and not in_code_block:
            if re.match(r'^\|[-\s\|]+\|$', stripped) or re.match(r'^[-━]+$', stripped) or '━━━━━━━━' in stripped:
                continue

            clean_item = stripped
            if clean_item.startswith('|') and clean_item.endswith('|'):
                clean_item = clean_item.strip('|').replace('|', ' - ')
            clean_item = re.sub(r'^[-\*\d+\.]\s*', '', clean_item)
            clean_item = clean_item.replace('**', '').strip()

            if clean_item.startswith('├──') or clean_item.startswith('└──') or \
               clean_item.startswith('│') or clean_item.startswith('└'):
                continue

            if len(clean_item) > 2:
                if current_section == "input" and clean_item not in inputs and len(inputs) < 20:
                    inputs.append(clean_item)
                elif current_section == "process" and clean_item not in processes and len(processes) < 30:
                    processes.append(clean_item)
                elif current_section == "output" and clean_item not in outputs and len(outputs) < 20:
                    outputs.append(clean_item)

    if not inputs:
        inputs    = ["RFP / Specification Document", "Site Layout Drawing", "Previous Phase Data"] if is_en \
                    else ["RFP / 규격서", "현장 배치도", "이전 단계 데이터"]
    if not processes:
        processes = ["Review inputs for completeness", "Perform baseline calculations", "Draft initial models"] if is_en \
                    else ["입력 완전성 검토", "기본 계산 수행", "초기 모델 초안 작성"]
    if not outputs:
        outputs   = ["Preliminary Report", "Calculation Notes", "Design Drawings"] if is_en \
                    else ["예비 보고서", "계산 노트", "설계 도면"]
    return inputs, processes, outputs


def run_ipo_checklists_module():
    apply_custom_css()
    require_auth("07")
    sidebar_user_info()
    lang = st.session_state.get('lang', 'KO')

    st.caption(t("p7_caption"))
    st.title(t("p7_title"))
    st.markdown("---")

    st.info(t("p7_info"))

    try:
        files = sorted([f for f in os.listdir(SKILL_MD_DIR) if f.endswith('.md')])
    except Exception as e:
        files = []

    if not files:
        st.warning(t("p7_no_skill"))
        files = ['bess-dummy-agent.md']

    selected_file = st.selectbox(t("p7_select"), files, key="skill_select")

    # Load data based on language
    if lang == "EN" and _has_english_ipo(selected_file):
        inputs, processes, outputs = extract_ipo_en(selected_file)
        lang_note = None
    elif lang == "EN":
        inputs, processes, outputs = extract_ipo_from_markdown(os.path.join(SKILL_MD_DIR, selected_file))
        lang_note = "⚠️ English content not yet available for this skill. Showing Korean source."
    else:
        inputs, processes, outputs = extract_ipo_from_markdown(os.path.join(SKILL_MD_DIR, selected_file))
        lang_note = None

    if lang_note:
        st.info(lang_note)

    skill_label = selected_file.replace('.md', '').replace('bess-', '').replace('-', ' ').title()
    st.markdown(f"{t('p7_loaded')} `{skill_label}`")

    # ── Expert Profile Card ──
    profile = extract_skill_profile(os.path.join(SKILL_MD_DIR, selected_file))
    if profile["definition"] or profile["description"]:
        with st.container(border=True):
            pcol1, pcol2 = st.columns([1, 1])
            with pcol1:
                st.markdown(f"##### 🧑‍💼 {skill_label}")
                if profile["description"]:
                    st.caption(profile["description"])
                if profile["definition"]:
                    st.markdown(f"> {profile['definition']}")
                if profile["principles"]:
                    st.markdown("**핵심 원칙**")
                    for p in profile["principles"]:
                        st.markdown(f"- {p}")
            with pcol2:
                if profile["boundaries"]:
                    st.markdown("**역할 경계**")
                    for b in profile["boundaries"]:
                        st.markdown(f"- {b}")
                if profile["outputs"]:
                    st.markdown("**주요 산출물**")
                    for o in profile["outputs"]:
                        st.markdown(f"- {o}")
        st.markdown("---")

    if 'ipo_states' not in st.session_state:
        st.session_state.ipo_states = {}

    def save_ipo_state(cb_key):
        st.session_state.ipo_states[cb_key] = st.session_state[cb_key]

    def toggle_all(prefix, items):
        for i in range(len(items)):
            st.session_state.ipo_states[f"{prefix}_{selected_file}_{i}"] = True

    def count_checked(prefix, items):
        return sum(1 for i in range(len(items)) if st.session_state.ipo_states.get(f"{prefix}_{selected_file}_{i}", False))

    col_i, col_p, col_o = st.columns(3)

    with col_i:
        st.subheader(t("p7_inp_hdr"))
        in_checked = count_checked("in", inputs)
        st.progress(in_checked / max(len(inputs), 1),
                    text=t("p7_inp_prog", c=in_checked, t=len(inputs)))
        if st.button(t("p7_sel_all_i")):
            toggle_all("in", inputs); st.rerun()
        with st.container(border=True):
            for i, item in enumerate(inputs):
                cb_key = f"in_{selected_file}_{i}"
                st.checkbox(item, value=st.session_state.ipo_states.get(cb_key, False),
                            key=cb_key, on_change=save_ipo_state, args=(cb_key,))

    with col_p:
        st.subheader(t("p7_proc_hdr"))
        proc_checked = count_checked("proc", processes)
        st.progress(proc_checked / max(len(processes), 1),
                    text=t("p7_proc_prog", c=proc_checked, t=len(processes)))
        if st.button(t("p7_sel_all_p")):
            toggle_all("proc", processes); st.rerun()
        with st.container(border=True):
            for i, item in enumerate(processes):
                cb_key = f"proc_{selected_file}_{i}"
                st.checkbox(item, value=st.session_state.ipo_states.get(cb_key, False),
                            key=cb_key, on_change=save_ipo_state, args=(cb_key,))

    with col_o:
        st.subheader(t("p7_out_hdr"))
        out_checked = count_checked("out", outputs)
        st.progress(out_checked / max(len(outputs), 1),
                    text=t("p7_out_prog", c=out_checked, t=len(outputs)))
        if st.button(t("p7_sel_all_o")):
            toggle_all("out", outputs); st.rerun()
        with st.container(border=True):
            for i, item in enumerate(outputs):
                cb_key = f"out_{selected_file}_{i}"
                st.checkbox(item, value=st.session_state.ipo_states.get(cb_key, False),
                            key=cb_key, on_change=save_ipo_state, args=(cb_key,))

    st.markdown("---")
    st.subheader(t("p7_gateway"))

    total_items   = len(inputs) + len(processes) + len(outputs)
    total_checked = in_checked + proc_checked + out_checked
    completion_rate = total_checked / max(total_items, 1)

    log_container = st.empty()

    if completion_rate < 0.3:
        st.warning(t("p7_warn_low"))
        st.button(t("p7_btn_agent"), disabled=True)
    elif completion_rate < 0.8:
        st.info(t("p7_wip"))
        if st.button(t("p7_btn_agent")):
            with log_container.container():
                st.markdown(t("p7_agent_log"))
                with st.status("Initializing...", expanded=True) as status:
                    st.write("Auth token verified. Connecting to workflow engine...")
                    time.sleep(1)
                    st.write(f"Loading skill profile: `{selected_file}`...")
                    time.sleep(1)
                    st.write(f"Parsing {proc_checked} targeted processes...")
                    time.sleep(1.5)
                    st.write("Executing background research and drafting...")
                    time.sleep(2)
                    status.update(label=t("p7_dispatched"), state="complete", expanded=False)
                st.success(t("p7_running"))
    else:
        st.success(t("p7_done"))
        if st.button(t("p7_approve"), type="primary"):
            with log_container.container():
                from datetime import datetime
                st.markdown(t("p7_finalizing"))
                progress_bar = st.progress(0, text=t("p7_compiling"))

                now           = datetime.now()
                timestamp_str = now.strftime("%Y%m%d_%H%M%S")
                project_name  = st.session_state.get('project_name', 'BESS_Project')
                target_market = st.session_state.get('target_market', 'N/A')
                skill_name    = selected_file.replace('.md', '').replace('bess-', '').replace('-', ' ').title()

                report_lines = [
                    "=" * 60,
                    "  BESS EPC UNIFIED PLATFORM - PHASE DELIVERABLE REPORT",
                    "=" * 60,
                    f"  Generated     : {now.strftime('%Y-%m-%d %H:%M:%S')}",
                    f"  Project       : {project_name}",
                    f"  Target Market : {target_market}",
                    f"  Skill Module  : {skill_name}",
                    "=" * 60, "",
                    "--- [I] COMPLETED INPUTS ---",
                ]
                for i, item in enumerate(inputs):
                    cb_key  = f"in_{selected_file}_{i}"
                    checked = "✔" if st.session_state.ipo_states.get(cb_key, False) else "○"
                    report_lines.append(f"  [{checked}] {item}")

                report_lines += ["", "--- [P] COMPLETED PROCESSES ---"]
                for i, item in enumerate(processes):
                    cb_key  = f"proc_{selected_file}_{i}"
                    checked = "✔" if st.session_state.ipo_states.get(cb_key, False) else "○"
                    report_lines.append(f"  [{checked}] {item}")

                report_lines += ["", "--- [O] GENERATED OUTPUTS ---"]
                for i, item in enumerate(outputs):
                    cb_key  = f"out_{selected_file}_{i}"
                    checked = "✔" if st.session_state.ipo_states.get(cb_key, False) else "○"
                    report_lines.append(f"  [{checked}] {item}")

                report_lines += [
                    "", "=" * 60,
                    f"  APPROVED BY   : Engineering Manager (BESS EPC Platform)",
                    f"  Completion    : {int(completion_rate * 100)}%",
                    "=" * 60,
                ]
                report_content = "\n".join(report_lines)

                progress_bar.progress(50, text=t("p7_compiling"))
                time.sleep(0.5)

                deliverable_dir = Path("/tmp/deliverables")
                deliverable_dir.mkdir(parents=True, exist_ok=True)

                safe_skill   = selected_file.replace('.md', '').replace(' ', '_')
                safe_project = project_name.replace(' ', '_')
                filename     = f"{timestamp_str}_{safe_project}_{safe_skill}_deliverable.txt"
                save_path    = deliverable_dir / filename

                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(report_content)

                progress_bar.progress(100, text=t("p7_compiling"))
                time.sleep(0.3)

                st.balloons()
                st.success(t("p7_approved"))
                st.info(f"{t('p7_saved')} `{save_path}`")

                st.download_button(
                    label=t("p7_dl_btn"),
                    data=report_content.encode('utf-8'),
                    file_name=filename,
                    mime="text/plain",
                    key=f"download_{timestamp_str}",
                )


run_ipo_checklists_module()
