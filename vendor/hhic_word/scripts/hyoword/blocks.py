"""Deterministic renderer for all 14 declarative block types in hyoword v2.0."""

from __future__ import annotations
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm

from .cover_header import build_abbreviations_section
from .design import (
    CALLOUT_THEMES,
    COLORS,
    CONTENT_WIDTH_LANDSCAPE_MM,
    CONTENT_WIDTH_PORTRAIT_MM,
    FontProfile,
    MARGINS_DEFAULT_MM,
    PAGE_A4_LANDSCAPE_MM,
    PAGE_A4_PORTRAIT_MM,
    classify_status_cell,
)
from .xml_helpers import (
    append_rich_text,
    apply_run_style,
    clear_para_numbering,
    set_cell_borders,
    set_cell_margins,
    set_cell_shading,
    set_cell_valign,
    set_para_bottom_border,
    set_para_ind,
    set_para_keep,
    set_para_outline_level,
    set_para_spacing,
    set_row_cant_split,
    set_row_header,
    set_table_borders,
    set_table_cell_margins,
    set_table_layout_and_widths,
)

LEADING_NUM_RE = re.compile(r"^\s*\d+(?:\.\d+)*\.?\s+")


def _roman(n: int) -> str:
    vals = [(10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]
    res = []
    for v, sym in vals:
        while n >= v:
            res.append(sym)
            n -= v
    return "".join(res) or "i"


class BlockRenderer:
    def __init__(
        self,
        doc,
        meta: Dict[str, Any],
        profile: FontProfile,
        base_dir: Path,
    ):
        self.doc = doc
        self.meta = meta
        self.profile = profile
        self.base_dir = base_dir
        self.lang = meta.get("language", "en")
        self.is_ko = self.lang == "ko"
        self.heading_counters = [0, 0, 0, 0]
        self.table_counter = 0
        self.figure_counter = 0
        self.current_width_mm = CONTENT_WIDTH_PORTRAIT_MM

    def render_all(self, blocks: List[Dict[str, Any]]):
        for idx, block in enumerate(blocks):
            btype = (block.get("type") or "").strip().lower()
            handler = getattr(self, f"_render_{btype}", None)
            if handler is None:
                raise ValueError(f"Block #{idx + 1}: Unsupported block type '{btype}'")
            handler(block)

        # Ensure if the document body ends with a table, a minimal 1pt paragraph follows it
        # so Word does not synthesize a tall 10pt trailing paragraph that could push onto a blank page.
        body_children = [ch for ch in self.doc._body._body if ch.tag != qn("w:sectPr")]
        if body_children and body_children[-1].tag == qn("w:tbl"):
            p_end = self.doc.add_paragraph()
            clear_para_numbering(p_end)
            set_para_spacing(p_end, before_pt=0.0, after_pt=0.0, line_mult=0.5)
            r_end = p_end.add_run()
            apply_run_style(r_end, self.profile, size_pt=1.0)

    def _keep_table_together(self, tbl, max_rows: int = 4):
        """Stop a lone row being stranded across a page break.

        Short tables (up to max_rows) stay on one page. Longer tables may split, but the header keeps
        two data rows with it and the last row never moves to a new page alone.
        """
        rows = list(tbl.rows)
        if len(rows) <= max_rows:
            keep_rows = rows[:-1]
        else:
            keep_rows = [rows[0], rows[1], rows[-2]]
        for row in keep_rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    pPr = p._p.get_or_add_pPr()
                    if pPr.find(qn("w:keepNext")) is None:
                        # keepNext must precede spacing/jc in CT_PPr, so insert right after an optional pStyle
                        p_style = pPr.find(qn("w:pStyle"))
                        pPr.insert(1 if p_style is not None else 0, OxmlElement("w:keepNext"))

    def _add_caption(self, kind: str, title: str, keep_with_next: bool = True):
        if not title:
            return
        p = self.doc.add_paragraph()
        clear_para_numbering(p)
        set_para_keep(p, keep_next=keep_with_next, keep_lines=True)
        set_para_spacing(p, before_pt=8.0 if keep_with_next else 4.0, after_pt=3.0, line_mult=1.12)

        if kind == "table":
            self.table_counter += 1
            label = f"표 {self.table_counter}" if self.is_ko else f"Table {self.table_counter}"
        else:
            self.figure_counter += 1
            label = f"그림 {self.figure_counter}" if self.is_ko else f"Figure {self.figure_counter}"

        r_lbl = p.add_run(f"{label}. ")
        apply_run_style(r_lbl, self.profile, size_pt=9.0, bold=True, color_hex=COLORS["deep_purple"])
        append_rich_text(p, title, self.profile, base_size_pt=9.0, base_color=COLORS["slate_muted"], base_bold=True)

    def _add_table_note(self, note: Optional[str], source: Optional[str] = None):
        if not note and not source:
            return
        p = self.doc.add_paragraph()
        clear_para_numbering(p)
        set_para_keep(p, keep_next=False, keep_lines=True)
        set_para_spacing(p, before_pt=2.5, after_pt=6.0, line_mult=1.12)
        if note:
            prefix = "주) " if self.is_ko else "Note: "
            r_n = p.add_run(prefix)
            apply_run_style(r_n, self.profile, size_pt=8.0, bold=True, color_hex=COLORS["slate_muted"])
            append_rich_text(p, note, self.profile, base_size_pt=8.0, base_color=COLORS["slate_muted"])
        if source:
            if note:
                r_sep = p.add_run("  |  ")
                apply_run_style(r_sep, self.profile, size_pt=8.0, color_hex=COLORS["slate_muted"])
            s_prefix = "출처: " if self.is_ko else "Source: "
            r_s = p.add_run(s_prefix)
            apply_run_style(r_s, self.profile, size_pt=8.0, bold=True, color_hex=COLORS["slate_muted"])
            append_rich_text(p, source, self.profile, base_size_pt=8.0, base_color=COLORS["slate_muted"])

    # ------------------------------------------------------------------
    # 1. Heading
    # ------------------------------------------------------------------
    def _render_heading(self, block: Dict[str, Any]):
        level = max(1, min(4, int(block.get("level", 1))))
        numbered = block.get("numbered", True)
        raw_text = (block.get("text") or "").strip()
        clean_text = LEADING_NUM_RE.sub("", raw_text) if numbered else raw_text

        prefix = ""
        if numbered:
            self.heading_counters[level - 1] += 1
            for k in range(level, 4):
                self.heading_counters[k] = 0
            if level == 1:
                prefix = f"{self.heading_counters[0]}. "
            else:
                nums = ".".join(str(self.heading_counters[i]) for i in range(level))
                prefix = f"{nums} "

        p = self.doc.add_paragraph()
        clear_para_numbering(p)
        set_para_keep(p, keep_next=True, keep_lines=True, page_break_before=bool(block.get("page_break_before", False)))
        if level <= 3:
            set_para_outline_level(p, level - 1)

        if level == 1:
            set_para_spacing(p, before_pt=16.0, after_pt=6.0, line_mult=1.15)
            set_para_bottom_border(p, color_hex=COLORS["border_light"], sz_eighths_pt=6, space_pt=3)
            r = p.add_run(f"{prefix}{clean_text}")
            apply_run_style(r, self.profile, size_pt=14.5, bold=True, color_hex=COLORS["deep_purple"])
        elif level == 2:
            set_para_spacing(p, before_pt=13.0, after_pt=4.5, line_mult=1.15)
            r = p.add_run(f"{prefix}{clean_text}")
            apply_run_style(r, self.profile, size_pt=12.0, bold=True, color_hex=COLORS["main_purple"])
        elif level == 3:
            set_para_spacing(p, before_pt=10.0, after_pt=3.0, line_mult=1.15)
            r = p.add_run(f"{prefix}{clean_text}")
            apply_run_style(r, self.profile, size_pt=10.8, bold=True, color_hex=COLORS["charcoal"])
        else:
            set_para_spacing(p, before_pt=8.0, after_pt=2.5, line_mult=1.15)
            r = p.add_run(f"{prefix}{clean_text}")
            apply_run_style(r, self.profile, size_pt=10.2, bold=True, color_hex=COLORS["slate_muted"])

    # ------------------------------------------------------------------
    # 2. Paragraph
    # ------------------------------------------------------------------
    def _render_paragraph(self, block: Dict[str, Any]):
        style_kind = (block.get("style") or "body").lower()
        texts = block.get("paragraphs") or [block.get("text", "")]
        if isinstance(texts, str):
            texts = [texts]

        for t in texts:
            p = self.doc.add_paragraph()
            clear_para_numbering(p)
            set_para_keep(p, keep_next=bool(block.get("keep_with_next", False)), keep_lines=False)
            if style_kind == "lead":
                set_para_spacing(p, before_pt=2.0, after_pt=6.0, line_mult=1.22)
                append_rich_text(p, t, self.profile, base_size_pt=10.8, base_color=COLORS["dark_ink"], base_bold=False)
            elif style_kind in ("note", "guidance"):
                set_para_spacing(p, before_pt=1.5, after_pt=4.5, line_mult=1.15)
                append_rich_text(p, t, self.profile, base_size_pt=9.2, base_color=COLORS["slate_muted"], base_italic=True)
            else:
                set_para_spacing(p, before_pt=1.0, after_pt=5.5, line_mult=1.22)
                append_rich_text(p, t, self.profile, base_size_pt=10.2, base_color=COLORS["charcoal"])

    # ------------------------------------------------------------------
    # 3. Clause List & Bullet List
    # ------------------------------------------------------------------
    def _render_clause_list(self, block: Dict[str, Any]):
        scheme = (block.get("scheme") or "bullet").lower()
        items = block.get("items") or []
        self._render_list_items(items, scheme=scheme, depth=0)

    def _render_bullet_list(self, block: Dict[str, Any]):
        self._render_clause_list({**block, "scheme": block.get("scheme", "bullet")})

    def _render_list_items(self, items: List[Any], scheme: str, depth: int):
        for idx, item in enumerate(items, start=1):
            if isinstance(item, dict):
                txt = item.get("text", "")
                head = item.get("head") or item.get("title")
                if head:
                    txt = f"**{head}**: {txt}" if txt else f"**{head}**"
                sub = item.get("sub_items") or item.get("items") or []
                sub_scheme = item.get("sub_scheme") or ("roman" if scheme == "alpha" else scheme)
            else:
                txt = str(item)
                sub = []
                sub_scheme = "bullet"

            # Determine prefix marker
            if scheme == "alpha":
                if depth == 0:
                    marker = f"({chr(96 + ((idx - 1) % 26) + 1)}) "
                elif depth == 1:
                    marker = f"({_roman(idx)}) "
                else:
                    marker = f"({idx}) "
            elif scheme == "numbered":
                marker = f"{idx}) " if depth == 0 else f"({chr(96 + ((idx - 1) % 26) + 1)}) "
            else:
                bullets = ["•  ", "▪  ", "–  "]
                marker = bullets[min(depth, len(bullets) - 1)]

            p = self.doc.add_paragraph()
            clear_para_numbering(p)
            left_mm = 6.0 + depth * 6.0
            hang_mm = 5.5 if scheme in ("alpha", "numbered") else 3.8
            set_para_ind(p, left_mm=left_mm, hanging_mm=hang_mm)
            set_para_spacing(p, before_pt=1.0, after_pt=3.5, line_mult=1.18)

            r_mk = p.add_run(marker)
            apply_run_style(
                r_mk,
                self.profile,
                size_pt=10.0 if depth == 0 else 9.5,
                bold=True,
                color_hex=COLORS["deep_purple"] if depth == 0 else COLORS["main_purple"],
            )
            append_rich_text(
                p,
                txt,
                self.profile,
                base_size_pt=10.0 if depth == 0 else 9.5,
                base_color=COLORS["charcoal"],
            )

            if sub:
                self._render_list_items(sub, scheme=sub_scheme, depth=depth + 1)

    # ------------------------------------------------------------------
    # 4. Callout Box (5 semantic kinds)
    # ------------------------------------------------------------------
    def _render_callout(self, block: Dict[str, Any]):
        raw_kind = (block.get("kind") or "executive_summary").lower()
        alias_map = {
            "summary": "executive_summary",
            "takeaway": "key_takeaway",
            "warning": "risk_warning",
            "risk": "risk_warning",
            "caution": "risk_warning",
            "hold": "contract_hold",
            "tbc": "contract_hold",
            "response": "draft_response",
            "info": "draft_response",
        }
        kind = alias_map.get(raw_kind, raw_kind)
        theme = CALLOUT_THEMES.get(kind, CALLOUT_THEMES["executive_summary"])

        tbl = self.doc.add_table(rows=1, cols=1)
        set_table_layout_and_widths(tbl, [self.current_width_mm])
        set_row_cant_split(tbl.rows[0], True)

        cell = tbl.cell(0, 0)
        set_cell_shading(cell, theme["bg"])
        set_cell_margins(cell, top_pt=7.5, bottom_pt=7.5, left_pt=11.0, right_pt=10.0)
        set_cell_borders(
            cell,
            left=("single", 24, theme["border_left"]),
            top=("single", 4, COLORS["border_card"]),
            right=("single", 4, COLORS["border_card"]),
            bottom=("single", 4, COLORS["border_card"]),
        )

        title = block.get("title") or (theme["default_label_ko"] if self.is_ko else theme["default_label_en"])
        p0 = cell.paragraphs[0]
        clear_para_numbering(p0)
        set_para_keep(p0, keep_next=True, keep_lines=True)
        set_para_spacing(p0, before_pt=0.0, after_pt=3.5, line_mult=1.15)
        r_t = p0.add_run(title)
        apply_run_style(r_t, self.profile, size_pt=9.8, bold=True, color_hex=theme["title_color"])

        body = block.get("body") or block.get("text")
        if body:
            body_list = [body] if isinstance(body, str) else body
            for b_txt in body_list:
                p_b = cell.add_paragraph()
                clear_para_numbering(p_b)
                set_para_spacing(p_b, before_pt=1.0, after_pt=3.0, line_mult=1.18)
                append_rich_text(p_b, b_txt, self.profile, base_size_pt=9.6, base_color=COLORS["charcoal"])

        bullets = block.get("bullets") or block.get("items") or []
        for b_item in bullets:
            p_bl = cell.add_paragraph()
            clear_para_numbering(p_bl)
            set_para_ind(p_bl, left_mm=4.5, hanging_mm=3.2)
            set_para_spacing(p_bl, before_pt=1.0, after_pt=2.5, line_mult=1.15)
            r_dot = p_bl.add_run("•  ")
            apply_run_style(r_dot, self.profile, size_pt=9.5, bold=True, color_hex=theme["title_color"])
            append_rich_text(p_bl, str(b_item), self.profile, base_size_pt=9.5, base_color=COLORS["charcoal"])

        # Spacing paragraph after callout table
        p_after = self.doc.add_paragraph()
        clear_para_numbering(p_after)
        set_para_spacing(p_after, before_pt=0.0, after_pt=4.0, line_mult=1.0)

    # ------------------------------------------------------------------
    # 5. Key-Value Table (kv_table)
    # ------------------------------------------------------------------
    def _render_kv_table(self, block: Dict[str, Any]):
        self._add_caption("table", block.get("caption", ""), keep_with_next=True)
        pairs = block.get("pairs") or block.get("rows") or []
        cols_mode = int(block.get("columns_mode", 2))

        if cols_mode == 4:
            row_count = (len(pairs) + 1) // 2
            tbl = self.doc.add_table(rows=max(1, row_count), cols=4)
            w_key = round(self.current_width_mm * 0.19, 2)
            w_val = round((self.current_width_mm - 2 * w_key) / 2.0, 2)
            set_table_layout_and_widths(tbl, [w_key, w_val, w_key, w_val])
        else:
            tbl = self.doc.add_table(rows=max(1, len(pairs)), cols=2)
            w_key = round(self.current_width_mm * 0.28, 2)
            w_val = round(self.current_width_mm - w_key, 2)
            set_table_layout_and_widths(tbl, [w_key, w_val])

        set_table_cell_margins(tbl, top_pt=4.5, bottom_pt=4.5, left_pt=7.0, right_pt=7.0)
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

        if cols_mode == 4:
            for r_i in range(row_count):
                row = tbl.rows[r_i]
                set_row_cant_split(row, True)
                for pair_offset in (0, 1):
                    p_idx = r_i * 2 + pair_offset
                    c_k = row.cells[pair_offset * 2]
                    c_v = row.cells[pair_offset * 2 + 1]
                    set_cell_shading(c_k, COLORS["soft_canvas"])
                    set_cell_valign(c_k, "center")
                    set_cell_valign(c_v, "center")
                    if p_idx < len(pairs):
                        item = pairs[p_idx]
                        k_txt = item.get("key", item[0] if isinstance(item, (list, tuple)) else "")
                        v_txt = item.get("value", item[1] if isinstance(item, (list, tuple)) else "")
                        p_k = c_k.paragraphs[0]
                        set_para_spacing(p_k, before_pt=1.0, after_pt=1.0, line_mult=1.12)
                        append_rich_text(p_k, str(k_txt), self.profile, base_size_pt=8.8, base_color=COLORS["deep_purple"], base_bold=True)
                        p_v = c_v.paragraphs[0]
                        set_para_spacing(p_v, before_pt=1.0, after_pt=1.0, line_mult=1.12)
                        append_rich_text(p_v, str(v_txt), self.profile, base_size_pt=9.0, base_color=COLORS["charcoal"])
        else:
            for r_i, item in enumerate(pairs):
                row = tbl.rows[r_i]
                set_row_cant_split(row, True)
                c_k, c_v = row.cells[0], row.cells[1]
                set_cell_shading(c_k, COLORS["soft_canvas"])
                set_cell_valign(c_k, "center")
                set_cell_valign(c_v, "center")
                k_txt = item.get("key", item[0] if isinstance(item, (list, tuple)) else "")
                v_txt = item.get("value", item[1] if isinstance(item, (list, tuple)) else "")
                if isinstance(item, dict) and item.get("highlight"):
                    set_cell_shading(c_v, COLORS["soft_lavender"])
                p_k = c_k.paragraphs[0]
                set_para_spacing(p_k, before_pt=1.5, after_pt=1.5, line_mult=1.15)
                append_rich_text(p_k, str(k_txt), self.profile, base_size_pt=9.0, base_color=COLORS["deep_purple"], base_bold=True)
                p_v = c_v.paragraphs[0]
                set_para_spacing(p_v, before_pt=1.5, after_pt=1.5, line_mult=1.15)
                append_rich_text(p_v, str(v_txt), self.profile, base_size_pt=9.0, base_color=COLORS["charcoal"])

        self._keep_table_together(tbl)
        self._add_table_note(block.get("note"), block.get("source"))

    # ------------------------------------------------------------------
    # 6. Standard Engineering / Spec Table (table / spec_table)
    # ------------------------------------------------------------------
    def _render_table(self, block: Dict[str, Any]):
        self._add_caption("table", block.get("caption", ""), keep_with_next=True)
        columns = block.get("columns") or []
        rows = block.get("rows") or []
        n_cols = len(columns)
        if n_cols == 0:
            raise ValueError("Table block requires non-empty 'columns'")

        # Calculate column widths in mm
        col_widths_mm = block.get("col_widths_mm")
        if col_widths_mm and len(col_widths_mm) == n_cols:
            total_given = sum(float(x) for x in col_widths_mm)
            scale = self.current_width_mm / total_given if total_given > 0 else 1.0
            widths = [round(float(x) * scale, 2) for x in col_widths_mm]
        else:
            # Smart proportional widths based on content length
            max_lens = []
            for c_i in range(n_cols):
                col_texts = [str(columns[c_i])] + [str(r[c_i]) for r in rows if c_i < len(r)]
                avg_len = max(6, min(65, max(len(t) for t in col_texts)))
                max_lens.append(avg_len ** 0.65)
            tot_weight = sum(max_lens)
            widths = [round(self.current_width_mm * (w / tot_weight), 2) for w in max_lens]
        # Adjust rounding diff on last column
        widths[-1] = round(widths[-1] + (self.current_width_mm - sum(widths)), 2)

        theme_mode = (block.get("theme") or "solid").lower()
        grid_mode = (block.get("grid") or "horizontal").lower()
        key_col = block.get("key_col", 0 if block.get("shade_first_col", True) else None)
        zebra = block.get("zebra", True)
        align_cols = block.get("align") or []

        tbl = self.doc.add_table(rows=1 + len(rows), cols=n_cols)
        set_table_layout_and_widths(tbl, widths)
        set_table_cell_margins(tbl, top_pt=4.5, bottom_pt=4.5, left_pt=6.5, right_pt=6.5)
        set_table_borders(
            tbl,
            grid_mode=grid_mode,
            top_color=COLORS["deep_purple"],
            top_sz=10,
            bottom_color=COLORS["deep_purple"],
            bottom_sz=10,
            inner_color=COLORS["border_light"],
            inner_sz=4,
        )

        # Header Row (Default: Light Hyosung Soft Lavender #EBE6FF fill + Deep Purple #2E008B text)
        hdr_row = tbl.rows[0]
        set_row_header(hdr_row, True)
        set_row_cant_split(hdr_row, True)
        hdr_bg = (
            COLORS["deep_purple"]
            if theme_mode == "dark"
            else (COLORS["border_card"] if theme_mode == "grey" else COLORS["soft_lavender"])
        )
        hdr_fg = COLORS["white"] if theme_mode == "dark" else COLORS["deep_purple"]
        for c_i, col_title in enumerate(columns):
            cell = hdr_row.cells[c_i]
            set_cell_shading(cell, hdr_bg)
            set_cell_valign(cell, "center")
            set_cell_borders(
                cell,
                bottom=("single", 6, COLORS["deep_purple"]),
            )
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if n_cols <= 5 and c_i > 0 else WD_ALIGN_PARAGRAPH.LEFT
            set_para_spacing(p, before_pt=2.5, after_pt=2.5, line_mult=1.1)
            append_rich_text(p, str(col_title), self.profile, base_size_pt=8.8, base_color=hdr_fg, base_bold=True)

        # Body Rows
        highlight_rows = set(block.get("highlight_rows") or [])
        for r_i, row_vals in enumerate(rows):
            row = tbl.rows[r_i + 1]
            set_row_cant_split(row, True)
            is_hi_row = r_i in highlight_rows
            for c_i in range(n_cols):
                cell = row.cells[c_i]
                set_cell_valign(cell, "center")
                val_str = str(row_vals[c_i]) if c_i < len(row_vals) else ""

                # Check semantic status cell
                status_colors = classify_status_cell(val_str)
                p = cell.paragraphs[0]
                set_para_spacing(p, before_pt=1.5, after_pt=1.5, line_mult=1.15)

                if c_i < len(align_cols):
                    al = align_cols[c_i].lower()
                    p.alignment = (
                        WD_ALIGN_PARAGRAPH.RIGHT
                        if al == "right"
                        else WD_ALIGN_PARAGRAPH.CENTER
                        if al == "center"
                        else WD_ALIGN_PARAGRAPH.LEFT
                    )
                elif status_colors is not None:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

                if status_colors is not None:
                    bg_hex, fg_hex = status_colors
                    set_cell_shading(cell, bg_hex)
                    r_st = p.add_run(val_str.strip())
                    apply_run_style(r_st, self.profile, size_pt=8.0, bold=True, color_hex=fg_hex)
                else:
                    if is_hi_row:
                        set_cell_shading(cell, COLORS["soft_lavender"])
                    elif key_col is not None and c_i == key_col:
                        set_cell_shading(cell, COLORS["soft_canvas"])
                    elif zebra and r_i % 2 == 1:
                        set_cell_shading(cell, COLORS["zebra_row"])

                    is_key = key_col is not None and c_i == key_col
                    append_rich_text(
                        p,
                        val_str,
                        self.profile,
                        base_size_pt=8.8,
                        base_color=COLORS["deep_purple"] if is_key else COLORS["charcoal"],
                        base_bold=is_key or is_hi_row,
                    )

        self._keep_table_together(tbl)
        self._add_table_note(block.get("note"), block.get("source"))

    def _render_spec_table(self, block: Dict[str, Any]):
        self._render_table(block)

    # ------------------------------------------------------------------
    # 7. Redline / Baseline vs Revised Comparison (redline_comparison / comparison)
    # ------------------------------------------------------------------
    def _render_redline_comparison(self, block: Dict[str, Any]):
        if self.is_ko:
            cols = block.get("columns") or [
                block.get("item_title", "쟁점 / 조항"),
                block.get("left_title", "당초 판단 / 기존 문안"),
                block.get("right_title", "후속 정정 / 수정(안)"),
                block.get("note_title", "근거 및 영향 검토"),
            ]
        else:
            cols = block.get("columns") or [
                block.get("item_title", "Clause / Topic"),
                block.get("left_title", "Baseline / Original Wording"),
                block.get("right_title", "Proposed Markup / Revised Position"),
                block.get("note_title", "Engineering & Contractual Rationale"),
            ]
        rows_in = block.get("rows") or []
        rows_out = []
        for r in rows_in:
            if isinstance(r, dict):
                row_tuple = [
                    r.get("item", r.get("clause", "")),
                    r.get("left", r.get("original", r.get("baseline", ""))),
                    r.get("right", r.get("revised", r.get("proposed", ""))),
                ]
                if len(cols) >= 4:
                    row_tuple.append(r.get("note", r.get("rationale", "")))
                rows_out.append(row_tuple)
            else:
                rows_out.append(list(r))

        default_widths = [26.0, 52.0, 54.0, 43.0] if len(cols) == 4 else [33.0, 71.0, 71.0]
        self._render_table(
            {
                "caption": block.get("caption", ""),
                "columns": cols,
                "rows": rows_out,
                "col_widths_mm": block.get("col_widths_mm") or default_widths[: len(cols)],
                "key_col": 0,
                "grid": block.get("grid", "full"),
                "note": block.get("note"),
                "source": block.get("source"),
            }
        )

    def _render_comparison(self, block: Dict[str, Any]):
        self._render_redline_comparison(block)

    # ------------------------------------------------------------------
    # 8. Requirement / Compliance Matrix (requirement_matrix)
    # ------------------------------------------------------------------
    def _render_requirement_matrix(self, block: Dict[str, Any]):
        if self.is_ko:
            cols = block.get("columns") or ["요건 ID", "근거 조항/규격", "요구사항 요약", "준수 상태", "검토 의견 및 증빙"]
        else:
            cols = block.get("columns") or ["Req. ID", "Clause / Standard", "Requirement Summary", "Compliance", "EPC Position & Evidence"]
        rows_in = block.get("rows") or block.get("requirements") or []
        rows_out = []
        for r in rows_in:
            if isinstance(r, dict):
                rows_out.append([
                    r.get("id", ""),
                    r.get("clause", r.get("ref", "")),
                    r.get("requirement", r.get("summary", "")),
                    r.get("status", "TBC"),
                    r.get("position", r.get("evidence", "")),
                ])
            else:
                rows_out.append(list(r))

        self._render_table(
            {
                "caption": block.get("caption", ""),
                "columns": cols,
                "rows": rows_out,
                "col_widths_mm": block.get("col_widths_mm") or [17.0, 27.0, 50.0, 28.0, 53.0],
                "key_col": 0,
                "grid": block.get("grid", "horizontal"),
                "note": block.get("note"),
                "source": block.get("source"),
            }
        )

    # ------------------------------------------------------------------
    # 9. Open Items / Clarifications Table (open_items)
    # ------------------------------------------------------------------
    def _render_open_items(self, block: Dict[str, Any]):
        if self.is_ko:
            cols = block.get("columns") or ["No.", "항목 / 쟁점", "추가 확인 필요 사항 (Required Clarification)", "영향 및 조치 계획", "상태"]
        else:
            cols = block.get("columns") or ["No.", "Subject / Clause", "Required Clarification / Missing Input", "Document / Design Impact", "Status"]
        items = block.get("items") or block.get("rows") or []
        rows_out = []
        for idx, item in enumerate(items, start=1):
            if isinstance(item, dict):
                row_data = [
                    str(item.get("no", idx)),
                    item.get("subject", ""),
                    item.get("clarification", item.get("question", "")),
                    item.get("impact", ""),
                ]
                if len(cols) >= 5:
                    row_data.append(item.get("status", "OPEN"))
                rows_out.append(row_data)
            else:
                rows_out.append(list(item))

        widths = [11.0, 34.0, 62.0, 48.0, 20.0] if len(cols) == 5 else [12.0, 38.0, 68.0, 57.0]
        self._render_table(
            {
                "caption": block.get("caption", "Open Items & Clarifications Required" if not self.is_ko else "미결 확인 필요 사항 및 향후 질의 목록"),
                "columns": cols,
                "rows": rows_out,
                "col_widths_mm": block.get("col_widths_mm") or widths[: len(cols)],
                "key_col": 0,
                "align": ["center", "left", "left", "left", "center"][: len(cols)],
                "note": block.get("note"),
                "source": block.get("source"),
            }
        )

    # ------------------------------------------------------------------
    # 10. Evidence & Source Traceability Table (evidence_log)
    # ------------------------------------------------------------------
    def _render_evidence_log(self, block: Dict[str, Any]):
        if self.is_ko:
            cols = block.get("columns") or ["근거 ID", "문서명 / 표준 / 원천", "근거 등급", "확인 상태 및 비고"]
        else:
            cols = block.get("columns") or ["Ref. ID", "Source Document / Standard", "Evidence Grade", "Verification Status & Scope"]
        sources = block.get("sources") or block.get("rows") or []
        rows_out = []
        for idx, src in enumerate(sources, start=1):
            if isinstance(src, dict):
                rows_out.append([
                    src.get("id", f"REF-{idx:02d}"),
                    src.get("title", src.get("document", "")),
                    src.get("grade", "E2"),
                    src.get("note", src.get("status", "")),
                ])
            else:
                rows_out.append(list(src))

        self._render_table(
            {
                "caption": block.get("caption", "Source Documents & Evidence Traceability" if not self.is_ko else "근거 자료 목록 및 검증 등급"),
                "columns": cols,
                "rows": rows_out,
                "col_widths_mm": block.get("col_widths_mm") or [18.0, 66.0, 22.0, 69.0],
                "key_col": 0,
                "align": ["center", "left", "center", "left"],
                "note": block.get("note"),
                "source": block.get("source"),
            }
        )

    # ------------------------------------------------------------------
    # 11. Abbreviations Block (abbreviations)
    # ------------------------------------------------------------------
    def _render_abbreviations(self, block: Dict[str, Any]):
        items = block.get("items") or block.get("abbreviations") or []
        build_abbreviations_section(self.doc, items, self.profile, is_ko=self.is_ko, page_break_after=bool(block.get("page_break_after", False)))

    # ------------------------------------------------------------------
    # 12. Figure / Image (figure / image)
    # ------------------------------------------------------------------
    def _render_figure(self, block: Dict[str, Any]):
        raw_path = block.get("path") or ""
        img_path = Path(raw_path)
        if not img_path.is_absolute():
            candidate = self.base_dir / img_path
            if candidate.exists():
                img_path = candidate
        if not img_path.exists():
            raise FileNotFoundError(f"Figure image file not found: {raw_path}")

        width_mm = min(float(block.get("width_mm", 155.0)), self.current_width_mm - 4.0)
        p_img = self.doc.add_paragraph()
        clear_para_numbering(p_img)
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_para_keep(p_img, keep_next=True, keep_lines=True)
        set_para_spacing(p_img, before_pt=6.0, after_pt=2.0)
        run = p_img.add_run()
        run.add_picture(str(img_path), width=Mm(width_mm))

        caption = block.get("caption") or ""
        if caption:
            self._add_caption("figure", caption, keep_with_next=False)
            # Center the figure caption
            self.doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    def _render_image(self, block: Dict[str, Any]):
        self._render_figure(block)

    # ------------------------------------------------------------------
    # 13. Page Break
    # ------------------------------------------------------------------
    def _render_page_break(self, _block: Dict[str, Any]):
        p = self.doc.add_paragraph()
        clear_para_numbering(p)
        set_para_spacing(p, before_pt=0.0, after_pt=0.0, line_mult=1.0)
        r = p.add_run()
        br = OxmlElement("w:br")
        br.set(qn("w:type"), "page")
        r._r.append(br)

    # ------------------------------------------------------------------
    # 14. Section Break (Portrait / Landscape switching)
    # ------------------------------------------------------------------
    def _render_section_break(self, block: Dict[str, Any]):
        orient_str = (block.get("orientation") or "portrait").lower()
        new_sec = self.doc.add_section(WD_SECTION.NEW_PAGE)
        new_sec.top_margin = Mm(MARGINS_DEFAULT_MM["top"])
        new_sec.bottom_margin = Mm(MARGINS_DEFAULT_MM["bottom"])
        new_sec.left_margin = Mm(MARGINS_DEFAULT_MM["left"])
        new_sec.right_margin = Mm(MARGINS_DEFAULT_MM["right"])
        new_sec.different_first_page_header_footer = False

        if orient_str == "landscape":
            new_sec.orientation = WD_ORIENT.LANDSCAPE
            new_sec.page_width = Mm(PAGE_A4_LANDSCAPE_MM[0])
            new_sec.page_height = Mm(PAGE_A4_LANDSCAPE_MM[1])
            self.current_width_mm = CONTENT_WIDTH_LANDSCAPE_MM
        else:
            new_sec.orientation = WD_ORIENT.PORTRAIT
            new_sec.page_width = Mm(PAGE_A4_PORTRAIT_MM[0])
            new_sec.page_height = Mm(PAGE_A4_PORTRAIT_MM[1])
            self.current_width_mm = CONTENT_WIDTH_PORTRAIT_MM
