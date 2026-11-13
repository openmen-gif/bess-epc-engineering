from datetime import datetime, timezone
from pathlib import Path

from streamlit.testing.v1 import AppTest

from utils import market_data, market_evidence, market_report


def test_market_download_generates_hhic_word_and_pdf(monkeypatch, tmp_path):
    now = datetime.now(timezone.utc)
    monkeypatch.setattr(market_data,'fetch_rss_feed',lambda *a,**k:{'items':[],'timestamp':now,'source':None})
    monkeypatch.setattr(market_data,'fetch_exchange_rates',lambda:{'timestamp':now,'source':'test'})
    monkeypatch.setattr(market_data,'fetch_commodity_prices',lambda:{'brent_crude_usd':None,'wti_crude_usd':None,
        'lithium_carbonate_usd_ton':None,'copper_usd_ton':None,'nickel_usd_ton':None,'timestamp':now,'source':None})
    def offline(url):
        raise OSError('offline')
    bundle = market_evidence.collect_evidence(now=now,get=offline)
    monkeypatch.setattr(market_evidence,'collect_evidence',lambda:bundle)
    generate = market_report.generate_word_report
    monkeypatch.setattr(market_report,'generate_word_report',lambda **kw:generate(output_dir=tmp_path,**kw))
    app = AppTest.from_file('pages/00_Market_Dashboard.py', default_timeout=120)
    app.session_state['auth_user']='tester'
    app.session_state['auth_role']='admin'
    app.session_state['lang']='KO'
    app.run()
    assert not app.exception, [e.value for e in app.exception]
    app.button(key='btn_gen_word').click().run()
    assert not app.exception, [e.value for e in app.exception]
    assert not app.error, [e.value for e in app.error]
    assert app.session_state['dl_word_bytes'].startswith(b'PK')
    assert app.session_state['dl_pdf_bytes'].startswith(b'%PDF')
    assert '_v4_' in app.session_state['dl_word_name']
    assert len(list(tmp_path.glob('*.validation.json'))) == 1


def test_forecast_labels_do_not_roll_over(monkeypatch):
    monkeypatch.setattr(market_data, '_CURRENT_YEAR_DYNAMIC', 2028)
    assert market_data._latest_actual_year() == 2025
    assert market_data._build_year_labels([2025,2026,2027]) == ['2025E','2026F','2027F']
