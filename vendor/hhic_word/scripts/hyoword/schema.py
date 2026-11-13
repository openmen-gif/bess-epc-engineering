"""Declarative JSON schema validation, table_sums verification, and fact scanning for hyoword."""

from __future__ import annotations
from decimal import Decimal, InvalidOperation
import re
from typing import Any, Dict, List, Tuple

SUPPORTED_BLOCK_TYPES = {
    "heading",
    "paragraph",
    "clause_list",
    "bullet_list",
    "callout",
    "kv_table",
    "table",
    "spec_table",
    "redline_comparison",
    "comparison",
    "requirement_matrix",
    "open_items",
    "evidence_log",
    "abbreviations",
    "figure",
    "image",
    "page_break",
    "section_break",
}

BANNED_EXPRESSIONS = [
    "완벽히 보장",
    "완벽하게 보장",
    "원천 차단",
    "100% 보장",
    "절대 발생하지 않",
    "unconditionally guaranteed",
    "zero risk guaranteed",
    "completely eliminates all risk",
]

HANGUL_RE = re.compile(r"[가-힣]")
TBC_TAG_RE = re.compile(r"\[(?:TO BE CONFIRMED|확인\s*필요|TBD|TBC|HOLD)[^\]]*\]", re.IGNORECASE)
NUMERIC_CLAIM_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:mm|cm|m|km|kV|V|A|kA|MW|MWh|kW|kWh|Hz|%|°C|ton|t|kg|years?|months?|days?|시간|개월|년|일)\b",
    re.IGNORECASE,
)

# Global (including Korea, US, Europe, MENA, APAC/AU) BESS / EPC abbreviations dictionary for "abbreviations": "auto"
COMMON_EPC_ABBREVS = {
    "ACB": "Air Circuit Breaker",
    "AEMO": "Australian Energy Market Operator",
    "AS/NZS": "Australian / New Zealand Standard",
    "AVR": "Automatic Voltage Regulator",
    "BESS": "Battery Energy Storage System",
    "BMS": "Battery Management System",
    "BoP": "Balance of Plant",
    "CAISO": "California Independent System Operator",
    "CIGRE": "International Council on Large Electric Systems",
    "COD": "Commercial Operation Date",
    "DMAR": "Dynamic Model Acceptance Report",
    "DNP": "Defects Notification Period",
    "DSO": "Distribution System Operator",
    "EBOP": "Electrical Balance of Plant",
    "EMS": "Energy Management System",
    "EMT": "Electromagnetic Transient (PSCAD Simulation)",
    "EOT": "Extension of Time",
    "EPC": "Engineering, Procurement, and Construction",
    "ERCOT": "Electric Reliability Council of Texas",
    "ESS": "Energy Storage System",
    "FAC": "Final Acceptance Certificate",
    "FAT": "Factory Acceptance Test",
    "FIDIC": "International Federation of Consulting Engineers",
    "GFM": "Grid-Forming",
    "GIS": "Gas Insulated Switchgear",
    "GPS": "Generator Performance Standards",
    "HHIC": "Hyosung Heavy Industries Corporation",
    "HVAC": "Heating, Ventilation, and Air Conditioning",
    "IEC": "International Electrotechnical Commission",
    "IEEE": "Institute of Electrical and Electronics Engineers",
    "ISO": "International Organization for Standardization",
    "ITP": "Inspection and Test Plan",
    "KEC": "Korea Electro-technical Code (한국전기설비규정)",
    "KEPCO": "Korea Electric Power Corporation (한국전력공사)",
    "KGS": "Korea Gas Safety Corporation (한국가스안전공사)",
    "KPX": "Korea Power Exchange (전력거래소)",
    "KS": "Korean Industrial Standards (한국산업표준)",
    "LDs": "Liquidated Damages",
    "LFP": "Lithium Iron Phosphate (LiFePO4)",
    "LNTP": "Limited Notice to Proceed",
    "MV": "Medium Voltage",
    "NEC": "National Electrical Code / New Engineering Contract",
    "NEM": "National Electricity Market",
    "NER": "National Electricity Rules",
    "NFPA": "National Fire Protection Association (e.g., NFPA 855)",
    "NSP": "Network Service Provider",
    "NTP": "Notice to Proceed",
    "OEM": "Original Equipment Manufacturer",
    "PAC": "Provisional Acceptance Certificate",
    "PC": "Practical Completion",
    "PCS": "Power Conversion System",
    "PFR": "Primary Frequency Response",
    "PJM": "PJM Interconnection (US Regional Transmission Organization)",
    "PMS": "Power Management System",
    "PPC": "Power Plant Controller",
    "PSCAD": "Power Systems Computer Aided Design (EMT Software)",
    "R1": "Pre-Energization Model & Grid Registration Package (R1)",
    "R2": "Registered Data / Model Validation Testing (R2)",
    "RFI": "Request for Information",
    "RFP": "Request for Proposal",
    "RFQ": "Request for Quotation",
    "RMS": "Root Mean Square (PSS®E Dynamic Simulation)",
    "RMU": "Ring Main Unit",
    "SAT": "Site Acceptance Test",
    "SCADA": "Supervisory Control and Data Acquisition",
    "SCR": "Short Circuit Ratio",
    "SLD": "Single Line Diagram",
    "SOC": "State of Charge",
    "SOH": "State of Health",
    "SWMS": "Safe Work Method Statement",
    "TBC": "To Be Confirmed",
    "TIA": "Time Impact Analysis",
    "TOC": "Taking Over Certificate",
    "TSO": "Transmission System Operator",
    "UL": "Underwriters Laboratories (e.g., UL 9540 / UL 9540A)",
    "VCB": "Vacuum Circuit Breaker",
    "VO": "Variation Order",
}


def normalize_and_validate_spec(data: Dict[str, Any], cli_profile: str | None = None) -> Tuple[Dict[str, Any], List[str], List[str]]:
    """Validate JSON spec, populate defaults, and return (normalized_data, errors, warnings)."""
    errors: List[str] = []
    warnings: List[str] = []

    if not isinstance(data, dict):
        return data, ["Root of JSON must be an object"], warnings

    meta = data.setdefault("meta", {})
    blocks = data.get("blocks")
    if not isinstance(blocks, list) or len(blocks) == 0:
        errors.append("'blocks' must be a non-empty array of document blocks")
        blocks = []

    doc_title = str(meta.get("doc_title") or meta.get("title") or "").strip()
    if not doc_title:
        errors.append("meta.doc_title (or meta.title) is required and must be non-empty")
    else:
        meta["doc_title"] = doc_title

    # Language detection
    if not meta.get("language"):
        meta["language"] = "ko" if HANGUL_RE.search(doc_title) else "en"

    # Profile resolution
    if cli_profile:
        meta["profile"] = cli_profile
    elif not meta.get("profile"):
        meta["profile"] = "modern" if meta["language"] == "ko" else "epc-en"

    # Defaults for optional meta fields
    meta.setdefault("project_name", "BESS EPC Project" if meta["language"] == "en" else "BESS EPC 프로젝트")
    meta.setdefault("doc_number", "HHIC-DOC-001")
    meta.setdefault("revision", "0")
    meta.setdefault("issue_date", "2026-10-16")
    meta.setdefault("include_cover", True)
    meta.setdefault("include_toc", bool(meta["include_cover"]))

    # Validate each block
    all_texts: List[str] = [doc_title, str(meta.get("project_name", ""))]
    prev_h_level = 0
    for idx, b in enumerate(blocks):
        if not isinstance(b, dict):
            errors.append(f"blocks[{idx}] must be an object")
            continue
        btype = str(b.get("type") or "").strip().lower()
        if btype not in SUPPORTED_BLOCK_TYPES:
            errors.append(f"blocks[{idx}]: unknown type '{btype}'. Supported: {sorted(SUPPORTED_BLOCK_TYPES)}")
            continue

        if btype == "heading":
            txt = str(b.get("text") or "").strip()
            if not txt:
                errors.append(f"blocks[{idx}] (heading): 'text' is required")
            lvl = int(b.get("level", 1))
            if lvl < 1 or lvl > 4:
                errors.append(f"blocks[{idx}] (heading): 'level' must be between 1 and 4 (got {lvl})")
            if prev_h_level > 0 and lvl > prev_h_level + 1:
                warnings.append(f"blocks[{idx}] (heading '{txt}'): heading level jumps from H{prev_h_level} to H{lvl}")
            prev_h_level = lvl
            all_texts.append(txt)

        elif btype == "paragraph":
            txt = b.get("text") or b.get("paragraphs")
            if not txt:
                errors.append(f"blocks[{idx}] (paragraph): 'text' or 'paragraphs' is required")
            else:
                all_texts.append(str(txt))

        elif btype in ("table", "spec_table"):
            cols = b.get("columns")
            rows = b.get("rows")
            if not isinstance(cols, list) or len(cols) < 2:
                errors.append(f"blocks[{idx}] ({btype}): 'columns' must have at least 2 columns")
            if not isinstance(rows, list) or len(rows) < 1:
                errors.append(f"blocks[{idx}] ({btype}): 'rows' must have at least 1 row")
            elif isinstance(cols, list):
                for r_i, r in enumerate(rows):
                    if not isinstance(r, list) or len(r) != len(cols):
                        errors.append(
                            f"blocks[{idx}] ({btype}) row {r_i}: column count mismatch (expected {len(cols)}, got {len(r) if isinstance(r, list) else 'non-list'})"
                        )
            all_texts.append(str(cols))
            all_texts.append(str(rows))

        elif btype in ("figure", "image"):
            if not b.get("path"):
                errors.append(f"blocks[{idx}] ({btype}): 'path' is required")

        else:
            all_texts.append(str(b))

    joined_corpus = "\n".join(all_texts)

    # Auto-populate abbreviations if set to "auto"
    if meta.get("abbreviations") == "auto":
        found_abbrevs = []
        for term, desc in sorted(COMMON_EPC_ABBREVS.items()):
            if re.search(rf"\b{re.escape(term)}\b", joined_corpus):
                found_abbrevs.append({"term": term, "description": desc})
        meta["abbreviations"] = found_abbrevs

    # Check banned overconfident expressions
    for phrase in BANNED_EXPRESSIONS:
        if phrase.lower() in joined_corpus.lower():
            errors.append(f"Banned overconfident expression detected: '{phrase}' (violates SKILL fact discipline)")

    # Validate meta.table_sums if specified
    for sum_spec in meta.get("table_sums") or []:
        tol = Decimal(str(sum_spec.get("tolerance", "0.01")))
        if "caption" in sum_spec and "column" in sum_spec:
            cap_sub = str(sum_spec["caption"]).strip().lower()
            col_idx = int(sum_spec["column"])
            expected_val = Decimal(str(sum_spec["expected"]))
            matched_tbl = None
            for b in blocks:
                if b.get("type") in ("table", "spec_table") and cap_sub in str(b.get("caption", "")).lower():
                    matched_tbl = b
                    break
            if matched_tbl is None:
                errors.append(f"meta.table_sums: no table found matching caption '{sum_spec['caption']}'")
                continue
            rows = matched_tbl.get("rows") or []
            calc_sum = Decimal("0")
            for r_i, r in enumerate(rows):
                first_cell = re.sub(r"[\*`~+]", "", str(r[0] if r else "")).strip().upper()
                raw_cell = re.sub(r"[\*`~+,]", "", str(r[col_idx] if col_idx < len(r) else "0")).strip()
                if first_cell.startswith(("TOTAL", "합계", "총계", "소계")):
                    try:
                        tot_cell_val = Decimal(raw_cell)
                        if abs(tot_cell_val - expected_val) > tol:
                            errors.append(
                                f"meta.table_sums failed on '{sum_spec['caption']}' TOTAL row: {tot_cell_val} != expected {expected_val}"
                            )
                    except InvalidOperation:
                        pass
                else:
                    try:
                        calc_sum += Decimal(raw_cell)
                    except InvalidOperation as exc:
                        errors.append(f"meta.table_sums invalid number '{raw_cell}' in '{sum_spec['caption']}' row {r_i}: {exc}")
            if abs(calc_sum - expected_val) > tol:
                errors.append(
                    f"meta.table_sums failed on '{sum_spec['caption']}': column {col_idx} sum({calc_sum}) != expected({expected_val}) within tolerance {tol}"
                )
        else:
            b_idx = sum_spec.get("block_index")
            target = sum_spec.get("target")
            operands = sum_spec.get("operands") or []
            if b_idx is None or b_idx < 0 or b_idx >= len(blocks):
                errors.append(f"meta.table_sums: invalid block_index {b_idx}")
                continue
            tbl_block = blocks[b_idx]
            rows = tbl_block.get("rows") or []
            try:
                t_r, t_c = target
                clean_target = re.sub(r"[\*`~+,]", "", str(rows[t_r][t_c])).strip()
                target_val = Decimal(clean_target)
                calc_sum = Decimal("0")
                for op_r, op_c in operands:
                    clean_op = re.sub(r"[\*`~+,]", "", str(rows[op_r][op_c])).strip()
                    calc_sum += Decimal(clean_op)
                if abs(target_val - calc_sum) > tol:
                    errors.append(
                        f"meta.table_sums failed on blocks[{b_idx}]: target cell [{t_r},{t_c}]={target_val} != sum({calc_sum}) within tolerance {tol}"
                    )
            except (IndexError, InvalidOperation, TypeError, ValueError) as exc:
                errors.append(f"meta.table_sums error on blocks[{b_idx}]: {exc}")

    return data, errors, warnings


def extract_fact_and_tbc_summary(data: Dict[str, Any]) -> Dict[str, Any]:
    """Scan all blocks for [TO BE CONFIRMED]/[확인 필요] tags and numeric engineering values."""
    corpus = str(data.get("blocks", []))
    tbc_tags = sorted(set(TBC_TAG_RE.findall(corpus)))
    numeric_claims = sorted(set(m.strip() for m in NUMERIC_CLAIM_RE.findall(corpus)))
    return {
        "unresolved_tbc_count": len(tbc_tags),
        "unresolved_tbc_tags": tbc_tags,
        "numeric_claims_count": len(numeric_claims),
        "numeric_claims_sample": numeric_claims[:40],
    }
