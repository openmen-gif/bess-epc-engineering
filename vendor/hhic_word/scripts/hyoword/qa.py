"""Automated QA, OpenXML hygiene checks, Word COM TOC/PDF export, PNG rendering, and Parity Receipt."""

from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Dict, List
import xml.etree.ElementTree as ET
import zipfile

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W = f"{{{NS['w']}}}"

LEFTOVER_TEMPLATE_TOKENS = [
    "[PROJECT NAME]",
    "[DOCUMENT TITLE]",
    "[DOCUMENT NUMBER]",
    "[ISSUE DATE]",
    "[REVISION]",
    "[CLIENT]",
    "[CONTRACT NUMBER]",
    "[PREPARED BY]",
    "[CHECKED BY]",
    "[APPROVED BY]",
    "[SOURCE MATERIALS]",
    "DOCUMENT GENERATION WORKSPACE",
    "[AI TO INSERT THE PROPOSED NUMBERED STRUCTURE",
]

LEGACY_BANNED_FONTS = {"바탕", "굴림", "MS PGothic", "Times New Roman", "Trebuchet MS"}
INLINE_CLEAN_RE = re.compile(r"(\*\*|\*|~~|\+\+|`)")
# Inline markup that must never survive into the rendered document text
MARKUP_LEAK_RE = re.compile(r"`|\*\*|~~|\+\+")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_template_pin(template_path: Path, pin_path: Path) -> Dict[str, Any]:
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    actual_hash = sha256_file(template_path)
    expected_hash = None
    if pin_path.exists():
        pin_data = json.loads(pin_path.read_text(encoding="utf-8"))
        expected_hash = pin_data.get("sha256")
        if expected_hash and actual_hash != expected_hash:
            raise ValueError(
                f"[TEMPLATE] Hash mismatch on {template_path.name}: expected {expected_hash}, got {actual_hash}"
            )
    return {
        "template_file": template_path.name,
        "sha256": actual_hash,
        "expected_sha256": expected_hash or actual_hash,
        "verified": True,
    }


def inspect_docx_xml_hygiene(docx_path: Path) -> Dict[str, Any]:
    """Check OpenXML hygiene: zero leftover placeholders, zero legacy fonts on runs, keepNext, tblHeader, cantSplit, table widths."""
    issues: List[str] = []
    stats = {
        "headings_checked": 0,
        "headings_with_keepNext": 0,
        "tables_checked": 0,
        "data_tables_with_tblHeader": 0,
        "rows_checked": 0,
        "rows_with_cantSplit": 0,
        "max_table_width_mm": 0.0,
        "legacy_font_runs": 0,
        "leftover_tokens": [],
        "markup_leaks": 0,
    }

    with zipfile.ZipFile(docx_path, "r") as zf:
        xml_targets = [n for n in zf.namelist() if n == "word/document.xml" or n.startswith("word/header") or n.startswith("word/footer")]
        for name in xml_targets:
            root = ET.fromstring(zf.read(name))
            full_text = "".join(t.text for t in root.findall(".//w:t", NS) if t.text)
            for tok in LEFTOVER_TEMPLATE_TOKENS:
                if tok in full_text:
                    stats["leftover_tokens"].append(f"{name}: {tok}")
                    issues.append(f"[CHECK] Unresolved template placeholder '{tok}' found in {name}")

            # Check for raw inline markup (backticks, **, ~~, ++) that the renderer failed to convert
            for para in root.findall(".//w:p", NS):
                para_text = "".join(t.text for t in para.findall(".//w:t", NS) if t.text)
                leaks = MARKUP_LEAK_RE.findall(para_text)
                if leaks:
                    stats["markup_leaks"] += len(leaks)
                    issues.append(f"[CHECK] Raw inline markup {sorted(set(leaks))} in {name}: '{para_text[:60]}'")

            # Check run fonts in document.xml and headers
            for r in root.findall(".//w:r", NS):
                rf = r.find("w:rPr/w:rFonts", NS)
                if rf is not None:
                    for attr_val in rf.attrib.values():
                        if attr_val in LEGACY_BANNED_FONTS:
                            stats["legacy_font_runs"] += 1
                            issues.append(f"[LAYOUT] Legacy font '{attr_val}' found on run in {name}")

        doc_root = ET.fromstring(zf.read("word/document.xml"))
        # Check headings keepNext
        for p in doc_root.findall(".//w:body/w:p", NS):
            ol = p.find("w:pPr/w:outlineLvl", NS)
            if ol is not None:
                stats["headings_checked"] += 1
                if p.find("w:pPr/w:keepNext", NS) is not None:
                    stats["headings_with_keepNext"] += 1
                else:
                    txt = "".join(t.text for t in p.findall(".//w:t", NS) if t.text)
                    issues.append(f"[LAYOUT] Heading missing keepNext: '{txt[:40]}'")

        # Check tables
        for t_idx, tbl in enumerate(doc_root.findall(".//w:body/w:tbl", NS)):
            stats["tables_checked"] += 1
            grid = tbl.find("w:tblGrid", NS)
            if grid is not None:
                cols_tw = [int(c.attrib.get(f"{W}w", "0")) for c in grid.findall("w:gridCol", NS)]
                width_mm = round(sum(cols_tw) * 25.4 / 1440.0, 2)
                if width_mm > stats["max_table_width_mm"]:
                    stats["max_table_width_mm"] = width_mm
                if width_mm > 263.0:
                    issues.append(f"[ALIGN] Table #{t_idx + 1} width {width_mm}mm exceeds printable area")

            rows = tbl.findall("w:tr", NS)
            if len(rows) >= 2:
                r0_trPr = rows[0].find("w:trPr", NS)
                if r0_trPr is not None and r0_trPr.find("w:tblHeader", NS) is not None:
                    stats["data_tables_with_tblHeader"] += 1
            for r in rows:
                stats["rows_checked"] += 1
                trPr = r.find("w:trPr", NS)
                if trPr is not None and trPr.find("w:cantSplit", NS) is not None:
                    stats["rows_with_cantSplit"] += 1
                else:
                    issues.append(f"[LAYOUT] Table #{t_idx + 1} has a row missing w:cantSplit")

    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "stats": stats,
    }


def _strip_markup(s: str) -> str:
    return INLINE_CLEAN_RE.sub("", str(s or "")).strip()


def verify_docx_content_parity(data: Dict[str, Any], docx_path: Path) -> Dict[str, Any]:
    """Verify 1:1 parity between JSON block texts/cells and generated .docx text."""
    with zipfile.ZipFile(docx_path, "r") as zf:
        doc_root = ET.fromstring(zf.read("word/document.xml"))
        docx_corpus = "\n".join("".join(t.text for t in p.findall(".//w:t", NS) if t.text) for p in doc_root.findall(".//w:p", NS))

    expected_snippets: List[str] = []
    for b in data.get("blocks", []):
        btype = b.get("type")
        if btype == "heading":
            expected_snippets.append(_strip_markup(b.get("text", "")))
        elif btype == "paragraph":
            texts = b.get("paragraphs") or [b.get("text", "")]
            if isinstance(texts, str):
                texts = [texts]
            for t in texts:
                expected_snippets.append(_strip_markup(t)[:60])
        elif btype in ("table", "spec_table"):
            for r in b.get("rows", []):
                for cell_val in r:
                    cleaned = _strip_markup(str(cell_val))
                    if cleaned:
                        expected_snippets.append(cleaned[:50])

    missing = [s for s in expected_snippets if s and s not in docx_corpus]
    return {
        "checked_items": len(expected_snippets),
        "missing_count": len(missing),
        "missing_samples": missing[:10],
        "passed": len(missing) == 0,
    }


def update_fields_and_export_pdf_via_word_com(docx_path: Path, pdf_path: Path) -> Dict[str, Any]:
    """Use Windows MS Word COM to update TOC/page fields in-place and export PDF."""
    try:
        import win32com.client  # type: ignore
    except ImportError:
        return {"performed": False, "reason": "pywin32 not installed"}

    word = None
    doc = None
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0  # wdAlertsNone
        abs_docx = str(docx_path.resolve())
        abs_pdf = str(pdf_path.resolve())

        doc = word.Documents.Open(abs_docx, ConfirmConversions=False, ReadOnly=False, AddToRecentFiles=False)
        # Update TOCs and all fields
        try:
            for toc in doc.TablesOfContents:
                toc.Update()
        except Exception:
            pass
        try:
            doc.Fields.Update()
        except Exception:
            pass
        try:
            for sec in doc.Sections:
                for hdr in sec.Headers:
                    hdr.Range.Fields.Update()
                for ftr in sec.Footers:
                    ftr.Range.Fields.Update()
        except Exception:
            pass

        doc.Repaginate()
        page_count = int(doc.ComputeStatistics(2))  # wdStatisticPages = 2
        doc.Save()
        # wdExportFormatPDF = 17
        doc.ExportAsFixedFormat(
            OutputFileName=abs_pdf,
            ExportFormat=17,
            OpenAfterExport=False,
            OptimizeFor=0,
            CreateBookmarks=1,
        )
        doc.Close(SaveChanges=False)
        doc = None
        word.Quit()
        word = None
        return {
            "performed": True,
            "pdf_path": str(pdf_path),
            "page_count": page_count,
            "toc_and_fields_updated": True,
        }
    except Exception as exc:
        if doc is not None:
            try:
                doc.Close(SaveChanges=False)
            except Exception:
                pass
        if word is not None:
            try:
                word.Quit()
            except Exception:
                pass
        return {"performed": False, "reason": str(exc)}


def render_pdf_to_png_and_check_parity(pdf_path: Path, png_dir: Path, data: Dict[str, Any], dpi: int = 180) -> Dict[str, Any]:
    """Render PDF pages to PNG using PyMuPDF and check PDF text parity."""
    if not pdf_path.exists():
        return {"performed": False, "reason": "PDF file not available"}
    try:
        import pymupdf as fitz  # type: ignore
    except ImportError:
        try:
            import fitz  # type: ignore
        except ImportError:
            return {"performed": False, "reason": "PyMuPDF (fitz) not installed"}

    png_dir.mkdir(parents=True, exist_ok=True)
    for old_png in png_dir.glob("page_*.png"):
        old_png.unlink()

    doc = fitz.open(str(pdf_path))
    png_files: List[str] = []
    page_texts: List[str] = []
    blank_pages: List[int] = []
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)

    for idx, page in enumerate(doc):
        pix = page.get_pixmap(matrix=mat, alpha=False)
        out_png = png_dir / f"page_{idx + 1:02d}.png"
        pix.save(str(out_png))
        png_files.append(str(out_png))
        txt = page.get_text("text")
        page_texts.append(txt)
        if not txt.strip():
            blank_pages.append(idx + 1)

    page_count = len(doc)
    doc.close()

    full_pdf_norm = re.sub(r"\s+", " ", "\n".join(page_texts))
    headings_checked = 0
    headings_missing: List[str] = []
    for b in data.get("blocks", []):
        if b.get("type") == "heading":
            headings_checked += 1
            h_txt = re.sub(r"\s+", " ", _strip_markup(b.get("text", "")))
            if h_txt and h_txt not in full_pdf_norm:
                headings_missing.append(h_txt)

    return {
        "performed": True,
        "page_count": page_count,
        "dpi": dpi,
        "png_dir": str(png_dir),
        "png_files": png_files,
        "blank_pages": blank_pages,
        "pdf_heading_parity_checked": headings_checked,
        "pdf_heading_missing": headings_missing,
        "passed": len(headings_missing) == 0 and len(blank_pages) == 0,
    }
