"""Low-level OpenXML (lxml / python-docx) helpers for hyoword v2.0."""

from __future__ import annotations
import re
from typing import Iterable, Optional
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from .design import COLORS, FontProfile, mm_to_twips, pt_to_half_pt, pt_to_twips

# Regex for inline rich markup:
# 1) [TO BE CONFIRMED...] / [확인 필요...] / [TBD] / [TBC]
# 2) ~~strikethrough~~
# 3) ++inserted++
# 4) `code`
# 5) **bold**
# 6) *italic*
INLINE_TOKEN_RE = re.compile(
    r"(\[(?:TO BE CONFIRMED|확인\s*필요|TBD|TBC|HOLD)[^\]]*\]"
    r"|~~.+?~~"
    r"|\+\+.+?\+\+"
    r"|`[^`]+`"
    r"|\*\*.+?\*\*"
    r"|\*[^*\n]+\*)",
    re.DOTALL,
)


def _get_or_add(parent, tag_name: str):
    child = parent.find(qn(tag_name))
    if child is None:
        child = OxmlElement(tag_name)
        parent.append(child)
    return child


def set_rpr_fonts(rPr, profile: FontProfile, mono: bool = False):
    """Set w:rFonts deterministically and strip any theme font attributes."""
    rFonts = _get_or_add(rPr, "w:rFonts")
    for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme", "w:hint"):
        if qn(attr) in rFonts.attrib:
            del rFonts.attrib[qn(attr)]
    if mono:
        rFonts.set(qn("w:ascii"), profile.mono)
        rFonts.set(qn("w:hAnsi"), profile.mono)
        rFonts.set(qn("w:eastAsia"), profile.east_asia)
        rFonts.set(qn("w:cs"), profile.mono)
    else:
        rFonts.set(qn("w:ascii"), profile.latin)
        rFonts.set(qn("w:hAnsi"), profile.latin)
        rFonts.set(qn("w:eastAsia"), profile.east_asia)
        rFonts.set(qn("w:cs"), profile.complex_script)


def apply_run_style(
    run,
    profile: FontProfile,
    size_pt: Optional[float] = 10.5,
    bold: Optional[bool] = None,
    italic: Optional[bool] = None,
    underline: Optional[bool] = None,
    strike: Optional[bool] = None,
    color_hex: Optional[str] = COLORS["charcoal"],
    shd_fill: Optional[str] = None,
    mono: bool = False,
):
    """Apply complete typography and OpenXML properties to a python-docx Run."""
    rPr = run._r.get_or_add_rPr()
    set_rpr_fonts(rPr, profile, mono=mono)

    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if underline is not None:
        run.underline = underline
    if strike:
        strike_el = _get_or_add(rPr, "w:strike")
        strike_el.set(qn("w:val"), "true")

    if size_pt is not None:
        half_pt = str(pt_to_half_pt(size_pt))
        sz = _get_or_add(rPr, "w:sz")
        sz.set(qn("w:val"), half_pt)
        szCs = _get_or_add(rPr, "w:szCs")
        szCs.set(qn("w:val"), half_pt)

    if color_hex:
        clr = _get_or_add(rPr, "w:color")
        for attr in ("w:themeColor", "w:themeTint", "w:themeShade"):
            if qn(attr) in clr.attrib:
                del clr.attrib[qn(attr)]
        clr.set(qn("w:val"), color_hex.lstrip("#").upper())

    if shd_fill:
        shd = _get_or_add(rPr, "w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), shd_fill.lstrip("#").upper())


def append_rich_text(
    paragraph,
    text: str,
    profile: FontProfile,
    base_size_pt: float = 10.5,
    base_color: str = COLORS["charcoal"],
    base_bold: bool = False,
    base_italic: bool = False,
):
    """Parse inline tokens (**bold**, *italic*, `code`, ~~del~~, ++ins++, [TBC...]) and add runs.

    Tokens may nest (e.g. **bold with `code`** or ++inserted **bold**++); inner markup is parsed recursively.
    """
    if text is None:
        return
    base_style = {"size_pt": base_size_pt, "bold": base_bold, "italic": base_italic, "color_hex": base_color}
    _append_inline_tokens(paragraph, str(text), profile, base_style)


def _append_inline_tokens(paragraph, text: str, profile: FontProfile, style: dict):
    for part in INLINE_TOKEN_RE.split(text):
        if not part:
            continue
        if (
            part.startswith("[")
            and part.endswith("]")
            and re.match(r"^\[(?:TO BE CONFIRMED|확인\s*필요|TBD|TBC|HOLD)", part, re.IGNORECASE)
        ):
            r = paragraph.add_run(part)
            apply_run_style(
                r,
                profile,
                size_pt=max(style["size_pt"] - 0.5, 8.5),
                bold=True,
                italic=False,
                color_hex=COLORS["main_purple"],
            )
        elif part.startswith("~~") and part.endswith("~~") and len(part) > 4:
            _append_inline_tokens(
                paragraph,
                part[2:-2],
                profile,
                {**style, "strike": True, "color_hex": COLORS["fail_fg"], "shd_fill": COLORS["fail_bg"]},
            )
        elif part.startswith("++") and part.endswith("++") and len(part) > 4:
            _append_inline_tokens(
                paragraph,
                part[2:-2],
                profile,
                {**style, "bold": True, "underline": True, "color_hex": COLORS["main_purple"], "shd_fill": COLORS["soft_lavender"]},
            )
        elif part.startswith("`") and part.endswith("`") and len(part) > 2:
            # Inline code renders in the surrounding body style so values and standards do not read as source code
            r = paragraph.add_run(part[1:-1])
            apply_run_style(r, profile, **style)
        elif part.startswith("**") and part.endswith("**") and len(part) > 4:
            _append_inline_tokens(paragraph, part[2:-2], profile, {**style, "bold": True})
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            _append_inline_tokens(paragraph, part[1:-1], profile, {**style, "italic": True})
        else:
            r = paragraph.add_run(part)
            apply_run_style(r, profile, **style)


def set_para_spacing(
    paragraph,
    before_pt: float = 0.0,
    after_pt: float = 5.0,
    line_mult: Optional[float] = 1.18,
):
    pPr = paragraph._p.get_or_add_pPr()
    spacing = _get_or_add(pPr, "w:spacing")
    for attr in ("w:beforeAutospacing", "w:afterAutospacing"):
        if qn(attr) in spacing.attrib:
            del spacing.attrib[qn(attr)]
    spacing.set(qn("w:before"), str(pt_to_twips(before_pt)))
    spacing.set(qn("w:after"), str(pt_to_twips(after_pt)))
    if line_mult is not None:
        spacing.set(qn("w:line"), str(int(round(line_mult * 240))))
        spacing.set(qn("w:lineRule"), "auto")


def set_para_ind(
    paragraph,
    left_mm: float = 0.0,
    right_mm: float = 0.0,
    hanging_mm: Optional[float] = None,
    first_line_mm: Optional[float] = None,
):
    pPr = paragraph._p.get_or_add_pPr()
    ind = _get_or_add(pPr, "w:ind")
    for attr in ("w:leftChars", "w:rightChars", "w:hangingChars", "w:firstLineChars", "w:hanging", "w:firstLine"):
        if qn(attr) in ind.attrib:
            del ind.attrib[qn(attr)]
    ind.set(qn("w:left"), str(mm_to_twips(left_mm)))
    if right_mm:
        ind.set(qn("w:right"), str(mm_to_twips(right_mm)))
    if hanging_mm is not None:
        ind.set(qn("w:hanging"), str(mm_to_twips(hanging_mm)))
    elif first_line_mm is not None:
        ind.set(qn("w:firstLine"), str(mm_to_twips(first_line_mm)))


def set_para_keep(paragraph, keep_next: bool = True, keep_lines: bool = True, page_break_before: bool = False):
    pPr = paragraph._p.get_or_add_pPr()
    if keep_next:
        _get_or_add(pPr, "w:keepNext")
    if keep_lines:
        _get_or_add(pPr, "w:keepLines")
    if page_break_before:
        _get_or_add(pPr, "w:pageBreakBefore")


def set_para_bottom_border(paragraph, color_hex: str = COLORS["border_light"], sz_eighths_pt: int = 6, space_pt: int = 4):
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = _get_or_add(pPr, "w:pBdr")
    bottom = _get_or_add(pBdr, "w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(sz_eighths_pt))
    bottom.set(qn("w:space"), str(space_pt))
    bottom.set(qn("w:color"), color_hex.lstrip("#").upper())


def set_para_numbering(paragraph, num_id: int | str, ilvl: int | str = 0):
    pPr = paragraph._p.get_or_add_pPr()
    numPr = _get_or_add(pPr, "w:numPr")
    ilvl_el = _get_or_add(numPr, "w:ilvl")
    ilvl_el.set(qn("w:val"), str(ilvl))
    numId_el = _get_or_add(numPr, "w:numId")
    numId_el.set(qn("w:val"), str(num_id))


def clear_para_numbering(paragraph):
    pPr = paragraph._p.get_or_add_pPr()
    numPr = pPr.find(qn("w:numPr"))
    if numPr is not None:
        pPr.remove(numPr)
    # Explicitly suppress inherited style numbering if needed
    numPr = OxmlElement("w:numPr")
    numId_el = OxmlElement("w:numId")
    numId_el.set(qn("w:val"), "0")
    numPr.append(numId_el)
    pPr.append(numPr)


def set_para_outline_level(paragraph, level_zero_based: int):
    pPr = paragraph._p.get_or_add_pPr()
    ol = _get_or_add(pPr, "w:outlineLvl")
    ol.set(qn("w:val"), str(level_zero_based))


def set_table_layout_and_widths(table, col_widths_mm: Iterable[float]):
    """Set fixed table layout, w:tblW, w:tblGrid, and each cell's w:tcW in twips."""
    widths_twips = [mm_to_twips(w) for w in col_widths_mm]
    total_twips = sum(widths_twips)

    tbl = table._tbl
    tblPr = tbl.tblPr
    tblW = _get_or_add(tblPr, "w:tblW")
    tblW.set(qn("w:w"), str(total_twips))
    tblW.set(qn("w:type"), "dxa")

    tblLayout = _get_or_add(tblPr, "w:tblLayout")
    tblLayout.set(qn("w:type"), "fixed")

    # Rebuild tblGrid
    old_grid = tbl.find(qn("w:tblGrid"))
    if old_grid is not None:
        tbl.remove(old_grid)
    new_grid = OxmlElement("w:tblGrid")
    for w_tw in widths_twips:
        gc = OxmlElement("w:gridCol")
        gc.set(qn("w:w"), str(w_tw))
        new_grid.append(gc)
    tblPr.addnext(new_grid)

    for row in table.rows:
        cells = row.cells
        for idx, w_tw in enumerate(widths_twips):
            if idx < len(cells):
                tcPr = cells[idx]._tc.get_or_add_tcPr()
                tcW = _get_or_add(tcPr, "w:tcW")
                tcW.set(qn("w:w"), str(w_tw))
                tcW.set(qn("w:type"), "dxa")


def set_table_cell_margins(table, top_pt: float = 5.0, bottom_pt: float = 5.0, left_pt: float = 7.0, right_pt: float = 7.0):
    tblPr = table._tbl.tblPr
    tblCellMar = _get_or_add(tblPr, "w:tblCellMar")
    for side, pt_val in (("top", top_pt), ("bottom", bottom_pt), ("left", left_pt), ("right", right_pt)):
        el = _get_or_add(tblCellMar, f"w:{side}")
        el.set(qn("w:w"), str(pt_to_twips(pt_val)))
        el.set(qn("w:type"), "dxa")


def set_table_borders(
    table,
    grid_mode: str = "horizontal",
    top_color: str = COLORS["deep_purple"],
    top_sz: int = 10,
    bottom_color: str = COLORS["deep_purple"],
    bottom_sz: int = 10,
    inner_color: str = COLORS["border_light"],
    inner_sz: int = 4,
):
    """Apply clean editorial horizontal borders or full engineering grid borders."""
    tblPr = table._tbl.tblPr
    tblBorders = _get_or_add(tblPr, "w:tblBorders")
    for child in list(tblBorders):
        tblBorders.remove(child)

    def _add_bdr(side: str, val: str, sz: int = 0, color: str = "auto"):
        b = OxmlElement(f"w:{side}")
        b.set(qn("w:val"), val)
        if val != "none" and val != "nil":
            b.set(qn("w:sz"), str(sz))
            b.set(qn("w:space"), "0")
            b.set(qn("w:color"), color.lstrip("#").upper())
        tblBorders.append(b)

    _add_bdr("top", "single" if top_sz > 0 else "none", top_sz, top_color)
    _add_bdr("bottom", "single" if bottom_sz > 0 else "none", bottom_sz, bottom_color)
    _add_bdr("insideH", "single" if inner_sz > 0 else "none", inner_sz, inner_color)
    if grid_mode == "full" and inner_sz > 0:
        _add_bdr("left", "single", inner_sz, inner_color)
        _add_bdr("right", "single", inner_sz, inner_color)
        _add_bdr("insideV", "single", inner_sz, inner_color)
    else:
        _add_bdr("left", "none")
        _add_bdr("right", "none")
        _add_bdr("insideV", "none")


def set_cell_borders(cell, **sides):
    """Set specific cell borders: e.g. left=('single', 24, '2E008B'), top=('none', 0, 'auto')."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = _get_or_add(tcPr, "w:tcBorders")
    for side, spec in sides.items():
        if spec is None:
            continue
        val, sz, color = spec
        b = _get_or_add(tcBorders, f"w:{side}")
        b.attrib.clear()
        b.set(qn("w:val"), val)
        if val not in ("none", "nil") and sz > 0:
            b.set(qn("w:sz"), str(sz))
            b.set(qn("w:space"), "0")
            b.set(qn("w:color"), color.lstrip("#").upper())


def set_cell_shading(cell, fill_hex: str):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = _get_or_add(tcPr, "w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill_hex.lstrip("#").upper())


def set_cell_valign(cell, align: str = "center"):
    tcPr = cell._tc.get_or_add_tcPr()
    vAlign = _get_or_add(tcPr, "w:vAlign")
    vAlign.set(qn("w:val"), align)


def set_cell_margins(cell, top_pt: float = 6.0, bottom_pt: float = 6.0, left_pt: float = 9.0, right_pt: float = 9.0):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = _get_or_add(tcPr, "w:tcMar")
    for side, pt_val in (("top", top_pt), ("bottom", bottom_pt), ("left", left_pt), ("right", right_pt)):
        el = _get_or_add(tcMar, f"w:{side}")
        el.set(qn("w:w"), str(pt_to_twips(pt_val)))
        el.set(qn("w:type"), "dxa")


def set_row_header(row, is_header: bool = True):
    trPr = row._tr.get_or_add_trPr()
    existing = trPr.find(qn("w:tblHeader"))
    if is_header and existing is None:
        trPr.append(OxmlElement("w:tblHeader"))
    elif not is_header and existing is not None:
        trPr.remove(existing)


def set_row_cant_split(row, cant_split: bool = True):
    trPr = row._tr.get_or_add_trPr()
    existing = trPr.find(qn("w:cantSplit"))
    if cant_split and existing is None:
        trPr.append(OxmlElement("w:cantSplit"))
    elif not cant_split and existing is not None:
        trPr.remove(existing)


def upgrade_document_styles(doc, profile: FontProfile):
    """Sanitize styles.xml and numbering.xml in-memory to Editorial Design System v2.0."""
    styles_el = doc.styles.element

    # 1. Update docDefaults (font + force left alignment instead of legacy justified 'both')
    rPrDef = styles_el.find(f".//{qn('w:rPrDefault')}/{qn('w:rPr')}")
    if rPrDef is not None:
        set_rpr_fonts(rPrDef, profile)
        sz = _get_or_add(rPrDef, "w:sz")
        sz.set(qn("w:val"), str(pt_to_half_pt(10.5)))
        szCs = _get_or_add(rPrDef, "w:szCs")
        szCs.set(qn("w:val"), str(pt_to_half_pt(10.5)))

    pPrDef = styles_el.find(f".//{qn('w:pPrDefault')}/{qn('w:pPr')}")
    if pPrDef is not None:
        jc_def = _get_or_add(pPrDef, "w:jc")
        jc_def.set(qn("w:val"), "left")

    # 2. Sanitize every style's rFonts to eliminate Gulim/Batang/Times New Roman/MS PGothic
    #    and replace any legacy justified ('both') paragraph alignment with 'left'
    for st in styles_el.findall(qn("w:style")):
        st_id = st.get(qn("w:styleId"), "")
        rPr = st.find(qn("w:rPr"))
        if rPr is None:
            rPr = OxmlElement("w:rPr")
            st.append(rPr)
        is_mono = "HTML" in st_id
        set_rpr_fonts(rPr, profile, mono=is_mono)

        pPr_existing = st.find(qn("w:pPr"))
        if pPr_existing is not None:
            jc_el = pPr_existing.find(qn("w:jc"))
            if jc_el is not None and jc_el.get(qn("w:val")) in ("both", "distribute"):
                jc_el.set(qn("w:val"), "left")
        elif st_id in ("a", "Normal"):
            pPr_norm = _get_or_add(st, "w:pPr")
            jc_norm = _get_or_add(pPr_norm, "w:jc")
            jc_norm.set(qn("w:val"), "left")

        # The donor Normal style switches widow/orphan control off; turn it back on
        if st_id in ("a", "Normal"):
            pPr_w = st.find(qn("w:pPr"))
            wc = pPr_w.find(qn("w:widowControl")) if pPr_w is not None else None
            if wc is not None:
                wc.set(qn("w:val"), "1")

        # Specific style upgrades for Headings & Body
        if st_id in ("HS1Title", "1"):
            pPr = _get_or_add(st, "w:pPr")
            jc = _get_or_add(pPr, "w:jc")
            jc.set(qn("w:val"), "left")
            _get_or_add(pPr, "w:keepNext")
            _get_or_add(pPr, "w:keepLines")
            sp = _get_or_add(pPr, "w:spacing")
            sp.set(qn("w:before"), str(pt_to_twips(16.0)))
            sp.set(qn("w:after"), str(pt_to_twips(6.0)))
            sz = _get_or_add(rPr, "w:sz")
            sz.set(qn("w:val"), str(pt_to_half_pt(14.5)))
            szCs = _get_or_add(rPr, "w:szCs")
            szCs.set(qn("w:val"), str(pt_to_half_pt(14.5)))
            _get_or_add(rPr, "w:b")
            clr = _get_or_add(rPr, "w:color")
            clr.set(qn("w:val"), COLORS["deep_purple"])
        elif st_id in ("HS11Title", "2"):
            pPr = _get_or_add(st, "w:pPr")
            jc = _get_or_add(pPr, "w:jc")
            jc.set(qn("w:val"), "left")
            _get_or_add(pPr, "w:keepNext")
            _get_or_add(pPr, "w:keepLines")
            sp = _get_or_add(pPr, "w:spacing")
            sp.set(qn("w:before"), str(pt_to_twips(13.0)))
            sp.set(qn("w:after"), str(pt_to_twips(4.0)))
            sz = _get_or_add(rPr, "w:sz")
            sz.set(qn("w:val"), str(pt_to_half_pt(12.0)))
            szCs = _get_or_add(rPr, "w:szCs")
            szCs.set(qn("w:val"), str(pt_to_half_pt(12.0)))
            _get_or_add(rPr, "w:b")
            clr = _get_or_add(rPr, "w:color")
            clr.set(qn("w:val"), COLORS["main_purple"])
        elif st_id in ("HS111Title", "3"):
            pPr = _get_or_add(st, "w:pPr")
            jc = _get_or_add(pPr, "w:jc")
            jc.set(qn("w:val"), "left")
            _get_or_add(pPr, "w:keepNext")
            _get_or_add(pPr, "w:keepLines")
            sp = _get_or_add(pPr, "w:spacing")
            sp.set(qn("w:before"), str(pt_to_twips(10.0)))
            sp.set(qn("w:after"), str(pt_to_twips(3.0)))
            sz = _get_or_add(rPr, "w:sz")
            sz.set(qn("w:val"), str(pt_to_half_pt(10.5)))
            szCs = _get_or_add(rPr, "w:szCs")
            szCs.set(qn("w:val"), str(pt_to_half_pt(10.5)))
            _get_or_add(rPr, "w:b")
            clr = _get_or_add(rPr, "w:color")
            clr.set(qn("w:val"), COLORS["charcoal"])
        elif st_id in ("10", "20", "30", "HSContents"):
            # TOC styles: clean profile font, crisp spacing
            pPr = _get_or_add(st, "w:pPr")
            sp = _get_or_add(pPr, "w:spacing")
            sp.set(qn("w:before"), "40")
            sp.set(qn("w:after"), "40")
            sp.set(qn("w:line"), "240")
            sp.set(qn("w:lineRule"), "auto")
            sz = _get_or_add(rPr, "w:sz")
            sz.set(qn("w:val"), str(pt_to_half_pt(10.0 if st_id == "10" else 9.5)))
            szCs = _get_or_add(rPr, "w:szCs")
            szCs.set(qn("w:val"), str(pt_to_half_pt(10.0 if st_id == "10" else 9.5)))
            clr = _get_or_add(rPr, "w:color")
            clr.set(qn("w:val"), COLORS["deep_purple"] if st_id == "10" else COLORS["charcoal"])
            i_el = rPr.find(qn("w:i"))
            if i_el is not None:
                rPr.remove(i_el)

    # 3. Also clean numbering.xml rFonts (except Symbol/Wingdings bullets)
    try:
        num_part = doc.part.numbering_part
        if num_part is not None:
            num_el = num_part.element
            for lvl in num_el.findall(f".//{qn('w:lvl')}"):
                numFmt = lvl.find(qn("w:numFmt"))
                fmt_val = numFmt.get(qn("w:val")) if numFmt is not None else ""
                if fmt_val != "bullet":
                    rPr = lvl.find(qn("w:rPr"))
                    if rPr is None:
                        rPr = OxmlElement("w:rPr")
                        lvl.append(rPr)
                    set_rpr_fonts(rPr, profile)
    except Exception:
        pass


def scrub_core_properties(doc, author: str = "", title: str = "", subject: str = ""):
    """Remove personal creator/lastModifiedBy names from docProps/core.xml unless specified."""
    cp = doc.core_properties
    cp.author = author or ""
    cp.last_modified_by = author or ""
    if title:
        cp.title = title
    if subject:
        cp.subject = subject
    cp.comments = "Generated deterministically by Hyosung Word Engine (15_Word-Auto-Skill v2.0)"
