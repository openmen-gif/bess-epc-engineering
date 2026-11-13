from datetime import datetime, timezone
from io import BytesIO

import pandas as pd
import pytest

from utils.market_evidence import (
    discover_inventory, parse_inventory, load_references, collect_evidence,
    reference_status,
    reference_needs_review,
)

NOW = datetime(2026, 11, 13, tzinfo=timezone.utc)


def test_inventory_discovers_latest_published_not_future():
    html = '<a href="xls/august_generator2026.xlsx">XLS</a><a href="xls/september_generator2026.xlsx">XLS</a><a href="xls/december_generator2026.xlsx">XLS</a>'
    period, url = discover_inventory(html, NOW)
    assert period == '2026-09'
    assert url == 'https://www.eia.gov/electricity/data/eia860m/xls/september_generator2026.xlsx'


def workbook(missing=False):
    df = pd.DataFrame({
        'Plant ID': [1, 2, 3, 4], 'Generator ID': ['A', 'B', 'C', 'D'],
        'Energy Source Code': ['MWH', 'MWH', 'NG', 'MWH'],
        'Status': ['OP', 'OP', 'OP', 'SB'], 'State': ['TX', 'CA', 'TX', 'TX'],
        'Nameplate Capacity (MW)': [100, None if missing else 200, 900, 50],
        'Nameplate Energy Capacity (MWh)': [250, 600, None, 200],
    })
    out = BytesIO()
    with pd.ExcelWriter(out, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Operating', index=False, startrow=2)
    return out.getvalue()


def test_inventory_uses_reported_energy_not_four_hour_assumption():
    result = parse_inventory(workbook(), '2026-09', 'https://www.eia.gov/test.xlsx', NOW)
    assert result['mw'] == 300
    assert result['mwh'] == 850
    assert result['count'] == 2
    assert result['period'] == '2026-09'


def test_missing_battery_capacity_fails_closed():
    with pytest.raises(ValueError, match='capacity'):
        parse_inventory(workbook(True), '2026-09', 'https://www.eia.gov/test.xlsx', NOW)


def test_eia_verbose_operating_codes():
    df = pd.read_excel(BytesIO(workbook()), sheet_name='Operating', header=2)
    df['Status'] = df['Status'].map({'OP':'(OP) Operating','SB':'(SB) Standby'})
    df = df.rename(columns={'State':'Plant State'})
    out = BytesIO()
    with pd.ExcelWriter(out, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Operating', index=False, startrow=2)
    assert parse_inventory(out.getvalue(),'2026-09','https://www.eia.gov/file',NOW)['mw'] == 300


@pytest.mark.parametrize('column',['State','Plant ID','Generator ID'])
def test_missing_scope_or_identity_column_rejected(column):
    df = pd.read_excel(BytesIO(workbook()), sheet_name='Operating', header=2).drop(columns=[column])
    out = BytesIO()
    with pd.ExcelWriter(out, engine='openpyxl') as writer:
        df.to_excel(writer,sheet_name='Operating',index=False,startrow=2)
    with pytest.raises(ValueError):
        parse_inventory(out.getvalue(),'2026-09','https://www.eia.gov/file',NOW)


def test_reference_forecast_never_becomes_actual():
    refs = load_references()
    forecast = next(r for r in refs if r['id'] == 'bnef-2026')
    assert forecast['value'] == 535
    assert forecast['kind'] == 'forecast'
    assert reference_status(forecast, datetime(2027, 11, 13, tzinfo=timezone.utc)) == 'review_due'
    assert forecast['kind'] == 'forecast'


def test_sources_are_not_averaged():
    refs = {r['id']: r for r in load_references()}
    assert refs['seia-2026q2']['value'] == 20.2
    assert refs['acp-2026q2']['value'] == 18.9
    assert refs['seia-2026q2']['url'] != refs['acp-2026q2']['url']


def test_offline_bundle_has_no_fake_live_values():
    def offline(url):
        raise OSError('offline')
    result = collect_evidence(now=NOW, get=offline)
    assert result['inventory']['status'] == 'unavailable'
    assert result['fx']['status'] == 'unavailable'
    assert result['references']
    assert all(r['retrieval_status'] == 'unavailable' for r in result['references'])
    assert all(r['verified_on'] != result['generated_at'] for r in result['references'])


def test_reachable_stale_reference_still_needs_review():
    ref = load_references()[0]
    ref['retrieval_status'] = 'matched'
    ref['freshness'] = reference_status(ref, datetime(2027,11,13,tzinfo=timezone.utc))
    assert reference_needs_review(ref)


def test_failed_newer_inventory_link_is_disclosed():
    def get(url):
        from utils.market_evidence import EIA_URL
        if url == EIA_URL:
            return b'<a href="xls/october_generator2026.xlsx">XLS</a><a href="xls/september_generator2026.xlsx">XLS</a>'
        if 'october_generator' in url:
            return b'<html>not published</html>'
        if 'september_generator' in url:
            return workbook()
        raise OSError('offline')
    inv = collect_evidence(now=NOW,get=get)['inventory']
    assert inv['period'] == '2026-09'
    assert inv['newer_unavailable'][0]['period'] == '2026-10'
