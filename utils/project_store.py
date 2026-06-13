# -*- coding: utf-8 -*-
"""
utils/project_store.py
프로젝트 데이터 저장/로드 (JSON 파일 기반, Docker /tmp 또는 로컬 경로)
HuggingFace Hub 동기화로 컨테이너 재시작 시에도 데이터 유지
"""
import json
import logging
import os
import threading as _threading
from pathlib import Path
from datetime import datetime
from filelock import FileLock

_log = logging.getLogger(__name__)

# Prefer /data (HF Spaces persistent storage), fallback to /tmp
_DEFAULT_STORE = "/data/bess_projects.json" if os.path.isdir("/data") else "/tmp/bess_projects.json"
_STORE_PATH = Path(os.environ.get("PROJECT_STORE_PATH", _DEFAULT_STORE))
# Cross-process write lock — multiple logged-in users share one JSON file,
# so guard read-modify-write so concurrent saves don't clobber each other.
_STORE_LOCK = Path(str(_STORE_PATH) + ".lock")

# ── HuggingFace Hub sync (persistent project data across container restarts) ──
_HF_REPO_ID = "openmen-gif/bess-user-data"
_HF_PROJ_FILENAME = "bess_projects.json"
_HF_TOKEN = os.environ.get("BESS_HF_TOKEN", "") or os.environ.get("HF_TOKEN", "")

# 마지막 동기화 결과 (진단 패널 표시용) — 실패 원인을 삼키지 않고 노출한다.
_LAST_DOWNLOAD_ERR = ""
_LAST_UPLOAD_ERR = ""


def _hf_download_projects() -> None:
    """Download bess_projects.json from HF Hub (best-effort)."""
    global _LAST_DOWNLOAD_ERR
    if not _HF_TOKEN:
        _log.info("HF_TOKEN not set, skipping project download")
        return
    try:
        from huggingface_hub import hf_hub_download
        _log.info("Downloading bess_projects.json from HF Hub repo=%s ...", _HF_REPO_ID)
        path = hf_hub_download(
            repo_id=_HF_REPO_ID,
            filename=_HF_PROJ_FILENAME,
            repo_type="dataset",
            token=_HF_TOKEN,
            local_dir=str(_STORE_PATH.parent),
        )
        downloaded = Path(path)
        if downloaded.resolve() != _STORE_PATH.resolve():
            import shutil
            shutil.copy2(downloaded, _STORE_PATH)
        _log.info("Downloaded bess_projects.json → %s", _STORE_PATH)
        _LAST_DOWNLOAD_ERR = ""
    except Exception as e:
        _LAST_DOWNLOAD_ERR = f"{type(e).__name__}: {e}"
        _log.warning("HF project download failed: %s", e)


def _hf_upload_projects() -> None:
    """Upload bess_projects.json to HF Hub."""
    global _LAST_UPLOAD_ERR
    if not _HF_TOKEN or not _STORE_PATH.exists():
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
            path_or_fileobj=str(_STORE_PATH),
            path_in_repo=_HF_PROJ_FILENAME,
            repo_id=_HF_REPO_ID,
            repo_type="dataset",
        )
        _log.info("Uploaded bess_projects.json to HF Hub successfully")
        _LAST_UPLOAD_ERR = ""
    except Exception as e:
        _LAST_UPLOAD_ERR = f"{type(e).__name__}: {e}"
        _log.error("HF project upload failed: %s", e)


# On startup: restore from HF Hub **synchronously** (blocking)
# Must complete before app serves requests, otherwise data appears empty.
if _HF_TOKEN and not _STORE_PATH.exists():
    _hf_download_projects()


def sync_status() -> dict:
    """영속성/동기화 상태 진단 (관리자 화면 표시용).
    토큰이 없으면 재배포 시 데이터가 사라진다 — 이를 즉시 식별하기 위함."""
    count = -1
    try:
        if _STORE_PATH.exists():
            with open(_STORE_PATH, "r", encoding="utf-8") as f:
                count = len(json.load(f))
    except Exception:
        count = -1
    return {
        "hf_token_set": bool(_HF_TOKEN),
        "hf_repo": _HF_REPO_ID,
        "store_path": str(_STORE_PATH),
        "store_exists": _STORE_PATH.exists(),
        "store_count": count,
        "data_dir_mounted": os.path.isdir("/data"),
        "last_download_err": _LAST_DOWNLOAD_ERR,
        "last_upload_err": _LAST_UPLOAD_ERR,
    }


def hf_backup_now() -> bool:
    """현재 프로젝트 파일을 HF Hub로 즉시 업로드 (관리자 수동 백업)."""
    if not _HF_TOKEN:
        return False
    _hf_upload_projects()
    return True


def hf_restore_now() -> bool:
    """HF Hub에서 프로젝트 파일을 즉시 내려받아 로컬을 덮어씀 (관리자 수동 복원)."""
    if not _HF_TOKEN:
        return False
    _hf_download_projects()
    return _STORE_PATH.exists()

# ── 기본 공정 단계 템플릿 ──────────────────────────────────────────────────────
DEFAULT_PHASES = [
    {"name": "설계",   "name_en": "Design",       "progress": 0, "status": "대기", "start_date": "", "end_date": ""},
    {"name": "조달",   "name_en": "Procurement",   "progress": 0, "status": "대기", "start_date": "", "end_date": ""},
    {"name": "시공",   "name_en": "Construction",  "progress": 0, "status": "대기", "start_date": "", "end_date": ""},
    {"name": "시운전", "name_en": "Commissioning", "progress": 0, "status": "대기", "start_date": "", "end_date": ""},
]

STATUS_OPTIONS    = ["계획중", "진행중", "완료", "보류"]
STATUS_OPTIONS_EN = ["Planned", "In Progress", "Completed", "On Hold"]
PHASE_STATUS      = ["대기", "진행중", "완료"]
PHASE_STATUS_EN   = ["Pending", "In Progress", "Completed"]


def _sanitize_projects(projects: list) -> list:
    """Ensure all progress values are int and dates are str."""
    for p in projects:
        for ph in p.get("phases", []):
            try:
                ph["progress"] = int(ph.get("progress", 0))
            except (ValueError, TypeError):
                ph["progress"] = 0
            if not isinstance(ph.get("start_date"), str):
                ph["start_date"] = str(ph.get("start_date", ""))
            if not isinstance(ph.get("end_date"), str):
                ph["end_date"] = str(ph.get("end_date", ""))
        if not isinstance(p.get("start_date"), str):
            p["start_date"] = str(p.get("start_date", ""))
        if not isinstance(p.get("end_date"), str):
            p["end_date"] = str(p.get("end_date", ""))
    return projects


def _load_raw() -> list:
    try:
        if _STORE_PATH.exists():
            with open(_STORE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return _sanitize_projects(data)
    except Exception:
        pass
    return []


def _save_raw(data: list) -> None:
    try:
        _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_STORE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    # Sync to HF Hub — use non-daemon thread and wait up to 30s
    t = _threading.Thread(target=_hf_upload_projects)
    t.start()
    t.join(timeout=30)


def _can_access(p: dict, owner: str | None, include_all: bool) -> bool:
    """소유권 검사: include_all(관리자) → 항상 True, 아니면 owner 일치 시 True.
    owner 필드가 없는 레거시 프로젝트는 include_all(관리자)에게만 보인다."""
    if include_all:
        return True
    return p.get("owner") == owner


def load_projects(owner: str | None = None, include_all: bool = False) -> list:
    """프로젝트 목록 반환.
    - include_all=True  : 전체 반환 (관리자).
    - owner 지정          : 해당 owner 프로젝트만 반환. owner 없는 레거시는 제외.
    - 둘 다 미지정         : 전체 반환 (하위 호환).
    """
    # 자가복구: 로컬 파일이 없고 토큰이 있으면 부팅 시 복원이 실패했을 수 있으므로
    # 첫 로드 때 HF에서 한 번 더 내려받기를 시도한다.
    if _HF_TOKEN and not _STORE_PATH.exists():
        _hf_download_projects()
    projects = _load_raw()
    if include_all or owner is None:
        return projects
    return [p for p in projects if p.get("owner") == owner]


def save_projects(projects: list) -> None:
    """전체 프로젝트 목록 저장."""
    with FileLock(str(_STORE_LOCK), timeout=10):
        _save_raw(projects)


def add_project(proj: dict, owner: str | None = None) -> None:
    with FileLock(str(_STORE_LOCK), timeout=10):
        projects = _load_raw()
        proj["id"] = datetime.now().strftime("%Y%m%d%H%M%S%f")
        proj["created_at"] = datetime.now().isoformat()
        if owner:
            proj["owner"] = owner
        projects.append(proj)
        _save_raw(projects)


def update_project(proj_id: str, updated: dict,
                   owner: str | None = None, include_all: bool = False) -> bool:
    with FileLock(str(_STORE_LOCK), timeout=10):
        projects = _load_raw()
        for i, p in enumerate(projects):
            if p.get("id") == proj_id:
                if not _can_access(p, owner, include_all):
                    return False
                projects[i].update(updated)
                projects[i]["updated_at"] = datetime.now().isoformat()
                _save_raw(projects)
                return True
    return False


def delete_project(proj_id: str,
                   owner: str | None = None, include_all: bool = False) -> bool:
    with FileLock(str(_STORE_LOCK), timeout=10):
        projects = _load_raw()
        target = next((p for p in projects if p.get("id") == proj_id), None)
        if not target or not _can_access(target, owner, include_all):
            return False
        projects = [p for p in projects if p.get("id") != proj_id]
        _save_raw(projects)
        return True


def get_project(proj_id: str) -> dict | None:
    for p in _load_raw():
        if p.get("id") == proj_id:
            return p
    return None


# ── 집계 헬퍼 ─────────────────────────────────────────────────────────────────

def get_kpi(projects: list | None = None) -> dict:
    """대시보드 KPI 집계: 진행중·완료·계획중·전체 공정 완료율."""
    if projects is None:
        projects = _load_raw()

    total     = len(projects)
    active    = sum(1 for p in projects if p.get("status") == "진행중")
    completed = sum(1 for p in projects if p.get("status") == "완료")
    planned   = sum(1 for p in projects if p.get("status") == "계획중")

    # 전체 공정 평균 완료율
    all_prog = []
    for p in projects:
        for ph in p.get("phases", []):
            all_prog.append(ph.get("progress", 0))
    avg_prog = round(sum(all_prog) / len(all_prog)) if all_prog else 0

    # 단계별 평균 (설계/조달/시공/시운전)
    phase_names = ["설계", "조달", "시공", "시운전"]
    phase_avg = {}
    for pname in phase_names:
        vals = []
        for p in projects:
            for ph in p.get("phases", []):
                if ph.get("name") == pname:
                    vals.append(ph.get("progress", 0))
        phase_avg[pname] = round(sum(vals) / len(vals)) if vals else 0

    return {
        "total": total,
        "active": active,
        "completed": completed,
        "planned": planned,
        "avg_progress": avg_prog,
        "phase_avg": phase_avg,
    }


def new_project_template() -> dict:
    return {
        "name": "",
        "name_en": "",
        "capacity_mw": 0.0,
        "capacity_mwh": 0.0,
        "region": "한국",
        "client": "",
        "status": "계획중",
        "start_date": "",
        "end_date": "",
        "notes": "",
        "phases": [dict(ph) for ph in DEFAULT_PHASES],
    }
