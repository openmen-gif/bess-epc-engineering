"""
Dual-mode report generator.

- API mode (IS_API_MODE=True):  delegates to FastAPI backend, falls back to local
- Standalone mode:              generates reports in-process via _report_local
"""
import os
import datetime
from utils.config import IS_API_MODE, API_BASE_URL


# ── API-mode: download from backend ──────────────────────────────────────────

def _download_report(report_type: str) -> str:
    """Request report from FastAPI backend and save locally."""
    import requests
    url = f"{API_BASE_URL}/report/generate"
    payload = {"report_type": report_type}

    response = requests.post(url, json=payload, stream=True, timeout=120)
    response.raise_for_status()

    cd = response.headers.get("content-disposition")
    if cd and "filename=" in cd:
        filename = cd.split("filename=")[1].strip('"\'')
    else:
        now_str = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        ext = "docx" if report_type == "word" else "pdf"
        filename = f"BESS_DeepAnalysis_{now_str}.{ext}"

    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "output_reports"))
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, filename)

    with open(out_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    return out_path


# ── Standalone-mode: local generation ─────────────────────────────────────────

def _local_generate_word() -> str:
    from utils._report_local import generate_word_report as _gen
    return _gen()


def _local_generate_pdf() -> str:
    from utils._report_local import generate_pdf_report as _gen
    return _gen()


# ── Public API (mode-aware with fallback) ─────────────────────────────────────

def generate_word_report() -> str:
    if IS_API_MODE:
        try:
            return _download_report("word")
        except Exception:
            pass  # fallback to local
    return _local_generate_word()


def generate_pdf_report() -> str:
    if IS_API_MODE:
        try:
            return _download_report("pdf")
        except Exception:
            pass  # fallback to local
    return _local_generate_pdf()
