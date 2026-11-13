"""HHIC report adapter. Document formatting is owned by the vendored skill."""
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from uuid import uuid4

from utils.market_evidence import collect_evidence

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / 'vendor/hhic_word/scripts/build_doc.py'
KIND = {'forecast':'전망','reported':'발표 실적'}
STATE = {'matched':'원문 수치 확인','changed':'원문 변경 확인 필요','unavailable':'조회 실패',
         'review_due':'갱신 검토 필요','reviewed_reference':'검토된 참조자료','future_date':'미래 날짜 확인 필요'}


def _clean(text):
    return str(text).replace('—', ',').replace('·', '/').replace('`','')


def build_spec(bundle, charts=None):
    created = datetime.fromisoformat(bundle['generated_at']).astimezone(timezone(timedelta(hours=9)))
    blocks = []
    def heading(text):
        blocks.append({'type':'heading','level':1,'text':text})
    def para(text):
        for line in text.splitlines():
            blocks.append({'type':'paragraph','text':line})
    def table(title, cols, rows, widths=None):
        block = {'type':'table','caption':title,'columns':cols,'rows':rows}
        if widths:
            block['col_widths_mm'] = widths
        blocks.append(block)

    heading('검토 요약')
    para('설치 전망의 확대를 수주 기회로 검토하되, 조달 단가와 계통 접속 조건은 사업별로 다시 확인해야 한다. '
         '이 보고서는 발표기관의 실적, 전망 및 생성 시 조회한 통계를 구분한다. 전망을 확정 수주량이나 매출로 해석하지 않는다.')
    table('작성 및 데이터 기준', ['구분','내용'], [
        ['생성 시각',created.strftime('%Y-%m-%d %H:%M KST')],
        ['갱신 방법','공식 자료의 원문 확인, EIA 월별 파일 및 ECB 기준환율 조회'],
        ['해석 제한','조회 시각은 통계 기준일이 아니다. 원문 수치 확인은 후속 발표 부재를 보장하지 않는다.'],
        ['검토 상태','외부 시장자료를 근거로 한 검토용 문서. 입찰 적용 조건은 확인 필요'],
    ], [35,140])
    table('의사결정용 시장 지표', ['지표 / 기간','값 / 성격','원문 및 갱신 상태'], [
        [r['label']+' / '+r['period'],f"{r['value']:g} {r['unit']} / {KIND[r['kind']]}",
         r['id']+' / '+STATE.get(r.get('retrieval_status'),'미조회')+' / '+STATE.get(r.get('freshness'),'확인 필요')]
        for r in bundle['references']], [65,45,65])
    para('검토 의견: 글로벌 설치 전망의 확대는 사업 발굴 근거가 되지만 수주 확정량은 아니다. '
         '미국과 호주의 신규 설치 실적은 시장 진입 검토에 활용하고, 국내 및 다른 권역은 접속권과 발주 공고를 먼저 확인한다. '
         '팩 가격을 EPC 총액으로 적용하지 않으며, 본문의 투자 예시는 현재 가정만으로 투자성을 뒷받침하지 못한다. '
         '조회 실패 또는 갱신 검토 필요 항목은 마지막 검토 당시의 참조값이며 최신값으로 확정하지 않는다.')
    heading('시장 참조자료')
    for ref in bundle['references']:
        blocks.append({'type':'heading','level':2,'text':ref['label'] + ' ' + ref['period']})
        table(ref['id'], ['항목','값'], [
            ['규모',f"{ref['value']:g} {ref['unit']} ({KIND[ref['kind']]})"],
            ['통계 기간',ref['period']],['집계 범위',ref['scope']],
            ['발표일',ref.get('published_on') or '공개 페이지 발표일 미확인'],
            ['내용 검토일',ref['verified_on']],
            ['이번 원문 조회',STATE.get(ref.get('retrieval_status'), '미조회')],
            ['원문 수집 시각',ref.get('retrieved_at') or '이번 조회 실패'],
            ['갱신 상태',STATE.get(ref.get('freshness'),'확인 필요')],
        ], [35,140])
        para('출처: ' + ref['title'] + '\n' + ref['url'])
        para('[확인 필요: 발주 지역, 사업 범위 및 후속 발표에 대한 적용성 검토]')
    para('미국 분기 실적은 SEIA와 ACP의 조사 범위 및 방법이 다르므로 별도로 제시한다. '
         '두 집계의 평균이나 합계를 시장 실적으로 사용하지 않는다. '
         'GW는 출력, GWh는 에너지이며, 팩 단가는 셀 가격 또는 EPC 총사업비와 구분한다.')

    heading('생성 시 조회한 공식 통계')
    inv = bundle['inventory']
    if inv['status'] == 'available':
        table('미국 운영 배터리 저장설비', ['항목','값'], [
            ['자료 기준월',inv['period']], ['설비 출력',f"{inv['mw']/1000:,.3f} GW"],
            ['신고 에너지용량',f"{inv['mwh']/1000:,.3f} GWh" if inv.get('mwh') is not None else '결측 존재: 합산 제외'],
            ['집계 발전기',str(inv['count'])], ['집계 범위',inv['scope']],
            ['수집 시각',inv['retrieved_at']],
        ],[35,140])
        para('출처: EIA Preliminary Monthly Electric Generator Inventory\n' + inv['url'])
        if inv.get('newer_unavailable'):
            para('[확인 필요: 더 최근 링크의 파일을 검증하지 못해 가장 최근 검증 가능한 월을 사용했다. '
                 + ', '.join(a['period'] for a in inv['newer_unavailable']) + ']')
        para('월별 파일에 신고된 값을 합산했다. 4시간 저장 가정으로 에너지용량을 만들어 넣지 않았다. '
             '누적 운영설비와 연간 신규 설치 실적은 직접 비교하지 않는다.')
    else:
        para('[확인 필요: EIA 최신 월별 자료 조회 또는 구조 검증 실패. 이전 용량으로 대체하지 않았다.]')
        para('공식 원문: ' + inv['url'])
    fx = bundle['fx']
    if fx['status'] == 'available':
        table('USD 기준 환율', ['통화','통화/USD','기준일'],
              [[k,f'{v:g}',fx['period']] for k,v in fx['rates'].items()], [40,65,70])
        para('출처: Frankfurter / ECB 기준환율\n' + fx['url'])
        para('조회 상태: 성공 / 수집 시각: ' + fx['retrieved_at'])
        para('해당 영업일의 기준환율이며 장중 매매가격이 아니다. 견적 적용 환율 및 헤지 조건은 별도 확인한다.')
    else:
        para('[확인 필요: 최신 기준환율 조회 실패 또는 7일 초과. 과거 환율을 현재값으로 표시하지 않았다.]')

    heading('후속 발표 점검')
    para('최근 90일 이내 공식 배터리 및 저장 관련 발표를 조회한다. 아래 제목은 검토 후보이며 '
         '수치나 정책 효력을 자동으로 확정하지 않는다. 원문 검토 후 참조자료에 반영한다.')
    for item in bundle['publications']:
        para(f"{item['published_on']} / {item['source']}: {_clean(item['title'])}\n{item['url']}")
    if not bundle['publications']:
        para('이번 조회에서 검토 후보를 확보하지 못했다. 후속 발표가 없다는 의미는 아니다.')
    table('공식 발표 조회 결과', ['출처','상태','후보 수'],
          [[s['source'],'조회 완료' if s['status']=='available' else '조회 실패',str(s.get('count','-'))]
           for s in bundle['sources']], [50,75,50])

    heading('EPC 사업 대응')
    para('아래 내용은 시장자료에 대한 사업 검토 의견이다. 사업별 설계 조건과 계약서가 확정되기 전에는 '
         '인허가 적합성, 납기 또는 수익을 보장하는 근거로 사용하지 않는다.')
    table('사업 단계별 확인사항', ['영역','검토 영향','다음 조치'], [
        ['입찰','시장 성장 전망과 실제 발주 파이프라인의 차이','발주 공고, 예산, 계통 접속 및 상업운전 일정을 확인한다.'],
        ['조달','팩 평균 가격과 EPC 총액의 범위 차이','동일 저장시간과 인도조건으로 셀, PCS, 변압기, 토목, 시운전 및 보증 견적을 비교한다.'],
        ['계통','출력 및 저장시간에 따른 수익 기회의 차이','접속점, 충방전 한도, 출력제한, 보조서비스 자격과 중복 참여 제한을 확인한다.'],
        ['안전','관할기관 및 배치 조건에 따른 설계 변경','발주처 요구사항, 소방 협의, 시험성적서와 적용 규격 판본을 확인한다.'],
        ['계약','환율, 현지화, 성능보증 및 일정 위험','가격 유효기간, 변경 조항, 지체상금 및 보증 경계를 문서화한다.'],
    ], [22,63,90])
    heading('사업성 및 시나리오')
    para('프로젝트별 현금흐름 입력이 없어 IRR 및 LCOS를 산출하지 않았다. '
         '전력시장 수익은 시간대별 운영 가능성과 중복 참여 제한을 반영해야 하며, '
         '기관별 평균 수익을 단순 합산하거나 가중평균해 사업 수익으로 확정하지 않는다.')
    table('검증할 시나리오', ['구분','입력 방향','필수 검증'], [
        ['보수','가격차 축소, CAPEX 증가, 접속 지연','충전비, 보조전력, 열화, 증설비 및 지연 비용'],
        ['기준','사업별 검증 견적 및 공개 시장자료 적용','운영 가능시간, 계약 수익 및 할인율'],
        ['낙관','추가 수익 참여와 조달비 개선 가정','수익 동시 실현 가능성과 상한 검증'],
    ], [25,75,75])
    para('[확인 필요: 용량, 저장시간, 투자비, 운영비, 효율, 사이클, 열화, 증설, 수익계약, 세율 및 할인율]')

    heading('근거 및 미결사항')
    blocks.append({'type':'evidence_log','caption':'출처 추적표','sources':[
        {'id':r['id'],'title':r['title']+' / '+r['period']+' / '+r['url'],
         'grade':'E3','status':'외부 공개자료, 사업 적용성 확인 필요'} for r in bundle['references']]})
    para('근거 등급은 문서 검토 기준에 따른다. 직접 프로젝트 정본은 E1, 내부 참조는 E2, '
         '사업 적용을 검증하지 않은 외부 가정은 E3, 필수 입력 누락은 E4로 관리한다. '
         '이 문서의 시장자료는 출처를 확인했더라도 프로젝트 계약 정본으로 취급하지 않는다.')
    items = [
        {'no':1,'subject':'견적 및 경제성 입력','clarification':'동일 조건의 공급사 견적과 사업별 수익 입력 확보',
         'impact':'입찰가, IRR 및 LCOS 산정 보류','status':'HOLD'},
        {'no':2,'subject':'규정 및 계약 판본','clarification':'관할기관, 발주처 요구사항 및 유효 규정 원문 확인',
         'impact':'설계 및 계약 책임 확정 보류','status':'HOLD'},
    ]
    for r in bundle['references']:
        if r.get('retrieval_status') != 'matched' or r.get('freshness') != 'reviewed_reference':
            items.append({'no':len(items)+1,'subject':r['id'],'clarification':'공식 원문 재조회 및 후속 발표 확인',
                          'impact':'현재값으로 확정하지 않음','status':'TBC'})
    for key in ('inventory','fx'):
        if bundle[key]['status'] != 'available':
            items.append({'no':len(items)+1,'subject':key,'clarification':'공식 데이터 수집 및 구조 재검증',
                          'impact':'해당 최신 지표 제외','status':'TBC'})
    blocks.append({'type':'open_items','caption':'확인 필요 항목','items':items})
    # Preserve the original 18 analysis topics; source lineage follows in appendices.
    from utils.market_report_content import analysis_blocks
    groups = []
    for block in blocks:
        if block['type'] == 'heading' and block['level'] == 1:
            groups.append([])
        groups[-1].append(block)
    blocks = groups[0] + analysis_blocks(bundle, charts)
    for group in groups[1:]:
        if group[0]['text'] not in ('EPC 사업 대응', '사업성 및 시나리오'):
            blocks.extend(group)
    def clean_tree(value):
        if isinstance(value, str):
            return _clean(value)
        if isinstance(value, list):
            return [clean_tree(v) for v in value]
        if isinstance(value, dict):
            return {k:clean_tree(v) for k,v in value.items()}
        return value
    blocks = clean_tree(blocks)
    return {'meta':{'doc_type':'technical_review','profile':'modern','language':'ko',
            'project_name':'BESS 시장 검토','doc_title':'BESS 시장 분석 보고서',
            'header_title':'BESS 시장 분석','doc_number':'BESS-MKT-002','revision':'3',
            'issue_date':created.date().isoformat(),'doc_status':'검토용',
            'include_cover':True,'include_toc':True,'abbreviations':'auto',
            'revisions':[{'rev':'3','date':created.date().isoformat(),
                          'description':'18개 분석 주제 및 시각화 보강','author':''}]},'blocks':blocks}


def _run(args, timeout=240):
    result = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace',
                            timeout=timeout, env={**os.environ,'PYTHONIOENCODING':'utf-8'})
    if result.returncode:
        raise RuntimeError('문서 처리 실패: ' + (result.stdout + result.stderr)[-1800:])
    return result


def _render(docx):
    """Isolated LibreOffice profile prevents concurrent report collisions."""
    soffice = shutil.which('libreoffice') or shutil.which('soffice')
    if not soffice:
        path = Path('C:/Program Files/LibreOffice/program/soffice.exe')
        soffice = str(path) if path.exists() else None
    if not soffice:
        raise RuntimeError('목차/PDF 렌더러 LibreOffice가 설치되지 않았습니다.')
    uno_python = str(Path(soffice).parent/'python.exe') if os.name == 'nt' else '/usr/bin/python3'
    with tempfile.TemporaryDirectory(prefix='bess-render-') as td:
        temp = Path(td)
        converted = temp / 'converted'
        converted.mkdir()
        updated = converted / docx.name
        _run([uno_python, str(ROOT/'scripts/render_market_uno.py'), str(docx),
              str(updated), soffice, str(temp/'profile')])
        if not updated.is_file():
            raise RuntimeError('Word 목차 변환 파일을 생성하지 못했습니다.')
        pdf = updated.with_suffix('.pdf')
        if not pdf.exists():
            raise RuntimeError('PDF 변환 파일을 생성하지 못했습니다.')
        shutil.copy2(updated, docx)
        shutil.copy2(pdf, docx.with_suffix('.pdf'))
    return docx.with_suffix('.pdf')


def generate_word_report(*, bundle=None, output_dir=None, render=True):
    bundle = bundle if bundle is not None else collect_evidence()
    folder = Path(output_dir) if output_dir else (Path('/data/output_reports') if Path('/data').is_dir() else ROOT/'output_reports')
    folder.mkdir(parents=True, exist_ok=True)
    stem = 'BESS_MarketReport_v3_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + uuid4().hex[:10]
    docx = folder / (stem + '.docx')
    from utils.market_report_content import render_charts
    charts = render_charts(bundle, folder / (stem + '_assets'))
    spec = build_spec(bundle, charts)
    source = folder / (stem + '.json')
    source.write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
    (folder/(stem+'.evidence.json')).write_text(json.dumps(bundle,ensure_ascii=False,indent=2),encoding='utf-8')
    _run([sys.executable,str(BUILDER),str(source),'--strict','--out',str(docx)])
    receipt_path = docx.with_suffix('.validation.json')
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    if receipt['style_summary']['warning_count'] or not receipt['docx_parity']['passed']:
        raise RuntimeError('HHIC 문서 검수 미통과')
    if render:
        pdf = _render(docx)
        from vendor.hhic_word.scripts.hyoword.qa import verify_docx_content_parity
        rendered_parity = verify_docx_content_parity(spec, docx)
        if not rendered_parity['passed']:
            raise RuntimeError('렌더링 후 DOCX 본문 대조 실패')
        receipt['rendered_docx_parity'] = rendered_parity
        import fitz
        with fitz.open(pdf) as pages:
            text = ''.join(p.get_text() for p in pages)
            # Fonts may introduce spaces between Korean glyphs in PDF extraction.
            compact = ''.join(text.split())
            missing = [b['text'] for b in spec['blocks'] if b['type']=='heading' and
                       ''.join(b['text'].split()) not in compact]
            blanks = [i+1 for i,p in enumerate(pages) if not p.get_text().strip()]
            if missing or blanks:
                raise RuntimeError(f'PDF 내용 검수 실패: 제목 누락 {missing}, 빈 페이지 {blanks}')
            receipt['render_validation'] = {'renderer':'LibreOffice','pages':len(pages),
                                          'toc_and_fields_updated':True,
                                          'missing_headings':missing,'blank_pages':blanks,'passed':True}
        receipt['output_pdf'] = str(pdf)
        receipt['output_docx_sha256'] = hashlib.sha256(docx.read_bytes()).hexdigest()
    receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    return str(docx)


def generate_pdf_report(**kwargs):
    kwargs['render'] = True
    return str(Path(generate_word_report(**kwargs)).with_suffix('.pdf'))
