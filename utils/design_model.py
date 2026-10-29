# -*- coding: utf-8 -*-
"""
design_model.py — 설계 페이지(02·04·05) 계산 결과의 단일 출처.

각 페이지가 계산 결과를 record() 로 남기면 13 3D 부지 배치·03·09 시뮬레이션이 같은 값을 받아 쓴다.
기록 시점의 상류 입력(01 용량·시장 등)을 서명으로 함께 저장해, 상류가 바뀐 뒤 재계산하지 않은
결과는 status() 가 "stale" 로 알린다. (2026-10-29 신설)

ss 인자는 기본 st.session_state — 테스트는 일반 dict 를 넘긴다.
"""
import json
import math
from datetime import datetime

DM_KEY = "design_model"
SCHEMA = "bess-design-model/1"

# 01 프로젝트 입력 + 02 단위 용량 — JSON 왕복 대상
PROJECT_KEYS = (
    "proj_name", "target_market", "capacity_mw", "duration_h", "battery_type", "grid_voltage",
    "site_temp_max", "site_temp_min", "rte_percent", "aux_loss_percent", "epc_margin",
    "pcs_unit_mw", "batt_unit_mwh", "dm_cable_length_m",
)

# 문자열 값 키 — 그 밖의 기록값은 전부 유한한 숫자여야 한다 (import_json 검증)
_TEXT_KEYS = {"proj_name", "target_market", "battery_type", "grid_voltage", "hv", "lv", "cable_circuit",
              "fire_agent", "n_enc_basis"}

# 섹션별 상류 입력 — 이 값들이 기록 시점과 달라지면 stale
SECTION_DEPS = {
    "system": ("capacity_mw", "duration_h", "rte_percent", "aux_loss_percent", "epc_margin"),
    "ebop":   ("capacity_mw", "aux_loss_percent", "target_market", "grid_voltage", "dm_cable_length_m"),
    "cbop":   ("capacity_mw", "duration_h", "num_containers", "batt_unit_mwh", "site_temp_max"),
}


def _ss(ss):
    if ss is None:
        import streamlit as st
        return st.session_state
    return ss


def _sig(section, ss):
    return {k: ss.get(k) for k in SECTION_DEPS.get(section, ())}


def record(section: str, values: dict, ss=None) -> None:
    """페이지 계산 결과를 기록. 값은 JSON 직렬화 가능한 스칼라로 넘긴다."""
    ss = _ss(ss)
    model = dict(ss.get(DM_KEY) or {})
    model[section] = {
        "values": {k: (float(v) if hasattr(v, "item") else v) for k, v in values.items()},
        "sig": _sig(section, ss),
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    ss[DM_KEY] = model


def get(section: str, ss=None):
    ent = (_ss(ss).get(DM_KEY) or {}).get(section)
    return ent["values"] if ent else None


def status(section: str, ss=None) -> str:
    """'ok' | 'stale' | 'missing'"""
    ss = _ss(ss)
    ent = (ss.get(DM_KEY) or {}).get(section)
    if not ent:
        return "missing"
    return "ok" if ent.get("sig") == _sig(section, ss) else "stale"


# ── 3D 배치 입력 조립 — 값마다 출처를 붙인다 ────────────────────────────────────
def layout_inputs(ss=None) -> dict:
    """{name: (value, source)} — source: 'p02'·'p04'·'p05'·'p01' 또는 '[가정]'"""
    ss = _ss(ss)
    sysv, ebv, cbv = get("system", ss), get("ebop", ss), get("cbop", ss)
    out = {}

    if cbv and cbv.get("n_enc"):
        out["n_enc"] = (int(cbv["n_enc"]), "p05")
    elif sysv and sysv.get("num_containers"):
        out["n_enc"] = (int(sysv["num_containers"]), "p02")
    else:
        out["n_enc"] = (20, "[가정]")
    out["n_pcs"] = (int(sysv["num_pcs"]), "p02") if sysv and sysv.get("num_pcs") else (5, "[가정]")

    def _dim(key, default, lo):   # 0·음수 치수는 배치를 깨뜨리므로 기본값으로
        v = cbv.get(key) if cbv else None
        return (float(v), "p05") if isinstance(v, (int, float)) and v >= lo else (default, "[가정]")
    out["enc_l"] = _dim("enc_l", 6.05, 0.5)
    out["enc_w"] = _dim("enc_w", 2.44, 0.5)
    out["trench_w"] = _dim("trench_w", 0.6, 0.05)
    # 구조 뷰 — 05 기초 패드 평면 치수(기본 = 인클로저 + 1 m)·트렌치 깊이
    out["pad_l"] = _dim("pad_l", out["enc_l"][0] + 1.0, 0.5)
    out["pad_w"] = _dim("pad_w", out["enc_w"][0] + 1.0, 0.5)
    out["trench_d"] = _dim("trench_d", 1.2, 0.1)
    out["water_m3"] = ((float(cbv["water_l"]) / 1000.0, "p05") if cbv and cbv.get("water_l")
                       else (0.0, "[가정]"))
    out["main_tr_mva"] = ((ebv["main_tr_mva"], "p04") if ebv and ebv.get("main_tr_mva")
                          else (None, "[가정]"))
    out["cable_area_mm2"] = ((ebv["cable_area_mm2"], "p04") if ebv and ebv.get("cable_area_mm2")
                             else (None, "[가정]"))
    out["target_market"] = ((ss.get("target_market"), "p01") if ss.get("target_market")
                            else ("KR (한국)", "[가정]"))
    return out


def per_container(ss=None) -> dict:
    """03·09 시뮬레이션 기본값 — 컨테이너 1기 기준. 05 미실행이면 빈 dict."""
    cbv = get("cbop", _ss(ss))
    if not cbv or not cbv.get("n_enc"):
        return {}
    n = max(int(cbv["n_enc"]), 1)
    out = {"enc_l": cbv.get("enc_l"), "enc_w": cbv.get("enc_w"), "n_enc": n}
    if cbv.get("bat_heat_kw") is not None:
        out["heat_kw"] = float(cbv["bat_heat_kw"]) / n
        # 컨테이너 HVAC = 배터리 발열 × (1+안전율) + 외피 1기분 U·A·ΔT.
        # 05 플랜트 냉방부하(PCS 스키드 발열 포함)를 대수로 나누면 컨테이너 HVAC 가 과대해져 09 과열을 놓친다
        out["hvac_kw"] = (out["heat_kw"] * (1 + float(cbv.get("hvac_safety_pct", 15.0)) / 100.0)
                          + float(cbv.get("env_ua_kw_k", 0.2)) * float(cbv.get("hvac_dt_k", 0.0)))
    if cbv.get("pad_l") and cbv.get("pad_w"):
        out["pad_l"], out["pad_w"] = max(float(cbv["pad_l"]), 0.5), max(float(cbv["pad_w"]), 0.5)
    return out


# ── JSON 내보내기·불러오기 ─────────────────────────────────────────────────────
def export_json(ss=None, layout_metrics=None) -> str:
    ss = _ss(ss)
    doc = {
        "schema": SCHEMA,
        "exported": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "project": {k: ss.get(k) for k in PROJECT_KEYS if ss.get(k) is not None},
        "sections": ss.get(DM_KEY) or {},
    }
    for k in ("num_containers", "num_pcs"):
        if ss.get(k) is not None:
            doc["project"][k] = ss.get(k)
    if layout_metrics:
        doc["layout_metrics"] = layout_metrics
    return json.dumps(doc, ensure_ascii=False, indent=2)


def import_json(text: str, ss=None) -> int:
    """export_json 결과를 세션에 복원. 복원한 항목 수 반환. 형식 불일치는 ValueError."""
    ss = _ss(ss)
    doc = json.loads(text)
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA:
        raise ValueError("지원하지 않는 형식: " + (repr(doc.get("schema")) if isinstance(doc, dict) else type(doc).__name__))
    proj, sections = doc.get("project") or {}, doc.get("sections") or {}
    if not isinstance(proj, dict) or not isinstance(sections, dict) or not all(
            isinstance(v, dict) and isinstance(v.get("values"), dict) for v in sections.values()):
        raise ValueError("project/sections 구조가 올바르지 않습니다")
    # 손으로 고친 파일의 문자열·NaN 값이 들어오면 05·13 이 int()/float() 변환에서 죽는다 — 입구에서 거부
    for where, items in [("project", proj.items())] + \
            [(f"sections.{s}", e["values"].items()) for s, e in sections.items()]:
        for k, v in items:
            if v is None:
                continue
            if k in _TEXT_KEYS:
                if not isinstance(v, str):
                    raise ValueError(f"{where}.{k} 는 문자열이어야 합니다: {v!r}")
            elif isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                raise ValueError(f"{where}.{k} 값이 유한한 숫자가 아닙니다: {v!r}")
    # 이전 프로젝트 값이 남지 않도록 대상 키를 먼저 비운다
    for k in PROJECT_KEYS + ("num_containers", "num_pcs", DM_KEY):
        ss.pop(k, None)
    n = 0
    for k, v in proj.items():
        if k in PROJECT_KEYS or k in ("num_containers", "num_pcs"):
            ss[k] = v
            # 01 위젯은 widget_<key> 상태를 우선하므로 지워서 새 값으로 다시 초기화되게 한다
            if ("widget_" + k) in ss:
                del ss["widget_" + k]
            n += 1
    ss[DM_KEY] = sections
    n += len(sections)
    return n
