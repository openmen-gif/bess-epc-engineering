import json
from datetime import datetime, timezone
from pathlib import Path
import zipfile

from utils.market_evidence import collect_evidence
from utils.market_report import build_spec, generate_word_report


def offline():
    def get(url):
        raise OSError('offline')
    return collect_evidence(datetime(2026,11,13,tzinfo=timezone.utc), get)


def test_spec_contains_sources_assumptions_and_no_unverified_returns():
    spec = build_spec(offline())
    assert spec['meta']['profile'] == 'modern'
    assert spec['meta']['include_cover'] is True
    text = json.dumps(spec, ensure_ascii=False)
    assert '535' in text and '20.2' in text and '18.9' in text
    assert '확인 필요' in text
    assert '실시간 수집' not in text
    assert {'evidence_log','open_items'} <= {b['type'] for b in spec['blocks']}


def test_collected_timestamps_are_in_document():
    b = offline()
    b['references'][0]['retrieved_at'] = '2026-11-13T01:02:03+00:00'
    b['fx'] = {'status':'available','period':'2026-11-12','rates':{'KRW':1334.1},
               'url':'https://api.frankfurter.dev/v1/latest', 'retrieved_at':'2026-11-13T02:03:04+00:00'}
    text = json.dumps(build_spec(b), ensure_ascii=False)
    assert b['references'][0]['retrieved_at'] in text
    assert b['fx']['retrieved_at'] in text


def test_offline_docx_uses_pinned_hhic_engine(tmp_path):
    doc = Path(generate_word_report(bundle=offline(), output_dir=tmp_path, render=False))
    assert doc.exists()
    receipt = json.loads(doc.with_suffix('.validation.json').read_text(encoding='utf-8'))
    assert receipt['engine'] == 'hyoword'
    assert receipt['style_summary']['warning_count'] == 0
    assert receipt['docx_parity']['passed']
    assert receipt['template_verification']['sha256'] == '4ec89b04f8c3a88b78aa6585a0c4164afa41dcba8a7133b13fa31c6afa4277b0'
    with zipfile.ZipFile(doc) as z:
        xml = z.read('word/document.xml').decode()
        assert '535' in xml and '확인 필요' in xml
        assert 'TOC' in xml


def test_unique_report_paths(tmp_path):
    b = offline()
    a = generate_word_report(bundle=b, output_dir=tmp_path, render=False)
    c = generate_word_report(bundle=b, output_dir=tmp_path, render=False)
    assert a != c


def test_rendered_toc_has_resolved_page_numbers(tmp_path):
    import fitz
    import re
    path = Path(generate_word_report(bundle=offline(), output_dir=tmp_path))
    with fitz.open(path.with_suffix('.pdf')) as pdf:
        toc = pdf[2].get_text()
        assert re.search(r'검토\s*요약\s*[.\s]*4\b', toc)
        assert len(pdf) >= 5
