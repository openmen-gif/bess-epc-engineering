# -*- coding: utf-8 -*-
"""
fig_compact.py — 3D 차트 전송량 줄이기 (2026-10-30 신설).

Streamlit 은 위젯을 바꿀 때마다 차트 전체를 JSON 으로 다시 보낸다. plotly 5 는 numpy float 를
17자리 문자열로 쓰므로, 화면에서 구분되지 않는 자릿수를 잘라 내면 전송량이 크게 준다.
트레이스·프레임의 수치 배열만 반올림하고 스칼라(투명도·색 범위 등)는 건드리지 않는다.
"""
import numpy as np

_KEEP = {"i", "j", "k"}   # Mesh3d 정점 인덱스 — 정수 그대로


def _round(v, nd):
    if isinstance(v, np.ndarray):
        return np.round(v, nd) if v.dtype.kind == "f" else v
    if isinstance(v, (list, tuple)) and v and any(isinstance(x, (float, list, tuple, np.ndarray)) for x in v):
        return [_round(x, nd) for x in v]
    if isinstance(v, float):
        return round(v, nd)
    return v


def _walk(obj, nd):
    out = {}
    for k, v in obj.items():
        if k in _KEEP:
            out[k] = v
        elif isinstance(v, dict):
            out[k] = _walk(v, nd)
        elif isinstance(v, (list, tuple, np.ndarray)):
            out[k] = _round(v, nd)
        else:
            out[k] = v   # 스칼라는 그대로
    return out


def compact(fig, nd: int = 2) -> dict:
    """go.Figure → 수치 배열을 nd 자리로 반올림한 dict (st.plotly_chart 에 그대로 넘긴다)."""
    d = fig.to_plotly_json()
    d["data"] = [_walk(t, nd) for t in d.get("data", [])]
    if d.get("frames"):
        d["frames"] = [{**f, "data": [_walk(t, nd) for t in f.get("data", [])]} for f in d["frames"]]
    return d
