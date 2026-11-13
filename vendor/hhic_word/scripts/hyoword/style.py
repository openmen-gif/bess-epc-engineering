"""Writing-style lint for doc JSON: flags patterns that make documents read as AI-generated.

Findings are warnings only (they never fail a build); see references/writing_style.md for the rules.
"""

from __future__ import annotations
import re
from typing import Any, Dict, List

EM_DASH = "—"
MIDDLE_DOT = "·"

# Words that describe the AI workflow rather than the engineering content
AI_TRACE_KO_RE = re.compile(r"세션|사용자\s*\(|스킬|에이전트|프롬프트|SOURCE_REVIEW")
AI_TRACE_EN_RE = re.compile(r"\b(?:sessions?|prompts?|skills?|LLM|chatbot|AI agent)\b", re.IGNORECASE)
# Evidence grades belong in the evidence_log grade column, not in running text or source lines
EVIDENCE_GRADE_RE = re.compile(r"\(E[1-4](?:\s*/\s*E[1-4])*\)")
# Korean term followed by a multi-word English echo, e.g. "핵심 요약 (Executive Summary)"
BILINGUAL_ECHO_RE = re.compile(r"[가-힣]+\s*\([A-Z][A-Za-z]+(?:[ &/-]+[A-Za-z]+)+\)")
BOLD_LABEL_RE = re.compile(r"^\s*\*\*[^*]{1,40}\*\*\s*:")
KO_PLAIN_END_RE = re.compile(r"다\.(?:\s|$)")
KO_BULLET_END_RE = re.compile(r"(?:함|임|됨|음)\.(?:\s|$)")

OVERUSED_KO = ["정밀", "명확히", "다각도", "체계적", "효과적으로", "3대 핵심", "핵심적"]
OVERUSED_EN = ["robust", "comprehensive", "seamless", "leverage", "delve", "it is important to note", "establishes", "strictly"]

MAX_HEADING_CHARS_KO = 25
MAX_HEADING_WORDS_EN = 10


def _walk_strings(node: Any, out: List[str]):
    if isinstance(node, str):
        out.append(node)
    elif isinstance(node, dict):
        for v in node.values():
            _walk_strings(v, out)
    elif isinstance(node, list):
        for v in node:
            _walk_strings(v, out)


def _sample(items: List[str], n: int = 3) -> List[str]:
    return [s if len(s) <= 50 else s[:47] + "..." for s in items[:n]]


def check_writing_style(data: Dict[str, Any]) -> Dict[str, Any]:
    """Return {'warning_count', 'warnings', 'counts'} for the validated doc spec."""
    meta = data.get("meta") or {}
    blocks = data.get("blocks") or []
    is_ko = meta.get("language") == "ko"

    all_strings: List[str] = []
    _walk_strings(meta, all_strings)
    _walk_strings(blocks, all_strings)
    corpus = "\n".join(all_strings)

    headings = [str(b.get("text") or "") for b in blocks if b.get("type") == "heading"]
    labels = headings + [str(b.get(k) or "") for b in blocks for k in ("title", "caption")] + [str(meta.get("doc_title") or "")]
    prose: List[str] = []
    bullets: List[str] = []
    for b in blocks:
        btype = b.get("type")
        if btype == "paragraph":
            _walk_strings(b.get("paragraphs") or b.get("text"), prose)
        elif btype == "callout":
            _walk_strings(b.get("body") or b.get("text"), prose)
            _walk_strings(b.get("bullets") or b.get("items"), bullets)
        elif btype == "clause_list":
            _walk_strings(b.get("items"), bullets)
    prose_text = "\n".join(prose + bullets)

    warnings: List[str] = []
    counts: Dict[str, Any] = {}

    counts["em_dash"] = corpus.count(EM_DASH)
    if counts["em_dash"]:
        warnings.append(f"{counts['em_dash']} em dash(es) '—'. Use a comma, colon or a new sentence.")

    counts["middle_dot"] = corpus.count(MIDDLE_DOT)
    if counts["middle_dot"]:
        warnings.append(f"{counts['middle_dot']} middle dot(s) '·'. Use '및', '/', or a comma.")

    trace_re = AI_TRACE_KO_RE if is_ko else AI_TRACE_EN_RE
    traces = [s for s in all_strings if trace_re.search(s)]
    if is_ko:
        traces += [s for s in all_strings if AI_TRACE_EN_RE.search(s) and s not in traces]
    counts["ai_trace"] = len(traces)
    if traces:
        warnings.append(f"{len(traces)} string(s) mention the AI workflow (session, user, skill, prompt): {_sample(traces)}")

    grade_hits = [s for s in all_strings if EVIDENCE_GRADE_RE.search(s)]
    counts["evidence_grade_in_text"] = len(grade_hits)
    if grade_hits:
        warnings.append(f"{len(grade_hits)} string(s) show evidence grades like '(E1/E2)'. Cite the document name and revision instead: {_sample(grade_hits)}")

    counts["backticks"] = corpus.count("`") // 2
    if counts["backticks"]:
        warnings.append(f"{counts['backticks']} `code` span(s). They render as plain text; drop the backticks around values and standards.")

    signed = [
        role for role, info in (meta.get("approvals") or {}).items()
        if isinstance(info, dict) and "signed" in str(info.get("signature", "")).lower()
    ]
    counts["signature_prefilled"] = len(signed)
    if signed:
        warnings.append(f"Approval signature pre-filled as 'Signed' for {signed}. Leave it blank until the person signs.")

    bold_labels = sum(1 for s in bullets if BOLD_LABEL_RE.match(s))
    counts["bold_label_bullets"] = f"{bold_labels}/{len(bullets)}"
    if len(bullets) >= 3 and bold_labels / len(bullets) >= 0.6:
        warnings.append(f"{bold_labels} of {len(bullets)} bullets start with '**Label**:'. Write most bullets as plain sentences.")

    vocab = OVERUSED_KO if is_ko else OVERUSED_EN
    found_vocab = sorted({w for w in vocab if w.lower() in corpus.lower()})
    if is_ko and corpus.count("핵심") > 4:
        found_vocab.append(f"핵심 x{corpus.count('핵심')}")
    counts["overused_words"] = found_vocab
    if found_vocab:
        warnings.append(f"Overused AI-style wording: {found_vocab}")

    if is_ko:
        echoes = [m.group(0) for s in labels for m in BILINGUAL_ECHO_RE.finditer(s)]
        counts["bilingual_echo_in_labels"] = len(echoes)
        if echoes:
            warnings.append(f"{len(echoes)} Korean label(s) repeat the English in brackets: {_sample(echoes)}")

        plain_end = len(KO_PLAIN_END_RE.findall(prose_text))
        bullet_end = len(KO_BULLET_END_RE.findall(prose_text))
        counts["ko_endings"] = {"~다.": plain_end, "~함/임/됨.": bullet_end}
        if plain_end and bullet_end:
            warnings.append(f"Mixed Korean sentence endings (~다. x{plain_end}, ~함/~임/~됨. x{bullet_end}). Use one register per document.")

        long_heads = [h for h in headings if len(h) > MAX_HEADING_CHARS_KO]
    else:
        long_heads = [h for h in headings if len(h.split()) > MAX_HEADING_WORDS_EN]
    counts["long_headings"] = len(long_heads)
    if long_heads:
        warnings.append(f"{len(long_heads)} heading(s) are long; keep them short and plain: {_sample(long_heads)}")

    return {"warning_count": len(warnings), "warnings": warnings, "counts": counts}
