# -*- coding: utf-8 -*-
"""
utils/project_store.py
프로젝트 데이터 저장/로드 (JSON 파일 기반, Docker /tmp 또는 로컬 경로)
"""
import json
import os
from pathlib import Path
from datetime import datetime

_STORE_PATH = Path(os.environ.get("PROJECT_STORE_PATH", "/tmp/bess_projects.json"))

# ── 기본 공정 단계 템플릿 ──────────────────────────────────────────────────────
DEFAULT_PHASES = [
    {"name": "설계",   "name_en": "Design",       "progress": 0, "status": "대기"},
    {"name": "조달",   "name_en": "Procurement",   "progress": 0, "status": "대기"},
    {"name": "시공",   "name_en": "Construction",  "progress": 0, "status": "대기"},
    {"name": "시운전", "name_en": "Commissioning", "progress": 0, "status": "대기"},
]

STATUS_OPTIONS    = ["계획중", "진행중", "완료", "보류"]
STATUS_OPTIONS_EN = ["Planned", "In Progress", "Completed", "On Hold"]
PHASE_STATUS      = ["대기", "진행중", "완료"]
PHASE_STATUS_EN   = ["Pending", "In Progress", "Completed"]


def _load_raw() -> list:
    try:
        if _STORE_PATH.exists():
            with open(_STORE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
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


def load_projects() -> list:
    """전체 프로젝트 목록 반환."""
    return _load_raw()


def save_projects(projects: list) -> None:
    """전체 프로젝트 목록 저장."""
    _save_raw(projects)


def add_project(proj: dict) -> None:
    projects = _load_raw()
    proj["id"] = datetime.now().strftime("%Y%m%d%H%M%S%f")
    proj["created_at"] = datetime.now().isoformat()
    projects.append(proj)
    _save_raw(projects)


def update_project(proj_id: str, updated: dict) -> bool:
    projects = _load_raw()
    for i, p in enumerate(projects):
        if p.get("id") == proj_id:
            projects[i].update(updated)
            projects[i]["updated_at"] = datetime.now().isoformat()
            _save_raw(projects)
            return True
    return False


def delete_project(proj_id: str) -> bool:
    projects = _load_raw()
    before = len(projects)
    projects = [p for p in projects if p.get("id") != proj_id]
    if len(projects) < before:
        _save_raw(projects)
        return True
    return False


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
