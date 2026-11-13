#!/usr/bin/env python3
"""Main CLI Builder for Hyosung MS Word Generation Engine (15_Word-Auto-Skill v2.0).

Usage:
    python skill/scripts/build_doc.py docs_json/my_doc.json --strict --render-pdf --render-png
"""

from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
import tempfile
import zipfile
import docx

# Ensure local package import works regardless of working directory
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
PROJECT_ROOT = SKILL_ROOT.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from hyoword import __version__
from hyoword.blocks import BlockRenderer
from hyoword.cover_header import (
    build_compact_memo_header,
    build_formal_cover_and_frontmatter,
    clear_document_body,
    enable_update_fields_on_open,
    extract_template_assets,
    upgrade_running_header_and_footer,
)
from hyoword.design import PROFILES
from hyoword.qa import (
    inspect_docx_xml_hygiene,
    render_pdf_to_png_and_check_parity,
    sha256_file,
    update_fields_and_export_pdf_via_word_com,
    verify_docx_content_parity,
    verify_template_pin,
)
from hyoword.schema import extract_fact_and_tbc_summary, normalize_and_validate_spec
from hyoword.style import check_writing_style
from hyoword.xml_helpers import scrub_core_properties, upgrade_document_styles


def resolve_template_paths() -> tuple[Path, Path]:
    candidates = [
        SKILL_ROOT / "templates" / "Word Template_Empty_No Project Data.docx",
        PROJECT_ROOT / "templates" / "Word Template_Empty_No Project Data.docx",
    ]
    for c in candidates:
        if c.exists():
            return c, c.parent / "template_pin.json"
    raise FileNotFoundError("Could not find 'Word Template_Empty_No Project Data.docx' in skill/templates or templates/")


def resolve_output_path(json_path: Path, meta: dict, cli_out: str | None) -> Path:
    if cli_out:
        return Path(cli_out).resolve()
    if meta.get("output"):
        out_str = str(meta["output"]).replace("{profile}", meta.get("profile", "epc-en"))
        out_p = Path(out_str)
        if not out_p.is_absolute():
            out_p = PROJECT_ROOT / out_p
        return out_p.resolve()

    # Check Claude.ai sandbox output directory
    sandbox_out = Path("/mnt/user-data/outputs")
    if sandbox_out.exists() and sandbox_out.is_dir():
        return (sandbox_out / f"{json_path.stem}.docx").resolve()

    out_dir = PROJECT_ROOT / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    return (out_dir / f"{json_path.stem}.docx").resolve()


def package_claude_skill() -> int:
    """Create a self-contained Claude.ai web skill zip package in output/."""
    out_dir = PROJECT_ROOT / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / "hhic-word-generator-skill.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(SKILL_ROOT.rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and not p.name.endswith(".pyc"):
                rel = p.relative_to(SKILL_ROOT)
                zf.write(p, Path("hhic-word-generator") / rel)
    print(f"[OK] packaged Claude skill -> {zip_path} (sha256={sha256_file(zip_path)[:16]})")
    return 0


def build_document(
    json_path: Path,
    cli_profile: str | None = None,
    cli_out: str | None = None,
    strict: bool = False,
    check_only: bool = False,
    render_pdf: bool = False,
    render_png: bool = False,
) -> int:
    if not json_path.exists():
        print(f"[ERROR] Input JSON file not found: {json_path}", file=sys.stderr)
        return 2

    try:
        raw_data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[ERROR] Failed to parse JSON {json_path}: {exc}", file=sys.stderr)
        return 2

    # 1. Verify Template Hash Gate
    tpl_path, pin_path = resolve_template_paths()
    try:
        tpl_info = verify_template_pin(tpl_path, pin_path)
        print(f"[TEMPLATE] verified {tpl_info['template_file']} (sha256={tpl_info['sha256'][:12]}...)")
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    # 2. Validate Schema & Fact Rules
    data, errors, warnings = normalize_and_validate_spec(raw_data, cli_profile=cli_profile)
    for w in warnings:
        print(f"[WARN] {w}")
    if errors:
        for err in errors:
            print(f"[CHECK] {err}", file=sys.stderr)
        return 2

    meta = data["meta"]
    blocks = data["blocks"]
    profile_key = meta["profile"]
    if profile_key not in PROFILES:
        print(f"[ERROR] Unknown profile '{profile_key}'. Available: {list(PROFILES.keys())}", file=sys.stderr)
        return 2
    profile = PROFILES[profile_key]
    fact_summary = extract_fact_and_tbc_summary(data)
    style_summary = check_writing_style(data)

    print(
        f"[INFO] profile={profile.name} ({profile.latin}/{profile.east_asia}) | "
        f"language={meta['language']} | include_cover={meta.get('include_cover', True)} | blocks={len(blocks)}"
    )
    print(
        f"[FACT] numeric_claims={fact_summary['numeric_claims_count']} | "
        f"tbc_tags={fact_summary['unresolved_tbc_count']} {fact_summary['unresolved_tbc_tags'][:5]}"
    )

    for w in style_summary["warnings"]:
        print(f"[STYLE] {w}")

    if check_only:
        print("[OK] --check-only passed: schema, table_sums, and fact rules clean.")
        return 0

    out_docx = resolve_output_path(json_path, meta, cli_out)
    out_docx.parent.mkdir(parents=True, exist_ok=True)
    out_pdf = out_docx.with_suffix(".pdf")
    out_png_dir = out_docx.parent / f"{out_docx.stem}_png"
    out_receipt = out_docx.with_suffix(".validation.json")

    # 3. Build into temporary file for atomic replacement
    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        tmp_docx = tmp_dir / out_docx.name
        tmp_pdf = tmp_dir / out_pdf.name

        doc = docx.Document(str(tpl_path))
        upgrade_document_styles(doc, profile)
        upgrade_running_header_and_footer(doc, meta, profile)
        enable_update_fields_on_open(doc)
        scrub_core_properties(
            doc,
            author=meta.get("author", ""),
            title=meta.get("doc_title", ""),
            subject=meta.get("project_name", ""),
        )

        assets = extract_template_assets(doc)
        clear_document_body(doc)

        if meta.get("include_cover", True):
            build_formal_cover_and_frontmatter(doc, meta, blocks, assets, profile)
        else:
            build_compact_memo_header(doc, meta, assets, profile)

        if not meta.get("frontmatter_only", False):
            renderer = BlockRenderer(doc, meta, profile, base_dir=json_path.parent)
            renderer.render_all(blocks)

        doc.save(str(tmp_docx))

        # 4. XML Hygiene & Structural Parity Gates
        hygiene = inspect_docx_xml_hygiene(tmp_docx)
        parity = (
            {"passed": True, "checked_count": 0, "missing_count": 0, "missing_samples": []}
            if meta.get("frontmatter_only", False)
            else verify_docx_content_parity(data, tmp_docx)
        )

        for issue in hygiene["issues"]:
            print(issue, file=sys.stderr if strict else sys.stdout)
        if not parity["passed"]:
            print(f"[CHECK] DOCX content parity missing {parity['missing_count']} items: {parity['missing_samples']}", file=sys.stderr)

        if strict and (not hygiene["passed"] or not parity["passed"]):
            print("[FAIL] Build aborted under --strict due to hygiene/parity errors.", file=sys.stderr)
            return 1

        # 5. Optional Word COM Field Update & PDF / PNG Visual QA
        com_result = {"performed": False, "reason": "not requested"}
        png_result = {"performed": False, "reason": "not requested"}

        if render_pdf or render_png:
            com_result = update_fields_and_export_pdf_via_word_com(tmp_docx, tmp_pdf)
            if com_result.get("performed"):
                print(f"[RENDER] Word COM updated TOC/fields and exported PDF ({com_result.get('page_count')} pages)")
                for idx in range(0, 20):
                    cand_pdf = out_pdf if idx == 0 else out_pdf.with_stem(
                        f"{out_pdf.stem}_updated" if idx == 1 else f"{out_pdf.stem}_updated_{idx}"
                    )
                    try:
                        shutil.copy2(tmp_pdf, cand_pdf)
                        if idx > 0:
                            out_pdf = cand_pdf
                            print(f"[WARN] Target PDF was open/locked; saved updated PDF to {out_pdf}")
                        break
                    except PermissionError:
                        continue
                if render_png:
                    png_result = render_pdf_to_png_and_check_parity(out_pdf, out_png_dir, data)
                    if png_result.get("performed"):
                        print(f"[RENDER] Rendered {png_result.get('page_count')} PNG pages -> {out_png_dir}")
            else:
                print(f"[WARN] Word COM PDF export skipped/failed: {com_result.get('reason')}")

        # Promote candidate .docx to final path (with fallback if file is currently open in MS Word)
        for idx in range(0, 20):
            cand_docx = out_docx if idx == 0 else out_docx.with_stem(
                f"{out_docx.stem}_updated" if idx == 1 else f"{out_docx.stem}_updated_{idx}"
            )
            try:
                shutil.copy2(tmp_docx, cand_docx)
                if idx > 0:
                    out_docx = cand_docx
                    print(f"[WARN] Target DOCX was open in Word; saved updated DOCX to {out_docx}")
                break
            except PermissionError:
                continue

    # 6. Write Validation Receipt (.validation.json)
    receipt = {
        "engine": "hyoword",
        "engine_version": __version__,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "input_json": str(json_path.resolve()),
        "output_docx": str(out_docx),
        "output_docx_sha256": sha256_file(out_docx),
        "output_pdf": str(out_pdf) if out_pdf.exists() else None,
        "profile": profile.name,
        "language": meta["language"],
        "include_cover": bool(meta.get("include_cover", True)),
        "template_verification": tpl_info,
        "xml_hygiene": hygiene,
        "docx_parity": parity,
        "fact_and_tbc_summary": fact_summary,
        "style_summary": style_summary,
        "word_com_pdf": com_result,
        "png_visual_qa": png_result,
        "overall_status": "clean" if (hygiene["passed"] and parity["passed"]) else "warnings",
    }
    out_receipt.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] saved {out_docx}")
    if out_pdf.exists() and (render_pdf or render_png):
        print(f"[OK] saved {out_pdf}")
    print(f"[OK] receipt {out_receipt} (checks: {receipt['overall_status']})")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Hyosung MS Word Generation Engine (hyoword v2.0)")
    parser.add_argument("json_path", nargs="?", help="Path to declarative document JSON file")
    parser.add_argument("--profile", choices=list(PROFILES.keys()), help="Override font/design profile")
    parser.add_argument("--out", help="Override output .docx file path")
    parser.add_argument("--strict", action="store_true", help="Fail on any hygiene, alignment, or parity issue")
    parser.add_argument("--check-only", action="store_true", help="Validate JSON schema and fact rules without building")
    parser.add_argument("--render-pdf", action="store_true", help="Update TOC/fields and export PDF via MS Word COM")
    parser.add_argument("--render-png", action="store_true", help="Export PDF and render page PNGs for visual QA")
    parser.add_argument("--verify-package", action="store_true", help="Verify MANIFEST.json integrity of skill package")
    parser.add_argument("--package-claude", action="store_true", help="Package skill into a zip for Claude.ai web")

    args = parser.parse_args()
    if args.verify_package:
        from hyoword.sandbox import verify_package_manifest
        info = verify_package_manifest(SKILL_ROOT)
        print(f"[OK] all {info['file_count']} files match MANIFEST.json ({info['name']} v{info['version']})")
        return 0
    if args.package_claude:
        return package_claude_skill()
    if not args.json_path:
        parser.error("json_path is required unless --verify-package or --package-claude is specified")

    return build_document(
        json_path=Path(args.json_path),
        cli_profile=args.profile,
        cli_out=args.out,
        strict=args.strict,
        check_only=args.check_only,
        render_pdf=args.render_pdf,
        render_png=args.render_png,
    )


if __name__ == "__main__":
    sys.exit(main())
