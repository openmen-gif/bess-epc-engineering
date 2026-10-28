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
        # 데이터셋은 이미 존재 — create_repo는 best-effort (fine-grained 토큰 403 대비)
        try:
            api.create_repo(
                repo_id=_HF_REPO_ID,
                repo_type="dataset",
                private=True,
                exist_ok=True,
            )
        except Exception as ce:
            _log.info("create_repo skipped (likely existing/no-create-perm): %s", ce)
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

# ── Token-cookie session persistence ──────────────────────────────────────────
# 예전 방식(IP+User-Agent 지문)은 같은 공유기·같은 브라우저면 남의 세션이 복원되는
# 결함이 있었다. 지금은 로그인 때 무작위 토큰을 발급해 쿠키에 담고, 서버에는 토큰의
# SHA-256 만 저장한다. 지문은 가입 속도 제한(_check_register_rate)에만 쓴다.
_SESSION_FILE = _USERS_FILE.parent / "sessions.json"
_SESSION_LOCK = _USERS_FILE.parent / "sessions.json.lock"
_SESSION_COOKIE = "bess_session"
_SESSION_TTL_SECONDS = 86400
_SESSION_MAX = 200
import time as _time


def _client_fingerprint() -> str:
    """Create a fingerprint from request headers (IP + User-Agent). Rate limiting only."""
    try:
        headers = st.context.headers
        ip = headers.get("X-Forwarded-For", headers.get("X-Real-Ip", "unknown"))
        ua = headers.get("User-Agent", "unknown")
        raw = f"{ip}|{ua}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]
    except Exception:
        return ""


def _load_sessions() -> dict:
    try:
        with FileLock(_SESSION_LOCK, timeout=3):
            if _SESSION_FILE.exists():
                with open(_SESSION_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
    except Exception:
        pass
    return {}


def _mutate_sessions(fn) -> bool:
    """세션 저장소 read-modify-write 를 잠금 한 번 안에서 원자적으로 수행 (tmp + os.replace).
    읽기 실패를 빈 저장소로 오인해 덮어쓰지 않도록 예외는 그대로 실패로 보고한다."""
    try:
        with FileLock(_SESSION_LOCK, timeout=3):
            store = {}
            if _SESSION_FILE.exists():
                with open(_SESSION_FILE, "r", encoding="utf-8") as f:
                    store = json.load(f)
            if not isinstance(store, dict):
                store = {}
            fn(store)
            tmp = _SESSION_FILE.with_suffix(".json.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(store, f, ensure_ascii=False, indent=2)
            os.replace(tmp, _SESSION_FILE)
        return True
    except Exception as e:
        _log.error("Session store update failed: %s", e)
        return False


def _token_key(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _cookie_token() -> str:
    try:
        return st.context.cookies.get(_SESSION_COOKIE, "") or ""
    except Exception:
        return ""


def _issue_session_token(username: str) -> None:
    """로그인 성공 시 토큰 발급 — 서버엔 해시만, 쿠키 기록은 다음 렌더에서 emit_session_cookie()."""
    token = secrets.token_urlsafe(32)
    now = _time.time()

    def _add(store: dict) -> None:
        # 만료분 정리 + 상한 유지 (가장 오래된 것부터)
        for k in [k for k, v in store.items()
                  if not isinstance(v, dict) or now - v.get("ts", 0) > _SESSION_TTL_SECONDS]:
            del store[k]
        if len(store) >= _SESSION_MAX:
            for k in sorted(store, key=lambda k: store[k].get("ts", 0))[: len(store) - _SESSION_MAX + 1]:
                del store[k]
        store[_token_key(token)] = {"u": username, "ts": now}

    if not _mutate_sessions(_add):
        return  # 저장 실패 시 쿠키를 심지 않는다 (이번 탭 로그인은 유지, 새로고침 복원만 불가)
    st.session_state["_auth_token"] = token
    st.session_state["_auth_cookie_op"] = "set"


def emit_session_cookie() -> None:
    """대기 중인 쿠키 기록/삭제를 브라우저에 반영 (높이 0 컴포넌트, 실행당 1회)."""
    op = st.session_state.pop("_auth_cookie_op", None)
    if not op:
        return
    if op == "set":
        token = st.session_state.get("_auth_token", "")
        if not token:
            return
        cookie = f"{_SESSION_COOKIE}={token}; path=/; max-age={_SESSION_TTL_SECONDS}; SameSite=Lax; Secure"
    else:
        cookie = f"{_SESSION_COOKIE}=; path=/; max-age=0; SameSite=Lax; Secure"
    import streamlit.components.v1 as _components
    # 토큰은 token_urlsafe(영숫자·-·_)라 JS 문자열에 그대로 넣어도 안전하다
    _components.html(
        "<script>try{window.parent.document.cookie=%s}catch(e){document.cookie=%s}</script>"
        % (json.dumps(cookie), json.dumps(cookie)),
        height=0,
    )


def restore_session() -> bool:
    """쿠키 토큰으로 서버 세션 복원. 역할·이름은 저장 시점이 아니라 현재 users.json 기준."""
    token = _cookie_token()
    if not token:
        return False
    key = _token_key(token)
    store = _load_sessions()
    session = store.get(key)
    if not isinstance(session, dict):
        return False
    if _time.time() - session.get("ts", 0) > _SESSION_TTL_SECONDS:
        _mutate_sessions(lambda s: s.pop(key, None))
        return False
    users = _load_users()
    user = users.get(session.get("u", ""))
    if not user:
        _mutate_sessions(lambda s: s.pop(key, None))
        return False
    st.session_state["auth_user"] = session["u"]
    st.session_state["auth_role"] = user.get("role", "viewer")
    st.session_state["auth_name"] = user.get("name", session["u"])
    st.session_state["_auth_token"] = token
    _log.info("Session restored for user=%s via token cookie", session["u"])
    return True


def _revoke_session_token() -> bool:
    tokens = {st.session_state.get("_auth_token", ""), _cookie_token()} - {""}
    if not tokens:
        return True

    def _drop(store: dict) -> None:
        for tok in tokens:
            store.pop(_token_key(tok), None)

    return _mutate_sessions(_drop)


def revoke_user_sessions(username: str) -> bool:
    """해당 사용자의 모든 서버 세션 폐기 — 비밀번호·역할 변경, 계정 삭제 시 호출."""
    def _drop(store: dict) -> None:
        for k in [k for k, v in store.items() if isinstance(v, dict) and v.get("u") == username]:
            del store[k]

    return _mutate_sessions(_drop)


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

# OWASP 2023 권고(PBKDF2-HMAC-SHA256 600,000회). 이보다 낮은 저장값은 로그인 때 재해시된다.
_PBKDF2_ITERATIONS = 600_000


def _hash_password(password: str) -> str:
    """Generate a PBKDF2-HMAC-SHA256 hash with a random 16-byte salt."""
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        _PBKDF2_ITERATIONS
    ).hex()
    return f"pbkdf2:sha256:{_PBKDF2_ITERATIONS}${salt}${hashed}"


def _needs_rehash(stored_hash: str) -> bool:
    """레거시 SHA-256 이거나 반복 횟수가 현재 기준 미만이면 True."""
    if "$" not in stored_hash:
        return True
    try:
        return int(stored_hash.split("$", 1)[0].split(":")[2]) < _PBKDF2_ITERATIONS
    except (IndexError, ValueError):
        return True


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
        # First run: create default admin account — 초기 비밀번호는 환경변수로만 받는다
        # (소스에 박혀 있던 기본값은 공개 저장소로 노출돼 2026-10-28 제거).
        init_pw = os.environ.get("BESS_ADMIN_INIT_PASSWORD", "")
        if not init_pw:
            _log.warning("users.json 없음 + BESS_ADMIN_INIT_PASSWORD 미설정 — "
                         "기본 관리자 계정을 만들지 않는다")
            return {}
        default = {
            "admin": {
                "password": _hash_password(init_pw),
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

_LOGIN_ATTEMPTS: dict[str, list[float]] = {}  # username → list of failed timestamps
_LOGIN_MAX_ATTEMPTS = 5
_LOGIN_LOCKOUT_SECONDS = 300   # 5 minutes


def login(username: str, password: str) -> bool:
    username_key = username.strip().lower()
    now = _time.time()
    # Check lockout
    attempts = _LOGIN_ATTEMPTS.get(username_key, [])
    attempts = [t for t in attempts if now - t < _LOGIN_LOCKOUT_SECONDS]
    _LOGIN_ATTEMPTS[username_key] = attempts
    if len(attempts) >= _LOGIN_MAX_ATTEMPTS:
        _log.warning("Login locked out for user=%s (%d attempts)", username_key, len(attempts))
        return False

    users = _load_users()
    user = users.get(username.strip())
    if user and _verify_password(password, user["password"]):
        # Auto-migration hook: legacy SHA256 or PBKDF2 below current iterations
        if _needs_rehash(user["password"]):
            user["password"] = _hash_password(password)
            _save_users(users)

        st.session_state["auth_user"] = username.strip()
        st.session_state["auth_role"] = user["role"]
        st.session_state["auth_name"] = user.get("name", username.strip())
        _LOGIN_ATTEMPTS.pop(username_key, None)  # Clear on success
        _issue_session_token(username.strip())
        return True
    # Record failed attempt
    _LOGIN_ATTEMPTS.setdefault(username_key, []).append(now)
    return False


def logout() -> None:
    # 서버 세션 폐기가 기준 — 쿠키 삭제는 다음 렌더의 emit_session_cookie() 가 보조로 수행
    if not _revoke_session_token():
        _log.error("Logout: server session revoke failed — cookie will still be cleared")
    for k in ["auth_user", "auth_role", "auth_name", "_auth_token"]:
        st.session_state.pop(k, None)
    st.session_state["_auth_cookie_op"] = "clear"


import re as _re

_REGISTER_ATTEMPTS: dict[str, list[float]] = {}  # IP → list of timestamps
_REGISTER_RATE_LIMIT = 5       # max registrations
_REGISTER_RATE_WINDOW = 3600   # per hour (seconds)


def _check_register_rate() -> bool:
    """Rate limit registration attempts per client fingerprint."""
    fp = _client_fingerprint() or "unknown"
    now = _time.time()
    attempts = _REGISTER_ATTEMPTS.get(fp, [])
    attempts = [t for t in attempts if now - t < _REGISTER_RATE_WINDOW]
    _REGISTER_ATTEMPTS[fp] = attempts
    return len(attempts) < _REGISTER_RATE_LIMIT


def _validate_password_strength(password: str) -> tuple[bool, str]:
    """Enforce minimum password policy: 8+ chars, at least 1 letter + 1 digit."""
    if len(password) < 8:
        return False, "비밀번호는 8자 이상이어야 합니다. / Password must be ≥ 8 characters."
    if not _re.search(r'[A-Za-z]', password):
        return False, "비밀번호에 영문자가 포함되어야 합니다. / Password must contain a letter."
    if not _re.search(r'[0-9]', password):
        return False, "비밀번호에 숫자가 포함되어야 합니다. / Password must contain a digit."
    return True, ""


def _validate_username(username: str) -> tuple[bool, str]:
    """Validate username format: 2-30 chars, alphanumeric + underscore/hyphen only."""
    if len(username) < 2 or len(username) > 30:
        return False, "아이디는 2~30자여야 합니다. / Username must be 2-30 characters."
    if not _re.match(r'^[A-Za-z0-9_-]+$', username):
        return False, "아이디는 영문, 숫자, _, - 만 사용 가능합니다. / Username: letters, digits, _, - only."
    return True, ""


def register(username: str, password: str, role: str, name: str) -> tuple[bool, str]:
    username = username.strip()
    if not username or not password:
        return False, "아이디와 비밀번호를 입력해주세요. / Username and password required."
    # Rate limit check
    if not _check_register_rate():
        return False, "등록 요청이 너무 많습니다. 잠시 후 다시 시도해주세요. / Too many registrations. Try again later."
    # Username validation
    ok, msg = _validate_username(username)
    if not ok:
        return False, msg
    # Password strength check
    ok, msg = _validate_password_strength(password)
    if not ok:
        return False, msg
    if role not in ROLES:
        return False, "유효하지 않은 역할입니다. / Invalid role."
    # 관리자 역할은 관리자만 부여 (UI 제한과 별개로 서버에서도 강제)
    if role == "admin" and current_role() != "admin":
        return False, "관리자 역할은 관리자만 부여할 수 있습니다. / Only admins can assign the admin role."
    users = _load_users()
    if username in users:
        return False, f"'{username}' 계정이 이미 존재합니다. / Account already exists."
    # Record registration attempt
    fp = _client_fingerprint() or "unknown"
    _REGISTER_ATTEMPTS.setdefault(fp, []).append(_time.time())
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
    revoke_user_sessions(username)
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
    if new_role or new_password:
        revoke_user_sessions(username)  # 탈취 토큰·옛 권한 세션 무효화
    return True, f"'{username}' 정보가 업데이트되었습니다. / Account updated."


def change_password(username: str, old_pw: str, new_pw: str) -> tuple[bool, str]:
    """Self-service password change — verifies old password first."""
    ok, msg = _validate_password_strength(new_pw)
    if not ok:
        return False, msg
    users = _load_users()
    user = users.get(username)
    if not user:
        return False, "존재하지 않는 계정입니다. / Account not found."
    if not _verify_password(old_pw, user["password"]):
        return False, "현재 비밀번호가 올바르지 않습니다. / Current password is incorrect."
    users[username]["password"] = _hash_password(new_pw)
    _save_users(users)
    # 다른 기기의 세션(탈취 토큰 포함)을 모두 끊고, 지금 탭에는 새 토큰을 다시 발급
    revoke_user_sessions(username)
    if st.session_state.get("auth_user") == username:
        _issue_session_token(username)
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
    if not is_authenticated() and not st.session_state.get("_auth_cookie_op"):
        restore_session()  # 하위 페이지에서 새로고침해도 쿠키로 복원 (로그아웃 직후엔 건너뜀)
    if not is_authenticated():
        emit_session_cookie()  # 로그아웃 직후 이 페이지에서 멈추므로 쿠키 삭제를 여기서 반영
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
    emit_session_cookie()  # 로그인 직후·로그아웃 직후 쿠키 반영 (모든 페이지가 이 함수를 부른다)
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
