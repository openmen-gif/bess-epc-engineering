"""Dated official evidence, separate from legacy illustrative market assumptions.

No Streamlit cache: each report requests current published inventory and FX.
Publisher benchmarks remain reviewed snapshots even if their page is reachable.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from io import BytesIO
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
EIA_URL = 'https://www.eia.gov/electricity/data/eia860m/'
FX_URL = 'https://api.frankfurter.dev/v1/latest?base=USD&symbols=KRW,EUR,JPY,CNY,GBP,AUD'
FEEDS = {
    'BNEF': 'https://about.bnef.com/feed/',
    'SEIA': 'https://seia.org/feed/',
    'EIA': 'https://www.eia.gov/rss/todayinenergy.xml',
}
MONTHS = {name: i for i, name in enumerate(
    ['january','february','march','april','may','june','july','august','september','october','november','december'], 1)}


def _get(url):
    response = requests.get(url, timeout=(5, 18), headers={'User-Agent': 'BESS-Market-Report/2.0'})
    response.raise_for_status()
    if len(response.content) > 30_000_000:
        raise ValueError('Source exceeds 30 MB limit')
    return response.content


def load_references():
    return json.loads((ROOT / 'data/market_references.json').read_text(encoding='utf-8'))


def reference_status(ref, now):
    basis = ref.get('published_on') or ref['verified_on']
    age = (now.date() - datetime.fromisoformat(basis).date()).days
    if age < 0 or datetime.fromisoformat(ref['verified_on']).date() > now.date():
        return 'future_date'
    return 'review_due' if age > ref['review_days'] else 'reviewed_reference'


def reference_needs_review(ref):
    return ref.get('retrieval_status') != 'matched' or ref.get('freshness') != 'reviewed_reference'


def _inventory_candidates(html, now):
    candidates = []
    for href in re.findall(r'''href=["']([^"']+\.xlsx)["']''', html, flags=re.I):
        match = re.search(r'([a-z]+)_generator(20\d{2})\.xlsx', href, re.I)
        if not match or match[1].lower() not in MONTHS:
            continue
        year, month = int(match[2]), MONTHS[match[1].lower()]
        url = urljoin(EIA_URL, href)
        if urlparse(url).hostname != 'www.eia.gov':
            continue
        if (year, month) < (now.year, now.month):
            candidates.append((f'{year:04}-{month:02}', url))
    if not candidates:
        raise ValueError('No dated EIA workbook link')
    return sorted(set(candidates), reverse=True)


def discover_inventory(html, now):
    return _inventory_candidates(html, now)[0]


def parse_inventory(content, period, url, now):
    raw = pd.read_excel(BytesIO(content), sheet_name='Operating', header=None)
    header = next((i for i in range(min(12, len(raw)))
                   if any(str(v).strip() == 'Plant ID' for v in raw.iloc[i])), None)
    if header is None:
        raise ValueError('EIA inventory header changed')
    frame = raw.iloc[header + 1:].copy()
    frame.columns = [re.sub(r'\s+', ' ', str(v)).strip() for v in raw.iloc[header]]
    def col(*names):
        return next((n for n in names if n in frame.columns), None)
    fuel = col('Energy Source Code', 'Energy Source 1')
    mw = col('Nameplate Capacity (MW)')
    status = col('Status')
    if not fuel or not mw or not status:
        raise ValueError('EIA capacity schema changed')
    operating = frame[status].astype(str).str.strip().str.match(r'^(?:OP$|\(OP\))')
    batteries = frame[(frame[fuel].astype(str).str.strip() == 'MWH') & operating].copy()
    # The geographic scope is the 50 states and DC, not US territories.
    state = col('State', 'Plant State')
    if not state or not {'Plant ID','Generator ID'} <= set(frame.columns):
        raise ValueError('Missing EIA geographic scope or generator identity')
    batteries = batteries[~batteries[state].isin(['PR','GU','VI','AS','MP'])]
    if batteries.empty:
        raise ValueError('No operating battery capacity rows')
    if batteries[['Plant ID','Generator ID',state]].isna().any().any():
        raise ValueError('Missing EIA geographic scope or generator identity')
    if batteries.duplicated(['Plant ID', 'Generator ID']).any():
        raise ValueError('Duplicate battery generator IDs')
    power = pd.to_numeric(batteries[mw], errors='coerce')
    if power.isna().any() or (power <= 0).any():
        raise ValueError('Missing or invalid battery power capacity')
    energy_col = col('Nameplate Energy Capacity (MWh)', 'Nameplate Energy Capacity (MWh) (AC)')
    energy = pd.to_numeric(batteries[energy_col], errors='coerce') if energy_col else None
    complete = energy is not None and energy.notna().all() and (energy > 0).all()
    return {'status':'available', 'period':period, 'url':url,
            'retrieved_at':now.isoformat(), 'mw':round(float(power.sum()), 3),
            'mwh':round(float(energy.sum()), 3) if complete else None,
            'energy_complete':bool(complete), 'count':len(batteries),
            'scope':'EIA-860M 운영 상태 OP, MWH 연료코드, 미국 50개 주 및 DC, 잠정 누적 명판용량'}


def parse_publications(content, source, now):
    root = ET.fromstring(content)
    result = []
    for item in root.findall('.//item'):
        title = unescape(item.findtext('title') or '')
        if not re.search(r'batter|storage|energy storage', title, re.I):
            continue
        try:
            published = parsedate_to_datetime(item.findtext('pubDate') or '')
            if published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
        age = (now - published).total_seconds() / 86400
        link = item.findtext('link') or ''
        if 0 <= age <= 90 and urlparse(link).scheme == 'https':
            result.append({'source':source,'title':title,'url':link,
                           'published_on':published.date().isoformat(), 'status':'review_required'})
    return sorted(result, key=lambda x:x['published_on'], reverse=True)[:5]


def collect_evidence(now=None, get=None):
    now = now or datetime.now(timezone.utc)
    get = get or _get
    refs = load_references()
    urls = list(dict.fromkeys([EIA_URL, FX_URL] + [r['url'] for r in refs] + list(FEEDS.values())))
    def retrieve(url):
        try:
            return url, get(url), None
        except Exception as exc:
            return url, None, type(exc).__name__
    with ThreadPoolExecutor(max_workers=8) as pool:
        responses = {u:(data,error) for u,data,error in pool.map(retrieve, urls)}
    result = {'generated_at':now.isoformat(), 'references':refs, 'publications':[], 'sources':[]}
    for ref in refs:
        data, error = responses[ref['url']]
        text = unescape(re.sub('<[^>]+>', ' ', data.decode('utf-8', errors='replace'))) if data else ''
        ref['retrieved_at'] = now.isoformat() if not error else None
        ref['retrieval_status'] = 'unavailable' if error else (
            'matched' if all(re.search(r'(?<![\d.])'+re.escape(t)+r'(?![\d.])', text) for t in ref['tokens']) else 'changed')
        ref['freshness'] = reference_status(ref, now)
        # Matching known tokens does not certify that this is the newest publication.
    try:
        raw, error = responses[EIA_URL]
        if error:
            raise ValueError(error)
        attempts = []
        for period, url in _inventory_candidates(raw.decode('utf-8'), now)[:3]:
            try:
                payload = get(url)
                if not payload.startswith(b'PK'):
                    raise ValueError('EIA link returned a non-workbook response')
                result['inventory'] = parse_inventory(payload, period, url, now)
                result['inventory']['newer_unavailable'] = attempts
                break
            except Exception as exc:
                attempts.append({'period':period,'url':url,'error':type(exc).__name__})
        else:
            raise ValueError('No valid recent EIA workbook')
    except Exception as exc:
        result['inventory'] = {'status':'unavailable','url':EIA_URL,'error':type(exc).__name__}
    try:
        raw, error = responses[FX_URL]
        if error:
            raise ValueError(error)
        data = json.loads(raw)
        day = datetime.fromisoformat(data['date']).date()
        if data.get('base') != 'USD' or not 0 <= (now.date() - day).days <= 7:
            raise ValueError('FX base/date invalid or stale')
        rates = data['rates']
        if not rates or any(not isinstance(v,(float,int)) or not 0 < v < 1e9 for v in rates.values()):
            raise ValueError('FX rates invalid')
        result['fx'] = {'status':'available','period':data['date'],'rates':rates,
                        'url':FX_URL,'retrieved_at':now.isoformat()}
    except Exception as exc:
        result['fx'] = {'status':'unavailable','url':FX_URL,'error':type(exc).__name__}
    for name, url in FEEDS.items():
        raw, error = responses[url]
        try:
            if error:
                raise ValueError(error)
            items = parse_publications(raw, name, now)
            result['publications'].extend(items)
            result['sources'].append({'source':name,'url':url,'status':'available','count':len(items)})
        except Exception as exc:
            result['sources'].append({'source':name,'url':url,'status':'unavailable','error':type(exc).__name__})
    return result
