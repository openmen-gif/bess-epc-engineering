import os
import requests
import datetime

API_BASE_URL = "http://localhost:8000/api/v1"

def _download_report(report_type: str) -> str:
    """Helper to request the generation API and save the downloaded file locally."""
    url = f"{API_BASE_URL}/report/generate"
    payload = {"report_type": report_type}
    
    try:
        response = requests.post(url, json=payload, stream=True)
        response.raise_for_status()
        
        # Determine filename from Content-Disposition if possible
        cd = response.headers.get("content-disposition")
        filename = ""
        if cd and "filename=" in cd:
            filename = cd.split("filename=")[1].strip('"\'')
        else:
            now_str = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            ext = "docx" if report_type == "word" else "pdf"
            filename = f"BESS_DeepAnalysis_{now_str}.{ext}"
            
        out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "output", "02_reports"))
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, filename)
        
        with open(out_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return out_path
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"API 요청 실패: API 서버(localhost:8000)가 실행 중인지 확인하세요. (상세 에러: {e})")

def generate_word_report() -> str:
    return _download_report("word")

def generate_pdf_report() -> str:
    return _download_report("pdf")
