"""Cover Page (Mode A), Compact Executive Banner (Mode B), TOC, and Running Header/Footer builder."""

from __future__ import annotations
from copy import deepcopy
from typing import Any, Dict, List
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from .design import COLORS, CONTENT_WIDTH_PORTRAIT_MM, FontProfile, pt_to_twips
from .xml_helpers import (
    _get_or_add,
    append_rich_text,
    apply_run_style,
    clear_para_numbering,
    set_cell_borders,
    set_cell_margins,
    set_cell_shading,
    set_cell_valign,
    set_para_bottom_border,
    set_para_keep,
    set_para_spacing,
    set_row_cant_split,
    set_row_header,
    set_table_borders,
    set_table_cell_margins,
    set_table_layout_and_widths,
)


def _format_cell_text(
    cell,
    text: str,
    profile: FontProfile,
    size_pt: float = 9.0,
    bold: bool = False,
    italic: bool = False,
    color_hex: str = COLORS["charcoal"],
    align=WD_ALIGN_PARAGRAPH.LEFT,
    before_pt: float = 1.5,
    after_pt: float = 1.5,
    rich: bool = True,
):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    set_para_spacing(p, before_pt=before_pt, after_pt=after_pt, line_mult=1.12)
    if rich:
        append_rich_text(
            p,
            text,
            profile,
            base_size_pt=size_pt,
            base_color=color_hex,
            base_bold=bold,
            base_italic=italic,
        )
    else:
        r = p.add_run(str(text or ""))
        apply_run_style(r, profile, size_pt=size_pt, bold=bold, italic=italic, color_hex=color_hex)


def upgrade_running_header_and_footer(doc, meta: Dict[str, Any], profile: FontProfile):
    """Restyle header2.xml and footer2.xml to Editorial Design System v2.0."""
    if not doc.sections:
        return
    sec0 = doc.sections[0]
    hdr = sec0.header
    if hdr and hdr.tables:
        tbl = hdr.tables[0]
        set_table_layout_and_widths(tbl, [43.0, 78.0, 17.0, 37.0])
        set_table_cell_margins(tbl, top_pt=2.5, bottom_pt=2.5, left_pt=4.0, right_pt=4.0)

        doc_title = meta.get("header_title") or meta.get("doc_title") or "TECHNICAL DOCUMENT"
        doc_no = meta.get("doc_number") or "TBD"
        rev = str(meta.get("revision", "0"))
        issue_date = meta.get("issue_date") or "-"

        # Clean borders across all raw <w:tc> elements (including vMerge="continue" cells in rows 1..2)
        raw_trs = tbl._tbl.findall(qn("w:tr"))
        for r_idx, tr_el in enumerate(raw_trs):
            trPr = _get_or_add(tr_el, "w:trPr")
            if trPr.find(qn("w:cantSplit")) is None:
                trPr.append(OxmlElement("w:cantSplit"))
            raw_tcs = tr_el.findall(qn("w:tc"))
            for c_idx, tc_el in enumerate(raw_tcs):
                tcPr = _get_or_add(tc_el, "w:tcPr")
                vAlign = _get_or_add(tcPr, "w:vAlign")
                vAlign.set(qn("w:val"), "center")
                tcBorders = _get_or_add(tcPr, "w:tcBorders")
                for ch in list(tcBorders):
                    tcBorders.remove(ch)

                b_top = ("single", 6, COLORS["deep_purple"]) if r_idx == 0 else ("single", 4, COLORS["border_light"])
                b_bottom = ("single", 8, COLORS["deep_purple"]) if r_idx == len(raw_trs) - 1 else ("single", 4, COLORS["border_light"])
                # For vertically merged cells (cols 0 and 1), suppress internal horizontal seam
                if c_idx in (0, 1):
                    if r_idx > 0:
                        b_top = ("none", 0, "auto")
                    if r_idx < len(raw_trs) - 1:
                        b_bottom = ("none", 0, "auto")

                for side, (b_val, b_sz, b_col) in (
                    ("top", b_top),
                    ("bottom", b_bottom),
                    ("left", ("single", 4, COLORS["border_light"])),
                    ("right", ("single", 4, COLORS["border_light"])),
                ):
                    b_el = OxmlElement(f"w:{side}")
                    b_el.set(qn("w:val"), b_val)
                    if b_val not in ("none", "nil") and b_sz > 0:
                        b_el.set(qn("w:sz"), str(b_sz))
                        b_el.set(qn("w:space"), "0")
                        b_el.set(qn("w:color"), b_col.lstrip("#").upper())
                    tcBorders.append(b_el)

        # Title cell at (0, 1)
        _format_cell_text(
            tbl.cell(0, 1),
            doc_title,
            profile,
            size_pt=9.5,
            bold=True,
            color_hex=COLORS["dark_ink"],
            align=WD_ALIGN_PARAGRAPH.CENTER,
            rich=False,
        )

        # Metadata cells on right: (0,2)/(0,3), (1,2)/(1,3), (2,2)/(2,3)
        meta_rows = [
            ("Doc. No.", doc_no),
            ("Rev.", rev),
            ("Date", issue_date),
        ]
        for idx, (label, val) in enumerate(meta_rows):
            if idx < len(tbl.rows):
                lbl_cell = tbl.cell(idx, 2)
                val_cell = tbl.cell(idx, 3)
                set_cell_shading(lbl_cell, COLORS["soft_canvas"])
                _format_cell_text(
                    lbl_cell,
                    label,
                    profile,
                    size_pt=7.5,
                    bold=True,
                    color_hex=COLORS["slate_muted"],
                    align=WD_ALIGN_PARAGRAPH.CENTER,
                    before_pt=1.0,
                    after_pt=1.0,
                    rich=False,
                )
                _format_cell_text(
                    val_cell,
                    val,
                    profile,
                    size_pt=7.5,
                    bold=True,
                    color_hex=COLORS["charcoal"],
                    align=WD_ALIGN_PARAGRAPH.CENTER,
                    before_pt=1.0,
                    after_pt=1.0,
                    rich=False,
                )

    # Upgrade footer2.xml (preserve PAGE / NUMPAGES fields, apply profile font + top hairline)
    ftr = sec0.footer
    if ftr and ftr.paragraphs:
        p = ftr.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        set_para_spacing(p, before_pt=4.0, after_pt=0.0, line_mult=1.0)
        pPr = p._p.get_or_add_pPr()
        pBdr = _get_or_add(pPr, "w:pBdr")
        top_b = _get_or_add(pBdr, "w:top")
        top_b.set(qn("w:val"), "single")
        top_b.set(qn("w:sz"), "4")
        top_b.set(qn("w:space"), "4")
        top_b.set(qn("w:color"), COLORS["border_light"])

        for r in p.runs:
            apply_run_style(r, profile, size_pt=8.5, bold=True, color_hex=COLORS["slate_muted"])


def enable_update_fields_on_open(doc):
    """Set <w:updateFields w:val='true'/> in word/settings.xml so Word auto-refreshes TOC & page numbers."""
    settings_el = doc.settings.element
    uf = settings_el.find(qn("w:updateFields"))
    if uf is None:
        uf = OxmlElement("w:updateFields")
        settings_el.append(uf)
    uf.set(qn("w:val"), "true")


def extract_template_assets(doc) -> Dict[str, Any]:
    """Extract reusable XML assets (cover logo drawing, section0 sectPr) before clearing template body."""
    body = doc._body._body
    logo_drawing = None
    sect0_pr = None

    for p in body.findall(qn("w:p")):
        drw = p.find(f".//{qn('w:drawing')}")
        if drw is not None and logo_drawing is None:
            logo_drawing = deepcopy(drw)
        sp = p.find(f"{qn('w:pPr')}/{qn('w:sectPr')}")
        if sp is not None and sect0_pr is None:
            sect0_pr = deepcopy(sp)

    return {
        "logo_drawing": logo_drawing,
        "sect0_pr": sect0_pr,
    }


def clear_document_body(doc):
    """Remove all paragraphs, tables, and SDT blocks from body while keeping final sectPr."""
    body = doc._body._body
    for child in list(body):
        if child.tag != qn("w:sectPr"):
            body.remove(child)


def _add_section_label(
    doc,
    text: str,
    profile: FontProfile,
    before_pt: float = 12.0,
    after_pt: float = 5.0,
    size_pt: float = 11.5,
    with_rule: bool = False,
):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    clear_para_numbering(p)
    set_para_keep(p, keep_next=True, keep_lines=True)
    set_para_spacing(p, before_pt=before_pt, after_pt=after_pt, line_mult=1.15)
    if with_rule:
        set_para_bottom_border(p, color_hex=COLORS["deep_purple"], sz_eighths_pt=8, space_pt=3)
    r = p.add_run(text)
    apply_run_style(r, profile, size_pt=size_pt, bold=True, color_hex=COLORS["deep_purple"])
    return p


def _add_page_break_para(doc):
    p_brk = doc.add_paragraph()
    clear_para_numbering(p_brk)
    set_para_spacing(p_brk, before_pt=0.0, after_pt=0.0, line_mult=1.0)
    r_brk = p_brk.add_run()
    br = OxmlElement("w:br")
    br.set(qn("w:type"), "page")
    r_brk._r.append(br)
    return p_brk


def _clean_approval_value(val: str) -> str:
    """Strip noisy [TO BE CONFIRMED: ...] brackets inside sign-off cells so the table stays clean."""
    s = str(val or "-").strip()
    if s.startswith("[TO BE CONFIRMED:") and s.endswith("]"):
        inner = s[len("[TO BE CONFIRMED:") : -1].strip()
        return f"{inner} (TBC)"
    if s.startswith("[확인 필요:") and s.endswith("]"):
        inner = s[len("[확인 필요:") : -1].strip()
        return f"{inner} (확인 예정)"
    return s


def build_formal_cover_and_frontmatter(
    doc,
    meta: Dict[str, Any],
    blocks: List[Dict[str, Any]],
    assets: Dict[str, Any],
    profile: FontProfile,
):
    """Build Mode A:
    - Page 1 (Section 0): Clean Executive Cover Page (Logo + Status Badge + Left-Aligned Hero Title + Simple 2-Column Summary)
    - Page 2 (Section 1): Simplified Document Control & Sign-Off Sheet (Light Lavender Headers, Horizontal Rules Only)
    - Page 3 (Section 1): Table of Contents (CONTENTS) + Abbreviations & Definitions (Light Lavender Header)
    """
    lang = meta.get("language", "en")
    is_ko = lang == "ko"

    # =========================================================================
    # PAGE 1: EXECUTIVE COVER PAGE (Left-Aligned Hero Title + Minimal 2-Col Summary)
    # =========================================================================
    # 1. Top Logo + Classification Bar
    top_tbl = doc.add_table(rows=1, cols=2)
    set_table_layout_and_widths(top_tbl, [75.0, 100.0])
    set_table_borders(top_tbl, grid_mode="horizontal", top_sz=0, bottom_sz=0, inner_sz=0)
    top_tbl.rows[0]._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))

    # Left cell: Hyosung Logo drawing
    c_logo = top_tbl.cell(0, 0)
    set_cell_borders(c_logo, top=("none", 0, "auto"), bottom=("none", 0, "auto"), left=("none", 0, "auto"), right=("none", 0, "auto"))
    set_cell_valign(c_logo, "center")
    p_logo = c_logo.paragraphs[0]
    p_logo.alignment = WD_ALIGN_PARAGRAPH.LEFT
    set_para_spacing(p_logo, before_pt=0.0, after_pt=2.0)
    if assets.get("logo_drawing") is not None:
        r_logo = p_logo.add_run()
        r_logo._r.append(deepcopy(assets["logo_drawing"]))
    else:
        r_logo = p_logo.add_run("HYOSUNG HEAVY INDUSTRIES")
        apply_run_style(r_logo, profile, size_pt=12.0, bold=True, color_hex=COLORS["deep_purple"])

    # Right cell: Document Status Pill
    c_status = top_tbl.cell(0, 1)
    set_cell_borders(c_status, top=("none", 0, "auto"), bottom=("none", 0, "auto"), left=("none", 0, "auto"), right=("none", 0, "auto"))
    set_cell_valign(c_status, "center")
    status_str = meta.get("doc_status") or ("내부 검토용" if is_ko else "FOR REVIEW")
    p_st = c_status.paragraphs[0]
    p_st.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_para_spacing(p_st, before_pt=0.0, after_pt=2.0)
    r_st = p_st.add_run(f"  {status_str}  ")
    apply_run_style(
        r_st,
        profile,
        size_pt=8.5,
        bold=True,
        color_hex=COLORS["deep_purple"],
        shd_fill=COLORS["soft_lavender"],
    )

    # 2. Hero Title Area (Strictly Left-Aligned, positioned at optical golden zone per Codex review)
    p_proj = doc.add_paragraph()
    p_proj.alignment = WD_ALIGN_PARAGRAPH.LEFT
    clear_para_numbering(p_proj)
    set_para_spacing(p_proj, before_pt=84.0, after_pt=8.0, line_mult=1.15)
    r_proj = p_proj.add_run(meta.get("project_name") or "PROJECT TECHNICAL & CONTRACTUAL DELIVERABLE")
    apply_run_style(r_proj, profile, size_pt=11.5, bold=True, color_hex=COLORS["main_purple"])

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    clear_para_numbering(p_title)
    set_para_spacing(p_title, before_pt=2.0, after_pt=12.0, line_mult=1.18)
    r_title = p_title.add_run(meta.get("doc_title") or "Document Title")
    apply_run_style(r_title, profile, size_pt=23.5, bold=True, color_hex=COLORS["dark_ink"])

    if meta.get("doc_subtitle"):
        p_sub = doc.add_paragraph()
        p_sub.alignment = WD_ALIGN_PARAGRAPH.LEFT
        clear_para_numbering(p_sub)
        set_para_spacing(p_sub, before_pt=2.0, after_pt=16.0, line_mult=1.2)
        r_sub = p_sub.add_run(meta["doc_subtitle"])
        apply_run_style(r_sub, profile, size_pt=12.0, bold=False, color_hex=COLORS["slate_muted"])

    # Deep Purple Accent Rule separating Hero Title zone from Lower Cover Summary Table
    p_rule = doc.add_paragraph()
    p_rule.alignment = WD_ALIGN_PARAGRAPH.LEFT
    clear_para_numbering(p_rule)
    set_para_spacing(p_rule, before_pt=6.0, after_pt=36.0, line_mult=1.0)
    set_para_bottom_border(p_rule, color_hex=COLORS["deep_purple"], sz_eighths_pt=18, space_pt=1)

    # 3. Simplified 2-Column Document Summary Table (Horizontal rules only, anchored to bottom margin)
    approvals_cfg = meta.get("approvals") or {}
    prepared_name = _clean_approval_value(
        (approvals_cfg.get("prepared_by") or {}).get("name") or meta.get("author_display") or "-"
    )
    org_name = meta.get("organization") or (
        "효성중공업(주)" if is_ko else "Hyosung Heavy Industries Corporation"
    )
    doc_no_str = meta.get("doc_number") or "TBD"
    rev_str = str(meta.get("revision", "0"))
    issue_date_str = meta.get("issue_date") or "-"

    summary_rows = [
        ("문서 번호" if is_ko else "DOCUMENT NO.", f"{doc_no_str} (Rev. {rev_str})"),
        ("발행 일자" if is_ko else "ISSUE DATE", issue_date_str),
        ("발주처 / 대상" if is_ko else "CLIENT / OWNER", meta.get("client") or "-"),
        ("계약 / 패키지" if is_ko else "CONTRACT REF.", meta.get("contract_no") or "-"),
        ("발행 / 작성" if is_ko else "PREPARED BY", f"{org_name}, {prepared_name}"),
    ]

    meta_tbl = doc.add_table(rows=len(summary_rows), cols=2)
    set_table_layout_and_widths(meta_tbl, [44.0, 131.0])
    set_table_cell_margins(meta_tbl, top_pt=7.0, bottom_pt=7.0, left_pt=8.0, right_pt=8.0)
    set_table_borders(
        meta_tbl,
        grid_mode="horizontal",
        top_color=COLORS["deep_purple"],
        top_sz=8,
        bottom_color=COLORS["deep_purple"],
        bottom_sz=8,
        inner_color=COLORS["border_light"],
        inner_sz=4,
    )

    # Anchor Cover Page summary table flush to the bottom margin of Page 1
    tblPr = meta_tbl._tbl.tblPr
    existing_tblp = tblPr.find(qn("w:tblpPr"))
    if existing_tblp is not None:
        tblPr.remove(existing_tblp)
    tblpPr = OxmlElement("w:tblpPr")
    tblpPr.set(qn("w:leftFromText"), "0")
    tblpPr.set(qn("w:rightFromText"), "0")
    tblpPr.set(qn("w:topFromText"), str(pt_to_twips(12.0)))
    tblpPr.set(qn("w:bottomFromText"), "0")
    tblpPr.set(qn("w:vertAnchor"), "margin")
    tblpPr.set(qn("w:horzAnchor"), "margin")
    tblpPr.set(qn("w:tblpXSpec"), "left")
    tblpPr.set(qn("w:tblpYSpec"), "bottom")
    tblPr.insert(0, tblpPr)

    for r_i, (k_txt, v_txt) in enumerate(summary_rows):
        row = meta_tbl.rows[r_i]
        set_row_cant_split(row, True)
        set_cell_shading(row.cells[0], COLORS["soft_canvas"])
        set_cell_valign(row.cells[0], "center")
        set_cell_valign(row.cells[1], "center")
        _format_cell_text(
            row.cells[0],
            k_txt,
            profile,
            size_pt=8.8,
            bold=True,
            color_hex=COLORS["deep_purple"],
            rich=False,
        )
        _format_cell_text(
            row.cells[1],
            v_txt,
            profile,
            size_pt=9.5 if r_i == 0 else 9.2,
            bold=(r_i == 0),
            color_hex=COLORS["deep_purple"] if r_i == 0 else COLORS["charcoal"],
            rich=False,
        )

    # 4. Insert Section 0 Break right after Cover Page Summary Table
    p_sect = doc.add_paragraph()
    clear_para_numbering(p_sect)
    set_para_spacing(p_sect, before_pt=0.0, after_pt=0.0, line_mult=1.0)
    if assets.get("sect0_pr") is not None:
        pPr = p_sect._p.get_or_add_pPr()
        pPr.append(deepcopy(assets["sect0_pr"]))

    # =========================================================================
    # PAGE 2: SIMPLIFIED DOCUMENT CONTROL & SIGN-OFF SHEET (Light Lavender Headers)
    # =========================================================================
    # 5. Approvals Sign-Off Table (total 175.0 mm: [34, 76, 35, 30] per Codex review)
    _add_section_label(
        doc,
        "결재 및 승인" if is_ko else "APPROVALS & SIGN-OFF",
        profile,
        before_pt=6.0,
        after_pt=5.0,
        size_pt=11.5,
        with_rule=False,
    )
    app_tbl = doc.add_table(rows=4, cols=4)
    set_table_layout_and_widths(app_tbl, [34.0, 76.0, 35.0, 30.0])
    set_table_cell_margins(app_tbl, top_pt=6.5, bottom_pt=6.5, left_pt=7.0, right_pt=7.0)
    set_table_borders(
        app_tbl,
        grid_mode="horizontal",
        top_color=COLORS["deep_purple"],
        top_sz=8,
        bottom_color=COLORS["deep_purple"],
        bottom_sz=8,
        inner_color=COLORS["border_light"],
        inner_sz=4,
    )
    app_headers = (
        ["구분", "성명 / 직책", "서명", "일자"]
        if is_ko
        else ["ROLE", "NAME / POSITION", "SIGNATURE", "DATE"]
    )
    set_row_header(app_tbl.rows[0], True)
    set_row_cant_split(app_tbl.rows[0], True)
    for c_i, h_txt in enumerate(app_headers):
        cell = app_tbl.cell(0, c_i)
        set_cell_shading(cell, COLORS["soft_lavender"])
        set_cell_valign(cell, "center")
        set_cell_borders(cell, bottom=("single", 6, COLORS["deep_purple"]))
        _format_cell_text(
            cell,
            h_txt,
            profile,
            size_pt=8.8,
            bold=True,
            color_hex=COLORS["deep_purple"],
            align=WD_ALIGN_PARAGRAPH.CENTER if c_i >= 2 else WD_ALIGN_PARAGRAPH.LEFT,
            rich=False,
        )

    role_rows = [
        ("작성" if is_ko else "Prepared By", approvals_cfg.get("prepared_by") or {}),
        ("검토" if is_ko else "Checked By", approvals_cfg.get("checked_by") or {}),
        ("승인" if is_ko else "Approved By", approvals_cfg.get("approved_by") or {}),
    ]
    for idx, (role_label, info) in enumerate(role_rows, start=1):
        row = app_tbl.rows[idx]
        set_row_cant_split(row, True)
        set_cell_shading(row.cells[0], COLORS["soft_canvas"])
        for c_i in range(4):
            set_cell_valign(row.cells[c_i], "center")
        clean_name = _clean_approval_value(info.get("name", "-"))
        is_tbc = "(TBC)" in clean_name or "(확인 예정)" in clean_name
        _format_cell_text(row.cells[0], role_label, profile, size_pt=9.0, bold=True, color_hex=COLORS["charcoal"], rich=False)
        _format_cell_text(row.cells[1], clean_name, profile, size_pt=9.0, color_hex=COLORS["slate_muted"] if is_tbc else COLORS["charcoal"], rich=False)
        _format_cell_text(row.cells[2], info.get("signature", "-"), profile, size_pt=9.0, color_hex=COLORS["slate_muted"], align=WD_ALIGN_PARAGRAPH.CENTER, rich=False)
        _format_cell_text(row.cells[3], info.get("date", "-"), profile, size_pt=9.0, color_hex=COLORS["charcoal"], align=WD_ALIGN_PARAGRAPH.CENTER, rich=False)

    # 6. Revision History Table (total 175.0 mm, Light #EBE6FF Header, before_pt=18.0 per Codex review)
    _add_section_label(
        doc,
        "개정 이력" if is_ko else "REVISION HISTORY",
        profile,
        before_pt=18.0,
        after_pt=5.0,
        size_pt=11.5,
        with_rule=False,
    )

    revs = meta.get("revisions") or [
        {
            "rev": str(meta.get("revision", "0")),
            "date": meta.get("issue_date") or "-",
            "description": "최초 발행" if is_ko else "Initial Issue for Review",
            "author": prepared_name,
        }
    ]
    rev_tbl = doc.add_table(rows=1 + len(revs), cols=4)
    set_table_layout_and_widths(rev_tbl, [18.0, 28.0, 94.0, 35.0])
    set_table_cell_margins(rev_tbl, top_pt=6.5, bottom_pt=6.5, left_pt=7.0, right_pt=7.0)
    set_table_borders(
        rev_tbl,
        grid_mode="horizontal",
        top_color=COLORS["deep_purple"],
        top_sz=8,
        bottom_color=COLORS["deep_purple"],
        bottom_sz=8,
        inner_color=COLORS["border_light"],
        inner_sz=4,
    )
    rev_headers = (
        ["Rev.", "일자", "개정 내용", "작성자"]
        if is_ko
        else ["REV.", "DATE", "DESCRIPTION", "PREPARED BY"]
    )
    set_row_header(rev_tbl.rows[0], True)
    set_row_cant_split(rev_tbl.rows[0], True)
    for c_i, h_txt in enumerate(rev_headers):
        cell = rev_tbl.cell(0, c_i)
        set_cell_shading(cell, COLORS["soft_lavender"])
        set_cell_valign(cell, "center")
        set_cell_borders(cell, bottom=("single", 6, COLORS["deep_purple"]))
        _format_cell_text(
            cell,
            h_txt,
            profile,
            size_pt=8.8,
            bold=True,
            color_hex=COLORS["deep_purple"],
            align=WD_ALIGN_PARAGRAPH.CENTER if c_i in (0, 1) else WD_ALIGN_PARAGRAPH.LEFT,
            rich=False,
        )

    for idx, rev_item in enumerate(revs, start=1):
        row = rev_tbl.rows[idx]
        set_row_cant_split(row, True)
        set_cell_shading(row.cells[0], COLORS["soft_canvas"])
        for c_i in range(4):
            set_cell_valign(row.cells[c_i], "center")
        _format_cell_text(row.cells[0], str(rev_item.get("rev", rev_item.get("no", "0"))), profile, size_pt=9.0, bold=True, color_hex=COLORS["deep_purple"], align=WD_ALIGN_PARAGRAPH.CENTER, rich=False)
        _format_cell_text(row.cells[1], str(rev_item.get("date", "-")), profile, size_pt=9.0, color_hex=COLORS["charcoal"], align=WD_ALIGN_PARAGRAPH.CENTER, rich=False)
        _format_cell_text(row.cells[2], str(rev_item.get("description", "-")), profile, size_pt=9.0, color_hex=COLORS["charcoal"], rich=False)
        _format_cell_text(row.cells[3], str(rev_item.get("author", rev_item.get("prepared_by", "-"))), profile, size_pt=9.0, color_hex=COLORS["charcoal"], rich=False)

    # Subtle 1-line note below Revision History table
    p_ctrl_note = doc.add_paragraph()
    p_ctrl_note.alignment = WD_ALIGN_PARAGRAPH.LEFT
    clear_para_numbering(p_ctrl_note)
    set_para_spacing(p_ctrl_note, before_pt=4.0, after_pt=4.0, line_mult=1.1)
    ctrl_msg = (
        "※ 본 문서의 정본은 지정된 문서관리 시스템에서 관리되며, 별도 표기가 없는 인쇄본은 비관리 참고본임."
        if is_ko
        else "Note: Master version is maintained in the document management system. Unstamped printed copies are uncontrolled."
    )
    r_cn = p_ctrl_note.add_run(ctrl_msg)
    apply_run_style(r_cn, profile, size_pt=8.0, italic=True, color_hex=COLORS["slate_muted"])

    # Separate Page 2 (Approvals & Revision History) from Page 3 (TOC & Abbreviations / Body)
    _add_page_break_para(doc)

    # =========================================================================
    # PAGE 3: TABLE OF CONTENTS (TOC) & ABBREVIATIONS
    # =========================================================================
    frontmatter_only = bool(meta.get("frontmatter_only", False))
    include_toc = meta.get("include_toc", True)
    if include_toc:
        build_clean_toc_block(doc, blocks, profile, is_ko=is_ko, static_preview_only=frontmatter_only)

    abbrevs = meta.get("abbreviations")
    if abbrevs:
        build_abbreviations_section(
            doc,
            abbrevs,
            profile,
            is_ko=is_ko,
            page_break_after=(not frontmatter_only and bool(blocks)),
        )
    elif include_toc and not frontmatter_only and bool(blocks):
        # Page break after TOC before Chapter 1 starts
        _add_page_break_para(doc)


def build_clean_toc_block(
    doc,
    blocks: List[Dict[str, Any]],
    profile: FontProfile,
    is_ko: bool = False,
    static_preview_only: bool = False,
):
    """Insert a bug-free Word Table of Contents (TOC \\o '1-3' \\h \\z \\u) + static preview entries."""
    p_toc_hdr = doc.add_paragraph()
    p_toc_hdr.alignment = WD_ALIGN_PARAGRAPH.LEFT
    clear_para_numbering(p_toc_hdr)
    set_para_keep(p_toc_hdr, keep_next=True, keep_lines=True)
    set_para_spacing(p_toc_hdr, before_pt=4.0, after_pt=8.0, line_mult=1.15)
    set_para_bottom_border(p_toc_hdr, color_hex=COLORS["deep_purple"], sz_eighths_pt=8, space_pt=4)
    r_th = p_toc_hdr.add_run("목차" if is_ko else "CONTENTS")
    apply_run_style(r_th, profile, size_pt=12.0, bold=True, color_hex=COLORS["deep_purple"])

    if static_preview_only:
        # Render clean TOC lines with right-aligned dot leaders for frontmatter-only concept preview
        counters = [0, 0, 0]
        sim_page = 3
        for b in blocks:
            if b.get("type") == "heading":
                lvl = int(b.get("level", 1))
                if 1 <= lvl <= 3:
                    if lvl == 1:
                        sim_page += 1
                    numbered = b.get("numbered", True)
                    prefix = ""
                    if numbered:
                        counters[lvl - 1] += 1
                        for k in range(lvl, 3):
                            counters[k] = 0
                        if lvl == 1:
                            prefix = f"{counters[0]}. "
                        elif lvl == 2:
                            prefix = f"{counters[0]}.{counters[1]} "
                        else:
                            prefix = f"{counters[0]}.{counters[1]}.{counters[2]} "
                    p_item = doc.add_paragraph()
                    p_item.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    clear_para_numbering(p_item)
                    set_para_spacing(p_item, before_pt=3.0 if lvl == 1 else 1.5, after_pt=2.0, line_mult=1.15)
                    pPr = p_item._p.get_or_add_pPr()
                    if lvl > 1:
                        ind = _get_or_add(pPr, "w:ind")
                        ind.set(qn("w:left"), str(pt_to_twips(18.0 * (lvl - 1))))
                    tabs = _get_or_add(pPr, "w:tabs")
                    tab = OxmlElement("w:tab")
                    tab.set(qn("w:val"), "right")
                    tab.set(qn("w:leader"), "dot")
                    tab.set(qn("w:pos"), "9921")
                    tabs.append(tab)

                    r_txt = p_item.add_run(f"{prefix}{b.get('text', '')}\t{sim_page}")
                    apply_run_style(
                        r_txt,
                        profile,
                        size_pt=10.0 if lvl == 1 else 9.25,
                        bold=(lvl == 1),
                        color_hex=COLORS["deep_purple"] if lvl == 1 else COLORS["charcoal"],
                    )
        return

    # Native Word TOC Field paragraph
    p_field = doc.add_paragraph()
    p_field.alignment = WD_ALIGN_PARAGRAPH.LEFT
    clear_para_numbering(p_field)
    set_para_spacing(p_field, before_pt=2.0, after_pt=4.0, line_mult=1.15)

    r_begin = p_field.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    fld_begin.set(qn("w:dirty"), "true")
    r_begin._r.append(fld_begin)

    r_instr = p_field.add_run()
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = ' TOC \\o "1-3" \\h \\z \\u '
    r_instr._r.append(instr)

    r_sep = p_field.add_run()
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    r_sep._r.append(fld_sep)

    # Pre-populate clean outline entries inside the TOC field for non-COM environments
    counters = [0, 0, 0]
    for b in blocks:
        if b.get("type") == "heading":
            lvl = int(b.get("level", 1))
            if 1 <= lvl <= 3:
                numbered = b.get("numbered", True)
                prefix = ""
                if numbered:
                    counters[lvl - 1] += 1
                    for k in range(lvl, 3):
                        counters[k] = 0
                    if lvl == 1:
                        prefix = f"{counters[0]}. "
                    elif lvl == 2:
                        prefix = f"{counters[0]}.{counters[1]} "
                    else:
                        prefix = f"{counters[0]}.{counters[1]}.{counters[2]} "
                indent_spaces = "    " * (lvl - 1)
                r_entry = p_field.add_run(f"{indent_spaces}{prefix}{b.get('text', '')}\n")
                apply_run_style(
                    r_entry,
                    profile,
                    size_pt=10.0 if lvl == 1 else 9.25,
                    bold=(lvl == 1),
                    color_hex=COLORS["deep_purple"] if lvl == 1 else COLORS["charcoal"],
                )

    r_end = p_field.add_run()
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    r_end._r.append(fld_end)


def build_abbreviations_section(
    doc,
    abbrevs: List[Dict[str, str]],
    profile: FontProfile,
    is_ko: bool = False,
    page_break_after: bool = True,
):
    """Build Abbreviations / Definitions table in Front-Matter or Body (Light Lavender Header)."""
    p_hdr = doc.add_paragraph()
    p_hdr.alignment = WD_ALIGN_PARAGRAPH.LEFT
    clear_para_numbering(p_hdr)
    set_para_keep(p_hdr, keep_next=True, keep_lines=True)
    set_para_spacing(p_hdr, before_pt=18.0, after_pt=5.0, line_mult=1.15)
    r_h = p_hdr.add_run("약어 및 용어 정의" if is_ko else "ABBREVIATIONS & DEFINITIONS")
    apply_run_style(r_h, profile, size_pt=12.0, bold=True, color_hex=COLORS["deep_purple"])

    tbl = doc.add_table(rows=1 + len(abbrevs), cols=2)
    set_table_layout_and_widths(tbl, [34.0, 141.0])
    set_table_cell_margins(tbl, top_pt=5.0, bottom_pt=5.0, left_pt=7.0, right_pt=7.0)
    set_table_borders(
        tbl,
        grid_mode="horizontal",
        top_color=COLORS["deep_purple"],
        top_sz=8,
        bottom_color=COLORS["deep_purple"],
        bottom_sz=8,
        inner_color=COLORS["border_light"],
        inner_sz=4,
    )
    set_row_header(tbl.rows[0], True)
    set_row_cant_split(tbl.rows[0], True)
    headers = ["약어 / 용어", "정의 및 설명"] if is_ko else ["TERM / ABBREVIATION", "FULL NAME & DEFINITION"]
    for c_i, h_txt in enumerate(headers):
        c = tbl.cell(0, c_i)
        set_cell_shading(c, COLORS["soft_lavender"])
        set_cell_valign(c, "center")
        set_cell_borders(c, bottom=("single", 6, COLORS["deep_purple"]))
        _format_cell_text(c, h_txt, profile, size_pt=8.8, bold=True, color_hex=COLORS["deep_purple"], rich=False)

    for idx, item in enumerate(abbrevs, start=1):
        row = tbl.rows[idx]
        set_row_cant_split(row, True)
        set_cell_shading(row.cells[0], COLORS["soft_canvas"])
        set_cell_valign(row.cells[0], "center")
        set_cell_valign(row.cells[1], "center")
        _format_cell_text(row.cells[0], item.get("term", ""), profile, size_pt=9.0, bold=True, color_hex=COLORS["deep_purple"], rich=False)
        _format_cell_text(row.cells[1], item.get("description", item.get("definition", "")), profile, size_pt=9.0, color_hex=COLORS["charcoal"], rich=False)

    if page_break_after:
        _add_page_break_para(doc)
    else:
        p_trail = doc.add_paragraph()
        clear_para_numbering(p_trail)
        set_para_spacing(p_trail, before_pt=0.0, after_pt=0.0, line_mult=0.5)
        r_tr = p_trail.add_run()
        apply_run_style(r_tr, profile, size_pt=1.0)


def build_compact_memo_header(
    doc,
    meta: Dict[str, Any],
    assets: Dict[str, Any],
    profile: FontProfile,
):
    """Build Mode B (include_cover: false): Sleek 1-page top metadata header banner (TF-1 style)."""
    lang = meta.get("language", "ko")
    is_ko = lang == "ko"

    # Attach header/footer references from sect0_pr to the body sectPr so Page 2+ gets running header
    # and Page 1+ gets running footer (with first-page header blanked via titlePg).
    sect0_pr = assets.get("sect0_pr")
    if doc.sections and sect0_pr is not None:
        body_sect_pr = doc.sections[0]._sectPr
        for old_ref in list(body_sect_pr.findall(qn("w:headerReference"))) + list(body_sect_pr.findall(qn("w:footerReference"))):
            body_sect_pr.remove(old_ref)
        default_ftr_rid = None
        for f_ref in sect0_pr.findall(qn("w:footerReference")):
            if f_ref.get(qn("w:type")) == "default":
                default_ftr_rid = f_ref.get(qn("r:id"))
        for ref_el in list(sect0_pr.findall(qn("w:headerReference"))) + list(sect0_pr.findall(qn("w:footerReference"))):
            cloned = deepcopy(ref_el)
            if cloned.tag == qn("w:footerReference") and cloned.get(qn("w:type")) == "first" and default_ftr_rid:
                cloned.set(qn("r:id"), default_ftr_rid)
            body_sect_pr.insert(0, cloned)
        doc.sections[0].different_first_page_header_footer = True

    # 1. Top Bar: Logo + Classification Badge
    top_tbl = doc.add_table(rows=1, cols=2)
    set_table_layout_and_widths(top_tbl, [75.0, 100.0])
    set_table_borders(top_tbl, grid_mode="horizontal", top_sz=0, bottom_sz=0, inner_sz=0)
    set_row_cant_split(top_tbl.rows[0], True)

    c_logo = top_tbl.cell(0, 0)
    set_cell_borders(c_logo, top=("none", 0, "auto"), bottom=("none", 0, "auto"), left=("none", 0, "auto"), right=("none", 0, "auto"))
    set_cell_valign(c_logo, "center")
    p_logo = c_logo.paragraphs[0]
    set_para_spacing(p_logo, before_pt=0.0, after_pt=1.0)
    if assets.get("logo_drawing") is not None:
        r_logo = p_logo.add_run()
        r_logo._r.append(deepcopy(assets["logo_drawing"]))
    else:
        r_logo = p_logo.add_run("HYOSUNG HEAVY INDUSTRIES")
        apply_run_style(r_logo, profile, size_pt=11.0, bold=True, color_hex=COLORS["deep_purple"])

    c_status = top_tbl.cell(0, 1)
    set_cell_borders(c_status, top=("none", 0, "auto"), bottom=("none", 0, "auto"), left=("none", 0, "auto"), right=("none", 0, "auto"))
    set_cell_valign(c_status, "center")
    status_str = meta.get("doc_status") or ("기술 검토 메모" if is_ko else "TECHNICAL REVIEW MEMO")
    p_st = c_status.paragraphs[0]
    p_st.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_para_spacing(p_st, before_pt=0.0, after_pt=1.0)
    r_st = p_st.add_run(f"  {status_str}  ")
    apply_run_style(r_st, profile, size_pt=8.5, bold=True, color_hex=COLORS["deep_purple"], shd_fill=COLORS["soft_lavender"])

    # 2. Title & Subtitle Banner
    p_title = doc.add_paragraph()
    clear_para_numbering(p_title)
    set_para_keep(p_title, keep_next=True, keep_lines=True)
    set_para_spacing(p_title, before_pt=4.0, after_pt=2.0, line_mult=1.15)
    r_title = p_title.add_run(meta.get("doc_title") or "Technical Review")
    apply_run_style(r_title, profile, size_pt=16.5, bold=True, color_hex=COLORS["dark_ink"])

    if meta.get("doc_subtitle"):
        p_sub = doc.add_paragraph()
        clear_para_numbering(p_sub)
        set_para_keep(p_sub, keep_next=True, keep_lines=True)
        set_para_spacing(p_sub, before_pt=0.0, after_pt=4.5, line_mult=1.12)
        r_sub = p_sub.add_run(meta["doc_subtitle"])
        apply_run_style(r_sub, profile, size_pt=10.0, color_hex=COLORS["slate_muted"])

    # 3. Compact 2x4 Metadata Grid (175.0 mm)
    hdr_tbl = doc.add_table(rows=2, cols=4)
    set_table_layout_and_widths(hdr_tbl, [28.0, 59.5, 28.0, 59.5])
    set_table_cell_margins(hdr_tbl, top_pt=3.5, bottom_pt=3.5, left_pt=6.0, right_pt=6.0)
    set_table_borders(
        hdr_tbl,
        grid_mode="full",
        top_color=COLORS["deep_purple"],
        top_sz=10,
        bottom_color=COLORS["deep_purple"],
        bottom_sz=10,
        inner_color=COLORS["border_light"],
        inner_sz=4,
    )
    prepared_name = ((meta.get("approvals") or {}).get("prepared_by") or {}).get("name") or meta.get("author_display") or "-"
    rows_spec = [
        (
            "문서번호" if is_ko else "Doc. No.",
            meta.get("doc_number") or "-",
            "기준일자" if is_ko else "Issue Date",
            f"{meta.get('issue_date', '-')} (Rev. {meta.get('revision', '0')})",
        ),
        (
            "프로젝트" if is_ko else "Project",
            meta.get("project_name") or "-",
            "작성 / 대상" if is_ko else "Prepared / For",
            f"{prepared_name} / {meta.get('client', '-')}",
        ),
    ]
    for r_i, (k1, v1, k2, v2) in enumerate(rows_spec):
        row = hdr_tbl.rows[r_i]
        set_row_cant_split(row, True)
        set_cell_shading(row.cells[0], COLORS["soft_canvas"])
        set_cell_shading(row.cells[2], COLORS["soft_canvas"])
        for c_i in range(4):
            set_cell_valign(row.cells[c_i], "center")
        _format_cell_text(row.cells[0], k1, profile, size_pt=8.5, bold=True, color_hex=COLORS["deep_purple"], before_pt=1.0, after_pt=1.0, rich=False)
        _format_cell_text(row.cells[1], v1, profile, size_pt=8.5, bold=(r_i == 0), color_hex=COLORS["charcoal"], before_pt=1.0, after_pt=1.0)
        _format_cell_text(row.cells[2], k2, profile, size_pt=8.5, bold=True, color_hex=COLORS["deep_purple"], before_pt=1.0, after_pt=1.0, rich=False)
        _format_cell_text(row.cells[3], v2, profile, size_pt=8.5, color_hex=COLORS["charcoal"], before_pt=1.0, after_pt=1.0)

    # Compact spacer paragraph
    p_sp = doc.add_paragraph()
    clear_para_numbering(p_sp)
    set_para_spacing(p_sp, before_pt=0.0, after_pt=2.0, line_mult=0.5)
    r_sp = p_sp.add_run()
    apply_run_style(r_sp, profile, size_pt=2.0)
