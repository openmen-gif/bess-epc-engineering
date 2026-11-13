"""Docker build gate: exercise the same offline DOCX/PDF path as production."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.market_evidence import collect_evidence
from utils.market_report import generate_word_report


def offline(url):
    raise OSError('Build validation is offline')


with tempfile.TemporaryDirectory(prefix='market-build-') as folder:
    bundle = collect_evidence(now=datetime.now(timezone.utc),get=offline)
    path = Path(generate_word_report(bundle=bundle,output_dir=folder))
    receipt = json.loads(path.with_suffix('.validation.json').read_text(encoding='utf-8'))
    assert receipt['render_validation']['passed']
    assert receipt['rendered_docx_parity']['passed']
    assert receipt['style_summary']['warning_count'] == 0
    print('MARKET_REPORT_BUILD_OK', receipt['render_validation']['pages'])
