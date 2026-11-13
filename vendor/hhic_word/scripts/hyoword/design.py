"""Editorial Design System v2.0 for Hyosung Word Engine (hyoword).

Purges legacy fonts (Batang, Gulim, Times New Roman, MS PGothic) and applies a
clean Light-Dominant & Soft-Tint corporate palette harmonized with 14_PPT-Auto-Skill.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict

# A4 Page Geometry (in mm and twips; 1 mm = 56.6929 twips)
PAGE_A4_PORTRAIT_MM = (210.0, 297.0)
PAGE_A4_LANDSCAPE_MM = (297.0, 210.0)
MARGINS_DEFAULT_MM = {
    "top": 20.0,
    "bottom": 20.0,
    "left": 20.0,
    "right": 15.0,
    "header": 12.0,
    "footer": 10.0,
}
CONTENT_WIDTH_PORTRAIT_MM = 175.0   # 210 - 20 - 15
CONTENT_WIDTH_LANDSCAPE_MM = 262.0  # 297 - 20 - 15


def mm_to_twips(mm_val: float) -> int:
    return int(round(mm_val * 1440.0 / 25.4))


def pt_to_half_pt(pt_val: float) -> int:
    return int(round(pt_val * 2.0))


def pt_to_twips(pt_val: float) -> int:
    return int(round(pt_val * 20.0))


# Core Color Palette (6-hex uppercase without '#')
COLORS: Dict[str, str] = {
    "deep_purple": "2E008B",      # Primary brand accent, H1, solid table headers
    "main_purple": "6428E6",      # Secondary brand accent, H2, TBC badges, links
    "mid_purple": "875FF0",       # Subtle accent lines
    "soft_lavender": "EBE6FF",    # Light purple tint for pills, TBC fill, light headers
    "soft_canvas": "F6F5FC",      # Key column shading, summary callout background
    "zebra_row": "FAFAFD",        # Ultra-light alternating row fill
    "amber_gold": "FFBE19",       # Key Takeaway left bar, highlight accent
    "charcoal": "262633",         # Primary body ink & H3
    "dark_ink": "1A1A26",         # Cover title ink
    "slate_muted": "66667E",      # Captions, headers/footers secondary text, sources
    "border_light": "D8D8E8",     # Subtle hairline table/grid border
    "border_card": "EAEAF6",      # Card/callout outer border
    "white": "FFFFFF",
    # Semantic colors
    "pass_bg": "E8F5E9",
    "pass_fg": "1B5E20",
    "warn_bg": "FFF8E1",
    "warn_fg": "B26A00",
    "fail_bg": "FFEBEE",
    "fail_fg": "B71C1C",
    "hold_bg": "EBE6FF",
    "hold_fg": "6428E6",
    "info_bg": "F4F9FC",
    "info_fg": "156082",
}


@dataclass(frozen=True)
class FontProfile:
    name: str
    latin: str
    east_asia: str
    complex_script: str
    mono: str
    description: str


PROFILES: Dict[str, FontProfile] = {
    "epc-en": FontProfile(
        name="epc-en",
        latin="Arial",
        east_asia="맑은 고딕",
        complex_script="Arial",
        mono="Consolas",
        description="Global EPC & corporate English technical, contract & claim documents (Arial + Malgun Gothic fallback)",
    ),
    "global-en": FontProfile(
        name="global-en",
        latin="Arial",
        east_asia="맑은 고딕",
        complex_script="Arial",
        mono="Consolas",
        description="Global EPC & corporate English technical, contract & claim documents (Arial + Malgun Gothic fallback)",
    ),
    "modern": FontProfile(
        name="modern",
        latin="Pretendard",
        east_asia="Pretendard",
        complex_script="Arial",
        mono="Consolas",
        description="Korean & global bilingual corporate reports, domestic EPC specs & technical reviews (Pretendard)",
    ),
    "kr-modern": FontProfile(
        name="kr-modern",
        latin="Pretendard",
        east_asia="Pretendard",
        complex_script="Arial",
        mono="Consolas",
        description="Korean domestic & HQ corporate technical/contractual documents (Pretendard)",
    ),
    "safe": FontProfile(
        name="safe",
        latin="Arial",
        east_asia="맑은 고딕",
        complex_script="Arial",
        mono="Courier New",
        description="Universal cross-PC distribution profile across all global environments (Arial + Malgun Gothic)",
    ),
}


CALLOUT_THEMES: Dict[str, Dict[str, str]] = {
    "executive_summary": {
        "border_left": COLORS["deep_purple"],
        "bg": COLORS["soft_canvas"],
        "title_color": COLORS["deep_purple"],
        "default_label_en": "EXECUTIVE SUMMARY",
        "default_label_ko": "핵심 요약",
    },
    "key_takeaway": {
        "border_left": COLORS["amber_gold"],
        "bg": "FFFDF7",
        "title_color": "996500",
        "default_label_en": "KEY TAKEAWAY & RECOMMENDATION",
        "default_label_ko": "핵심 시사점 및 권고사항",
    },
    "risk_warning": {
        "border_left": "D32F2F",
        "bg": "FFF5F5",
        "title_color": COLORS["fail_fg"],
        "default_label_en": "CONTRACTUAL / TECHNICAL CAUTION",
        "default_label_ko": "주의 및 리스크 경계 사항",
    },
    "contract_hold": {
        "border_left": COLORS["main_purple"],
        "bg": COLORS["soft_lavender"],
        "title_color": COLORS["main_purple"],
        "default_label_en": "HOLD / TO BE CONFIRMED",
        "default_label_ko": "확인 필요 항목",
    },
    "draft_response": {
        "border_left": "156082",
        "bg": COLORS["info_bg"],
        "title_color": COLORS["info_fg"],
        "default_label_en": "PROPOSED RESPONSE / POSITION WORDING",
        "default_label_ko": "검토 의견 및 회신 문안 초안",
    },
}


# Status keywords mapped to (background_hex, text_hex)
STATUS_RULES = [
    (
        ("NON-COMPLIANT", "FAIL", "FAILED", "REJECTED", "CRITICAL", "HIGH RISK", "HIGH", "OPEN ISSUE", "불충족", "부적합", "불가", "고위험"),
        (COLORS["fail_bg"], COLORS["fail_fg"]),
    ),
    (
        ("COMPLIANT", "PASS", "PASSED", "ACCEPTED", "CLOSED", "VERIFIED", "OK", "충족", "적합", "완료", "승인"),
        (COLORS["pass_bg"], COLORS["pass_fg"]),
    ),
    (
        ("DEVIATION", "CLARIFICATION", "CLARIFY", "PARTIAL", "WARN", "WARNING", "MEDIUM RISK", "MEDIUM", "CONDITIONAL", "조건부", "보완필요", "일부충족", "주의"),
        (COLORS["warn_bg"], COLORS["warn_fg"]),
    ),
    (
        ("TBC", "TBD", "HOLD", "PENDING", "OPEN", "UNDER REVIEW", "TO BE CONFIRMED", "확인필요", "확인 필요", "미확인", "보류"),
        (COLORS["hold_bg"], COLORS["hold_fg"]),
    ),
]


def classify_status_cell(text: str) -> tuple[str, str] | None:
    """Return (bg_hex, fg_hex) if cell text matches a known compliance/risk status token."""
    cleaned = (text or "").strip().upper()
    if not cleaned or len(cleaned) > 42:
        return None
    token = cleaned.strip("[]()")
    for keywords, (bg, fg) in STATUS_RULES:
        for kw in keywords:
            if token == kw or token.startswith(kw + " ") or token.startswith(kw + ":") or token.startswith(kw + "/") or token.endswith(" " + kw):
                return (bg, fg)
    return None
