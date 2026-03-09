import os
import datetime
import tempfile
import platform
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# 한글 폰트 설정: Windows=맑은 고딕, Linux=Noto Sans CJK KR (설치 필요: packages.txt)
def _set_korean_font():
    if platform.system() == "Windows":
        matplotlib.rcParams["font.family"] = "Malgun Gothic"
        return
    # Linux: Noto CJK 폰트 파일 직접 탐색
    import matplotlib.font_manager as fm
    noto_candidates = [f for f in fm.findSystemFonts() if "NotoSansCJK" in f or "NotoSerifCJK" in f or "noto" in f.lower()]
    if noto_candidates:
        prop = fm.FontProperties(fname=noto_candidates[0])
        matplotlib.rcParams["font.family"] = prop.get_name()
    else:
        # 폰트 없으면 영문 레이블 사용 (chart 제목/축은 영문으로 이미 변경됨)
        matplotlib.rcParams["font.family"] = "DejaVu Sans"

_set_korean_font()
matplotlib.rcParams["axes.unicode_minus"] = False

from docx import Document
from docx.shared import Pt, Mm, Inches, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

import utils.market_data as md

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False


FONT = "맑은 고딕"
CLR_H1 = RGBColor(0x1F, 0x4E, 0x79)       # Navy #1F4E79
CLR_H2 = RGBColor(0x2E, 0x75, 0xB6)       # Blue #2E75B6
CLR_LINK = "2196F3"
CLR_PAGE_NUM = "9E9E9E"
CLR_HEADER_BG = "1F4E79"
CLR_ALT_ROW = "F2F7FB"

# ================= DOCX Utilities =================

def add_hyperlink(paragraph, url: str, text: str, size_pt: float = 10):
    part = paragraph.part
    r_id = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
    hl = OxmlElement("w:hyperlink")
    hl.set(qn("r:id"), r_id)
    run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    rFonts = OxmlElement("w:rFonts")
    rFonts.set(qn("w:ascii"), "Calibri")
    rFonts.set(qn("w:eastAsia"), "맑은 고딕")
    rPr.append(rFonts)
    color = OxmlElement("w:color")
    color.set(qn("w:val"), CLR_LINK)
    rPr.append(color)
    u = OxmlElement("w:u")
    u.set(qn("w:val"), "single")
    rPr.append(u)
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

def add_toc(doc):
    from docx.shared import Mm as _Mm
    for lvl, indent in [("TOC 1", _Mm(0)), ("TOC 2", _Mm(5))]:
        try:
            toc_style = doc.styles[lvl]
        except KeyError:
            toc_style = doc.styles.add_style(lvl, 1)
        toc_style.font.size = Pt(10)
        toc_style.font.name = FONT
        toc_style.paragraph_format.space_before = Pt(0)
        toc_style.paragraph_format.space_after = Pt(0)
        toc_style.paragraph_format.line_spacing = Pt(11)
        toc_style.paragraph_format.left_indent = indent
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
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
    placeholder = p.add_run("목차 갱신: Ctrl+A → F9")
    placeholder.italic = True
    placeholder.font.size = Pt(9)
    placeholder.font.color.rgb = RGBColor(0x80, 0x80, 0x80)
    _fld_run("end")
    settings = doc.settings.element
    upd = OxmlElement("w:updateFields")
    upd.set(qn("w:val"), "true")
    settings.append(upd)

def add_page_number(section):
    footer = section.footer
    para = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    para.clear()
    para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    def _r(fld_type=None, instr=None, literal=None):
        r = OxmlElement("w:r")
        rPr = OxmlElement("w:rPr")
        for tag, val in [("w:sz", "18"), ("w:szCs", "18")]:
            el = OxmlElement(tag); el.set(qn("w:val"), val); rPr.append(el)
        clr = OxmlElement("w:color"); clr.set(qn("w:val"), CLR_PAGE_NUM); rPr.append(clr)
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

def _setup_doc(title=None):
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = FONT
    style.font.size = Pt(12)
    style.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    h1 = doc.styles["Heading 1"]
    h1.font.size = Pt(16)
    h1.font.bold = True
    h1.font.color.rgb = CLR_H1
    h1.font.name = FONT
    h1.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    h1.paragraph_format.page_break_before = False
    h2 = doc.styles["Heading 2"]
    h2.font.size = Pt(13)
    h2.font.bold = True
    h2.font.color.rgb = CLR_H2
    h2.font.name = FONT
    h2.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    h2.paragraph_format.page_break_before = False
    try:
        h3 = doc.styles["Heading 3"]
    except KeyError:
        h3 = doc.styles.add_style("Heading 3", 1)
    h3.font.size = Pt(12)
    h3.font.bold = True
    h3.font.color.rgb = CLR_H2
    h3.font.name = FONT
    sec = doc.sections[0]
    sec.page_width = Mm(210)
    sec.page_height = Mm(297)
    sec.top_margin = Mm(25)
    sec.bottom_margin = Mm(25)
    sec.left_margin = Mm(30)
    sec.right_margin = Mm(20)
    sec.header_distance = Mm(12)
    sec.footer_distance = Mm(12)
    if title:
        header = sec.header
        hp = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hr = hp.add_run(title)
        hr.font.size = Pt(8)
        hr.font.color.rgb = RGBColor(0x80, 0x80, 0x80)
        hr.font.name = FONT
    return doc

def _styled_table(doc, headers, rows, col_widths_mm=None):
    n_cols = len(headers)
    tbl = doc.add_table(rows=1 + len(rows), cols=n_cols)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    tblPr = tbl._tbl.tblPr
    tblW = OxmlElement("w:tblW")
    tblW.set(qn("w:type"), "dxa")
    tblW.set(qn("w:w"), str(int(160 / 25.4 * 1440)))
    tblPr.append(tblW)
    if col_widths_mm is None:
        col_widths_mm = [160 / n_cols] * n_cols
    for i, w in enumerate(col_widths_mm):
        tw = int(w / 25.4 * 1440)
        for row_idx in range(1 + len(rows)):
            cell = tbl.cell(row_idx, i)
            cell.width = Emu(tw * 635)
    for i, h in enumerate(headers):
        cell = tbl.cell(0, i)
        cell.text = ""
        p = cell.paragraphs[0]
        r = p.add_run(str(h))
        r.bold = True
        r.font.size = Pt(12)
        r.font.name = FONT
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        tcPr = cell._element.find(qn("w:tcPr"))
        if tcPr is None:
            tcPr = OxmlElement("w:tcPr")
            cell._element.insert(0, tcPr)
        shading = OxmlElement("w:shd")
        shading.set(qn("w:val"), "clear")
        shading.set(qn("w:color"), "auto")
        shading.set(qn("w:fill"), CLR_HEADER_BG)
        tcPr.append(shading)
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = tbl.cell(ri + 1, ci)
            cell.text = ""
            p = cell.paragraphs[0]
            r = p.add_run(str(val))
            r.font.size = Pt(12)
            r.font.name = FONT
            if ri % 2 == 1:
                tcPr = cell._element.find(qn("w:tcPr"))
                if tcPr is None:
                    tcPr = OxmlElement("w:tcPr")
                    cell._element.insert(0, tcPr)
                shading = OxmlElement("w:shd")
                shading.set(qn("w:val"), "clear")
                shading.set(qn("w:color"), "auto")
                shading.set(qn("w:fill"), CLR_ALT_ROW)
                tcPr.append(shading)
    return tbl

def _add_news_section(doc, category, max_items=5, analysis: str = ""):
    feed = md.fetch_rss_feed(category, max_items=max_items)
    news = feed.get("items", [])
    heading_text = (f"[{category}] 분석 및 최신 뉴스" if analysis
                    else f"[{category}] 관련 최신 뉴스")
    doc.add_heading(heading_text, level=2)
    if analysis:
        p = doc.add_paragraph(analysis)
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(6)
        for run in p.runs:
            run.font.size = Pt(10)
            run.font.name = FONT
    if not news:
        doc.add_paragraph(
            "⚠️ 실시간 뉴스를 가져오지 못했습니다. (네트워크 접근 제한 또는 일시적 오류일 수 있습니다.)",
            style="Normal"
        )
        return []
    for item in news[:max_items]:
        p = doc.add_paragraph(style="List Bullet")
        title = item.get("title", "")
        link = item.get("link", "")
        if link:
            add_hyperlink(p, link, title)
        else:
            r = p.add_run(title)
            r.font.size = Pt(12)
            r.font.name = FONT
    return news

def _add_chart_to_doc(doc, fig, width_inches=5.8):
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.close()
    try:
        fig.savefig(tmp.name, dpi=200, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        doc.add_picture(tmp.name, width=Inches(width_inches))
        last_p = doc.paragraphs[-1]
        last_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass

def _chart_growth():
    yr = md.LATEST_ACTUAL_YEAR
    names = [md.REGIONAL_DATA[r]["name_en"] for r in md.REGIONS]
    gwh = [md.REGIONAL_DATA[r]["installed_gwh"].get(yr, 0) for r in md.REGIONS]
    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(names, gwh, color=["#1F4E79", "#2E75B6", "#5B9BD5", "#A5C8E1", "#D6E4F0", "#F0C27B", "#E8856C"])
    ax.set_ylabel("Installed Capacity (GWh)")
    ax.set_title(f"BESS Installed Capacity by Market ({yr})", fontsize=13, fontweight="bold")
    for bar, val in zip(bars, gwh):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3, f"{val}", ha="center", fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return fig

def _chart_region():
    yr = md.LATEST_ACTUAL_YEAR
    names = [md.REGIONAL_DATA[r]["name_en"] for r in md.REGIONS]
    gwh = [md.REGIONAL_DATA[r]["installed_gwh"].get(yr, 0) for r in md.REGIONS]
    fig, ax = plt.subplots(figsize=(7, 5))
    colors = ["#1F4E79", "#2E75B6", "#5B9BD5", "#A5C8E1", "#D6E4F0", "#F0C27B", "#E8856C"]
    ax.pie(gwh, labels=names, autopct="%1.1f%%", colors=colors, startangle=90)
    ax.set_title(f"BESS Market Share by Region ({yr})", fontsize=13, fontweight="bold")
    fig.tight_layout()
    return fig


# ================= Main Generator =================

def generate_word_report():
    """Generates a BESS Deep Analysis Word (.docx) report."""
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))  # KST
    now_str = now.strftime("%Y-%m-%d")
    
    if os.path.isdir("/data"):
        out_dir = "/data/output_reports"
    else:
        out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "output_reports"))
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"BESS_DeepAnalysis_{now.strftime('%Y%m%d%H%M%S')}.docx")

    doc = _setup_doc()
    sec0 = doc.sections[0]

    # Cover Page
    for _ in range(4): doc.add_paragraph()
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    tr = title_p.add_run("BESS 심층 시장 분석 보고서")
    tr.font.size = Pt(28)
    tr.font.bold = True
    tr.font.color.rgb = CLR_H1
    tr.font.name = FONT

    sub_p = doc.add_paragraph()
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sr = sub_p.add_run("Deep Market Intelligence Analysis")
    sr.font.size = Pt(16)
    sr.font.color.rgb = CLR_H2

    doc.add_paragraph()
    date_p = doc.add_paragraph()
    date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    date_p.add_run(now_str).font.size = Pt(12)

    for _ in range(3): doc.add_paragraph()
    org_p = doc.add_paragraph()
    org_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    org_p.add_run("BESS EPC AI Agent System").font.size = Pt(12)

    # TOC
    _toc_h = doc.add_heading("목차", level=1)
    _toc_h.paragraph_format.page_break_before = True
    add_toc(doc)
    add_page_number(sec0)

    # 1. Executive Summary
    _h1 = doc.add_heading("1. Executive Summary", level=1)
    _h1.paragraph_format.page_break_before = True
    doc.add_paragraph(
        "본 보고서는 주요 글로벌 대상 시장의 BESS(Battery Energy Storage System) 산업 동향을 심층적으로 분석합니다. "
        "분석 시점 기준 글로벌 시장의 성장률과 가격 동향, 정책 프레임워크를 조망합니다."
    )
    doc.add_heading("핵심 지표 요약", level=2)
    _yr = md.LATEST_ACTUAL_YEAR
    summary_rows = [
        [f"글로벌 {_yr}년 설치 용량", f"{md.GLOBAL_CAPACITY_GWH.get(_yr, 'N/A')} GWh"],
        [f"LFP 셀 가격 ({_yr})", f"${md.LFP_CELL_PRICE.get(_yr, 'N/A')}/kWh"],
        [f"NMC 셀 가격 ({_yr})", f"${md.NMC_CELL_PRICE.get(_yr, 'N/A')}/kWh"],
        [f"시스템 CAPEX ({_yr})", f"${md.SYSTEM_CAPEX.get(_yr, 'N/A')}/kWh"],
        ["분석 시점", now_str],
    ]
    _styled_table(doc, ["항목", "값"], summary_rows, col_widths_mm=[70, 90])

    # Section 1 interpretation
    _lfp_2022 = md.LFP_CELL_PRICE.get(2022, 80)
    _lfp_cur  = md.LFP_CELL_PRICE.get(_yr, _lfp_2022)
    _lfp_drop = round((1 - _lfp_cur / _lfp_2022) * 100)
    _cap_cur  = md.GLOBAL_CAPACITY_GWH.get(_yr, 0)
    _cap_prev = md.GLOBAL_CAPACITY_GWH.get(_yr - 1, 0)
    _yoy_g    = round((_cap_cur - _cap_prev) / _cap_prev * 100) if _cap_prev else 0
    _mkt_val  = md.GLOBAL_MARKET_VALUE_B_USD.get(_yr, 0)
    _p_interp = doc.add_paragraph(
        f"글로벌 BESS 시장은 {_yr}년 {_cap_cur} GWh를 기록하며 전년 대비 {_yoy_g}% 성장하였습니다. "
        f"시장 규모는 약 ${_mkt_val}B USD로, LFP 셀 단가는 2022년($80/kWh) 대비 {_lfp_drop}% 하락한 "
        f"${_lfp_cur}/kWh까지 내려왔습니다. "
        "가격 하락·정책 지원 확대·재생에너지 연계 수요 증가가 복합적으로 시장 성장을 견인하고 있으며, "
        "2027년 370 GWh 돌파가 전망됩니다."
    )
    _p_interp.paragraph_format.space_before = Pt(4)
    for _r in _p_interp.runs:
        _r.font.size = Pt(10); _r.font.name = FONT

    # 2. 시장별 심층 분석
    _h2 = doc.add_heading("2. 시장별 심층 분석", level=1)
    _h2.paragraph_format.page_break_before = True
    for idx, r_name in enumerate(md.REGIONS):
        r_data = md.REGIONAL_DATA[r_name]
        doc.add_heading(f"2.{idx+1} {r_name} ({r_data['name_en']})", level=2)

        _cur_r  = r_data["installed_gwh"].get(_yr, 0)
        _prev_r = r_data["installed_gwh"].get(_yr - 1, 0)
        _yoy_r  = round((_cur_r - _prev_r) / _prev_r * 100) if _prev_r else 0
        _kp     = ", ".join(r_data.get("key_players", [])[:5])
        _avg_sz = r_data.get("avg_project_size_mwh", "N/A")
        _scale  = "대형 그리드 스케일" if isinstance(_avg_sz, (int, float)) and _avg_sz >= 200 else "중소형"
        _p_ov = doc.add_paragraph(
            f"{r_name} 시장은 {_yr}년 {_cur_r} GWh를 기록하여 전년 대비 {_yoy_r}% 성장하였습니다. "
            f"파이프라인 {r_data['pipeline_gwh']} GWh로 향후 성장 잠재력이 크며, "
            f"평균 프로젝트 규모 {_avg_sz} MWh의 {_scale} 시장이 주도합니다. "
            f"주요 참여 기업: {_kp}."
        )
        _p_ov.paragraph_format.space_after = Pt(4)
        for _r in _p_ov.runs:
            _r.font.size = Pt(10); _r.font.name = FONT

        detail_rows = [
            [f"설치 용량 ({_yr})", f"{_cur_r} GWh"],
            [f"YoY 성장률 ({_yr - 1}→{_yr})", f"+{_yoy_r}%"],
            ["중기 연간 성장률", f"{r_data['growth_rate_pct']}%"],
            ["파이프라인 (허가/계획)", f"{r_data['pipeline_gwh']} GWh"],
            ["주요 수익 모델", r_data['revenue_model']],
        ]
        _styled_table(doc, ["항목", "데이터"], detail_rows, col_widths_mm=[55, 105])

        doc.add_heading("주요 성장 동인", level=3)
        for kd in r_data.get("key_drivers", []):
            doc.add_paragraph(kd, style="List Bullet")

        doc.add_heading("정책 환경 및 규제", level=3)
        for p in r_data['policy']:
            doc.add_paragraph(p, style="List Bullet")

        _add_news_section(doc, f"{r_name} 시장", 3)

    # 3. 주요 카테고리별 전문 동향
    _h3 = doc.add_heading("3. 전문 카테고리 분석", level=1)
    _h3.paragraph_format.page_break_before = True
    doc.add_paragraph("BESS 사업에 영향을 미치는 주요 거시적 및 미시적 카테고리 이슈 현황입니다.")
    _yr = md.LATEST_ACTUAL_YEAR
    _CAT_ANALYSIS = {
        "배터리 가격": (
            f"LFP 셀 단가는 공급 과잉과 기술 혁신으로 지속 하락하여 {_yr}년 기준 "
            f"${md.LFP_CELL_PRICE.get(_yr, 'N/A')}/kWh 수준이며, NMC는 "
            f"${md.NMC_CELL_PRICE.get(_yr, 'N/A')}/kWh입니다. "
            "중국 제조사의 규모의 경제가 가격 하락을 주도하고 있으며, "
            f"시스템 CAPEX({_yr}: ${md.SYSTEM_CAPEX.get(_yr, 'N/A')}/kWh)는 "
            "향후 2~3년 내 $150/kWh 이하 진입이 전망됩니다."
        ),
        "프로젝트": (
            "글로벌 BESS 프로젝트는 대형화·장시간화 추세로 4시간 이상 장기저장 비중이 확대되고 있습니다. "
            "미국·영국·호주를 중심으로 그리드 스케일 독립형(Standalone) BESS 프로젝트가 급증하며, "
            "재생에너지 연계 하이브리드 구성이 EPC 수주의 핵심 형태로 부각됩니다. "
            "PPA 기반 장기 수익 모델과 주파수 조정(FR)·용량 시장(Capacity Market) 참여가 사업성의 핵심입니다."
        ),
        "경쟁사": (
            "글로벌 BESS 시장은 CATL, BYD 등 중국 제조사와 Tesla Megapack, Fluence, Wärtsilä 등 "
            "통합 솔루션 공급자 간 경쟁이 심화되고 있습니다. "
            "EPC 관점에서는 시스템 통합 역량과 O&M 서비스 패키지가 핵심 차별화 요소이며, "
            "현지화 전략 및 프로젝트 파이낸싱 조달 역량이 수주 경쟁력을 결정합니다."
        ),
        "공급망": (
            "리튬·코발트·망간 등 핵심 광물의 공급망 안정성이 BESS 원가 리스크의 핵심 변수입니다. "
            "미국 IRA(인플레이션 감축법) 시행으로 북미 현지 생산 수요가 급증하였고, "
            "공급망 다변화를 위한 한국·일본·유럽 제조사의 현지 투자가 가속화되고 있습니다. "
            "셀 소싱 전략(단일 vs 멀티 공급사)이 프로젝트 리스크 관리의 핵심 요소로 부상하고 있습니다."
        ),
        "정책·규제": (
            "미국 IRA, 유럽 Net-Zero Industry Act, 영국 Capacity Market 등 주요 시장의 정책 지원이 "
            "BESS 수요를 견인하고 있습니다. "
            "계통 연계 기준(Grid Code) 및 안전 규정(NFPA 855, IEC 62933) 강화가 진행 중이며, "
            "ESS 화재 안전 기준과 소방 설계가 프로젝트 인허가의 핵심 요건으로 부상하고 있습니다. "
            "각국의 탄소중립 로드맵 이행이 중장기 BESS 수요 성장의 근본 동인입니다."
        ),
    }
    for c in ["배터리 가격", "프로젝트", "경쟁사", "공급망", "정책·규제"]:
        _add_news_section(doc, c, 5, analysis=_CAT_ANALYSIS.get(c, ""))

    # 4. 시각화
    _h4 = doc.add_heading("4. 시각화 분석", level=1)
    _h4.paragraph_format.page_break_before = True
    _yr4 = md.LATEST_ACTUAL_YEAR
    _bars = [(r, md.REGIONAL_DATA[r]["name_en"],
              md.REGIONAL_DATA[r]["installed_gwh"].get(_yr4, 0),
              md.REGIONAL_DATA[r]["growth_rate_pct"]) for r in md.REGIONS]
    _total4 = sum(x[2] for x in _bars)
    _bars_sorted = sorted(_bars, key=lambda x: x[2], reverse=True)
    _top3_sum4   = sum(x[2] for x in _bars_sorted[:3])
    _top3_pct4   = round(_top3_sum4 / _total4 * 100) if _total4 else 0
    _fastest4    = sorted(_bars, key=lambda x: x[3], reverse=True)[0]

    doc.add_heading("4.1 시장별 설치 용량", level=2)
    _add_chart_to_doc(doc, _chart_growth())
    _p_bar = doc.add_paragraph(
        f"[그림 분석] {_yr4}년 글로벌 설치 용량 합계 {_total4:.1f} GWh 중, "
        f"{_bars_sorted[0][1]}({_bars_sorted[0][2]} GWh)이 1위를 차지합니다. "
        f"상위 3개 시장({', '.join(x[1] for x in _bars_sorted[:3])})의 합산 비중은 "
        f"{_top3_pct4}%로 시장 집중도가 높습니다. "
        f"성장률 최고 시장은 {_fastest4[0]}({_fastest4[1]}, 중기 CAGR {_fastest4[3]}%)로 "
        f"신흥 시장 중 가장 빠른 확대세를 보입니다."
    )
    _p_bar.paragraph_format.space_before = Pt(4)
    for _r in _p_bar.runs:
        _r.font.size = Pt(10); _r.font.name = FONT

    _pie_sorted = sorted(_bars, key=lambda x: x[2], reverse=True)
    _shares4    = [(x[1], round(x[2] / _total4 * 100, 1)) for x in _pie_sorted]
    _top3_sh    = round(sum(s[1] for s in _shares4[:3]), 1)

    doc.add_heading("4.2 지역별 시장 점유율", level=2)
    _add_chart_to_doc(doc, _chart_region())
    _p_pie = doc.add_paragraph(
        f"[그림 분석] {_shares4[0][0]}이 {_shares4[0][1]}%로 압도적 1위이며, "
        f"{_shares4[1][0]} {_shares4[1][1]}%, {_shares4[2][0]} {_shares4[2][1]}%가 뒤를 잇습니다. "
        f"상위 3개 지역 합산 점유율 {_top3_sh}%로 시장이 집중되어 있으며, "
        f"{_shares4[-1][0]}({_shares4[-1][1]}%)는 아직 소규모이나 "
        f"중기 성장률 {_fastest4[3]}%로 가장 빠른 성장이 전망됩니다."
    )
    _p_pie.paragraph_format.space_before = Pt(4)
    for _r in _p_pie.runs:
        _r.font.size = Pt(10); _r.font.name = FONT

    # 5. 시나리오 분석
    _h5 = doc.add_heading("5. 시나리오 분석", level=1)
    _h5.paragraph_format.page_break_before = True
    doc.add_paragraph("각국 시장 및 거시경제 상황에 따른 BESS 확산 중장기 시나리오 전망입니다.")
    scen_rows = []
    scen_rows.append(["연도", "보수적", "기준", "낙관적"])
    for yr in md.YEARS:
        cons = md.SCENARIOS["보수적 (Conservative)"]["capacity_gwh"].get(yr, 0)
        base = md.SCENARIOS["기본 (Base)"]["capacity_gwh"].get(yr, 0)
        opti = md.SCENARIOS["낙관적 (Optimistic)"]["capacity_gwh"].get(yr, 0)
        scen_rows.append([str(yr), f"{cons} GWh", f"{base} GWh", f"{opti} GWh"])
    _styled_table(doc, scen_rows[0], scen_rows[1:], col_widths_mm=[30, 40, 40, 40])

    # Section 5 interpretation
    _sb = md.SCENARIOS["기본 (Base)"]
    _sc = md.SCENARIOS["보수적 (Conservative)"]
    _so = md.SCENARIOS["낙관적 (Optimistic)"]
    _p_scen = doc.add_paragraph(
        f"기본 시나리오({_sb['description']}) 기준 2024~2030년 CAGR {_sb['cagr_pct']}%로 "
        f"2030년 {_sb['capacity_gwh'].get(2030, 0)} GWh(시장 가치 ${_sb['market_value_b'].get(2030, 0)}B)가 전망됩니다. "
        f"낙관 시나리오({_so['description']}) 실현 시 CAGR {_so['cagr_pct']}%로 "
        f"2030년 {_so['capacity_gwh'].get(2030, 0)} GWh까지 확대 가능하며, "
        f"보수 시나리오({_sc['description']}) 하에서도 {_sc['capacity_gwh'].get(2030, 0)} GWh(CAGR {_sc['cagr_pct']}%)로 "
        "견조한 성장이 예상됩니다. "
        "시나리오 편차의 핵심 변수는 IRA·RE정책 지속성, 배터리 가격 하락 속도, "
        "전력시장 설계 개혁의 실행 속도입니다."
    )
    _p_scen.paragraph_format.space_before = Pt(4)
    for _r in _p_scen.runs:
        _r.font.size = Pt(10); _r.font.name = FONT

    doc.save(out_path)
    return out_path

def generate_pdf_report():
    """Generate PDF by converting the Word Deep Report via docx2pdf in an STA thread."""
    import threading
    import shutil
    import docx2pdf

    word_path = generate_word_report()
    pdf_path = word_path.replace('.docx', '.pdf')

    # COM/Word cannot handle paths with Korean (non-ASCII) characters.
    # Convert using an ASCII temp path, then copy to the final destination.
    tmp_dir = tempfile.gettempdir()
    tmp_docx = os.path.join(tmp_dir, "bess_report_tmp.docx")
    tmp_pdf  = os.path.join(tmp_dir, "bess_report_tmp.pdf")
    shutil.copy2(word_path, tmp_docx)

    errors = []
    def _convert():
        try:
            import pythoncom
            pythoncom.CoInitialize()
            try:
                docx2pdf.convert(tmp_docx, tmp_pdf)
            finally:
                pythoncom.CoUninitialize()
        except Exception as e:
            errors.append(e)

    t = threading.Thread(target=_convert, daemon=True)
    t.start()
    t.join(timeout=120)

    if errors:
        raise RuntimeError(f"PDF 변환 오류: {errors[0]}")

    if os.path.exists(tmp_pdf):
        shutil.copy2(tmp_pdf, pdf_path)
        for p in (tmp_docx, tmp_pdf):
            try:
                os.unlink(p)
            except Exception:
                pass
        return os.path.abspath(pdf_path)
    raise FileNotFoundError(f"PDF가 생성되지 않았습니다: {pdf_path}")
