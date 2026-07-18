# -*- coding: utf-8 -*-
"""
utils/theme.py — 대시보드 디자인 토큰 + Plotly 공용 다크 테마 (SSOT)

- 색상 정본은 PALETTE 하나. css_loader의 CSS 변수(--bess-*)와 값이 동일해야 한다.
- import 시 plotly 템플릿 "bess_dark"를 등록하고 기본값으로 지정하므로,
  각 페이지는 `from utils import theme`(또는 아래 헬퍼 import)만으로
  px/go 차트가 다크 테마·브랜드 colorway를 자동 적용받는다.
- 기존 페이지의 paper_bgcolor/font 수동 선언과 값이 같아 중복 선언이 있어도 무해.
"""
import plotly.graph_objects as go
import plotly.io as pio

# ── 디자인 토큰 (css_loader.py --bess-* 변수와 1:1) ─────────────────────────
PALETTE = {
    "bg":       "#0d1117",   # 앱 배경
    "bg2":      "#161b22",   # 사이드바·카드 배경
    "bg3":      "#21262d",   # 익스팬더·상승 표면
    "border":   "#30363d",   # 테두리·차트 그리드
    "text":     "#e6edf3",   # 본문
    "text2":    "#c9d1d9",   # 차트 텍스트·보조 본문
    "muted":    "#8b949e",   # 라벨·캡션
    "accent":   "#58a6ff",   # 주 강조 (파랑)
    "accent2":  "#79c0ff",   # 밝은 파랑 (그라디언트 종점)
    "ok":       "#3fb950",   # 성공/합격
    "warn":     "#e3b341",   # 경고 (노랑)
    "danger":   "#f85149",   # 위험/불합격
    "orange":   "#f78166",
    "purple":   "#bc8cff",
    "cyan":     "#00b4d8",
    "grad_a":   "#1E3A5F",   # 카드 그라디언트 시작
    "grad_b":   "#2E75B6",   # 카드 그라디언트 끝
}

# 카테고리 차트 기본 색 순서 (브랜드 colorway)
COLORWAY = [PALETTE["accent"], PALETTE["ok"], PALETTE["orange"],
            PALETTE["warn"], PALETTE["purple"], PALETTE["cyan"],
            PALETTE["danger"], PALETTE["accent2"]]

# 3D scene 축 공통 속성 (03·09·10 페이지 공용)
AX3D = dict(color=PALETTE["text2"], gridcolor=PALETTE["border"],
            backgroundcolor="rgba(0,0,0,0)")

# 2D 레이아웃 공통 속성 (기존 페이지들의 수동 선언과 동일 값)
DARK_LAYOUT = dict(paper_bgcolor="rgba(0,0,0,0)",
                   plot_bgcolor="rgba(0,0,0,0)",
                   font=dict(color=PALETTE["text2"]))


def _register_template():
    tpl = go.layout.Template()
    tpl.layout = go.Layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=PALETTE["text2"], size=13,
                  family="'Pretendard Variable', Pretendard, 'Segoe UI', sans-serif"),
        title=dict(font=dict(color=PALETTE["text"], size=15)),
        colorway=COLORWAY,
        xaxis=dict(gridcolor=PALETTE["border"], zerolinecolor=PALETTE["border"],
                   linecolor=PALETTE["border"]),
        yaxis=dict(gridcolor=PALETTE["border"], zerolinecolor=PALETTE["border"],
                   linecolor=PALETTE["border"]),
        legend=dict(font=dict(color=PALETTE["text2"]), bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor=PALETTE["bg3"],
                        font=dict(color=PALETTE["text"], size=12),
                        bordercolor=PALETTE["border"]),
        scene=dict(xaxis=AX3D, yaxis=AX3D, zaxis=AX3D,
                   bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=40, r=20, t=48, b=40),
    )
    pio.templates["bess_dark"] = tpl
    pio.templates.default = "bess_dark"


_register_template()


def apply_dark(fig, **layout_kw):
    """기존 figure에 다크 크롬을 명시 적용 (템플릿 미적용 경로 보정용)."""
    fig.update_layout(template="bess_dark", **layout_kw)
    return fig
