---
name: bess-output-generator
description: "전사 문서 표준화, 출력 형식 선택, A4/A3 인쇄, Excel/Word/PDF/Python 파일 생성"
---

# SCV: output-generator (출력 관리자)

> [!NOTE]
> **[Hybrid 에이전트 호환성 구문]**
> - **VSCode (Claude Code) 인식용:** 이 문서를 전문가 페르소나(Persona)의 지식 컨텍스트로 활용하여 텍스트 및 코드 기반 답변을 사용자에게 제공하세요.
> - **Antigravity (Agent) 인식용:** 이 문서를 도메인 지식(Skill)으로 로드하세요. 계산, 파일 생성 또는 시스템 연동이 필요한 경우, 직접 Python 코드를 작성하고 터미널 도구(`run_command`)를 실행하여 워크플로우를 완수하세요.


## 한 줄 정의
콘텐츠(내용)와 형식(출력)을 분리하여, 어떤 BESS 산출물이든 사용자가 원하는 형식으로 즉시 생성한다.

## 받는 인풋
필수: 콘텐츠 유형 (BOQ / 절차서 / 재무분석 / 계통연계 / 에이전트 설계)
선택: 출력 형식 (미명시 시 선택지 제시), 언어(한/영/일), 인쇄 여부



## 출처(Sources) 포함 원칙 (모든 출력물 필수)

### 핵심 원칙
**모든 산출물의 마지막 페이지에 반드시 "참고 출처 (Sources)" 섹션을 포함한다.**
출처 없는 데이터는 검증 불가능하므로 완성된 산출물이 아니다.

### 출처 섹션 표준 형식
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📎 참고 출처 (Sources)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

No   출처명                          URL / 문서 참조                              수집일
──────────────────────────────────────────────────────────────────────────────────────
1    [출처 기관/매체명]               [URL 전체 또는 문서 제목·번호]               [YYYY-MM-DD]
2    [출처 기관/매체명]               [URL 전체 또는 문서 제목·번호]               [YYYY-MM-DD]
...
──────────────────────────────────────────────────────────────────────────────────────
※ 본 문서의 모든 수치·분석은 위 공개 출처에 기반하며, 투자 자문이 아닙니다.
```

### 적용 규칙
```
✅ 필수:
├── 본문에서 인용한 모든 데이터의 원 출처(URL 포함) 수록
├── 출처별 수집일(데이터 기준일) 명시
├── web_search / web_fetch 로 수집한 URL 원본 그대로 기재
├── 유료 리포트 참조 시: 리포트 제목 + 발행 기관 + 발행일 기재 (URL 대신)
├── 사용자 제공 자료 참조 시: "[사용자 제공]" + 파일명 기재
└── 번호(No) 순서: 본문 등장 순서 기준

❌ 금지:
├── 출처 섹션 생략 (어떤 출력 형식이든 필수)
├── URL 축약·단축 (원본 URL 그대로 기재)
├── 출처 없이 수치 제시 (본문 [미확인] 태그 항목도 출처란에 "[미확인]" 표기)
└── 데이터 기준일 누락
```

### 형식별 출처 위치
```
Word (.docx)  → 마지막 페이지 (별도 섹션, 페이지 나누기 후)
Excel (.xlsx) → 별도 "Sources" 시트 (마지막 시트)
PDF (.pdf)    → 마지막 페이지
Python (.py)  → 모듈 docstring 내 SOURCES 섹션 + 결과 출력 시 말미 표시
PPT (.pptx)   → 마지막 슬라이드 (참고 출처 슬라이드)
HTML          → <footer> 또는 마지막 섹션
인쇄 패키지   → 모든 출력물 각각에 출처 페이지 포함
```



## A4 인쇄 표준 (모든 출력물 공통 기준)

### 핵심 원칙
현장 지참, 계통 운영자 제출, 고객 보고 모두 A4 기준으로 즉시 인쇄 가능해야 한다.
출력물이 화면에서만 보이고 인쇄하면 깨지는 것은 완성된 산출물이 아니다.

### A4 페이지 기본 설정 (전 출력물 공통)
```
페이지 크기:  A4 (210 × 297mm)
기본 방향:    세로 (Portrait)
  → 표 넓이 초과 시: 가로 (Landscape, 297 × 210mm)
```

### 여백 가이드 — 3가지 옵션 (★ 2026-05-20 보강)

**좌우 여백은 사용 시나리오에 따라 의도적으로 다르게 설정한다.** "비대칭이 보인다"는 것은 잘못이 아니라 binding 여유 또는 mirror margin 의도이다. 단, 출력 시점에 어떤 옵션을 적용할지 사전 결정·문서화 필수.

#### 옵션 A — 단면 인쇄 / 좌우 대칭 (기본 권장값 ★)
**용도**: 디지털 배포(이메일·PDF 첨부), 짧은 보고서(<10p), 단면 출력 검토용
```
상25 / 하25 / 좌25 / 우25 mm  (균형 우선, 4-방향 동일)
본문 폭 = 210 - 25 - 25 = 160mm
```

#### 옵션 B — 단면 인쇄 / 좌측 제본 여유 (긴 보고서·제본 용)
**용도**: 인쇄 후 좌측 스테이플·링 제본 예정인 보고서, 절차서, 매뉴얼
```
상25 / 하25 / 좌30 / 우20 mm  (좌측 5mm 제본 여유)
본문 폭 = 210 - 30 - 20 = 160mm (옵션 A와 동일)
※ 좌우 비대칭은 의도된 제본 공간, 단면 출력 시 우측이 더 가까워 보일 수 있음 — 정상
```

#### 옵션 C — 양면 인쇄 / Mirror Margin (책자형 출력)
**용도**: 양면 인쇄 책자형 보고서, 사용자 매뉴얼, 50p+ 장문 문서
```
홀수 페이지(앞면):  상25 / 하25 / inside 30 / outside 20 mm
짝수 페이지(뒷면):  상25 / 하25 / inside 30 / outside 20 mm
                     ↑ 좌측이 30(안쪽)
                     ↑ 우측이 30(안쪽)
본문 폭 = 160mm (양면 모두 동일)
```

#### 체크리스트·현장 작업지 (별도 기준 — 좌우 대칭으로 통일)
| 용도 | 상 | 하 | 좌 | 우 | 비고 |
|------|----|----|----|----|------|
| 체크리스트 (단면) | 12 | 12 | 15 | 15 | 좌우 대칭 (구 좌15/우10에서 변경) |
| 체크리스트 (좌측 제본) | 12 | 12 | 18 | 12 | 제본 시 binding 6mm |
| 현장 작업지 | 10 | 10 | 10 | 10 | 4-방향 동일 (최소 여백) |
| 명함·라벨 | 5 | 5 | 5 | 5 | 4-방향 동일 |

#### 옵션 결정 트리
```
출력 형식이 무엇인가?
├─ 디지털 (PDF/Word 첨부, 화면 검토만) → 옵션 A (대칭)
├─ 단면 인쇄 + 제본 예정 (스테이플·바인더) → 옵션 B (좌30/우20)
├─ 양면 인쇄 (책자형, 50p+) → 옵션 C (mirror)
├─ 체크리스트·서명용 → 체크리스트 기준
└─ 현장 작업지·휴대용 → 현장 작업지 기준
```

**원칙**: 옵션은 산출물 metadata에 명시 (예: `## 출력 옵션: A (단면 대칭, 25mm 4-방향)`)

### 헤더·푸터 (모든 페이지 공통)
```
헤더 (모든 페이지):
  좌: [프로젝트명] — [문서번호]
  우: [버전] | [날짜]

푸터 (모든 페이지):
  좌: [회사명]
  우: Page [X] of [Y]

※ 양면 인쇄(옵션 C) 시:
  홀수 페이지(앞): 좌·우 위치 정상
  짝수 페이지(뒤): 좌·우 위치 mirror (좌↔우 교환)
```

### 타이포그래피 기준 (전 출력물 공통 — 기본 12pt)
```
※ 모든 출력물의 본문 기본 폰트는 12pt 이다.
  다른 BESS 스킬(직원)의 산출물도 동일 기준을 따른다.

글자 크기 체계:
  문서 제목:        24~28pt Bold
  섹션 제목 (H1):   16pt Bold Navy #1F4E79
  소제목 (H2):      13pt Bold Blue #2E75B6
  본문 (기본값):    12pt           ← ★ 전 출력물 기본값
  표 헤더:          12pt Bold
  표 본문:          12pt           ← ★ 본문과 동일 (통일 원칙)
  캡션·각주:        9pt
  Sources URL:      10pt 파란색 밑줄 ← ★ 하이퍼링크 전용
  헤더·푸터:        8~9pt

폰트 패밀리:
  한글: 맑은 고딕 (Malgun Gothic)
  영문: Calibri 또는 Arial
  코드: Consolas 또는 D2Coding

적용 우선순위:
  Word (.docx)  → Normal 스타일 font.size = Pt(12)
  Excel (.xlsx) → 기본 셀 font.size = 12
  PDF  (.pdf)   → body_text font.size = 12
  Python (.py)  → 출력 결과 본문 12pt (GUI·리포트 공통)
  HTML          → body { font-size: 12pt; }
```

### Excel A4 인쇄 설정 코드
```python
from openpyxl import load_workbook
from openpyxl.worksheet.page import PageMargins, PrintPageSetup

def apply_a4_print_settings(ws, landscape=False, fit_to_width=True):
    """
    Excel 시트에 A4 인쇄 설정 적용 — 기본 폰트 12pt
    landscape=True → A4 가로, False → A4 세로
    fit_to_width=True → 페이지 너비에 맞춤
    """
    # ★ 기본 폰트: 12pt, 맑은 고딕
    from openpyxl.styles import Font
    default_font = Font(name="맑은 고딕", size=12)  # ★ 기본값 12pt
    for row in ws.iter_rows():
        for cell in row:
            if cell.font.size is None or cell.font.size < 10:
                cell.font = default_font

    # 페이지 크기: A4 = 9 (openpyxl 코드)
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.orientation = (
        ws.ORIENTATION_LANDSCAPE if landscape
        else ws.ORIENTATION_PORTRAIT
    )
    
    # ★ 여백 — 3가지 옵션 (★ 2026-05-20 보강)
    # 옵션 A (기본 권장): 단면 인쇄·대칭, 25mm 4-방향
    ws.page_margins = PageMargins(
        top    = 0.984,   # 25mm
        bottom = 0.984,   # 25mm
        left   = 0.984,   # 25mm (대칭)
        right  = 0.984,   # 25mm (대칭)
        header = 0.315,
        footer = 0.315
    )

    # 옵션 B: 단면 인쇄 + 좌측 제본 여유 (구 기본값)
    # ws.page_margins = PageMargins(
    #     top=0.984, bottom=0.984, left=1.181, right=0.787,
    #     header=0.315, footer=0.315
    # )

    # 옵션 C: 양면 인쇄 / Mirror Margin
    # openpyxl은 mirror margin 직접 미지원 — odd/even 시트 분리 후
    # ws.print_options.differentOddEven = True  (워크북 단위 설정)

    # 체크리스트용 좁은 여백 (대칭)
    # ws.page_margins = PageMargins(
    #     top=0.472, bottom=0.472, left=0.591, right=0.591
    # )

    # 현장 작업지 (4-방향 최소 여백)
    # ws.page_margins = PageMargins(
    #     top=0.394, bottom=0.394, left=0.394, right=0.394
    # )
    
    if fit_to_width:
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
    
    # 격자선 인쇄 (체크리스트)
    ws.print_options.gridLines = True
    
    # 제목 행 반복 (헤더 행 = 1~3행)
    ws.print_title_rows = '1:3'
    
    # 헤더/푸터
    ws.oddHeader.center.text  = "&P / &N"   # 페이지/전체
    ws.oddFooter.left.text    = "[회사명]"
    ws.oddFooter.right.text   = "&D"        # 날짜

def set_print_area(ws, last_row, last_col):
    """인쇄 영역 지정"""
    from openpyxl.utils import get_column_letter
    ws.print_area = f"A1:{get_column_letter(last_col)}{last_row}"
```

### Word A4 설정 코드 (docx-js / python-docx)
```python
from docx import Document
from docx.shared import Mm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

def create_a4_document(title, project_code, version):
    """A4 표준 Word 문서 생성 — 본문 기본 12pt"""
    doc = Document()

    # ★ 기본 폰트 설정: 본문 12pt, 맑은 고딕
    style = doc.styles["Normal"]
    style.font.name = "맑은 고딕"
    style.font.size = Pt(12)          # ★ 기본값 12pt
    style.element.rPr.rFonts.set(qn("w:eastAsia"), "맑은 고딕")

    # A4 페이지 설정
    section = doc.sections[0]
    section.page_width  = Mm(210)   # A4 너비
    section.page_height = Mm(297)   # A4 높이

    # ★ 여백 — 3가지 옵션 (★ 2026-05-20 보강)
    # 옵션 A (기본 권장): 단면 대칭, 25mm 4-방향
    section.top_margin    = Mm(25)
    section.bottom_margin = Mm(25)
    section.left_margin   = Mm(25)   # 대칭
    section.right_margin  = Mm(25)   # 대칭
    section.header_distance = Mm(12)
    section.footer_distance = Mm(12)

    # 옵션 B (단면 + 좌측 제본 여유): left=30, right=20
    # 옵션 C (양면 mirror): section.mirror_margins = True (python-docx 1.1+)

    # 헤더 설정
    header = section.header
    header_para = header.paragraphs[0]
    header_para.text = f"{project_code}  —  {title}"
    header_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    # 푸터 (페이지 번호)
    footer = section.footer
    footer_para = footer.paragraphs[0]
    # 페이지 번호 필드 추가
    add_page_number(footer_para)

    return doc
```

### PDF A4 설정 코드 (reportlab)
```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate

def create_a4_pdf(filename, title, project_code, layout="A"):
    """
    A4 표준 PDF 생성 — 본문 기본 12pt
    layout: "A" 단면 대칭(기본), "B" 단면 좌측 제본, "C" 양면 mirror
    """
    # ★ 여백 옵션 매트릭스 (★ 2026-05-20 보강)
    MARGINS = {
        "A": (25, 25, 25, 25),   # top, bottom, left, right (단면 대칭, 기본)
        "B": (25, 25, 30, 20),   # 단면 + 좌측 제본 5mm 여유
        "C": (25, 25, 30, 20),   # 양면 mirror (inside 30, outside 20)
    }
    top_mm, bot_mm, left_mm, right_mm = MARGINS.get(layout, MARGINS["A"])

    doc = SimpleDocTemplate(
        filename,
        pagesize = A4,                  # (595.3, 841.9) points
        topMargin    = top_mm  * mm,
        bottomMargin = bot_mm  * mm,
        leftMargin   = left_mm * mm,
        rightMargin  = right_mm* mm,
        title        = title,
        author       = project_code
    )
    # ※ 옵션 C(양면 mirror)는 reportlab PageTemplate odd/even 분리 필요

    # ★ 본문 스타일: 12pt 기본
    styles = getSampleStyleSheet()
    styles["Normal"].fontSize = 12     # ★ 기본값 12pt
    styles["Normal"].leading  = 16     # 행간 (12pt × 1.33)

    return doc, styles
```

### PDF A4 설정 코드 (fpdf2)
```python
from fpdf import FPDF

class BESS_PDF(FPDF):
    """A4 표준 PDF — 본문 기본 12pt
    layout: 'A'=단면 대칭(기본), 'B'=단면 좌측 제본, 'C'=양면 mirror
    """
    def __init__(self, layout="A"):
        super().__init__(orientation="P", unit="mm", format="A4")
        # ★ 여백 옵션 (★ 2026-05-20 보강)
        margins = {
            "A": (25, 25, 25),   # top, left, right (단면 대칭)
            "B": (25, 30, 20),   # 단면 + 좌측 제본
            "C": (25, 30, 20),   # 양면 mirror (alias 페이지로 처리)
        }
        top_m, left_m, right_m = margins.get(layout, margins["A"])
        self.set_margins(left=left_m, top=top_m, right=right_m)
        self.set_auto_page_break(auto=True, margin=25)
        # ★ 한글 폰트 등록
        self.add_font("korean", "", r"C:\Windows\Fonts\malgun.ttf")
        self.add_font("korean", "B", r"C:\Windows\Fonts\malgunbd.ttf")

    def body_text(self, text):
        self.set_font("korean", "", 12)  # ★ 본문 기본 12pt
        self.multi_cell(0, 6, text)

    def heading(self, text, level=1):
        sizes = {1: 18, 2: 14, 3: 12}
        self.set_font("korean", "B", sizes.get(level, 12))
        self.cell(0, 10, text, new_x="LMARGIN", new_y="NEXT")
```

### PowerPoint(.pptx) 여백·안전 영역 (★ 2026-05-20 신규)

PPT는 인쇄가 아닌 화면 발표·인쇄 양면 적용 모두 가능. 화면(16:9 widescreen) 기준 안전 영역과 인쇄 변환 시 A4 여백 모두 고려.

```python
# python-pptx 기준
from pptx import Presentation
from pptx.util import Inches, Mm, Pt

def create_a4_ppt(filename, layout="widescreen"):
    """
    BESS 표준 PPT 생성
    layout: 'widescreen' (16:9, 13.3x7.5"), 'standard' (4:3, 10x7.5"),
            'a4_landscape' (인쇄용 297x210mm)
    """
    prs = Presentation()

    if layout == "widescreen":
        prs.slide_width  = Inches(13.333)   # 16:9 widescreen
        prs.slide_height = Inches(7.5)
        SAFE = {"top": Inches(0.5), "left": Inches(0.5),
                "right": Inches(0.5), "bottom": Inches(0.5)}
    elif layout == "standard":
        prs.slide_width  = Inches(10)        # 4:3
        prs.slide_height = Inches(7.5)
        SAFE = {"top": Inches(0.5), "left": Inches(0.5),
                "right": Inches(0.5), "bottom": Inches(0.5)}
    elif layout == "a4_landscape":
        prs.slide_width  = Mm(297)           # A4 가로 인쇄 호환
        prs.slide_height = Mm(210)
        SAFE = {"top": Mm(20), "left": Mm(20),
                "right": Mm(20), "bottom": Mm(20)}

    return prs, SAFE

# ★ PPT 좌우 대칭 원칙
# - 슬라이드 가장자리 안전 영역은 4-방향 동일 (대칭)
# - 제목·본문·푸터 모두 좌우 동일 margin 적용
# - 인쇄 변환 시 A4 여백은 Word/PDF 옵션 A(대칭) 따름
```

```javascript
// pptxgenjs (Node.js) 기준
const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";  // 13.3" x 7.5" (16:9 widescreen)

// ★ 안전 영역 상수 (좌우 대칭)
const MARGIN = 0.5;  // inch (12.7mm)
const SAFE = {
  top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN,
  contentWidth:  13.3 - MARGIN * 2,  // 12.3"
  contentHeight: 7.5  - MARGIN * 2,  // 6.5"
};

slide.addText("제목", {
  x: SAFE.left, y: SAFE.top, w: SAFE.contentWidth, h: 0.6,
  fontFace: "Malgun Gothic", fontSize: 32, bold: true
});
```

### HTML/Web 여백 (★ 2026-05-20 신규)

웹 페이지(대시보드·온라인 리포트)는 print CSS와 screen CSS 분리.

```css
/* 화면 (screen) — 좌우 자동 중앙 정렬 */
body {
  max-width: 1024px;       /* 본문 최대 폭 */
  margin: 0 auto;          /* ★ 좌우 자동 대칭 */
  padding: 20px;           /* 내부 여백 4-방향 동일 */
  font-family: "Malgun Gothic", "Calibri", sans-serif;
  font-size: 12pt;
}

/* 인쇄 (print) — A4 옵션 A 적용 (대칭) */
@page {
  size: A4 portrait;
  margin: 25mm;             /* ★ 4-방향 25mm (옵션 A, 기본 권장) */
}

/* 옵션 B (좌측 제본) — 좌우 비대칭 */
@page :left  { margin-left: 30mm; margin-right: 20mm; }
@page :right { margin-left: 30mm; margin-right: 20mm; }

/* 옵션 C (양면 mirror) */
@page :left  { margin-left: 20mm; margin-right: 30mm; }
@page :right { margin-left: 30mm; margin-right: 20mm; }

@media print {
  body { max-width: none; margin: 0; padding: 0; }
  h1, h2 { page-break-before: avoid; }
  table  { page-break-inside: avoid; }
}
```

### 여백 일관성 체크리스트 (출력 전 필수 검증)

- [ ] 어떤 옵션(A/B/C)을 적용했는지 산출물 metadata에 명시
- [ ] 좌우 비대칭은 의도된 binding/mirror 인지 확인 (실수 아님)
- [ ] 본문 폭 = 160mm 일관 (옵션 A/B/C 모두 동일)
- [ ] 표·이미지가 본문 폭을 초과하지 않음
- [ ] 헤더/푸터가 양면 인쇄(옵션 C) 시 mirror 적용 확인
- [ ] PPT 안전 영역(0.5" / 12.7mm) 내 콘텐츠 배치
- [ ] HTML print CSS의 `@page` 규칙이 옵션 A/B/C 중 어느 것인지 명시

> 복합 출력 패키지 조합 및 콘텐츠×형식 매핑 표는 아래 [F] 복합 출력 전략 / 콘텐츠 × 형식 매핑 테이블 섹션 참조.

## 품질 체크리스트 (출력 전 필수 확인)

공통:
- [ ] 파일명 네이밍 규칙 준수
- [ ] 버전 및 날짜 포함
- [ ] **참고 출처(Sources) 섹션 포함 — 마지막 페이지/시트에 URL·수집일 포함**
- [ ] /mnt/user-data/outputs/ 저장 완료
- [ ] present_files() 사용자 전달

Excel 추가:
- [ ] 수식 오류 0개 (#REF!, #DIV/0!, #VALUE! 없음)
- [ ] 최종 형식 사용자 확인 및 승인



## ✨ Premium Aesthetics Checklist (프리미엄 미학 체크리스트)

단순한 보고서를 넘어 'Wowed at first glance'를 위한 추가 최적화 요소:

- **Color Harmony**: 단순한 원색 대신 BESS 브랜드 컬러(#1F4E79, #2E75B6)와 차분한 그레이(#F2F2F2)를 조화롭게 사용.
- **Micro-Animations (HTML/React)**: 대시보드 출력 시 숫자가 스크롤되거나 차트가 부드럽게 그려지는 효과 포함.
- **Glassmorphism (Web)**: 웹 기반 출력물에는 반투명 배경과 미세한 외곽선(Inner Border)을 사용하여 유려한 질감 표현.
- **Typography**: 맑은 고딕 대신 가독성이 뛰어난 'Inter' 또는 'Roboto' 폰트 사용 (환경 허용 시).
- [ ] 헤더/푸터 설정 (프로젝트명, 페이지번호)
- [ ] 제목 행 반복 설정
- [ ] [요확인] 항목 노란 배경 표시

Word 추가:
- [ ] A4 여백 옵션(A/B/C) 명시 (기본: A 단면 대칭 25mm 4-방향)
- [ ] **테이블 col_widths 합계 = 160mm** (A4 본문 폭, 옵션 A/B/C 모두 동일), autofit 비활성화
- [ ] 좌우 비대칭(옵션 B/C)은 metadata에 명시 — 실수 아닌 의도
- [ ] 목차 자동 생성 (Word TOC 필드, add_toc)
- [ ] 헤더: 프로젝트명 + 문서번호
- [ ] 푸터: 버전 + 날짜 + 페이지번호
- [ ] 서명란 별도 페이지 (충분한 여백)
- [ ] 양면 인쇄 옵션 C 적용 시 `section.mirror_margins = True` 확인

Python 추가:
- [ ] 실행 가능 확인 (문법 오류 없음)
- [ ] 실행 방법 주석 (의존성 포함)
- [ ] 계산 결과에 단위 및 계산 근거 포함

PDF 추가:
- [ ] A4 크기 확인 (210 × 297mm)
- [ ] 여백 옵션(A/B/C) 명시 — `create_a4_pdf(layout="A")`
- [ ] 헤더/푸터 포함
- [ ] 폰트 내장(Embed)
- [ ] 인쇄 미리보기 이상 없음

PPT 추가:
- [ ] 슬라이드 크기 명시 (widescreen 13.3x7.5" / standard 10x7.5" / a4_landscape 297x210mm)
- [ ] 안전 영역 0.5"(12.7mm) 4-방향 동일 적용
- [ ] 좌우 대칭 layout — 제목·본문·푸터 좌우 동일 margin
- [ ] 한글 폰트 명시 (Malgun Gothic 또는 맑은 고딕)
- [ ] 인쇄 변환 검토 (A4 가로 호환 여부)

HTML 추가:
- [ ] `body max-width` + `margin: 0 auto` 좌우 자동 대칭
- [ ] `@page` 규칙으로 인쇄 시 옵션(A/B/C) 명시
- [ ] `@media print` 분리하여 화면/인쇄 스타일 격리
- [ ] 페이지 나누기 제어 (`page-break-before/inside: avoid`)

인쇄 패키지 추가:
- [ ] 판정란 크기 ≥ 8mm (손 체크 가능)
- [ ] 결과 기입란 여백 충분
- [ ] 현장 가독성 — 본문 12pt, 표 내부 12pt (통일)
- [ ] 서명란 행 높이 ≥ 12mm

## 차트/그래프 생성 규칙

모든 보고서·브리핑 문서에 시각화 요소를 포함하여 출력 품질을 보장한다.

### 생성 도구
- 차트 생성: `matplotlib` (Python)
- 저장 형식: PNG, DPI 200 이상
- 한글 폰트: 맑은 고딕 (malgun), unicode_minus = False

### 차트 종류별 가이드
| 용도 | 추천 차트 | 주의사항 |
|------|----------|----------|
| 시장 규모/용량 비교 | 수직 막대 | Y축 0 시작 필수 |
| 점유율/랭킹 | 수평 막대 | 내림차순 정렬 |
| 가격/성장 추이 | 선 차트 | 데이터 포인트 라벨 |
| 구성 비율 | 도넛/파이 | 항목 5개 이하 |
| 기술 비교 | Radar | 축 7개 이하 |
| 이중 축 (값+비율) | 막대+선 복합 | 축 색상 구분 |

### 필수 포함 요소
- 차트 제목 (bold, 14pt)
- 축 레이블 + 단위
- 데이터 값 라벨
- 캡션: `[Figure N] 설명 (Source: 출처명)`
- 출력 경로: /output/[카테고리]/charts/

### DOCX 삽입 규칙
- `doc.add_picture(path, width=Inches(5.8))` — A4 본문 폭 맞춤
- 차트 전후 빈 줄 1개
- 캡션은 차트 바로 아래, 중앙 정렬, 8pt, 회색

## 참고 출처(Sources) 삽입 규칙

모든 보고서·브리핑 문서의 마지막에 Sources 섹션을 필수 포함한다.

### 출처 테이블 형식
| 열 | 내용 | 글자 크기 |
|------|------|----------|
| No | [1], [2]... | 10pt |
| 출처 | 기관명 (날짜) | 10pt |
| 제목 | 문서/기사 제목 | 10pt |
| URL | 클릭 가능한 전체 URL | 10pt, 파란색 #2196F3, 밑줄 |

### 본문 내 인용
- 수치 인용 시 `[출처번호]` 표기 (예: 300 GWh [1])
- 동일 출처 재인용 시 동일 번호 사용



### 검증된 필수 코드 패턴 (python-docx)

> 아래 3개 함수를 모든 DOCX 생성 스크립트에 그대로 복사·사용한다.

#### ① add_hyperlink — URL을 클릭 가능 링크로 삽입

```python
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def add_hyperlink(paragraph, url: str, text: str, size_pt: float = 10):
    """
    paragraph 에 클릭 가능한 하이퍼링크 삽입 (검증 완료 패턴).
    - w:hyperlink + r:id 관계 → Word가 클릭 시 브라우저 열기
    - 스타일: Calibri/맑은고딕, 파란색 #2196F3, 밑줄, 10pt 기본
    """
    part = paragraph.part
    r_id = part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )

    hl = OxmlElement("w:hyperlink")
    hl.set(qn("r:id"), r_id)

    run = OxmlElement("w:r")

    rPr = OxmlElement("w:rPr")
    # 폰트
    rFonts = OxmlElement("w:rFonts")
    rFonts.set(qn("w:ascii"),   "Calibri")
    rFonts.set(qn("w:eastAsia"),"맑은 고딕")
    rPr.append(rFonts)
    # 색상 #2196F3
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "2196F3")
    rPr.append(color)
    # 밑줄
    u = OxmlElement("w:u")
    u.set(qn("w:val"), "single")
    rPr.append(u)
    # 크기 (half-points)
    twips = str(int(size_pt * 2))
    for tag in ("w:sz", "w:szCs"):
        el = OxmlElement(tag)
        el.set(qn("w:val"), twips)
        rPr.append(el)

    run.append(rPr)

    t = OxmlElement("w:t")
    t.set(qn("xml:space"), "preserve")
    t.text = text
    run.append(t)

    hl.append(run)
    paragraph._p.append(hl)
```

#### ② add_toc — TOC 필드 삽입 (점선 + 페이지 번호 + 자동 갱신)

```python
from docx.shared import Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def add_toc(doc):
    """
    Word TOC 필드 삽입.
    - Heading 1~2 수집, 점선 dot-leader + 페이지 번호 + 하이퍼링크 자동 생성
    - TOC 1/2 스타일: 10pt, space 0pt, line_spacing 11pt (최소 간격)
    - 문서 열 때 w:updateFields = true → 자동 갱신
    - 수동 갱신: Ctrl+A → F9
    """
    # ★ TOC 1/2 스타일 간격 축소 (기본값 너무 넓음)
    from docx.shared import Mm as _Mm
    for lvl, indent in [("TOC 1", _Mm(0)), ("TOC 2", _Mm(5))]:
        try:
            toc_style = doc.styles[lvl]
        except KeyError:
            toc_style = doc.styles.add_style(lvl, 1)  # 1 = PARAGRAPH
        toc_style.font.size = Pt(10)
        toc_style.font.name = "맑은 고딕"
        toc_style.paragraph_format.space_before = Pt(0)
        toc_style.paragraph_format.space_after  = Pt(0)
        toc_style.paragraph_format.line_spacing = Pt(11)  # 고정 줄간격 11pt (단일)
        toc_style.paragraph_format.left_indent  = indent

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after  = Pt(0)

    def _fld_run(fld_type=None, instr=None):
        r = p.add_run()
        if fld_type:
            fc = OxmlElement("w:fldChar")
            fc.set(qn("w:fldCharType"), fld_type)
            r._element.append(fc)
        if instr:
            it = OxmlElement("w:instrText")
            it.set(qn("xml:space"), "preserve")
            it.text = instr
            r._element.append(it)
        return r

    _fld_run("begin")
    _fld_run(instr=' TOC \\o "1-2" \\h \\z \\u ')
    _fld_run("separate")
    placeholder = p.add_run("목차 갱신: Ctrl+A → F9  (또는 우클릭 → 필드 업데이트)")
    placeholder.italic = True
    placeholder.font.size = Pt(9)
    placeholder.font.color.rgb = RGBColor(0x80, 0x80, 0x80)
    _fld_run("end")

    # 문서 열 때 자동 갱신
    settings = doc.settings.element
    upd = OxmlElement("w:updateFields")
    upd.set(qn("w:val"), "true")
    settings.append(upd)
```

#### ③ add_page_number — 푸터 오른쪽 "Page X / Y"

```python
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def add_page_number(section):
    """
    section.footer 오른쪽에 'Page X / Y' 필드 삽입.
    - PAGE / NUMPAGES Word 필드 사용 → Word가 자동 계산
    - 폰트: 9pt(18 half-pts), 회색 #9E9E9E
    """
    footer = section.footer
    para   = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    para.clear()
    para.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    def _r(fld_type=None, instr=None, literal=None):
        r = OxmlElement("w:r")
        rPr = OxmlElement("w:rPr")
        for tag, val in [("w:sz","18"), ("w:szCs","18")]:
            el = OxmlElement(tag); el.set(qn("w:val"), val); rPr.append(el)
        clr = OxmlElement("w:color"); clr.set(qn("w:val"), "9E9E9E"); rPr.append(clr)
        r.append(rPr)
        if fld_type:
            fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), fld_type); r.append(fc)
        if instr:
            it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve")
            it.text = f" {instr} "; r.append(it)
        if literal:
            t = OxmlElement("w:t"); t.set(qn("xml:space"), "preserve")
            t.text = literal; r.append(t)
        return r

    p = para._p
    for item in [
        _r("begin"), _r(instr="PAGE"), _r("separate"), _r(literal="1"), _r("end"),
        _r(literal=" / "),
        _r("begin"), _r(instr="NUMPAGES"), _r("separate"), _r(literal="1"), _r("end"),
    ]:
        p.append(item)
```




## 역할 경계 (소유권 구분)

> **Output Generator** vs **All Departments** 업무 구분

| 구분 | Output Generator | All Departments |
|------|------------------|-----------------|
| 소유권 | Document standardization, A4/A3 print optimization, format review, naming rules | Content creation, domain-specific deliverables |

**협업 접점**: All departments create content -> Output Generator reviews format/standard before final output



## 산출물

| 산출물 | 형식 | 주기·시점 | 수신자 |
|--------|------|-----------|--------|
| 표준화 문서 (서식 적용본) | Word/Excel/PDF | 각 산출물 최종 출력 전 | 전 담당자 |
| 인쇄용 패키지 (A4/A3 최적화) | PDF + 인쇄 묶음 | 현장 지참/제출 시 | 현장팀, 발주처 |
| 문서 형식 검토 결과 | 체크리스트 | 산출물 완성 시 | 요청 담당자 |
| 파일명·버전 규칙 적용본 | 전 형식 | 산출물 저장 시 | 전 담당자 |
| 차트/시각화 자산 | PNG (DPI≥200) | 보고서 삽입 시 | 요청 담당자 |

## 라우팅 키워드
Excel, Word, PDF, Python코드, A4인쇄,
출력, 문서형식, 인쇄, xlsx, docx, pptx, reportlab, fpdf2, python-docx, openpyxl,
서식, 템플릿, 파일생성, 출력관리, 인쇄패키지, 현장지참용, 체크리스트인쇄,
차트, 그래프, matplotlib, 시각화, TOC, 목차, 페이지번호, 하이퍼링크, Sources,
A4여백, 헤더푸터, 폰트, 12pt, 맑은고딕, Calibri, 파일네이밍
bess-output-generator

---

## 출력 형식 선택 메뉴

출력 형식이 명시되지 않은 경우, 항상 아래 선택지를 먼저 제시:

```
어떤 형식으로 출력할까요?

📊 [A] Excel (.xlsx)
   → 견적서/BOM, 재무모델, 체크리스트, 데이터 분석표
   ※ A4 인쇄 최적화 자동 적용 가능

📄 [B] Word (.docx)
   → 절차서, 보고서, 계약문서, 기술사양서
   ※ A4 기본 / 서명란 포함 선택 가능

🐍 [C] Python 코드 (.py)
   → 재계산 자동화 도구 (tkinter GUI / matplotlib / Streamlit)

📕 [D] PDF (.pdf)
   → 최종 제출용 / 서명 문서 / A4 인쇄 바로 가능

🖨️ [E] 인쇄용 패키지 (A4 최적화)
   → Excel + Word + PDF를 A4 인쇄 기준으로 동시 생성
   → 현장 지참용 / 계통 운영자 제출용

🔀 [F] 복합 출력
   → 여러 형식을 동시에 생성 (예: Word 절차서 + Excel 체크리스트 + PDF)

💻 [G] HTML / React
   → 인터랙티브 대시보드, 웹 기반 계산기

📊 [H] PowerPoint (.pptx)
   → 발표 자료, 제안서, 투자자 자료, 진도 보고서
   → 홍보 전문가(bess-presentation-designer)와 연계
```

---

## 보고서 유형별 서식 기준 (마케터 보고서 Tool 연계)

> MarketScheduler v2.0 등 Tool이 보고서를 자동 생성할 때,
> 출력관리자가 정의한 아래 서식 기준에 따라 유형별로 다르게 적용해야 한다.

```
보고서 유형별 출력관리자 서식 기준표
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
항목             일일(Daily)    주간(Weekly)    월간(Monthly)  심층(Deep)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
분량 목표        1~2p           3~5p            8~12p          15~25p
표지             없음           없음            간소화 (1p)    풀 커버 (1p)
목차 (TOC)       불필요         불필요          add_toc() 필수  add_toc() 필수
페이지 번호      불필요         불필요          add_page_number() add_page_number()
차트 수          0              2              4              6+
차트 삽입        —              width=5.8in     width=5.8in    width=5.8in
페이지 브레이크  없음           차트 앞 1회     섹션별          섹션+차트별
본문 폰트        12pt           12pt           12pt           12pt
표 폰트          12pt           12pt           12pt           12pt
여백             상25/하25/     상25/하25/      상25/하25/     상25/하25/
                 좌30/우20mm    좌30/우20mm     좌30/우20mm    좌30/우20mm
헤더             날짜만          기간            프로젝트코드   프로젝트코드
푸터             없음            없음            Page X/Y       Page X/Y
하이퍼링크       Sources만       Sources만       Sources+본문   Sources+본문
Sources 최소     5건             10건            20건           29건+
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

핵심 원칙: 일일은 간결함, 주간은 비교, 월간은 정량분석, 심층은 전략보고서
유형별 분량을 초과하면 콘텐츠를 축약하고, 미달하면 분석을 보강한다.
```

---

## 핵심 역량 및 업무 범위 (수행 절차)

> 출력관리자의 핵심 업무 절차는 아래 형식별 생성 가이드(Excel/Word/Python/PDF/인쇄패키지/복합출력)와 콘텐츠×형식 매핑에 따라 수행한다.

## 형식별 생성 가이드

### [A] Excel (.xlsx)
읽을 스킬: `/mnt/skills/public/xlsx/SKILL.md`

표준 시트 구조:
```
Sheet 1: Cover & Summary (A4 세로 — 1페이지)
  핵심 지표 + 차트 + 프로젝트 정보

Sheet 2: Main Data (A4 가로 — 멀티페이지)
  실제 데이터 (파란=입력, 검정=수식, 녹색=참조)
  조건부 서식: 합격#C6EFCE / 불합격#FFC7CE / 요확인#FFEB9C

Sheet 3: Print Ready (A4 최적화 — 현장용)
  본문 12pt, 헤더 반복, 격자선 인쇄
```

색상 체계:
```python
HEADER_BG  = "1F4E79"   # 진한 파란 (헤더 배경)
SUB_HEADER = "2E75B6"   # 중간 파란 (소헤더)
INPUT_FONT = "0000FF"   # 파란 글자 (입력값)
FORMULA    = "000000"   # 검정 (수식)
PASS_BG    = "C6EFCE"   # 연한 초록 (합격)
FAIL_BG    = "FFC7CE"   # 연한 빨강 (불합격)
CHECK_BG   = "FFEB9C"   # 연한 노랑 ([요확인])
```

### [B] Word (.docx)
읽을 스킬: `/mnt/skills/public/docx/SKILL.md`

표준 문서 구조:
```
[커버 페이지] — A4 세로 1페이지
  로고 자리 | 프로젝트명 | 문서 제목
  문서번호 | 버전 | 작성일 | 승인자

[문서 이력] — Rev / Date / Author / Description
[목차] — 자동 생성
[본문] — 섹션별 (1. / 1.1 / 1.1.1 체계)
[서명란] — 별도 페이지 (A4 하단 충분한 여백)
```

시험 항목 표 형식 (A4 최적화):
```
열 너비 비율 (총 160mm 기준 — 보고서 여백 좌30+우20=50mm):
No(10) | 시험명(38) | 기준(28) | 합격기준(32) | 결과(20) | 판정(16) | 서명(16)
글자 크기: 헤더 12pt Bold, 본문 12pt
```

테이블 너비 고정 규칙 (필수):
```
★ 모든 테이블의 col_widths 합계 = 160mm (A4 본문 폭)
  A4(210mm) - 좌여백(30mm) - 우여백(20mm) = 160mm

★ autofit 비활성화 (Word 자동 너비 조정 방지):
  tbl.autofit = False
  tblW = OxmlElement("w:tblW")
  tblW.set(qn("w:type"), "dxa")
  tblW.set(qn("w:w"), str(int(160 / 25.4 * 1440)))  # 160mm → twips
  tbl._tbl.tblPr.append(tblW)

★ 위반 시: 테이블이 페이지 경계를 넘거나 좌우 정렬이 깨짐 → 반려
```

### [C] Python 코드 (.py)

패턴 선택:
```python
# C-1: tkinter GUI (분석 도구)
class BESSAnalysisTool:
    """
    도구명: [Tool Name]
    버전: 1.0 | 작성: [날짜]
    실행: python tool_name.py
    의존성: pip install numpy pandas matplotlib openpyxl
    """

# C-2: 순수 계산 스크립트 (배치용)
def main():
    """BESS [분석유형] 계산 스크립트"""
    # 1. 파라미터 정의
    # 2. 계산 실행
    # 3. 결과 출력 (테이블 + 단위)
    # 4. Excel/PDF 저장 (선택)

# C-3: Streamlit 웹 앱 (인터랙티브)
import streamlit as st
st.set_page_config(page_title="BESS Analysis", layout="wide")
```

코드 품질 기준:
```
✅ 모듈 설명 docstring (도구명/버전/실행방법/의존성)
✅ 타입 힌트 (Python 3.8+)
✅ 에러 처리 (try/except + [요확인] 메시지)
✅ 단위 주석 (kW, kWh, %, 원/kWh)
✅ __main__ 진입점
✅ 계산 결과: 수치 + 단위 + 계산 근거 함께 출력
```

### [D] PDF (.pdf)
읽을 스킬: `/mnt/skills/public/pdf/SKILL.md`

생성 방식 선택:
1. **reportlab** — 프로그래밍 방식 (차트 포함 보고서)
2. **Word → PDF (docx2pdf)** — Windows COM 자동화 (Word 설치 필수, 품질 최우선)
3. **Word → PDF (LibreOffice)** — Linux/CI 환경 (soffice 변환)
4. **Excel → PDF** — 스프레드시트 (인쇄 영역 기준)

```python
# Word → PDF 변환 (Windows — docx2pdf, 권장)
# pip install docx2pdf
from docx2pdf import convert
import time
convert("input.docx", "output.pdf")
time.sleep(2)  # COM 해제 대기

# Word → PDF 변환 (Linux — LibreOffice)
# soffice --headless --convert-to pdf input.docx
```

### Word 문서 고급 패턴

#### TOC (목차) 표준 필드코드 삽입
> 📌 표준 TOC 삽입은 위 [검증된 필수 코드 패턴](#검증된-필수-코드-패턴-python-docx)의 `add_toc(doc)` 함수를 사용한다.
> 해당 정본 함수는 TOC 1/2 스타일 간격 축소 + `w:updateFields`(문서 열 때 자동 갱신)까지 포함한 완성형이므로, 별도 간이 변형(`add_toc_field`)은 사용하지 않는다.

#### 페이지 번호 (오른쪽 하단)
```python
# 푸터에 PAGE / NUMPAGES 필드코드 삽입
# fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT  ← 오른쪽 정렬
# PAGE 필드: fldChar begin → instrText ' PAGE ' → separate → '1' → end
# NUMPAGES 필드: 동일 패턴, instrText ' NUMPAGES '
```

#### Heading 스타일 커스텀 (색상/크기 통일)
```python
# Heading 1: Navy 16pt Bold (#1F4E79)
h1 = doc.styles['Heading 1']
h1.font.size = Pt(16)
h1.font.bold = True
h1.font.color.rgb = RGBColor.from_string("1F4E79")

# Heading 2: Blue 13pt Bold (#2E75B6)
h2 = doc.styles['Heading 2']
h2.font.size = Pt(13)
h2.font.bold = True
h2.font.color.rgb = RGBColor.from_string("2E75B6")
```

### [E] 인쇄용 패키지 (A4 최적화 동시 생성)

BESS 프로젝트 현장 지참용 패키지:
```
/output/[프로젝트코드]/print_package/
  ├── [코드]_Procedure_v[X].pdf     ← 절차서 (A4 세로)
  ├── [코드]_Checklist_v[X].xlsx    ← 체크리스트 (A4 가로, 인쇄 설정)
  ├── [코드]_Summary_v[X].pdf       ← 1페이지 요약 (A4 세로)
  └── README.txt                    ← 인쇄 순서 안내
```

체크리스트 인쇄 최적화 규칙:
```
- A4 가로 기준
- 판정란 (□P □F □N/A): 최소 8mm 높이 (손으로 체크 가능)
- 결과 기입란: 충분한 여백 (측정값 수기 기입 가능)
- 글자 크기: 본문 12pt, 표 내부 12pt (본문과 동일 통일)
- 한 행 높이: 최소 7mm
- 서명란 행 높이: 최소 12mm
```

### [F] 복합 출력 전략

최고 활용 조합:
| 사용 사례 | 조합 |
|---------|------|
| 시운전 현장 패키지 | Word(절차서) + Excel(체크리스트) + PDF(제출본) |
| 재무 분석 보고 | Python(계산코드) + Excel(모델) + PDF(경영보고) |
| 견적서 패키지 | Excel(BOQ) + Word(Cover Letter) + PDF(최종본) |
| 기술 제안서 | Word(본문) + Excel(비교표) + PDF(제출본) |

복합 출력 실행 순서:
```
1. 데이터/계산 처리 (Python 또는 직접)
2. Excel 생성 → A4 인쇄 설정 적용
3. Word 생성 → A4 여백·헤더·푸터 적용
4. PDF 변환 (Word/Excel → PDF)
5. /mnt/user-data/outputs/ 에 저장
6. present_files() 로 사용자에게 전달
```

---

## 콘텐츠 × 형식 매핑 테이블

| 콘텐츠 스킬 | Excel⭐ | Word⭐ | Python⭐ | PDF | PPT⭐ | 인쇄 패키지 |
|------------|--------|-------|---------|-----|-------|-----------|
| bess-precom-report | 체크리스트 | 절차서 ⭐ | - | 제출본 | 시운전 보고 | ⭐ 현장용 |
| bess-epc-bom | BOQ ⭐ | Cover Letter | 계산기 | 최종본 | 견적 제안 | 견적 패키지 |
| bess-grid-interconnection | 결과표 | 절차서 ⭐ | - | 제출본 | 계통연계 보고 | ⭐ 현장용 |
| bess-financial-analysis | 모델 ⭐ | 보고서 | 분석도구 ⭐ | 경영보고 | ⭐ 투자자 발표 | - |
| bess-system-engineer | 인터페이스표 | 설계서 ⭐ | - | 제출본 | 시스템 설명 | - |
| bess-ebop-engineer | 케이블스케줄 | SLD 보고서 | - | 제출본 | 전기설계 발표 | - |
| bess-cbop-engineer | 물량산출 | 배치 보고서 | - | 제출본 | 토건설계 발표 | - |
| bess-pcs-expert | 벤더비교 ⭐ | 사양검토서 | 제어코드 | 제출본 | PCS 기술 발표 | - |
| bess-battery-expert | 열화분석 ⭐ | 안전성보고서 | 분석도구 | 제출본 | 배터리 기술 발표 | - |
| bess-scheduler | 공정표 ⭐ | 공정보고서 | - | 제출본 | ⭐ 진도 보고 | - |
| bess-agent-framework | WBS | 프레임워크 | 구현코드 ⭐ | - | - | - |

---

## 파일 네이밍 규칙

```
[프로젝트코드]_[문서유형]_v[버전]_[날짜].[확장자]

예시:
HOK001_PreCommProcedure_v1.0_20250228.docx
HOK001_Checklist_v1.0_20250228.xlsx    ← 인쇄 설정 포함
ROM001_BOQ_v2.1_20250228.xlsx
BESS_FinancialModel_v1.3_20250228.xlsx
BESS_FinancialAnalyzer_v1.3.py
HOK001_InterconnectionTest_v1.0_20250228.pdf
```

---

## 목차(TOC) · 페이지 번호 · 하이퍼링크 필수 규칙

> **이 섹션의 규칙과 코드는 모든 DOCX 산출물에 예외 없이 적용한다.**
> 아래 "검증된 필수 코드 패턴"을 복사하여 그대로 사용하고 수정하지 않는다.

### 규칙 요약

| 항목 | 규칙 | 위반 시 |
|------|------|--------|
| 본문 폰트 | **12pt 통일** (`Normal` 스타일 강제 적용) | 반려 |
| 목차 | **Word TOC 필드** — 점선+페이지번호+하이퍼링크 자동 생성, 문서 열 때 자동 갱신 | 반려 |
| 페이지 번호 | **푸터 오른쪽 "Page X / Y"** — PAGE/NUMPAGES 필드 사용 | 반려 |
| 하이퍼링크 | **클릭 가능한 실제 하이퍼링크** — `w:hyperlink + part.relate_to()` 구조 | 반려 |

> ❌ 수동 텍스트 목차 / 텍스트 URL / 페이지 번호 직접 입력 → 절대 금지

> 📌 **코드 본체는 위 [검증된 필수 코드 패턴 (python-docx)](#검증된-필수-코드-패턴-python-docx) 섹션의 `add_hyperlink` / `add_toc` / `add_page_number` 3개 함수를 그대로 복사·사용한다.** (중복 게재 제거 — 단일 정본 유지)

---

### 적용 체크리스트 (출력 전 필수 확인)

```
DOCX 필수 3종 세트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
□ add_toc(doc)           호출됨?  → 목차 페이지에서 호출
□ add_page_number(sec)   호출됨?  → section 설정 후 즉시 호출
□ add_hyperlink() 사용   확인?    → Sources 테이블 URL 셀 전부

하이퍼링크 검증
□ part.relate_to() 로 r:id 생성
□ w:hyperlink 요소 안에 w:r 직접 생성 (paragraph.add_run() 사용 금지)
□ w:rPr 안에 color/u/sz/szCs 모두 삽입

TOC 검증
□ instrText = ' TOC \o "1-2" \h \z \u ' (공백 포함)
□ w:updateFields val="true" → settings 요소에 추가
□ TOC 1/2 스타일: 10pt, space 0pt, line_spacing 11pt (최소 간격)
□ 문서 열 때 자동 갱신 확인 (최초 저장 후 재열기로 확인)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---


## 협업 관계
```
[전부서]         ──형식검토──▶   [출력관리자] ──표준화문서──▶ [최종수신자]
[프로젝트매니저]  ──보고서──▶    [출력관리자] ──형식적용──▶  [발주처/경영진]
[홍보전문가]     ──발표자료──▶   [출력관리자] ──인쇄최적화──▶ [대상청중]
```

---

## 하지 않는 것
- 콘텐츠 생성 → 해당 BESS 전문가 스킬이 담당
- 단가·수치 임의 가정 → 반드시 해당 스킬에서 [요확인] 태그 발행
- 인쇄 설정 없이 Excel 생성 (화면 전용 출력은 반쪽짜리 산출물)
- 차트 없이 보고서 출력 → 최소 3개 시각화 포함 필수
- 목차 없이 문서 출력 → 3페이지 이상 문서는 점선+페이지번호 포함 TOC 필수
- URL을 일반 텍스트로 삽입 → 반드시 클릭 가능한 하이퍼링크로 삽입
- 푸터 페이지 번호 없이 문서 출력 → 오른쪽 하단 "Page X / Y" 필수

## 운영 학습 (Operational Learnings)

> 근거: `.connect-ai-bess-brain` 세션 마이닝 (2026-06-08). 전 도메인 공통 규칙은 [`CONSISTENCY_GUARDRAILS.md`](./CONSISTENCY_GUARDRAILS.md) 참조.

### 재사용 지식 (세션 누적)
- 견적서(Q)/BOM 필수항목 스키마: 부품명/부품번호/제조사/모델/단가/수량/총액/세금·운송 + 참고출처(URL+수집일) 의무 — 근거: `sessions/2026-06-05T01-17-31/bess-output-generator.md`
- A4 인쇄 표준 "옵션 A": 단면 대칭, 25mm 4-방향 여백, 헤더/푸터/페이지번호/제목행 반복 — 근거: `sessions/2026-06-05T01-17-31/bess-output-generator.md`
- 자동화 파이프라인 규약: CSV→pandas→FPDF/Excel 자동 생성, BOM↔견적 데이터 연계(변경 자동 반영), 계층 BOM 추적성 — 근거: `sessions/2026-05-21T06-28-02/bess-output-generator.md`
- 출처 표기 규약: 모든 데이터에 [출처명]-[URL/문서참조]-[수집일] 3요소(CLAUDE.md 하이퍼링크 증거 원칙과 일치) — 근거: `sessions/2026-06-05T01-17-31/bess-output-generator.md`

### 정합성 가드레일 (반복 오류 차단)
- ❌ frontmatter `department: "Support / Document Team"`(영문) vs 타 도메인 "운영본부(COO 산하)" 드리프트 → ✅ 부서명 "운영본부(COO 산하)" 한글 단일 표기 — 근거: `00_Skill_MD/bess-output-generator.md`
- ❌ 예시 출처 placeholder 환각(examplebattery.com / 2023-04-15 등 가짜 URL·과거일자) → ✅ 실제 출처로 치환 강제, example.com·과거 placeholder 금지 — 근거: `sessions/2026-06-05T13-23-17/bess-output-generator.md`
