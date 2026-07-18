# DESIGN.md — BESS EPC 대시보드 시각 정본 (SSOT)

> 색·폰트·간격·컴포넌트의 단일 기준. 코드/운영 정본은 CLAUDE.md, 시각 정본은 이 문서.
> **토큰 구현 정본**: `utils/theme.py`의 `PALETTE` (Python) ↔ `utils/css_loader.py`의 `:root { --bess-* }` (CSS) ↔ `.streamlit/config.toml [theme]` — 3곳은 항상 같은 값을 유지한다.

## 1. 색상 토큰

| 토큰 | 값 | 용도 |
|------|-----|------|
| `bg` | `#0d1117` | 앱 배경 (index.html 셸 배경과 동일해야 함) |
| `bg2` | `#161b22` | 사이드바·카드·메트릭 배경 |
| `bg3` | `#21262d` | 익스팬더·상승 표면·호버라벨 |
| `border` | `#30363d` | 테두리·차트 그리드 |
| `text` | `#e6edf3` | 본문 |
| `text2` | `#c9d1d9` | 차트 텍스트·보조 본문 |
| `muted` | `#8b949e` | 라벨·캡션 |
| `accent` | `#58a6ff` | 주 강조·제목·링크 (config.toml primaryColor) |
| `accent2` | `#79c0ff` | h1 그라디언트 종점 |
| `ok` | `#3fb950` | 성공·합격·메트릭 값 |
| `warn` | `#e3b341` | 경고 |
| `danger` | `#f85149` | 위험·불합격 |
| `orange` / `purple` / `cyan` | `#f78166` / `#bc8cff` / `#00b4d8` | 카테고리 색·덕트 마커 |
| `grad_a` → `grad_b` | `#1E3A5F` → `#2E75B6` | 마켓 카드 그라디언트 |

## 2. 타이포그래피

- 기본 폰트: **Pretendard Variable** (jsdelivr dynamic-subset CDN, css_loader에서 @import) → 폴백 Segoe UI.
- h1: 2.5rem/800, accent→accent2 그라디언트 텍스트 (인쇄 시 검정으로 해제됨 — css_loader @media print).
- h2~h4: accent 단색. 본문 16px, 메트릭 값 2.0rem/700 `tabular-nums`.

## 3. 차트 (Plotly)

- 전역 템플릿 **`bess_dark`** — `utils/theme.py` import 시 등록되고 기본값으로 지정된다.
  - 새 페이지는 `from utils import theme` 한 줄이면 px/go 차트가 다크·브랜드 colorway 자동 적용.
  - 카테고리 colorway: accent → ok → orange → warn → purple → cyan → danger → accent2.
- 3D scene 축은 `theme.AX3D`, 2D 공통은 `theme.DARK_LAYOUT` 참조 (신규 하드코딩 금지).
- **예외(유지)**: 물리 시각화 컬러맵은 과학 표준을 유지한다 — 열=RdYlBu_r/Inferno, 화재=Hot_r, 공기흐름=Blues.

## 4. 컴포넌트 규약

- 메트릭: 카드형(bg2 + border + radius 10px + hover 시 accent 테두리) — css_loader가 전역 적용.
- 버튼: 그린 그라디언트(실행 액션 시맨틱), radius 8px. 위험 액션은 danger 계열 커스텀 금지(스트림릿 기본 유지).
- 탭: 언더라인 accent. 스크롤바: 얇은 다크.
- 반응형: 768px(모바일)·480px(소형)·1024px(태블릿) 분기와 @media print(잉크 절약 흑백)는 css_loader에 정의 — 삭제 금지.

## 5. 변경 절차

1. 색·폰트 변경은 `utils/theme.py` → `utils/css_loader.py` :root → `.streamlit/config.toml` 순으로 3곳 동기 수정.
2. 페이지에 색을 직접 쓰지 말 것 — `PALETTE`/CSS 변수 참조. 부득이한 리터럴은 이 문서의 토큰 값과 일치시킨다.
3. 이 문서와 코드가 어긋나면 같은 PR에서 동기화한다.

*최초 제정: 2026-07-18 (디자인 토큰화 리프레시와 함께)*
