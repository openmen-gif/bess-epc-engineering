"""Declarative page boundaries and keep rules for the A4 HHIC report.

No document/template mutation: declarative HHIC JSON block options.
"""
from copy import deepcopy

# Start a new reading unit. Related short chapters flow together within it.
PAGE_STARTS = {
    '시장별 심층 분석', '시각화 분석', '프로젝트 파이프라인',
    '사업 개발 및 투자 분석', '시장 참조자료', '후속 발표 점검', '근거 및 미결사항',
}


def arrange_a4(blocks):
    blocks = deepcopy(blocks)
    chapter = ''
    for i, block in enumerate(blocks):
        if block['type'] == 'heading':
            if block['level'] == 1:
                chapter = block['text']
                if chapter in PAGE_STARTS:
                    block['page_break_before'] = True
        if block['type'] == 'paragraph':
            block['keep_together'] = True
            following = blocks[i+1] if i+1 < len(blocks) else {}
            if following.get('type') == 'table':
                block['keep_with_next'] = True
            if following.get('type') == 'paragraph' and following['text'].startswith(('공식 원문:', 'https://')):
                block['keep_with_next'] = True
            if block['text'].startswith(('출처:', '공식 확인 창구:', '공식 원문:')):
                block['style'] = 'note'
            # Keep each country brief and short chart-led section as a reading unit.
            if following.get('type') == 'figure' and chapter in ('전력시장 및 거래','운영 및 자산관리','시장 시나리오'):
                block['keep_with_next'] = True
        if block['type'] == 'figure':
            block['keep_with_next'] = True
        if block['type'] == 'table':
            following = blocks[i+1] if i+1 < len(blocks) else {}
            block['compact'] = True
            if len(block['rows']) <= 10:
                block['keep_together'] = True
                block['keep_with_next'] = following.get('type') == 'paragraph'
            # Stable column widths prevent long notes squeezing labels/numbers.
            if not block.get('col_widths_mm'):
                count = len(block['columns'])
                block['col_widths_mm'] = {2:[40,135],3:[38,62,75],4:[54,34,34,53]}.get(count)
            if block['caption'] == '경쟁사 분석 검토표':
                block['col_widths_mm'] = [50,25,100]
            elif block['caption'] == '기존 사업 명칭 확인 목록':
                block['col_widths_mm'] = [58,22,95]
    # A short table's source and caveat are one unit. Stop at headings, figures
    # and other tables so, e.g., EIA and FX do not become an oversized chain.
    for i, block in enumerate(blocks):
        if block['type'] != 'table' or not block.get('keep_with_next'):
            continue
        j = i + 1
        while j < len(blocks) and blocks[j]['type'] == 'paragraph':
            following = blocks[j+1] if j+1 < len(blocks) else {}
            if following.get('type') == 'paragraph':
                blocks[j]['keep_with_next'] = True
            elif following.get('type') == 'table':
                blocks[j]['keep_with_next'] = False
            j += 1
    # Begin the long watchlist on its own page instead of orphaning a few rows
    # below the project chart. It remains splittable for future extra records.
    watch = next((i for i,b in enumerate(blocks) if b.get('caption') == '기존 사업 명칭 확인 목록'),None)
    if watch is not None:
        blocks.insert(watch,{'type':'page_break'})
    return blocks


def check_pdf_layout(spec, pages):
    """Check physical co-location, beyond DOCX text parity. No position guessing."""
    compact = lambda text: ''.join(str(text).split())
    texts = [compact(page.get_text()) for page in pages]
    errors = []
    tables = figures = notes = 0
    blocks = spec['blocks']
    for i, block in enumerate(blocks):
        if block['type'] == 'table' and block.get('keep_together'):
            tables += 1
            cells = [compact(c) for row in block['rows'] for c in row]
            matches = [p for p,text in enumerate(texts)
                       if compact(block['caption']) in text and all(c in text for c in cells)]
            if not matches:
                errors.append('표 분리: '+block['caption'])
            if block.get('keep_with_next'):
                trailing = []
                j = i+1
                while j < len(blocks) and blocks[j]['type'] == 'paragraph':
                    trailing.append(compact(blocks[j]['text']))
                    j += 1
                notes += bool(trailing)
                if trailing and not any(all(t in texts[p] for t in trailing) for p in matches):
                    errors.append('표 설명 분리: '+block['caption'])
        elif block['type'] == 'figure':
            figures += 1
            following = blocks[i+1] if i+1 < len(blocks) else {}
            if following.get('type') == 'paragraph' and not any(
                    compact(block['caption']) in text and compact(following['text']) in text for text in texts):
                errors.append('그림 설명 분리: '+block['caption'])
    return {'tables_checked':tables,'table_notes_checked':notes,'figures_checked':figures,
            'errors':errors,'passed':not errors}
