# -*- coding: utf-8 -*-
"""
auth_helper.py
사용자 인증 및 역할 기반 접근 제어 (RBAC)
User authentication and role-based access control
"""
import hashlib
import json
import logging
import os
import secrets
from pathlib import Path
from filelock import FileLock
import streamlit as st

_log = logging.getLogger(__name__)

# ── User data file ─────────────────────────────────────────────────────────────
# Prefer /data (HF Spaces persistent storage), fallback to code directory
if os.path.isdir("/data"):
    _USERS_FILE = Path("/data/users.json")
    _LOCK_FILE  = Path("/data/users.json.lock")
else:
    _USERS_FILE = Path(__file__).parent / "users.json"
    _LOCK_FILE  = Path(__file__).parent / "users.json.lock"

# ── HuggingFace Hub sync (persistent user data across container restarts) ─────
_HF_REPO_ID = "openmen-gif/bess-user-data"   # private dataset repo
_HF_FILENAME = "users.json"
_HF_TOKEN = os.environ.get("BESS_HF_TOKEN", "") or os.environ.get("HF_TOKEN", "")

import threading as _threading

def _hf_download() -> None:
    """Download users.json from HF Hub (best-effort)."""
    if not _HF_TOKEN:
        _log.info("HF_TOKEN not set, skipping download")
        return
    try:
        from huggingface_hub import hf_hub_download
        _log.info("Downloading users.json from HF Hub repo=%s ...", _HF_REPO_ID)
        path = hf_hub_download(
            repo_id=_HF_REPO_ID,
            filename=_HF_FILENAME,
            repo_type="dataset",
            token=_HF_TOKEN,
            local_dir=str(_USERS_FILE.parent),
        )
        downloaded = Path(path)
        if downloaded.resolve() != _USERS_FILE.resolve():
            import shutil
            shutil.copy2(downloaded, _USERS_FILE)
        _log.info("Downloaded users.json → %s", _USERS_FILE)
    except Exception as e:
        _log.warning("HF download failed: %s", e)


def _hf_upload() -> None:
    """Upload users.json to HF Hub."""
    if not _HF_TOKEN:
        return
    if not _USERS_FILE.exists():
        _log.warning("users.json not found, skipping upload")
        return
    try:
        from huggingface_hub import HfApi
        api = HfApi(token=_HF_TOKEN)
        api.create_repo(
            repo_id=_HF_REPO_ID,
            repo_type="dataset",
            private=True,
            exist_ok=True,
        )
        api.upload_file(
            path_or_fileobj=str(_USERS_FILE),
            path_in_repo=_HF_FILENAME,
            repo_id=_HF_REPO_ID,
            repo_type="dataset",
        )
        _log.info("Uploaded users.json to HF Hub successfully")
    except Exception as e:
        _log.error("HF upload failed: %s", e)


# On startup: migrate users.json from code directory → /data/ if needed
_OLD_USERS_FILE = Path(__file__).parent / "users.json"
if os.path.isdir("/data") and _OLD_USERS_FILE.exists() and not _USERS_FILE.exists():
    import shutil
    shutil.copy2(_OLD_USERS_FILE, _USERS_FILE)

# On startup: log token info for debugging
_log.info("HF_TOKEN source: BESS_HF_TOKEN=%s, HF_TOKEN=%s, using=%s",
          "set" if os.environ.get("BESS_HF_TOKEN") else "empty",
          "set" if os.environ.get("HF_TOKEN") else "empty",
          f"{_HF_TOKEN[:8]}..." if len(_HF_TOKEN) > 8 else "(none)")

# On startup: restore from HF Hub **synchronously** (blocking)
# Must complete before app serves requests, otherwise users.json appears empty.
if _HF_TOKEN and not _USERS_FILE.exists():
    _hf_download()

# ── Token store for session persistence across refreshes ─────────────────────
_TOKEN_FILE = _USERS_FILE.parent / "tokens.json"
_TOKEN_LOCK = _USERS_FILE.parent / "tokens.json.lock"

def _load_token_store() -> dict:
    """Load server-side token→user mapping."""
    try:
        with FileLock(_TOKEN_LOCK, timeout=3):
            if _TOKEN_FILE.exists():
                with open(_TOKEN_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Prune old tokens (keep max 100)
                if len(data) > 100:
                    keys = list(data.keys())
                    for k in keys[:-50]:
                        del data[k]
                return data
    except Exception:
        pass
    return {}

def _save_token_store(store: dict) -> None:
    """Save server-side token→user mapping."""
    try:
        with FileLock(_TOKEN_LOCK, timeout=3):
            with open(_TOKEN_FILE, "w", encoding="utf-8") as f:
                json.dump(store, f, ensure_ascii=False, indent=2)
    except Exception as e:
        _log.warning("Token store save failed: %s", e)


# ── Role definitions ───────────────────────────────────────────────────────────
ROLES = ["admin", "engineer", "viewer"]
ROLE_RANK = {"admin": 3, "engineer": 2, "viewer": 1}

ROLE_LABEL = {
    "admin":    {"ko": "🔴 관리자", "en": "🔴 Admin"},
    "engineer": {"ko": "🟡 엔지니어", "en": "🟡 Engineer"},
    "viewer":   {"ko": "🟢 뷰어", "en": "🟢 Viewer"},
}

# ── Page access map: page_number → minimum role ────────────────────────────────
PAGE_MIN_ROLE: dict[str, str] = {
    "01": "viewer",
    "02": "viewer",
    "03": "viewer",
    "04": "viewer",
    "05": "viewer",
    "06": "viewer",
    "07": "engineer",
    "08": "engineer",
    "09": "engineer",
    "10": "engineer",
    "11": "engineer",
    "12": "engineer",
}


# ── Internal helpers ───────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    """Generate a PBKDF2-HMAC-SHA256 hash with a random 16-byte salt."""
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        100000
    ).hex()
    return f"pbkdf2:sha256:100000${salt}${hashed}"


def _verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored hash. Retains legacy SHA256 support for migration."""
    # Legacy SHA256 Check (64 hex characters)
    if len(stored_hash) == 64 and "$" not in stored_hash:
        return hashlib.sha256(password.encode("utf-8")).hexdigest() == stored_hash
    
    # Modern PBKDF2 Check
    try:
        parts = stored_hash.split("$")
        if len(parts) != 3:
            return False
        algo_info, salt, expected_hash = parts
        algo_name, hash_algo, iters = algo_info.split(":")
        
        computed = hashlib.pbkdf2_hmac(
            hash_algo,
            password.encode("utf-8"),
            bytes.fromhex(salt),
            int(iters)
        ).hex()
        return secrets.compare_digest(computed, expected_hash)
    except Exception:
        return False


def _load_users() -> dict:
    with FileLock(_LOCK_FILE, timeout=5):
        if _USERS_FILE.exists():
            with open(_USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        # First run: create default admin account
        default = {
            "admin": {
                "password": _hash_password("djflsdk79"),
                "role": "admin",
                "name": "관리자",
            }
        }
        with open(_USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default


def _save_users(users: dict) -> None:
    tmp_file = _USERS_FILE.with_suffix('.json.tmp')
    with FileLock(_LOCK_FILE, timeout=5):
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_file, _USERS_FILE)
    # Sync to HF Hub — use non-daemon thread and wait up to 30s
    t = _threading.Thread(target=_hf_upload)
    t.start()
    t.join(timeout=30)


# ── Public auth functions ──────────────────────────────────────────────────────

def login(username: str, password: str) -> bool:
    users = _load_users()
    user = users.get(username.strip())
    if user and _verify_password(password, user["password"]):
        # Auto-migration hook for legacy SHA256 users
        if len(user["password"]) == 64 and "$" not in user["password"]:
            user["password"] = _hash_password(password)
            _save_users(users)
        
        st.session_state["auth_user"] = username.strip()
        st.session_state["auth_role"] = user["role"]
        st.session_state["auth_name"] = user.get("name", username.strip())
        return True
    return False


def logout() -> None:
    for k in ["auth_user", "auth_role", "auth_name"]:
        st.session_state.pop(k, None)
    # Clear persistent cookie
    try:
        from streamlit_cookies_controller import CookieController as _CC
        _CC().remove("bess_auth_v1")
    except Exception:
        pass


def register(username: str, password: str, role: str, name: str) -> tuple[bool, str]:
    username = username.strip()
    if not username or not password:
        return False, "아이디와 비밀번호를 입력해주세요. / Username and password required."
    if role not in ROLES:
        return False, "유효하지 않은 역할입니다. / Invalid role."
    users = _load_users()
    if username in users:
        return False, f"'{username}' 계정이 이미 존재합니다. / Account already exists."
    users[username] = {
        "password": _hash_password(password),
        "role": role,
        "name": name.strip() or username,
    }
    _save_users(users)
    return True, f"'{username}' 계정이 등록되었습니다. / Account registered."


# Accounts protected from UI modification/deletion (developer-only)
PROTECTED_USERS: set[str] = {"admin"}


def delete_user(username: str) -> tuple[bool, str]:
    if username == st.session_state.get("auth_user"):
        return False, "자신의 계정은 삭제할 수 없습니다. / Cannot delete your own account."
    if username in PROTECTED_USERS:
        return False, f"'{username}' 계정은 개발자 보호 계정입니다. / Protected account — developer only."
    users = _load_users()
    if username not in users:
        return False, "존재하지 않는 계정입니다. / Account not found."
    del users[username]
    _save_users(users)
    return True, f"'{username}' 계정이 삭제되었습니다. / Account deleted."


def update_user(username: str, new_role: str = None, new_name: str = None,
                new_password: str = None) -> tuple[bool, str]:
    # Protected users: block role/name changes from UI (password change allowed for self)
    caller = st.session_state.get("auth_user", "")
    if username in PROTECTED_USERS and caller != username and (new_role or new_name):
        return False, f"'{username}' 계정은 개발자 보호 계정입니다. / Protected account — developer only."
    users = _load_users()
    if username not in users:
        return False, "존재하지 않는 계정입니다. / Account not found."
    if new_role:
        users[username]["role"] = new_role
    if new_name:
        users[username]["name"] = new_name.strip()
    if new_password:
        users[username]["password"] = _hash_password(new_password)
    _save_users(users)
    return True, f"'{username}' 정보가 업데이트되었습니다. / Account updated."


def change_password(username: str, old_pw: str, new_pw: str) -> tuple[bool, str]:
    """Self-service password change — verifies old password first."""
    if not new_pw or len(new_pw) < 4:
        return False, "새 비밀번호는 4자 이상이어야 합니다. / New password must be ≥ 4 characters."
    users = _load_users()
    user = users.get(username)
    if not user:
        return False, "존재하지 않는 계정입니다. / Account not found."
    if not _verify_password(old_pw, user["password"]):
        return False, "현재 비밀번호가 올바르지 않습니다. / Current password is incorrect."
    users[username]["password"] = _hash_password(new_pw)
    _save_users(users)
    return True, "비밀번호가 변경되었습니다. / Password changed successfully."


def get_all_users() -> dict:
    return _load_users()


# ── Session state queries ──────────────────────────────────────────────────────

def is_authenticated() -> bool:
    return "auth_user" in st.session_state


def current_role() -> str:
    return st.session_state.get("auth_role", "viewer")


def has_access(page_num: str) -> bool:
    min_role = PAGE_MIN_ROLE.get(page_num, "admin")
    return ROLE_RANK.get(current_role(), 0) >= ROLE_RANK.get(min_role, 99)


# ── Gate function ──────────────────────────────────────────────────────────────

def require_auth(page_num: str = None) -> None:
    """
    Call at the top of every page function.
    - If not logged in → show login link and stop.
    - If page_num given and role too low → show access denied and stop.
    """
    if not is_authenticated():
        st.warning("🔒 로그인이 필요합니다. / Login required.")
        st.page_link("pages/00_Login.py", label="🔑 로그인 / Login")
        st.stop()
    if page_num and not has_access(page_num):
        role = current_role()
        lang = st.session_state.get("lang", "KO")
        role_label = ROLE_LABEL.get(role, {}).get("ko" if lang == "KO" else "en", role)
        min_role = PAGE_MIN_ROLE.get(page_num, "admin")
        min_label = ROLE_LABEL.get(min_role, {}).get("ko" if lang == "KO" else "en", min_role)
        st.error(
            f"**접근 권한 없음** — 이 페이지는 **{min_label}** 이상 필요합니다. "
            f"현재 역할: **{role_label}**\n\n"
            f"**Access Denied** — This page requires **{min_label}** or higher. "
            f"Current role: **{role_label}**"
        )
        st.stop()


# ── Per-run sidebar deduplication flag (reset by Dashboard.py each rerun)
_sidebar_shown: bool = False


# ── Sidebar widget ─────────────────────────────────────────────────────────────

def sidebar_user_info() -> None:
    """Render user badge + logout button in the sidebar. Safe to call multiple times."""
    global _sidebar_shown
    if _sidebar_shown or not is_authenticated():
        return
    _sidebar_shown = True
    lang = st.session_state.get("lang", "KO")
    role = current_role()
    name = st.session_state.get("auth_name", st.session_state.get("auth_user", ""))
    role_label = ROLE_LABEL.get(role, {}).get("ko" if lang == "KO" else "en", role)
    st.sidebar.markdown(f"👤 **{name}** &nbsp; `{role_label}`")
    if st.sidebar.button(
        "🚪 로그아웃" if lang == "KO" else "🚪 Logout",
        key="_global_logout_btn",
    ):
        logout()
        st.rerun()
    st.sidebar.markdown("---")
