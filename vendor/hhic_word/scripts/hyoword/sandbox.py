"""Isolated CLI execution and package verification for uploaded Hyosung Word skill packages.

No network requests or MS Word COM automation are required in Linux sandboxes (ChatGPT / Claude web).
"""

from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from .qa import sha256_file


def verify_package_manifest(package_root: str | Path) -> dict:
    """Verify MANIFEST.json hashes inside an extracted or local skill package."""
    root = Path(package_root).resolve(strict=True)
    manifest_path = root / "MANIFEST.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"MANIFEST.json not found in {root}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_files: dict[str, str] = manifest.get("files", {})
    if not expected_files:
        raise ValueError("MANIFEST.json contains no file digests")

    mismatches: list[str] = []
    for rel_path, expected_hash in expected_files.items():
        fp = (root / rel_path).resolve()
        if not fp.is_relative_to(root) or not fp.is_file():
            mismatches.append(f"missing: {rel_path}")
            continue
        actual_hash = sha256_file(fp)
        if actual_hash != expected_hash:
            mismatches.append(f"mismatch: {rel_path} (expected {expected_hash[:12]}, got {actual_hash[:12]})")

    if mismatches:
        raise RuntimeError("Package integrity verification failed:\n  " + "\n  ".join(mismatches))

    return {
        "name": manifest.get("name"),
        "version": manifest.get("version"),
        "file_count": len(expected_files),
        "status": "verified",
    }


def build_uploaded_doc(
    package_root: str | Path,
    work_dir: str | Path,
    doc_spec: dict,
    output_docx: str | Path,
    timeout: int = 180,
) -> Path:
    """Verify skill package, write declarative doc JSON, run build_doc.py --strict, and publish DOCX + receipt."""
    package = Path(package_root).resolve(strict=True)
    work = Path(work_dir).resolve(strict=True)
    out = Path(output_docx).resolve()

    if out.suffix.lower() != ".docx" or out.is_relative_to(package) or work.is_relative_to(package):
        raise ValueError("work_dir and output_docx (.docx) must be outside the immutable package_root")

    if not isinstance(doc_spec, dict) or not isinstance(doc_spec.get("blocks"), list):
        raise ValueError("doc_spec must be a dict containing a 'blocks' list")

    verify_package_manifest(package)

    cli = package / "scripts" / "build_doc.py"
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")

    def _run(args: list[str]) -> subprocess.CompletedProcess:
        res = subprocess.run(
            [sys.executable, str(cli), *args],
            cwd=work,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
            shell=False,
        )
        print(res.stdout, end="")
        if res.returncode != 0:
            raise RuntimeError(f"build_doc.py exited with {res.returncode}:\n{res.stderr}\n{res.stdout}")
        return res

    doc_json_path = work / "doc_spec.json"
    doc_json_path.write_text(json.dumps(doc_spec, ensure_ascii=False, indent=2), encoding="utf-8")
    out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="hyoword-build-", dir=out.parent) as tmp:
        candidate = Path(tmp) / "result.docx"
        res = _run([str(doc_json_path), "--out", str(candidate), "--strict"])
        if "checks: clean" not in res.stdout or not candidate.is_file():
            raise RuntimeError("build_doc.py did not confirm a clean DOCX build")

        receipt_path = candidate.with_suffix(".validation.json")
        if receipt_path.is_file():
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["output_docx"] = str(out)
            receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
            shutil.copy2(receipt_path, out.with_suffix(".validation.json"))

        shutil.copy2(candidate, out)

    return out
