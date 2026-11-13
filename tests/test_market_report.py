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
        body_page = next(i+1 for i,p in enumerate(pdf) if '설치 전망의 확대' in p.get_text())
        toc = ''.join(pdf[i].get_text() for i in range(2,body_page-1))
        assert re.search(r'검토\s*요약\s*[.\s]*'+str(body_page)+r'\b', toc)
        assert len(pdf) >= 5


def test_comprehensive_analysis_topics_are_preserved():
    spec = build_spec(offline())
    headings = [b['text'] for b in spec['blocks'] if b['type'] == 'heading' and b['level'] == 1]
    required = ['시장별 심층 분석','전문 카테고리 분석','시각화 분석','글로벌 트렌드 및 성장률',
                '경쟁사 분석','프로젝트 파이프라인','환율 및 원자재 영향','시장 시나리오',
                '사업 개발 및 투자 분석','전력시장 및 거래','운영 및 자산관리','안전 및 규제',
                '배터리 및 장주기 기술','인허가 및 개발 일정','프로젝트 파이낸싱',
                'EPC 계약 구조','전략적 시사점']
    assert set(required) <= set(headings)
    for name in required:
        start = next(i for i,b in enumerate(spec['blocks']) if b.get('text') == name)
        end = next((i for i in range(start+1,len(spec['blocks'])) if spec['blocks'][i].get('type') == 'heading' and spec['blocks'][i].get('level') == 1),len(spec['blocks']))
        body = spec['blocks'][start+1:end]
        assert any(b['type'] == 'table' for b in body), name
        assert sum(len(b.get('text','')) for b in body if b['type'] == 'paragraph') >= 150, name


def test_figures_and_financial_calculations(tmp_path):
    from utils.market_report_content import render_charts, illustrative_case
    charts = render_charts(offline(), tmp_path)
    spec = build_spec(offline(), charts)
    figures = [b for b in spec['blocks'] if b['type'] == 'figure']
    assert len(figures) == 8
    assert all(Path(b['path']).stat().st_size > 10000 for b in figures)
    case = illustrative_case()
    assert case['energy'] == 116400
    assert case['capex'] == 94000000
    # 116400 * (110 - 40 / 0.85) - 3200000, independently evaluated.
    assert abs(case['cash'] - 4126352.941176471) < .01
    assert case['npv'] < 0 and case['payback'] > 15
    assert illustrative_case(efficiency=.9)['cash'] > case['cash']
    assert illustrative_case(1.2)['npv'] < case['npv']
    text = json.dumps(spec,ensure_ascii=False)
    assert '13148' not in text and '13,148' not in text
    assert '3287' in text and '196' in text


def test_a4_layout_keeps_content_and_groups_sections():
    spec = build_spec(offline())
    sections = {b['text']: b for b in spec['blocks'] if b['type'] == 'heading'}
    assert sections['시각화 분석']['page_break_before']
    assert sections['사업 개발 및 투자 분석']['page_break_before']
    assert sections['시장 참조자료']['page_break_before']
    assert all(b.get('keep_with_next') for i,b in enumerate(spec['blocks'][:-1])
               if b['type'] == 'paragraph' and spec['blocks'][i+1]['type'] == 'table'
               and i and spec['blocks'][i-1]['type'] == 'heading')


def test_chart_design_uses_semantics_and_print_resolution(tmp_path):
    from utils.market_report_charts import draw_chart
    from utils.market_report_content import chart_definitions
    kinds = {}
    for definition in chart_definitions(offline()):
        fig, kind = draw_chart(definition)
        kinds[definition[0]] = kind
        assert fig.dpi >= 220
        assert fig.get_figwidth()/fig.get_figheight() >= 3
    assert kinds['cash'] == 'waterfall'
    assert kinds['capex'] == 'horizontal'
    assert kinds['efficiency'] == 'line'
    assert len(set(kinds.values())) >= 3


def test_small_table_rows_keep_conclusion_with_them(tmp_path):
    from docx import Document
    path = generate_word_report(bundle=offline(), output_dir=tmp_path, render=False)
    doc = Document(path)
    table = next(t for t in doc.tables if t.cell(0,0).text == '단계' and len(t.rows) == 6)
    assert all(p._p.find('w:pPr/w:keepNext',namespaces=p._p.nsmap) is not None
               for row in table.rows for cell in row.cells for p in cell.paragraphs)


def test_pdf_layout_rejects_detached_table_caveat():
    from utils.market_report_layout import check_pdf_layout
    class Page:
        def __init__(self,text): self.text = text
        def get_text(self): return self.text
    spec = {'blocks':[{'type':'table','caption':'환율','rows':[['KRW','1337.13']],
                      'keep_together':True,'keep_with_next':True},
                      {'type':'paragraph','text':'기준환율이며 거래 호가가 아니다.'}]}
    result = check_pdf_layout(spec,[Page('환율 KRW 1337.13'),Page('기준환율이며 거래 호가가 아니다.')])
    assert result['errors'] == ['표 설명 분리: 환율']
    assert check_pdf_layout(spec,[Page('환율 KRW 1337.13 기준환율이며 거래 호가가 아니다.')])['passed']
