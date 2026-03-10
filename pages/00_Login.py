# -*- coding: utf-8 -*-
"""
00_Login.py
사용자 로그인 / 계정 등록 / 계정 관리 페이지
User login, registration, and account management page
"""
import streamlit as st
# page_config is set in Dashboard.py (layout="wide")

from utils.css_loader import apply_custom_css
from utils.auth_helper import (
    login, register, delete_user, update_user, change_password,
    get_all_users, is_authenticated, current_role,
    ROLES, ROLE_LABEL, PAGE_MIN_ROLE, PROTECTED_USERS, sidebar_user_info,
)


def run_login_page():
    apply_custom_css()

    lang = st.session_state.get("lang", "KO")
    is_en = (lang == "EN")

    sidebar_user_info()  # deduped by Dashboard.py

    st.title("🔑 " + ("BESS EPC 플랫폼 — 로그인" if not is_en else "BESS EPC Platform — Login"))
    st.markdown("---")

    # ── Already logged in ─────────────────────────────────────────────────
    if is_authenticated():
        role = current_role()
        username = st.session_state.get("auth_user", "")
        name = st.session_state.get("auth_name", username)
        role_label = ROLE_LABEL.get(role, {}).get("ko" if not is_en else "en", role)
        st.success(
            ("✅ 로그인됨: " if not is_en else "✅ Logged in as: ") +
            f"**{name}** ({role_label})"
        )
        st.info("🏠 " + ("왼쪽 사이드바에서 Dashboard를 클릭하세요." if not is_en else "Click Dashboard in the left sidebar to return."))
        if role == "admin":
            tab_myacct, tab_manage = st.tabs([
                "👤 " + ("내 계정 설정" if not is_en else "My Account"),
                "⚙️ " + ("계정 관리" if not is_en else "Manage Accounts"),
            ])
            with tab_myacct:
                _my_account_form(username, is_en)
            with tab_manage:
                _admin_manage(is_en)
        else:
            _my_account_form(username, is_en)
        return

    # ── Not logged in: Login / Register tabs ──────────────────────────────
    tab_login, tab_register = st.tabs([
        "🔐 " + ("로그인" if not is_en else "Login"),
        "📝 " + ("계정 등록" if not is_en else "Register"),
    ])

    with tab_login:
        _login_form(is_en)

    with tab_register:
        _register_form(is_en)

    # ── Default account hint ───────────────────────────────────────────────
    with st.expander("ℹ️ " + ("기본 계정 정보" if not is_en else "Default Account"), expanded=False):
        st.markdown(
            "처음 실행 시 기본 관리자 계정이 생성됩니다:\n\n"
            "- **아이디**: `admin`\n"
            "- **비밀번호**: `djflsdk79`\n\n"
            "보안을 위해 로그인 후 비밀번호를 변경하거나 새 계정을 만들어주세요."
            if not is_en else
            "A default admin account is created on first run:\n\n"
            "- **Username**: `admin`\n"
            "- **Password**: `djflsdk79`\n\n"
            "For security, please change the password or create a new account after login."
        )


def _login_form(is_en: bool) -> None:
    st.markdown("#### " + ("로그인" if not is_en else "Sign In"))
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input(
            "아이디 / Username",
            placeholder="admin",
        )
        password = st.text_input(
            "비밀번호 / Password",
            type="password",
            placeholder="••••••••",
        )
        submitted = st.form_submit_button(
            "🔐 " + ("로그인" if not is_en else "Login"),
            type="primary",
            use_container_width=True,
        )
        if submitted:
            if not username or not password:
                st.error("아이디와 비밀번호를 입력해주세요. / Please enter username and password.")
            elif login(username, password):
                st.success(
                    ("로그인 성공! 페이지를 새로고침합니다…" if not is_en
                     else "Login successful! Refreshing…")
                )
                st.rerun()
            else:
                st.error(
                    "아이디 또는 비밀번호가 올바르지 않습니다. / Invalid username or password."
                )


def _register_form(is_en: bool) -> None:
    st.markdown("#### " + ("새 계정 등록" if not is_en else "Create Account"))
    st.caption(
        "뷰어/엔지니어 역할은 자가 등록 가능합니다. 관리자(Admin) 역할은 관리자만 부여할 수 있습니다."
        if not is_en else
        "Viewer/Engineer roles can be self-registered. Admin role can only be assigned by an admin."
    )

    SELF_ROLES = ["viewer", "engineer"]
    role_labels_ko = {"viewer": "🟢 뷰어 — 기본 조회 (01~06)", "engineer": "🟡 엔지니어 — 전체 도구 (01~11)"}
    role_labels_en = {"viewer": "🟢 Viewer — Basic access (01~06)", "engineer": "🟡 Engineer — All tools (01~11)"}
    role_labels = role_labels_en if is_en else role_labels_ko

    with st.form("register_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            reg_username = st.text_input("아이디 / Username *", placeholder="hong_engineer")
            reg_password = st.text_input("비밀번호 / Password *", type="password")
        with col_b:
            reg_name = st.text_input(
                "이름 / Display Name",
                placeholder="홍길동" if not is_en else "Hong Gil-dong",
            )
            reg_confirm = st.text_input("비밀번호 확인 / Confirm Password", type="password")

        reg_role = st.selectbox(
            "역할 / Role *",
            SELF_ROLES,
            format_func=lambda r: role_labels.get(r, r),
            index=0,
        )

        submitted = st.form_submit_button(
            "📝 " + ("계정 등록" if not is_en else "Register"),
            type="primary",
            use_container_width=True,
        )
        if submitted:
            if reg_password != reg_confirm:
                st.error("비밀번호가 일치하지 않습니다. / Passwords do not match.")
            else:
                ok, msg = register(reg_username, reg_password, reg_role, reg_name)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)


def _my_account_form(username: str, is_en: bool) -> None:
    st.markdown("#### 👤 " + ("내 계정 설정" if not is_en else "My Account Settings"))
    users = get_all_users()
    uinfo = users.get(username, {})
    current_name = uinfo.get("name", username)

    # ── Display name change ────────────────────────────────────────────────
    with st.form("myacct_name_form"):
        new_name = st.text_input(
            "표시 이름 / Display Name",
            value=current_name,
        )
        if st.form_submit_button("✏️ " + ("이름 변경" if not is_en else "Update Name"),
                                  use_container_width=True):
            if new_name.strip():
                ok, msg = update_user(username, new_name=new_name)
                if ok:
                    st.session_state["auth_name"] = new_name.strip()
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.error("이름을 입력해주세요. / Please enter a name.")

    st.markdown("---")

    # ── Password change ────────────────────────────────────────────────────
    st.markdown("##### 🔑 " + ("비밀번호 변경" if not is_en else "Change Password"))
    with st.form("myacct_pw_form", clear_on_submit=True):
        old_pw  = st.text_input("현재 비밀번호 / Current Password", type="password")
        new_pw  = st.text_input("새 비밀번호 / New Password", type="password")
        new_pw2 = st.text_input("새 비밀번호 확인 / Confirm New Password", type="password")
        if st.form_submit_button("🔑 " + ("비밀번호 변경" if not is_en else "Change Password"),
                                  type="primary", use_container_width=True):
            if new_pw != new_pw2:
                st.error("새 비밀번호가 일치하지 않습니다. / New passwords do not match.")
            else:
                ok, msg = change_password(username, old_pw, new_pw)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)


def _admin_manage(is_en: bool) -> None:
    st.markdown("#### ⚙️ " + ("계정 관리 (관리자 전용)" if not is_en else "Account Management (Admin Only)"))

    users = get_all_users()

    # ── User list table ────────────────────────────────────────────────────
    st.markdown("##### " + ("등록된 계정 목록" if not is_en else "Registered Accounts"))
    for uname, uinfo in users.items():
        role = uinfo.get("role", "viewer")
        name = uinfo.get("name", uname)
        role_label = ROLE_LABEL.get(role, {}).get("ko" if not is_en else "en", role)
        is_self = (uname == st.session_state.get("auth_user"))

        is_protected = uname in PROTECTED_USERS
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 5, 1])
            with c1:
                st.markdown(f"**{name}** `{uname}`")
                self_tag = " **(나)**" if not is_en else " **(you)**"
                tags = role_label + (self_tag if is_self else "")
                if is_protected:
                    tags += " 🔒" + (" 개발자 보호" if not is_en else " dev-protected")
                st.caption(tags)
            with c2:
                if is_protected:
                    st.caption(
                        "🔒 이 계정은 개발자 보호 계정입니다. UI에서 역할 변경 불가." if not is_en
                        else "🔒 Developer-protected account. Role cannot be changed via UI."
                    )
                else:
                    # Role change form — one per user, button-triggered
                    with st.form(key=f"role_form_{uname}"):
                        fc1, fc2 = st.columns([3, 1])
                        with fc1:
                            new_role = st.selectbox(
                                "역할 변경" if not is_en else "Change Role",
                                ROLES,
                                index=ROLES.index(role),
                                key=f"sel_role_{uname}",
                            )
                        with fc2:
                            st.markdown("<br>", unsafe_allow_html=True)
                            save = st.form_submit_button(
                                "저장" if not is_en else "Save",
                                type="primary",
                                use_container_width=True,
                            )
                        if save:
                            ok, msg = update_user(uname, new_role=new_role)
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
            with c3:
                st.markdown("<br><br>", unsafe_allow_html=True)
                if not is_self and not is_protected:
                    if st.button("🗑", key=f"del_{uname}", help=("계정 삭제" if not is_en else "Delete")):
                        ok, msg = delete_user(uname)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

    st.markdown("---")

    # ── Add new account (admin) ────────────────────────────────────────────
    st.markdown("##### " + ("새 계정 추가" if not is_en else "Add New Account"))
    with st.form("admin_add_form", clear_on_submit=True):
        ca, cb, cc, cd = st.columns([2, 2, 2, 1])
        with ca:
            new_user = st.text_input("아이디 / Username")
        with cb:
            new_pw = st.text_input("비밀번호 / Password", type="password")
        with cc:
            new_name = st.text_input("이름 / Name")
        with cd:
            new_role_sel = st.selectbox("역할 / Role", ROLES, index=1)
        submitted = st.form_submit_button(
            "➕ " + ("계정 추가" if not is_en else "Add Account"),
            type="primary",
            use_container_width=True,
        )
        if submitted:
            ok, msg = register(new_user, new_pw, new_role_sel, new_name)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    st.markdown("---")

    # ── Page access matrix ─────────────────────────────────────────────────
    with st.expander("📋 " + ("페이지 접근 권한 매트릭스" if not is_en else "Page Access Matrix"), expanded=False):
        page_names = {
            "01": "01 Project Setup",
            "02": "02 System Engineering",
            "03": "03 3D Simulation",
            "04": "04 EBOP Engineer",
            "05": "05 CBOP Engineer",
            "06": "06 Data Analyst",
            "07": "07 IPO Checklists",
            "08": "08 Tool Launcher",
            "09": "09 Container Thermal",
            "10": "10 Fire Spread",
            "11": "11 Cyber Security",
        }
        role_icons = {"admin": "🔴", "engineer": "🟡", "viewer": "🟢"}
        for pnum, pname in page_names.items():
            min_r = PAGE_MIN_ROLE.get(pnum, "admin")
            icon = role_icons.get(min_r, "⚪")
            st.markdown(f"{icon} **{pname}** — 최소: `{min_r}`" if not is_en else
                        f"{icon} **{pname}** — min: `{min_r}`")


run_login_page()
