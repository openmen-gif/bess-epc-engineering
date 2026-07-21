import logging
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape
import re
from datetime import datetime
import streamlit as st

_log = logging.getLogger(__name__)

# ============================================================
# RSS 피드 URL — 직접 뉴스 사이트 (클라우드 서버 접근 가능)
# 각 카테고리마다 복수 소스를 순서대로 시도
# ============================================================

RSS_FEEDS = {
    "배터리 가격": [
        "https://www.energy-storage.news/feed/",
        "https://electrek.co/tag/battery/feed/",
        "https://www.pv-tech.org/feed/",
        "https://cleantechnica.com/feed/",
        "https://www.rechargenews.com/rss",
    ],
    "한국 시장": [
        "https://www.energy-storage.news/feed/",
        "https://cleantechnica.com/feed/",
        "https://electrek.co/tag/energy-storage/feed/",
        "https://www.pv-tech.org/feed/",
    ],
    "미국 시장": [
        "https://www.utilitydive.com/feeds/news/",
        "https://electrek.co/tag/energy-storage/feed/",
        "https://cleantechnica.com/feed/",
        "https://www.energy-storage.news/feed/",
        "https://www.rechargenews.com/rss",
    ],
    "호주 시장": [
        "https://reneweconomy.com.au/feed/",
        "https://www.energy-storage.news/feed/",
        "https://electrek.co/tag/energy-storage/feed/",
        "https://cleantechnica.com/feed/",
    ],
    "영국 시장": [
        "https://www.energy-storage.news/feed/",
        "https://www.rechargenews.com/rss",
        "https://www.pv-tech.org/feed/",
        "https://cleantechnica.com/feed/",
    ],
    "EU 시장": [
        "https://www.energy-storage.news/feed/",
        "https://www.pv-tech.org/feed/",
        "https://www.rechargenews.com/rss",
        "https://cleantechnica.com/feed/",
    ],
    "일본 시장": [
        "https://www.energy-storage.news/feed/",
        "https://electrek.co/tag/energy-storage/feed/",
        "https://cleantechnica.com/feed/",
        "https://www.pv-tech.org/feed/",
    ],
    "프로젝트": [
        "https://www.energy-storage.news/feed/",
        "https://www.pv-tech.org/feed/",
        "https://electrek.co/tag/energy-storage/feed/",
        "https://www.utilitydive.com/feeds/news/",
        "https://www.rechargenews.com/rss",
    ],
    "경쟁사": [
        "https://electrek.co/tag/tesla-megapack/feed/",
        "https://www.energy-storage.news/feed/",
        "https://www.pv-tech.org/feed/",
        "https://cleantechnica.com/feed/",
    ],
    "공급망": [
        "https://www.pv-tech.org/feed/",
        "https://electrek.co/tag/battery/feed/",
        "https://cleantechnica.com/feed/",
        "https://www.rechargenews.com/rss",
        "https://www.energy-storage.news/feed/",
    ],
    "안전·화재": [
        "https://www.energy-storage.news/feed/",
        "https://electrek.co/tag/energy-storage/feed/",
        "https://cleantechnica.com/feed/",
        "https://www.utilitydive.com/feeds/news/",
    ],
    "정책·규제": [
        "https://www.utilitydive.com/feeds/news/",
        "https://www.energy-storage.news/feed/",
        "https://cleantechnica.com/feed/",
        "https://www.rechargenews.com/rss",
        "https://electrek.co/tag/energy-storage/feed/",
    ],
}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

# 카테고리별 관련도 키워드 — 영문 RSS 본문에서 매칭. 대소문자 무시.
# 매칭되는 키워드가 1개라도 포함된 기사를 우선 노출하고, 부족하면 원본 순서로 보충.
RSS_CATEGORY_KEYWORDS = {
    "한국 시장": [
        "korea", "korean", "samsung sdi", "lg energy", "lg energy solution",
        "sk on", "sk innovation", "kepco", "hanwha", "doosan", "kpx",
    ],
    "일본 시장": [
        "japan", "japanese", "tokyo", "kansai", "sumitomo", "ngk insulators",
        "panasonic", "hokkaido", "feed-in premium", "jepx",
    ],
    "미국 시장": [
        "united states", "u.s.", " us ", "us-", "american", "california",
        "texas", "ercot", "caiso", "pjm", "miso", "nyiso", "iso-ne", "spp",
        "ira ", "inflation reduction act", "ferc", "doe ", "biden", "trump",
    ],
    "호주 시장": [
        "australia", "australian", "aemo", "nem ", "fcas", "neoen",
        "agl ", "origin energy", "akaysha", "victorian", "queensland", "nsw",
    ],
    "영국 시장": [
        "uk ", "u.k.", "united kingdom", "british", "britain", "england",
        "national grid", "ofgem", "national grid eso", "balancing mechanism",
        "dynamic containment", "capacity market", "rema",
    ],
    "EU 시장": [
        "eu ", "european", "europe", "germany", "france", "spain", "italy",
        "netherlands", "poland", "ireland", "denmark", "sweden", "repowereu",
        "fit for 55", "epex", "nord pool",
    ],
    "중동 시장": [
        "middle east", "uae", "saudi", "saudi arabia", "qatar", "oman",
        "egypt", "acwa power", "masdar", "neom", "vision 2030", "dubai",
    ],
    "배터리 가격": [
        "battery price", "cell price", "lfp", "nmc", "$/kwh", "/kwh",
        "lithium price", "lithium carbonate", "battery cost",
    ],
    "프로젝트": [
        "project", "groundbreaking", "commissioning", "operational",
        "online", "mwh", "gwh", "energization", "completion", "milestone",
    ],
    "경쟁사": [
        "catl", "byd", "tesla", "megapack", "fluence", "sungrow", "eve energy",
        "wärtsilä", "wartsila", "samsung sdi", "lg energy", "powin",
    ],
    "공급망": [
        "supply chain", "lithium", "cobalt", "nickel", "manufacturing",
        "factory", "gigafactory", "production", "raw material", "mining",
    ],
    "안전·화재": [
        "fire", "safety", "thermal runaway", "incident", "nfpa", "ul 9540",
        "explosion", "blaze", "burning", "extinguish",
    ],
    "정책·규제": [
        "policy", "regulation", "ira ", "ferc", "doe ", "capacity market",
        "subsidy", "incentive", "battery regulation", "legislation",
        "tax credit", "itc ", "ptc ",
    ],
}


def _item_matches_category(item: dict, keywords: list) -> bool:
    """RSS 아이템(title+description)이 카테고리 키워드 중 하나라도 포함하면 True."""
    if not keywords:
        return True
    haystack = f"{item.get('title', '')} {item.get('description', '')}".lower()
    return any(kw.lower() in haystack for kw in keywords)


def _filter_by_category(items: list, category: str, max_items: int) -> list:
    """카테고리 키워드로 필터링. 관련 기사를 앞에, 나머지를 뒤에 배치하여 max_items 채움."""
    keywords = RSS_CATEGORY_KEYWORDS.get(category, [])
    if not keywords:
        return items[:max_items]
    matched = [it for it in items if _item_matches_category(it, keywords)]
    others = [it for it in items if it not in matched]
    return (matched + others)[:max_items]

def _strip_html(text: str) -> str:
    """Remove HTML tags and decode entities."""
    text = unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_summary(title: str, desc_raw: str, content_raw: str) -> str:
    """Build a meaningful summary that differs from the title.

    Priority: content:encoded (longer body) > description.
    Strips HTML, removes leading title duplication, and truncates.
    """
    # Prefer content:encoded (full article body) for richer summary
    body = _strip_html(content_raw) if content_raw else _strip_html(desc_raw)

    if not body:
        return ""

    # Remove leading text that duplicates the title
    title_clean = title.strip().rstrip(".")
    if body.startswith(title_clean):
        body = body[len(title_clean):].lstrip(" :;–—-.,\n")

    # If body is still too similar to title (>80% overlap), try harder
    if len(body) < 20 or _similarity(title_clean, body) > 0.8:
        # Use content if we haven't already, or desc as last resort
        alt = _strip_html(content_raw) if content_raw and body == _strip_html(desc_raw) else _strip_html(desc_raw)
        if alt and len(alt) > len(body):
            body = alt
            if body.startswith(title_clean):
                body = body[len(title_clean):].lstrip(" :;–—-.,\n")

    # Truncate to ~250 chars at a word boundary
    if len(body) > 250:
        cut = body[:250].rfind(" ")
        body = body[:cut if cut > 100 else 250] + "…"

    return body if body else ""


def _similarity(a: str, b: str) -> float:
    """Quick Jaccard-like similarity between two strings (word-level)."""
    sa = set(a.lower().split())
    sb = set(b.lower().split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


# Namespace for content:encoded
_NS = {"content": "http://purl.org/rss/1.0/modules/content/"}


def _fetch_one_rss(url: str, max_items: int, timeout: int) -> list:
    """Try to fetch a single RSS URL. Returns list of items or empty list."""
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            tree = ET.parse(resp)
        items = []
        for item in tree.findall(".//item")[:max_items]:
            title = item.findtext("title", "")
            link  = item.findtext("link", "")
            pub   = item.findtext("pubDate", "")
            desc_raw = item.findtext("description", "")
            content_raw = item.findtext("content:encoded", "", _NS)
            summary = _extract_summary(title, desc_raw, content_raw)
            if title:
                items.append({"title": title, "link": link, "pubDate": pub, "description": summary})
        return items
    except Exception as e:
        _log.warning("RSS fetch failed [%s]: %s", url, e)
        return []

@st.cache_data(ttl=1800)
def fetch_rss_feed(category, max_items=6, timeout=12):
    """Try each RSS source in order until we get results.
    각 RSS에서 max_items * 4 만큼 미리 가져와 카테고리 키워드 필터링 후 max_items 선택.
    """
    urls = RSS_FEEDS.get(category, [])
    if isinstance(urls, str):
        urls = [urls]
    pool_size = max(max_items * 4, 20)
    for url in urls:
        items = _fetch_one_rss(url, pool_size, timeout)
        if items:
            filtered = _filter_by_category(items, category, max_items)
            return {"items": filtered, "timestamp": datetime.now(), "source": url}
    return {"items": [], "timestamp": datetime.now(), "source": None}

def clear_rss_cache():
    """Clear the Streamlit cache for RSS feeds to force a refresh."""
    fetch_rss_feed.clear()


# ============================================================
# RSS 시장 인용 수치 자동 추출 (Phase C)
# 보고서 'Recent Market Commentary' 섹션을 채우는 헬퍼.
# ============================================================

# 숫자 + 단위 패턴 — BESS 시장에서 자주 인용되는 수치 형태
# 예: "$115/kWh", "12.5 GWh", "550 MW", "$5 billion", "30%"
_QUOTE_PATTERNS = [
    re.compile(r"\$\s?\d{1,4}(?:,\d{3})*(?:\.\d+)?\s?/\s?(?:kWh|MWh|Wh)", re.I),
    re.compile(r"\$\s?\d{1,4}(?:,\d{3})*(?:\.\d+)?\s?(?:million|billion|trillion|M|B)\b", re.I),
    re.compile(r"\b\d{1,4}(?:,\d{3})*(?:\.\d+)?\s?(?:GWh|MWh|GW|MW|kWh)\b", re.I),
    re.compile(r"\b\d{1,3}(?:\.\d+)?\s?%\s?(?:CAGR|YoY|year-over-year|growth|increase|decline)?", re.I),
]

# 흥미로운 BESS 시장 키워드 — 헤드라인이 BESS 관련인지 1차 필터
_MARKET_KEYWORDS = re.compile(
    r"\b(BESS|battery storage|energy storage|grid storage|lithium[- ]ion|"
    r"LFP|NMC|cell price|battery price|battery cost|gigafactory|GWh|"
    r"capacity|deploy|installed|pipeline|CAPEX|LCOS|LCOE)\b",
    re.I,
)


def _split_sentences(text: str) -> list[str]:
    """간단한 문장 분리기 (영문 기준)."""
    if not text:
        return []
    # 마침표/물음표/느낌표 뒤 공백 기준 분리
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p and p.strip()]


def _extract_quoted_figures(text: str) -> list[str]:
    """텍스트에서 시장 수치 패턴(예: $115/kWh, 12 GWh)을 매치한 substring 리스트 반환."""
    if not text:
        return []
    matches = []
    for pat in _QUOTE_PATTERNS:
        for m in pat.finditer(text):
            matches.append(m.group(0))
    return matches


def extract_market_commentary(categories: list = None, max_items: int = 8) -> list[dict]:
    """이미 fetch된 RSS feeds에서 시장 인용 수치를 자동 추출.

    Args:
        categories: 검색할 RSS 카테고리 (None이면 RSS_FEEDS 모든 키)
        max_items: 반환할 최대 인용 개수

    Returns:
        [{"quote": "...", "figures": ["$115/kWh", "12 GWh"], "title": "...",
          "url": "...", "pub_date": "...", "source": "..."}]
    """
    if categories is None:
        categories = list(RSS_FEEDS.keys())

    seen_titles = set()
    commentary = []

    for cat in categories:
        try:
            feed = fetch_rss_feed(cat, max_items=10)
        except Exception as e:
            _log.warning("commentary fetch failed for %s: %s", cat, e)
            continue
        for item in feed.get("items", []):
            title = item.get("title") or ""
            if title in seen_titles:
                continue

            haystack = f"{title}. {item.get('description', '')}"
            # BESS 관련 키워드 필터
            if not _MARKET_KEYWORDS.search(haystack):
                continue

            # 수치 패턴 추출
            figures = []
            best_sentence = ""
            for sent in _split_sentences(haystack):
                figs = _extract_quoted_figures(sent)
                if figs:
                    figures.extend(figs)
                    if not best_sentence or len(sent) < len(best_sentence):
                        best_sentence = sent

            if not figures:
                continue

            # 중복 제거 (대소문자/공백 normalize)
            uniq_figs = []
            seen_norm = set()
            for f in figures:
                norm = re.sub(r"\s+", "", f).lower()
                if norm not in seen_norm:
                    seen_norm.add(norm)
                    uniq_figs.append(f.strip())

            seen_titles.add(title)
            commentary.append({
                "quote": best_sentence[:300] if best_sentence else title,
                "figures": uniq_figs[:5],
                "title": title,
                "url": item.get("link", ""),
                "pub_date": item.get("pubDate", ""),
                "source": cat,
            })

            if len(commentary) >= max_items:
                return commentary

    return commentary

# ============================================================
# 환율 / 유가 / 원자재 실시간 데이터
# ============================================================

@st.cache_data(ttl=1800)  # 30분 캐시
def fetch_exchange_rates():
    """USD 기준 환율 조회 (open.er-api.com — 무료, 키 불필요)."""
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            import json
            data = json.loads(resp.read().decode())
        rates = data.get("rates", {})
        return {
            "timestamp": datetime.now(),
            "USD_KRW": rates.get("KRW"),
            "USD_EUR": rates.get("EUR"),
            "USD_JPY": rates.get("JPY"),
            "USD_CNY": rates.get("CNY"),
            "USD_AUD": rates.get("AUD"),
            "USD_GBP": rates.get("GBP"),
            "source": "open.er-api.com",
        }
    except Exception as e:
        return {"timestamp": datetime.now(), "error": str(e), "source": "open.er-api.com"}


@st.cache_data(ttl=1800)  # 30분 캐시
def fetch_commodity_prices():
    """유가·리튬·구리 등 원자재 가격 (cdn.jsdelivr.net 경유 commodities-api fallback)."""
    result = {
        "timestamp": datetime.now(),
        "brent_crude_usd": None,
        "wti_crude_usd": None,
        "lithium_carbonate_usd_ton": None,
        "copper_usd_ton": None,
        "nickel_usd_ton": None,
        "source": None,
    }
    # Primary: fetch from econdb.com open API (no key needed, CORS-friendly)
    try:
        url = "https://www.econdb.com/api/series/RBRTE/?format=json"
        req = urllib.request.Request(url, headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            import json
            data = json.loads(resp.read().decode())
        # Latest data point
        values = data.get("data", {}).get("values", [])
        if values:
            result["brent_crude_usd"] = round(values[-1], 2)
            result["source"] = "econdb.com"
    except Exception:
        pass

    # ── Fallback reference values ────────────────────────────────────
    # 정기 갱신 필요. 갱신 시 _COMMODITY_REF_DATE도 같이 업데이트.
    _COMMODITY_REF_DATE = "2026-07"
    _FALLBACK = {
        "brent_crude_usd": 72.5,
        "wti_crude_usd": 68.8,
        # 출처: TradingEconomics https://tradingeconomics.com/commodity/lithium
        # (2026-07-13 CNY 165,000/t ≈ $23.1k, 6/29 저점 CNY 151,750 반등); 변동성 큼
        "lithium_carbonate_usd_ton": 23000,
        "copper_usd_ton": 9200,
        "nickel_usd_ton": 16800,
    }
    if result["brent_crude_usd"] is None:
        result["brent_crude_usd"] = _FALLBACK["brent_crude_usd"]
        result["wti_crude_usd"] = _FALLBACK["wti_crude_usd"]
        result["source"] = f"reference (as of {_COMMODITY_REF_DATE}, offline)"
    if result["wti_crude_usd"] is None:
        result["wti_crude_usd"] = round(result["brent_crude_usd"] * 0.95, 2)

    # Lithium / Copper / Nickel — 실시간 API 미지원, 참조값 사용
    result["lithium_carbonate_usd_ton"] = _FALLBACK["lithium_carbonate_usd_ton"]
    result["copper_usd_ton"] = _FALLBACK["copper_usd_ton"]
    result["nickel_usd_ton"] = _FALLBACK["nickel_usd_ton"]
    result["metals_source"] = f"reference (as of {_COMMODITY_REF_DATE})"
    return result


# ============================================================
# 시장 데이터 (Built-in Defaults)
# ============================================================

YEARS = [2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030]
_CURRENT_YEAR_DYNAMIC = datetime.now().year


def _build_year_labels(years):
    """실적/추정/전망 라벨을 동적 부여 — 작년까지는 실적, 올해는 추정(E), 미래는 전망(F)."""
    cy = _CURRENT_YEAR_DYNAMIC
    labels = []
    for y in years:
        if y < cy:
            labels.append(str(y))
        elif y == cy:
            labels.append(f"{y}E")
        else:
            labels.append(f"{y}F")
    return labels


YEAR_LABELS = _build_year_labels(YEARS)

# ============================================================
# 데이터 신선도 메타 — 보고서/대시보드에 자동 표시
# 각 카테고리의 마지막 큐레이션 시점과 1차 출처를 명시.
# 갱신 시 이 dict와 해당 상수를 함께 수정.
# ============================================================
DATA_SNAPSHOT_AS_OF = "2026-07-21"
# 2026-07-21 갱신: 전체 카테고리 재검증(WebSearch, BNEF/SEIA/ess-news/CnEVPost/공식 정부발표).
#   글로벌 용량·시장가치·셀가·CAPEX: BNEF 최신 공개치와 일치 재확인(무변경) — 2025 실적
#   112GW/307GWh, 2026F 158GW/459GWh(2026-05 BNEF 재확인), LFP 최저 $36/kWh(2025 실적) 그대로.
#   변경분: COMPETITORS 전면 개편(2026-07-14 ess-news 첫 공식 BESS 통합업체 랭킹 — Sungrow #1
#   신규 등극, BYD 2025 실적 1위 60GWh 반영, CATL 셀 출하 121GWh로 갱신, Honeywell→Envision 교체).
#   호주 pipeline_gwh 97.3→121.3(CIS Tender 7+8 신규 확정분, 2026-05~06).
# 2026-07-19 갱신: 핵심 지표 웹 재검증 — BNEF 1H2026(2026F 158GW/459GWh)·턴키 $117/kWh·
#   미국 Q1 9.7GWh 최신치와 일치 확인(무변경), 리튬 $24k→$23k (TradingEconomics 2026-07-13).
# 2026-06-11 갱신: 글로벌 연간도입·CAPEX·셀가·리튬·지역 2025 실적을 최신 공개통계로 재추정.
# 1차 출처: BNEF Energy Storage Market Outlook 1H2026 (2025=112GW/307GWh, 2026F=158GW/459GWh),
#   BNEF 2025 Battery Price Survey(LFP셀 최저 $36·정치형팩 $70·턴키 $117/kWh),
#   SolarPower Europe(EU 2025 27.1GWh), Energy-Storage.News(UK 4GWh), pv-mag(호주 11.4GWh),
#   IEEFA(일본 0.62GW 연계), Utility Dive/BNEF(미국 18GW/54.6GWh), TradingEconomics(리튬 ~$24.2k/t).

# 최근 분기 실적 — 월간/분기 공개 트래커(현재 시점 앵커). 분기가 바뀌면 반드시 갱신할 것
# (report_local.py의 경과일 경고 로직이 이 period를 기준으로 자동 판정함).
RECENT_QUARTER = {
    "period": "2026 Q1",
    "global_gwh": 126.4,
    "global_yoy_pct": 54,          # 전년동기 대비 (SEIA/ESS-news, 2026-05)
    "us_gwh": 9.7,
    "us_yoy_pct": 32,              # 전년동기 대비, 역대 최대 Q1 (SEIA Energy Storage Outlook Q2 2026)
    "lfp_cell_low_usd_kwh": 47,    # CEEC 7GWh 조달 최저가 (ess-news, 2026-05)
    "source": "SEIA Energy Storage Market Outlook Q2 2026 (2026-05) · ESS-News/CEEC",
}

DATA_FRESHNESS = {
    "global_market": {
        "label": "글로벌 시장 규모 (capacity/value/price/CAPEX)",
        "as_of": "2026-05-15",
        "source": "BloombergNEF Energy Storage Outlook + Lithium-ion Battery Price Survey + Wood Mackenzie ESS Service",
        "type": "snapshot",
        "note": "분기별 큐레이션. 실제 라이브 갱신은 Phase B의 EIA/IEA 어댑터에서 일부 지표만 가능.",
    },
    "regional": {
        "label": "지역별 설치 용량·파이프라인·점유율",
        "as_of": "2026-05-15",
        "source": "BNEF Regional Outlook, IEA Energy Storage Tracker, 각국 정부 통계(EIA·KPX·METI·AEMO·NESO·ENTSO-E)",
        "type": "snapshot",
        "note": "Phase B에서 US 데이터는 EIA API로 라이브 갱신 시도.",
    },
    "competitors": {
        "label": "경쟁사 매출·점유율·생산능력",
        "as_of": "2026-04",
        "source": "SNE Research Global ESS Tracker, 각사 IR/연차 보고서, S&P Global Market Intelligence",
        "type": "snapshot",
    },
    "scenarios": {
        "label": "시나리오 분석 (Base/Bull/Bear)",
        "as_of": "2026-05-15",
        "source": "내부 시나리오 모델 (BNEF·IEA·McKinsey 자료 종합)",
        "type": "model",
    },
    "revenue_stacking": {
        "label": "지역별 수익 스태킹 구조",
        "as_of": "2026-04",
        "source": "Modo Energy, Aurora Research, Wood Mac Energy Storage Service, 각국 ISO 공시",
        "type": "snapshot",
    },
    "investment": {
        "label": "프로젝트 투자 경제성 (IRR/Payback/LCOE)",
        "as_of": "2026-04",
        "source": "Lazard LCOS, NREL ATB, BNEF Cost Survey",
        "type": "snapshot",
    },
    "operations": {
        "label": "운영·O&M·EMS",
        "as_of": "2026-03",
        "source": "EPRI ESIC, DNV Storage Services, 제조사 공개 자료",
        "type": "snapshot",
    },
    "safety": {
        "label": "안전·화재·표준 (NFPA 855, UL 9540, KS C 8564 등)",
        "as_of": "2026-05",
        "source": "NFPA, UL, IEC, KS, AS/NZS 공식 발행본 (최신 개정 추적)",
        "type": "regulatory",
        "note": "표준은 발행본이 최신본 그대로 인용 — 개정 시점만 갱신.",
    },
    "fire_incidents": {
        "label": "BESS 화재 사고 사례",
        "as_of": "2026-05-15",
        "source": "EPRI BESS Failure Incident Database, 보도자료, 사고조사 보고서",
        "type": "case_log",
    },
    "battery_tech": {
        "label": "배터리 기술 동향 (LFP/NMC/Na-ion/SSB/VRFB/Fe-Air)",
        "as_of": "2026-04",
        "source": "BNEF Battery Technology Outlook, IEA Battery Storage Roadmap, 각사 R&D 발표",
        "type": "snapshot",
    },
    "ldes": {
        "label": "장기 저장(LDES) 시장",
        "as_of": "2026-04",
        "source": "DOE LDES Initiative, LDES Council (McKinsey), Form Energy/ESS Inc. 등 IR",
        "type": "snapshot",
    },
    "permitting": {
        "label": "지역별 인허가·계통연계 데이터",
        "as_of": "2026-03",
        "source": "LBNL Queued Up 보고서(미국), Ofgem/NESO(영국), AEMO ISP(호주), 각국 TSO 공시",
        "type": "snapshot",
    },
    "financing": {
        "label": "프로젝트 파이낸싱·보험",
        "as_of": "2026-03",
        "source": "Inframation, IJ Global, 주요 인프라 펀드 IR (Blackrock·Brookfield·Macquarie)",
        "type": "snapshot",
    },
    "epc_contracts": {
        "label": "EPC 계약 구조·원가 분해",
        "as_of": "2026-03",
        "source": "BNEF Cost Survey, Wood Mac Project Cost Service, 시장 통설 종합",
        "type": "snapshot",
    },
    "fx_rates": {
        "label": "환율 (USD/KRW·JPY·EUR·CNY·GBP·AUD)",
        "as_of": "live",
        "source": "open.er-api.com (현재값) + Frankfurter/ECB 기준환율 (월별 추이)",
        "type": "live_api",
        "note": "보고서 생성 시점에 실시간 fetch. 월별 추이 차트는 ECB 공식 기준환율 기반.",
    },
    "commodities": {
        "label": "원자재 (Brent·WTI·리튬·구리·니켈)",
        "as_of": "2026-Q1",
        "source": "econdb(Brent, 가용 시) + 참조값(금속: 무료 실시간 공개 시세 부재로 분기 큐레이션)",
        "type": "reference",
        "note": "리튬·구리·니켈은 무료 실시간 API가 없어 분기 참조값. Brent는 공개 API 가용 시 갱신, 실패 시 참조값.",
    },
    "news_rss": {
        "label": "산업 뉴스 헤드라인",
        "as_of": "live",
        "source": "Energy-Storage.News, Electrek, PV-Tech, CleanTechnica, Recharge News, Utility Dive, RenewEconomy",
        "type": "live_rss",
        "note": "각 카테고리 fetch 시 실시간 갱신.",
    },
}


def get_data_freshness_summary() -> dict:
    """대시보드/보고서에 표시할 요약 dict를 반환.

    Returns:
        {
            "snapshot_as_of": "2026-05-15",
            "oldest_section": ("operations", "2026-03"),
            "newest_section": ("global_market", "2026-05-15"),
            "live_sections": ["fx_commodity", "news_rss"],
            "all_sections": [{...}, ...],
        }
    """
    static_items = [
        (k, v) for k, v in DATA_FRESHNESS.items()
        if v.get("type") not in ("live_api", "live_rss")
    ]
    static_dates = [(k, v["as_of"]) for k, v in static_items]
    static_dates.sort(key=lambda x: x[1])

    live_sections = [
        k for k, v in DATA_FRESHNESS.items()
        if v.get("type") in ("live_api", "live_rss")
    ]

    return {
        "snapshot_as_of": DATA_SNAPSHOT_AS_OF,
        "oldest_section": static_dates[0] if static_dates else None,
        "newest_section": static_dates[-1] if static_dates else None,
        "live_sections": live_sections,
        "all_sections": [{"key": k, **v} for k, v in DATA_FRESHNESS.items()],
    }


# ---- 글로벌 연간 도입량 (GWh/yr) — 누적 아님, 당해 연도 신규 도입 ----
# 2022-2025 BNEF 실적, 2026 BNEF 전망, 2027-2030 외삽(연 ~15-20%, 불확실).
# 출처: BNEF ESMO 1H2026 — 2022:35·2023:99·2024:170·2025:307 GWh, 2026F:459 GWh.
GLOBAL_CAPACITY_GWH = {
    2022: 35,
    2023: 99,
    2024: 170,
    2025: 307,
    2026: 459,
    2027: 560,
    2028: 660,
    2029: 760,
    2030: 860,
}

# ---- 글로벌 턴키 시스템 시장 규모 추정 (B USD) = 연간도입(GWh) × 턴키단가($/kWh) / 1000 ----
GLOBAL_MARKET_VALUE_B_USD = {
    2022: 10.5,
    2023: 22.8,
    2024: 28.1,
    2025: 35.9,
    2026: 48.2,
    2027: 54.3,
    2028: 59.4,
    2029: 63.8,
    2030: 68.8,
}

# ---- LFP 셀 가격 $/kWh — BNEF 2025: LFP셀 최저 $36·LFP팩 $81·정치형팩 $70 ----
LFP_CELL_PRICE = {
    2022: 95,
    2023: 75,
    2024: 58,
    2025: 45,
    2026: 40,
    2027: 35,
    2028: 31,
    2029: 28,
    2030: 25,
}

# ---- 시스템 CAPEX (턴키 4h, 글로벌 평균 $/kWh) — BNEF 2025=$117, Ember ~$125 ----
SYSTEM_CAPEX = {
    2022: 300,
    2023: 230,
    2024: 165,
    2025: 117,
    2026: 105,
    2027: 97,
    2028: 90,
    2029: 84,
    2030: 80,
}

# ---- NMC 셀 가격 $/kWh (참고) — BNEF 2025 NMC팩 $128 ----
NMC_CELL_PRICE = {
    2022: 120,
    2023: 98,
    2024: 88,
    2025: 82,
    2026: 74,
    2027: 66,
    2028: 59,
    2029: 53,
    2030: 48,
}

# ---- 지역별 데이터 ----
REGIONAL_DATA = {
    "한국": {
        "name_en": "South Korea",
        "installed_gwh": {2022: 1.5, 2023: 2.5, 2024: 3.5, 2025: 5.0, 2026: 7.0, 2027: 9.5, 2028: 12.5, 2029: 16.0, 2030: 20.0},
        "pipeline_gwh": 25.0,
        "market_share_pct": 1.6,
        "key_drivers": [
            "재생에너지 확대 정책 (2030 RE 30%)",
            "전력거래소 주파수조정(FR) 시장",
            "피크 저감 및 전력 품질 개선 수요",
            "제주도 풍력 출력제한 대응",
            "탄소중립 2050 로드맵",
        ],
        "revenue_model": "주파수조정(FR), 피크저감, 에너지 차익거래, 재생에너지 연계",
        "policy": [
            "ESS 설치 의무화 (신재생 연계)",
            "전력시장 보조서비스 확대",
            "ESS 화재 안전기준 강화 (KS C 8564)",
            "한전 ESS 요금제도 개편",
            "K-RE100 이행 지원",
        ],
        "key_players": ["삼성SDI", "LG에너지솔루션", "SK온", "한화에너지", "두산에너바일리티"],
        "avg_project_size_mwh": 50,
        "growth_rate_pct": 38,
    },
    "일본": {
        "name_en": "Japan",
        # 2026-07-21 재검증: 2026년 연간 도입 전망 2.5~3.5GWh(시장조사기관, BNEF급 공신력은
        # 아님) 범위 내 하단에 위치 — 현재값(2.5) 유지, 그리드스케일 연 1GW+ 목표(2026~)는
        # policy에 반영.
        "installed_gwh": {2022: 0.15, 2023: 0.2, 2024: 0.3, 2025: 1.2, 2026: 2.5, 2027: 4.5, 2028: 7.0, 2029: 10.0, 2030: 14.0},
        "pipeline_gwh": 30.0,
        "market_share_pct": 0.4,
        "key_drivers": [
            "2050 탄소중립 선언",
            "재생에너지 FIT/FIP 전환",
            "용량시장(Capacity Market) 도입",
            "노후 화력 대체 수요",
            "섬 지역 마이크로그리드",
        ],
        "revenue_model": "FIT/FIP 연계, 용량시장, 수급조정시장, 피크 저감",
        "policy": [
            "제6차 에너지기본계획",
            "FIP(Feed-in Premium) 제도",
            "용량시장 2024년 본격 운영",
            "축전지 보조금 제도",
            "화재 안전 규정 (소방법)",
        ],
        "key_players": ["Sumitomo Electric", "NGK Insulators", "Panasonic", "Tesla", "BYD"],
        "avg_project_size_mwh": 40,
        "growth_rate_pct": 42,
    },
    "미국": {
        "name_en": "United States",
        # 2026-07-21 재검증(SEIA/Benchmark Mineral Intelligence): 2025 실적 55.0GWh(18GW)
        # BNEF·Utility Dive 교차치와 일치, Q1 2026 9.7GWh(+32%YoY, 역대 최대 분기)도
        # RECENT_QUARTER와 일치 — 연도별 궤적 무변경. SEIA는 2030 누적 610GWh+ 를
        # "상향 조정"이라 발표(본 표 누적합 725GWh로 이미 상회 — 과소평가 아님, 무변경 유지).
        "installed_gwh": {2022: 18.0, 2023: 26.0, 2024: 37.0, 2025: 55.0, 2026: 73.0, 2027: 93.0, 2028: 115.0, 2029: 140.0, 2030: 168.0},
        "pipeline_gwh": 180.0,
        "market_share_pct": 18.0,
        "key_drivers": [
            "IRA(Inflation Reduction Act) ITC 30-50%",
            "CAISO/ERCOT/PJM 전력시장 수익",
            "태양광+ESS 하이브리드 확대",
            "극한 기후 대비 전력 안정성",
            "데이터센터/AI 전력수요 급증",
        ],
        "revenue_model": "에너지 차익거래, 용량시장, 보조서비스, ITC/PTC 세제혜택, 태양광+ESS 번들",
        "policy": [
            "IRA - ITC 30% (독립형 ESS 포함)",
            "IRA - 국내 제조 보너스 10%",
            "캘리포니아 SB 100 (2045 100% RE)",
            "FERC Order 2222 (DER 시장참여)",
            "각 주별 ESS 설치 목표",
        ],
        "key_players": ["Tesla", "Fluence", "NextEra Energy", "AES", "Vistra", "Plus Power"],
        "avg_project_size_mwh": 400,
        "growth_rate_pct": 50,
    },
    "호주": {
        "name_en": "Australia",
        # 2026-07-21 재검증: CIS Tender 7(2026-05-23, 2.0GW/7.9GWh, 19개 프로젝트) +
        # Tender 8(2026-06-24, 4.2GW/16.1GWh, 15개 프로젝트, 역대 최대 단일 조달) 신규 확정분
        # 반영해 97.3 → 121.3GWh로 갱신. NEM 계통연계 대기 중인 용량은 45GW(2026년 초 기준,
        # infrastructureaustralia.gov.au)로 별도 지표(파이프라인보다 넓은 선행 지표).
        "installed_gwh": {2022: 3.2, 2023: 5.5, 2024: 8.3, 2025: 11.4, 2026: 12.9, 2027: 16.0, 2028: 20.0, 2029: 25.0, 2030: 30.0},
        "pipeline_gwh": 121.3,
        "market_share_pct": 3.7,
        "key_drivers": [
            "석탄발전 퇴출 가속화",
            "NEM(National Electricity Market) 변동성",
            "대규모 VPP(Virtual Power Plant)",
            "주택용 태양광+ESS 보급 (2026년 가정용 배터리 12GWh+ 누적)",
            "2030 재생에너지 82% 목표",
        ],
        "revenue_model": "FCAS(주파수조정), 에너지 차익거래, 용량결제, VPP, 네트워크 지원",
        "policy": [
            "Capacity Investment Scheme — Tender 8(2026-06) 역대 최대 4.2GW/16.1GWh 낙찰, Tender 10 진행 중(2026-08-18 마감)",
            "ARENA 보조금 프로그램",
            "NEM 용량시장 도입 논의",
            "각 주별 재생에너지 목표",
            "가정용 배터리 보조금(연방 정부, 2026년 42만+ 가구 설치)",
        ],
        "key_players": ["Neoen", "AGL Energy", "Origin Energy", "Tesla", "Sungrow"],
        "avg_project_size_mwh": 300,
        "growth_rate_pct": 45,
    },
    "영국": {
        "name_en": "United Kingdom",
        "installed_gwh": {2022: 1.8, 2023: 2.4, 2024: 3.1, 2025: 4.0, 2026: 5.2, 2027: 6.5, 2028: 8.0, 2029: 9.5, 2030: 11.0},
        "pipeline_gwh": 35.0,
        "market_share_pct": 1.3,
        "key_drivers": [
            "2035 전력 탈탄소화 목표",
            "풍력(해상) 확대에 따른 유연성 수요",
            "보조서비스 수익 모델 다양화",
            "Cap & Floor 수익 안정 메커니즘",
            "EFR/DC/DM/FFR 시장 성장",
        ],
        # 2026-07-21 재검증: Q1 2026 기준 GB 전체 7.2GW 가동(소스별 11.8~18GWh로 상이 —
        # 방법론 차이로 단일 수치 확정 어려워 연도별 궤적은 보수적으로 유지, 정책만 갱신).
        # Clean Power 2030 목표 23~27GW로 상향, 단 grid 연결 대기열(221GW)이 목표 대비
        # 과잉이라 NESO가 2026년 중 Gate 2 확정 오퍼로 대대적 정리 진행 중.
        "revenue_model": "Dynamic Containment, FFR, T-4 용량시장, 에너지 차익거래, Balancing Mechanism",
        "policy": [
            "Net Zero Strategy 2050",
            "Contracts for Difference (CfD)",
            "용량시장 (Capacity Market T-4)",
            "REMA (전력시장개혁) 검토",
            "그리드 연결 대기열 정리(NESO Gate 2, 2026년 중 확정 오퍼 발급) — Clean Power 2030 목표 23~27GW",
        ],
        "key_players": ["Gresham House", "Gore Street", "Harmony Energy", "Zenobe", "EDF"],
        "avg_project_size_mwh": 100,
        "growth_rate_pct": 40,
    },
    "EU": {
        "name_en": "European Union",
        # 2026-07-21 재검증(SolarPower Europe): 2025 실적 27.1GWh 정확히 일치(무변경).
        # 2026 전망은 기존 37.0 → 50.0으로 상향(SolarPower Europe "2026년 50GWh 초과 전망"),
        # 2030 138GWh 목표치에 맞춰 2027~2029 보간 재추정.
        "installed_gwh": {2022: 7.0, 2023: 12.0, 2024: 18.7, 2025: 27.1, 2026: 50.0, 2027: 68.0, 2028: 88.0, 2029: 112.0, 2030: 138.0},
        "pipeline_gwh": 80.0,
        "market_share_pct": 9.0,
        "key_drivers": [
            "REPowerEU 에너지 독립 가속",
            "EU 에너지저장 목표 (2030 200GW)",
            "독일 Energiewende 유연성 확보",
            "이탈리아/스페인 태양광+ESS",
            "전력시장 설계 개혁",
        ],
        "revenue_model": "보조서비스(FCR/aFRR), 에너지 차익거래, 용량시장, 태양광 연계, 네트워크 혼잡 관리",
        "policy": [
            "EU Battery Regulation (2027 시행)",
            "REPowerEU 에너지저장 강조",
            "Fit for 55 패키지",
            "각국 에너지저장 목표 설정",
            "탄소국경조정메커니즘(CBAM)",
        ],
        "key_players": ["Fluence", "BYD", "Sungrow", "Wärtsilä", "NEC ES", "CATL"],
        "avg_project_size_mwh": 150,
        "growth_rate_pct": 44,
    },
    "중동": {
        "name_en": "Middle East",
        "installed_gwh": {2022: 0.5, 2023: 1.2, 2024: 3.0, 2025: 6.0, 2026: 9.5, 2027: 14.0, 2028: 19.0, 2029: 25.0, 2030: 32.0},
        # 2026-07-21 재검증: 사우디 BESS 프로그램 Group 2(3GW/12GWh, 27개 개발사 예비심사
        # 통과, 2026-07-03) + UAE Masdar 태양광 5.2GW 연계 19GWh BESS(세계 최초급) 신규
        # 확정분 반영해 35.0 → 45.0으로 상향. 사우디 자체 2030 대형 BESS 목표만 48GWh로,
        # 지역 전체 installed_gwh 2030(32.0)을 이미 상회 — 연도별 궤적은 지역 통합
        # 공신력 있는 소스(BNEF/IEA 등) 확보 전까지 보수적으로 유지, 파이프라인만 우선 갱신.
        "pipeline_gwh": 45.0,
        "market_share_pct": 2.0,
        "key_drivers": [
            "사우디 Vision 2030 (50% RE 목표)",
            "UAE Net Zero 2050",
            "대규모 태양광+ESS 프로젝트 (Masdar 19GWh 세계 최초급 등)",
            "피크 수요 관리 (냉방 부하)",
            "석유 의존도 탈피 전략",
        ],
        "revenue_model": "PPA/BOO 모델, 피크 저감, 태양광+ESS 하이브리드, 정부 프로젝트 입찰",
        "policy": [
            "사우디 NREP (재생에너지 프로그램) — BESS 대형 입찰 Group 2(3GW/12GWh) 2026-07 예비심사 완료",
            "UAE IRENA 협력 프레임워크",
            "카타르 National Vision 2030",
            "오만 Green Hydrogen 전략",
            "이집트 EETC 입찰 프로그램",
        ],
        "key_players": ["ACWA Power", "Masdar", "ENGIE", "EDF", "CATL", "BYD"],
        "avg_project_size_mwh": 500,
        "growth_rate_pct": 75,
    },
}

REGIONS = list(REGIONAL_DATA.keys())

def _latest_actual_year() -> int:
    """현재 연도 기준으로 데이터가 있는 가장 최근 실적 연도를 동적으로 반환."""
    candidate = datetime.now().year - 1
    while candidate > 2022 and candidate not in GLOBAL_CAPACITY_GWH:
        candidate -= 1
    return candidate

LATEST_ACTUAL_YEAR = _latest_actual_year()


def derive_project_status(project_year: int, reference_year: int = None) -> str:
    """프로젝트 COD 연도 vs 기준 연도로 상태를 동적 도출.
    reference_year ≥ project_year → '운영중'
    reference_year + 1 == project_year → '건설중'
    그 외(미래) → '계획중'
    """
    if reference_year is None:
        reference_year = LATEST_ACTUAL_YEAR
    if project_year <= reference_year:
        return "운영중"
    if project_year == reference_year + 1:
        return "건설중"
    return "계획중"


def project_pipeline_with_status(reference_year: int = None):
    """PROJECT_PIPELINE을 현재 기준 연도에 맞춰 status가 동적 계산된 사본으로 반환."""
    if reference_year is None:
        reference_year = LATEST_ACTUAL_YEAR
    out = []
    for p in PROJECT_PIPELINE:
        q = dict(p)
        q["status"] = derive_project_status(p["year"], reference_year)
        out.append(q)
    return out


# ---- 주요 프로젝트 파이프라인 ----
PROJECT_PIPELINE = [
    {"name": "Edwards & Sanborn", "region": "미국", "capacity_mw": 3287, "capacity_mwh": 13148, "status": "운영중", "developer": "Terra-Gen", "year": 2024},
    {"name": "Moss Landing Phase III", "region": "미국", "capacity_mw": 750, "capacity_mwh": 3000, "status": "운영중", "developer": "Vistra", "year": 2024},
    {"name": "Gateway (Gemini Solar)", "region": "미국", "capacity_mw": 690, "capacity_mwh": 2760, "status": "운영중", "developer": "Primergy Solar", "year": 2024},
    {"name": "Victorian Big Battery", "region": "호주", "capacity_mw": 600, "capacity_mwh": 2400, "status": "건설중", "developer": "Neoen", "year": 2025},
    {"name": "Waratah Super Battery", "region": "호주", "capacity_mw": 850, "capacity_mwh": 1700, "status": "운영중", "developer": "Akaysha Energy", "year": 2024},
    {"name": "Shuqaiq ESS", "region": "중동", "capacity_mw": 1000, "capacity_mwh": 4000, "status": "계획중", "developer": "ACWA Power", "year": 2026},
    {"name": "신안 태양광+ESS", "region": "한국", "capacity_mw": 200, "capacity_mwh": 800, "status": "건설중", "developer": "한전/SK", "year": 2025},
    {"name": "제주 FR ESS", "region": "한국", "capacity_mw": 150, "capacity_mwh": 600, "status": "운영중", "developer": "한전", "year": 2024},
    {"name": "Hokkaido Wind+ESS", "region": "일본", "capacity_mw": 300, "capacity_mwh": 1200, "status": "건설중", "developer": "Sumitomo", "year": 2026},
    {"name": "Pillswood BESS", "region": "영국", "capacity_mw": 196, "capacity_mwh": 392, "status": "운영중", "developer": "Harmony Energy", "year": 2024},
    {"name": "BESS de Fos", "region": "EU", "capacity_mw": 320, "capacity_mwh": 640, "status": "건설중", "developer": "TotalEnergies", "year": 2025},
    {"name": "Lago Escondido", "region": "미국", "capacity_mw": 600, "capacity_mwh": 2400, "status": "건설중", "developer": "Intersect Power", "year": 2025},
    {"name": "NEOM Green ESS", "region": "중동", "capacity_mw": 500, "capacity_mwh": 2000, "status": "계획중", "developer": "NEOM/ACWA", "year": 2027},
    {"name": "Lünen BESS", "region": "EU", "capacity_mw": 250, "capacity_mwh": 500, "status": "운영중", "developer": "RWE", "year": 2024},
    {"name": "Cottam BESS", "region": "영국", "capacity_mw": 500, "capacity_mwh": 1000, "status": "건설중", "developer": "EDF", "year": 2026},
    {"name": "큰솔라 ESS", "region": "한국", "capacity_mw": 100, "capacity_mwh": 400, "status": "건설중", "developer": "두산에너바일리티", "year": 2025},
    {"name": "Osaka Grid Battery", "region": "일본", "capacity_mw": 200, "capacity_mwh": 800, "status": "계획중", "developer": "Kansai Electric", "year": 2026},
    {"name": "Hornsdale Phase 3", "region": "호주", "capacity_mw": 300, "capacity_mwh": 900, "status": "계획중", "developer": "Neoen", "year": 2026},
]

# ---- 경쟁사 데이터 ----
# 2026-07-21 재검증: 2025 실적(시스템 출하량 기준, ~460GWh 글로벌 시장, ess-news/electrek)과
# 2026 신규 발표된 첫 공식 BESS 통합업체 랭킹(Sungrow #1·Tesla #2·CATL #3·BYD #4·Envision/Trina 공동5위,
# ess-news 2026-07-14)으로 순위·수치 갱신. CATL capacity_gwh는 셀 출하량 기준(121GWh, 5년 연속 1위,
# 글로벌 셀 점유율 약 39%, CnEVPost) — 시스템 통합 순위(3위)와 다른 지표이므로 strength에 별도 표기.
COMPETITORS = [
    {"name": "Sungrow", "country": "중국", "type": "PCS/시스템", "market_share_pct": 9.0, "revenue_b_usd": 4.2, "capacity_gwh": 43, "strength": "2026 글로벌 BESS 통합업체 1위(ess-news 첫 공식 랭킹), PCS 기술·가격 경쟁력", "weakness": "브랜드 인지도(서방)"},
    {"name": "BYD", "country": "중국", "type": "셀/시스템", "market_share_pct": 13.0, "revenue_b_usd": 9.5, "capacity_gwh": 60, "strength": "2025 시스템 출하 1위(60GWh, Tesla 추월), 수직 계열화, Blade Battery 안전성", "weakness": "미국 시장 진입 장벽, 2026 랭킹 4위로 하락"},
    {"name": "Tesla (Megapack)", "country": "미국", "type": "시스템", "market_share_pct": 10.2, "revenue_b_usd": 7.5, "capacity_gwh": 47, "strength": "2025 출하 +49%YoY, 브랜드·SW 통합(Autobidder), 2026 랭킹 2위", "weakness": "높은 가격, 납기 지연"},
    {"name": "CATL", "country": "중국", "type": "셀/시스템", "market_share_pct": 22.0, "revenue_b_usd": 14.0, "capacity_gwh": 121, "strength": "셀 출하 5년 연속 1위(121GWh, 글로벌 셀 점유율 약 39%), 2026 시스템 통합 랭킹 3위 신규 진입", "weakness": "지정학적 리스크, 셀·시스템 이중 포지셔닝"},
    {"name": "Samsung SDI", "country": "한국", "type": "셀", "market_share_pct": 6.5, "revenue_b_usd": 3.8, "capacity_gwh": 12, "strength": "NMC 기술력, 미국/유럽 공장", "weakness": "LFP 라인업 후발"},
    {"name": "LG Energy Solution", "country": "한국", "type": "셀", "market_share_pct": 5.5, "revenue_b_usd": 3.2, "capacity_gwh": 10, "strength": "글로벌 생산 네트워크, 2026 통합업체 톱10 진입", "weakness": "ESS 전용 투자 제한적"},
    {"name": "Fluence", "country": "미국", "type": "시스템", "market_share_pct": 7.0, "revenue_b_usd": 3.5, "capacity_gwh": 16, "strength": "SW 플랫폼(Mosaic), Siemens/AES 백업", "weakness": "수익성 미확보"},
    {"name": "Wärtsilä", "country": "핀란드", "type": "시스템", "market_share_pct": 3.0, "revenue_b_usd": 1.5, "capacity_gwh": 7, "strength": "EPC 경험, GEMS 플랫폼", "weakness": "셀 외부 조달 의존"},
    {"name": "Envision", "country": "중국", "type": "셀/시스템", "market_share_pct": 4.0, "revenue_b_usd": 2.0, "capacity_gwh": 9, "strength": "2026 통합업체 랭킹 공동 5위 신규 진입, 재생에너지 통합 역량", "weakness": "서방 트랙레코드 제한적"},
    {"name": "EVE Energy", "country": "중국", "type": "셀", "market_share_pct": 5.0, "revenue_b_usd": 2.2, "capacity_gwh": 10, "strength": "LFP 대형셀 경쟁력, 가격", "weakness": "글로벌 트랙레코드"},
]

# ---- 시나리오 분석 데이터 ----
# 2026-07-21 재검증: 기존 시나리오 기준선(예: 기본 시나리오 2025년 150GWh)이 6월 BNEF
# 대개정(GLOBAL_CAPACITY_GWH 2025 실적 200→307GWh) 이후 갱신이 안 돼, 본문 실적(307GWh)의
# 절반도 안 되는 수치가 그대로 남아있었음(9장 시나리오 차트가 나머지 본문과 모순).
# 2024·2025는 3개 시나리오 모두 이미 확정된 실적(GLOBAL_CAPACITY_GWH/VALUE와 동일값)으로
# 통일하고, 불확실성은 2026년 이후 미래 구간에만 반영해 분기시키는 방식으로 재설계.
# 기본(Base) 시나리오는 GLOBAL_CAPACITY_GWH·GLOBAL_MARKET_VALUE_B_USD와 완전히 동일.
SCENARIOS = {
    "보수적 (Conservative)": {
        "description": "글로벌 경기 둔화, 정책 지연, 공급망 불안정",
        "capacity_gwh": {2024: 170, 2025: 307, 2026: 370, 2027: 425, 2028: 480, 2029: 535, 2030: 590},
        "market_value_b": {2024: 28.1, 2025: 35.9, 2026: 40, 2027: 44, 2028: 48, 2029: 52, 2030: 56},
        "cell_price": {2024: 58, 2025: 45, 2026: 42, 2027: 39, 2028: 37, 2029: 35, 2030: 33},
        "cagr_pct": 23,
    },
    "기본 (Base)": {
        "description": "현재 정책 유지, 기술 발전 지속, 안정적 성장",
        "capacity_gwh": {2024: 170, 2025: 307, 2026: 459, 2027: 560, 2028: 660, 2029: 760, 2030: 860},
        "market_value_b": {2024: 28.1, 2025: 35.9, 2026: 48.2, 2027: 54.3, 2028: 59.4, 2029: 63.8, 2030: 68.8},
        "cell_price": {2024: 55, 2025: 45, 2026: 40, 2027: 35, 2028: 31, 2029: 28, 2030: 25},
        "cagr_pct": 31,
    },
    "낙관적 (Optimistic)": {
        "description": "강력한 정책 지원, 기술 혁신 가속, 수요 폭증",
        "capacity_gwh": {2024: 170, 2025: 307, 2026: 530, 2027: 680, 2028: 830, 2029: 1000, 2030: 1200},
        "market_value_b": {2024: 28.1, 2025: 35.9, 2026: 56, 2027: 68, 2028: 80, 2029: 92, 2030: 105},
        "cell_price": {2024: 53, 2025: 45, 2026: 38, 2027: 32, 2028: 27, 2029: 24, 2030: 21},
        "cagr_pct": 39,
    },
}

# ---- BESS 사업 개발 및 수익 모델 데이터 ----
REVENUE_STACKING = {
    "미국": {
        "energy_arbitrage": {"share_pct": 35, "avg_revenue_kwh_yr": 45, "trend": "상승",
                             "desc": "CAISO/ERCOT 일중 가격 스프레드 확대로 차익거래 수익 증가. 특히 ERCOT 실시간 가격 변동성이 높아 4시간 BESS 기준 $40-55/kWh/yr 수익 가능."},
        "capacity_market": {"share_pct": 25, "avg_revenue_kwh_yr": 30, "trend": "안정",
                            "desc": "PJM Capacity Market, CAISO RA(Resource Adequacy) 등 용량 결제 안정적. 연간 $25-35/kWh 수준."},
        "ancillary_services": {"share_pct": 20, "avg_revenue_kwh_yr": 25, "trend": "하락",
                               "desc": "주파수조정(Regulation), 스피닝 리저브 시장. BESS 참여 증가로 단가 하락 추세."},
        "itc_ptc": {"share_pct": 15, "avg_revenue_kwh_yr": 20, "trend": "안정",
                    "desc": "IRA ITC 30%(독립형 ESS 포함) + 국내 제조 보너스 10% + 에너지 커뮤니티 10%. 최대 50% ITC 가능."},
        "tolling_ppa": {"share_pct": 5, "avg_revenue_kwh_yr": 8, "trend": "상승",
                        "desc": "유틸리티/C&I 대상 장기 Tolling Agreement 또는 PPA 구조. 10-15년 장기 계약으로 프로젝트 파이낸싱 안정화."},
    },
    "영국": {
        "ancillary_services": {"share_pct": 40, "avg_revenue_kwh_yr": 50, "trend": "변동",
                               "desc": "Dynamic Containment(DC), Dynamic Regulation(DR), Dynamic Moderation(DM) 등 주파수 응답 시장. DC 단가 변동폭 크나 고수익 가능."},
        "capacity_market": {"share_pct": 25, "avg_revenue_kwh_yr": 28, "trend": "상승",
                            "desc": "T-4 용량시장 경매 참여. 1시간 이상 duration 요구. 2024년 이후 de-rating 강화로 4시간 BESS 유리."},
        "energy_arbitrage": {"share_pct": 25, "avg_revenue_kwh_yr": 30, "trend": "상승",
                             "desc": "Wholesale market 일중 스프레드 + Balancing Mechanism(BM) 참여. 풍력 간헐성 증가로 스프레드 확대."},
        "balancing_mechanism": {"share_pct": 10, "avg_revenue_kwh_yr": 15, "trend": "상승",
                                "desc": "National Grid ESO Balancing Mechanism 참여. 실시간 수급 조정 시장으로 BESS에 유리."},
    },
    "호주": {
        "fcas": {"share_pct": 35, "avg_revenue_kwh_yr": 55, "trend": "변동",
                 "desc": "FCAS(Frequency Control Ancillary Services) 8개 시장 참여. 특히 Fast FCAS(6초/60초)에서 BESS 높은 수익 달성."},
        "energy_arbitrage": {"share_pct": 30, "avg_revenue_kwh_yr": 40, "trend": "상승",
                             "desc": "NEM 스팟시장 가격 변동성 극대화 활용. 석탄 퇴출 가속으로 가격 스파이크 빈도 증가."},
        "capacity_payment": {"share_pct": 20, "avg_revenue_kwh_yr": 25, "trend": "상승",
                             "desc": "Capacity Investment Scheme(CIS) 통한 장기 수익 계약. 연방정부 주도 역경매 방식."},
        "network_support": {"share_pct": 15, "avg_revenue_kwh_yr": 18, "trend": "안정",
                            "desc": "TNSP/DNSP 네트워크 지원 계약. 송배전 혼잡 해소, 전압 조정 서비스 제공."},
    },
    "한국": {
        "frequency_regulation": {"share_pct": 50, "avg_revenue_kwh_yr": 35, "trend": "안정",
                                 "desc": "전력거래소 주파수조정(FR) 시장이 BESS 주요 수익원. SMP+용량요금 구조. 한전 ESS 요금제 개편에 따른 변동 가능성."},
        "peak_shaving": {"share_pct": 25, "avg_revenue_kwh_yr": 20, "trend": "안정",
                         "desc": "피크 시간대 수요 저감을 통한 전력요금 절감. 산업용/상업용 수요처 대상."},
        "re_integration": {"share_pct": 15, "avg_revenue_kwh_yr": 12, "trend": "상승",
                           "desc": "재생에너지 출력 제한 대응 및 연계 ESS. 제주도 풍력 커튼먼트 해소 중심."},
        "energy_trading": {"share_pct": 10, "avg_revenue_kwh_yr": 8, "trend": "상승",
                           "desc": "에너지 차익거래 시장 초기 단계. 전력시장 개편(실시간 시장 도입)에 따라 성장 전망."},
    },
    "EU": {
        "ancillary_services": {"share_pct": 35, "avg_revenue_kwh_yr": 42, "trend": "안정",
                               "desc": "FCR(주파수 억제 예비력), aFRR(자동 주파수 복원 예비력) 시장 참여. 독일 FCR 시장이 가장 활발."},
        "energy_arbitrage": {"share_pct": 30, "avg_revenue_kwh_yr": 35, "trend": "상승",
                             "desc": "Day-ahead/Intraday 시장 가격차 활용. 재생에너지 비중 증가로 음전가(Negative price) 빈도 증가 → 저가 충전 기회."},
        "capacity_mechanism": {"share_pct": 20, "avg_revenue_kwh_yr": 22, "trend": "상승",
                               "desc": "이탈리아 Capacity Market, 프랑스 Mécanisme de Capacité, 폴란드 용량시장 등 각국 개별 운영."},
        "congestion_mgmt": {"share_pct": 15, "avg_revenue_kwh_yr": 15, "trend": "상승",
                            "desc": "송전망 혼잡 관리(Redispatch) 및 DSO 유연성 시장. 분산 BESS의 새로운 수익원으로 부상."},
    },
}

# ---- BESS 사업 투자 경제성 데이터 ----
INVESTMENT_ECONOMICS = {
    "4h_utility": {
        "name": "유틸리티급 4시간 BESS (100MW/400MWh)",
        "capex_per_kwh": 235, "opex_per_kwh_yr": 8,
        "irr_base_pct": 12.5, "irr_optimistic_pct": 16.0, "irr_conservative_pct": 8.5,
        "payback_years": 7, "project_life_years": 20,
        "degradation_yr_pct": 2.0, "eol_capacity_pct": 70,
        "revenue_kwh_yr": 35, "lcoe_kwh": 0.12,
    },
    "2h_peaker": {
        "name": "피크 대응 2시간 BESS (50MW/100MWh)",
        "capex_per_kwh": 260, "opex_per_kwh_yr": 10,
        "irr_base_pct": 14.0, "irr_optimistic_pct": 18.5, "irr_conservative_pct": 9.0,
        "payback_years": 6, "project_life_years": 15,
        "degradation_yr_pct": 2.5, "eol_capacity_pct": 70,
        "revenue_kwh_yr": 45, "lcoe_kwh": 0.15,
    },
    "ci_behindmeter": {
        "name": "C&I Behind-the-Meter (1MW/4MWh)",
        "capex_per_kwh": 310, "opex_per_kwh_yr": 12,
        "irr_base_pct": 10.0, "irr_optimistic_pct": 13.5, "irr_conservative_pct": 6.5,
        "payback_years": 9, "project_life_years": 15,
        "degradation_yr_pct": 2.0, "eol_capacity_pct": 70,
        "revenue_kwh_yr": 40, "lcoe_kwh": 0.18,
    },
    "re_hybrid": {
        "name": "태양광+ESS 하이브리드 (200MW PV + 100MW/400MWh BESS)",
        "capex_per_kwh": 220, "opex_per_kwh_yr": 7,
        "irr_base_pct": 11.0, "irr_optimistic_pct": 14.5, "irr_conservative_pct": 7.5,
        "payback_years": 8, "project_life_years": 25,
        "degradation_yr_pct": 1.8, "eol_capacity_pct": 70,
        "revenue_kwh_yr": 30, "lcoe_kwh": 0.10,
    },
}

# ---- Offtake / PPA 구조 데이터 ----
OFFTAKE_STRUCTURES = [
    {"type": "Tolling Agreement", "duration_yr": "10-15", "risk_profile": "낮음",
     "revenue_certainty": "높음", "typical_market": "미국, 호주",
     "desc": "오프테이커가 BESS 충방전 권한을 보유하고 고정 용량 비용 지급. 프로젝트 파이낸싱에 가장 유리한 구조."},
    {"type": "Merchant (순수 시장)", "duration_yr": "N/A", "risk_profile": "높음",
     "revenue_certainty": "낮음", "typical_market": "영국, EU",
     "desc": "전력시장 가격에 100% 노출. 높은 수익 잠재력이나 변동성 큼. 영국 BESS 프로젝트의 주류 모델."},
    {"type": "Contracted + Merchant 혼합", "duration_yr": "5-10 + 시장", "risk_profile": "중간",
     "revenue_certainty": "중간", "typical_market": "미국, 호주, EU",
     "desc": "기본 수익은 장기 계약(Tolling/Capacity)으로 확보하고, 잔여 수익을 시장에서 추가 확보하는 하이브리드 구조."},
    {"type": "PPA (전력구매계약)", "duration_yr": "15-20", "risk_profile": "낮음",
     "revenue_certainty": "높음", "typical_market": "미국, 중동",
     "desc": "유틸리티 또는 C&I 수요처와 장기 고정가 PPA. 태양광+ESS 번들에서 주로 활용. ITC 적용 가능."},
    {"type": "Capacity Contract", "duration_yr": "1-15", "risk_profile": "낮음-중간",
     "revenue_certainty": "중간-높음", "typical_market": "영국, EU, 호주",
     "desc": "용량시장 경매 낙찰을 통한 고정 용량 수익 확보. T-4(영국), CIS(호주) 등 정부 주도 메커니즘."},
    {"type": "Virtual PPA (VPPA)", "duration_yr": "10-15", "risk_profile": "중간",
     "revenue_certainty": "중간", "typical_market": "미국, EU",
     "desc": "물리적 전력 인도 없이 재무적 정산만 수행하는 구조. C&I 기업의 RE100 대응 및 ESS 연계에 활용 증가."},
]

# ---- 전력시장 구조 및 거래 데이터 ----
POWER_MARKET_STRUCTURES = {
    "미국": {
        "market_type": "ISO/RTO 분산시장",
        "key_markets": ["CAISO", "ERCOT", "PJM", "NYISO", "ISO-NE", "MISO", "SPP"],
        "settlement": "5분 실시간 + 시간별 Day-ahead + 보조서비스",
        "bess_participation": "에너지 시장, 용량 시장, 보조서비스(Regulation, Reserves) 전면 참여 가능",
        "avg_spread_kwh": "$35-55 (CAISO/ERCOT 기준 일중 스프레드)",
        "key_trend": "ERCOT 음전가 빈도 증가(태양광 과잉), CAISO Duck Curve 심화로 저녁 피크 스프레드 확대. "
                     "FERC Order 2222 시행으로 분산자원(DER) 시장 참여 활성화. AI 기반 입찰 최적화 도입 가속.",
    },
    "영국": {
        "market_type": "단일 도매시장",
        "key_markets": ["N2EX (Day-ahead)", "EPEX Spot", "Balancing Mechanism"],
        "settlement": "30분 결제 + 실시간 Balancing",
        "bess_participation": "도매시장, Balancing Mechanism, Dynamic Containment/Regulation/Moderation, T-4 용량시장",
        "avg_spread_kwh": "£30-50 (일중 스프레드)",
        "key_trend": "해상풍력 확대로 Balancing 수요 급증. Dynamic Containment 단가 변동성 확대(£5-17/MW/hr). "
                     "REMA(전력시장개혁) 검토 중으로 Locational Marginal Pricing 도입 가능성. Duration 4시간 이상 우대 논의.",
    },
    "호주": {
        "market_type": "NEM (National Electricity Market)",
        "key_markets": ["NEM Spot", "FCAS (8개 시장)", "Contract Market"],
        "settlement": "5분 결제 (2021년 전환)",
        "bess_participation": "에너지 스팟시장, FCAS 8개 시장(Raise/Lower × Contingency/Regulation × 6s/60s/5min/delayed), 네트워크 지원",
        "avg_spread_kwh": "A$40-70 (NEM 스팟 일중 스프레드, 변동 극심)",
        "key_trend": "석탄 퇴출 가속(Eraring 2025, Liddell 폐쇄)으로 가격 스파이크 빈도 증가. "
                     "FCAS 시장에서 BESS가 지배적 위치(80%+ 점유). Capacity Investment Scheme 도입으로 장기 수익 안정화 기대.",
    },
    "한국": {
        "market_type": "CBP (Cost-Based Pool, 변동비 반영 시장)",
        "key_markets": ["전력거래소(KPX) 일일 시장", "보조서비스(주파수조정)"],
        "settlement": "시간별 SMP + 용량요금",
        "bess_participation": "주파수조정(FR) 시장 중심, 피크저감, 재생에너지 연계. 에너지 차익거래는 제한적(SMP 구조)",
        "avg_spread_kwh": "₩15,000-25,000/kWh (SMP 기준 제한적 스프레드)",
        "key_trend": "실시간 시장 도입 논의 진행 중. 전력시장 개편(Cost-Based → Bid-Based) 추진으로 BESS 사업 기회 확대 전망. "
                     "K-RE100 이행 확대로 재생에너지 연계 ESS 수요 증가. FR 시장 참여자 증가로 단가 하락 추세.",
    },
    "EU": {
        "market_type": "통합 유럽 전력시장 (EUPHEMIA)",
        "key_markets": ["EPEX Spot", "Nord Pool", "OMIE", "GME", "각국 Balancing 시장"],
        "settlement": "시간별/15분 Day-ahead + Intraday continuous + Balancing",
        "bess_participation": "Day-ahead/Intraday, FCR/aFRR/mFRR 예비력 시장, 용량시장(이탈리아, 프랑스, 폴란드)",
        "avg_spread_kwh": "€25-45 (독일/프랑스 기준)",
        "key_trend": "재생에너지 비중 증가로 음전가(Negative price) 빈도 급증 → 저가 충전 기회 확대. "
                     "Intraday 시장 유동성 증가로 BESS 수익 기회 다변화. DSO 유연성 시장 신규 개설 추세.",
    },
}

# ---- BESS 운영 및 자산관리 데이터 ----
OPERATIONS_DATA = {
    "performance_metrics": {
        "round_trip_efficiency": {"value": "86-92%", "trend": "개선", "desc": "LFP 기준 RTE 88-90%, NMC 86-89%. 셀 기술 발전 및 PCS 효율 향상으로 지속 개선."},
        "availability": {"value": "97-99%", "trend": "안정", "desc": "유틸리티급 BESS 평균 가용률 98%+. 예방정비 스케줄링 및 모듈 이중화로 고가용성 유지."},
        "augmentation_strategy": {"value": "Year 7-10", "trend": "표준화", "desc": "열화 보상을 위한 셀 증설(Augmentation). 초기 설계 시 증설 공간 확보가 표준화되는 추세."},
        "cycle_life": {"value": "6,000-10,000", "trend": "증가", "desc": "LFP 셀 기준 80% SOH까지 사이클 수. 대형 셀(280Ah+)에서 8,000+ 사이클 달성."},
    },
    "om_cost_trends": {
        2022: {"fixed_per_kw_yr": 12.0, "variable_per_mwh": 2.5, "total_per_kwh_yr": 8.5},
        2023: {"fixed_per_kw_yr": 11.0, "variable_per_mwh": 2.3, "total_per_kwh_yr": 7.8},
        2024: {"fixed_per_kw_yr": 10.0, "variable_per_mwh": 2.0, "total_per_kwh_yr": 7.0},
        2025: {"fixed_per_kw_yr": 9.5, "variable_per_mwh": 1.8, "total_per_kwh_yr": 6.5},
        2026: {"fixed_per_kw_yr": 9.0, "variable_per_mwh": 1.6, "total_per_kwh_yr": 6.0},
        2027: {"fixed_per_kw_yr": 8.5, "variable_per_mwh": 1.5, "total_per_kwh_yr": 5.5},
        2028: {"fixed_per_kw_yr": 8.0, "variable_per_mwh": 1.4, "total_per_kwh_yr": 5.1},
        2029: {"fixed_per_kw_yr": 7.6, "variable_per_mwh": 1.3, "total_per_kwh_yr": 4.8},
        2030: {"fixed_per_kw_yr": 7.2, "variable_per_mwh": 1.2, "total_per_kwh_yr": 4.5},
    },
    "ems_platforms": [
        {"name": "Tesla Autobidder", "vendor": "Tesla", "feature": "AI 기반 실시간 입찰 최적화, Megapack 전용", "market": "미국, 호주, 영국"},
        {"name": "Fluence Mosaic", "vendor": "Fluence", "feature": "멀티벤더 지원, 수익 스태킹 최적화, 클라우드 기반", "market": "글로벌"},
        {"name": "Wärtsilä GEMS", "vendor": "Wärtsilä", "feature": "하이브리드 발전 최적화, 마이크로그리드 관리", "market": "글로벌"},
        {"name": "Doosan GridBridge", "vendor": "두산에너바일리티", "feature": "국내 전력시장 최적화, KPX 연계", "market": "한국"},
        {"name": "Powin StackOS", "vendor": "Powin", "feature": "배터리 수명 최적화, 열관리 AI", "market": "미국, 호주"},
    ],
    "degradation_mgmt": [
        "SOC 관리: 일상 운영 SOC 10-90% 범위 유지로 사이클 수명 극대화",
        "열관리: 셀 온도 15-35°C 유지. HVAC/액냉 시스템으로 열폭주 방지 및 수명 연장",
        "C-rate 제어: 0.5C 이하 충방전 우선. 고출력 운전(1C+) 시간 최소화",
        "Calendar Aging 최소화: 장기 고SOC 대기 회피. 비운전 시 SOC 50% 유지",
        "Augmentation 계획: 7-10년차 초기 용량 대비 15-20% 셀 증설로 계약 성능 유지",
        "예방정비: 분기별 절연 저항/접촉 저항 측정, 연 1회 셀 밸런싱 및 BMS 캘리브레이션",
    ],
}

# ---- 안전·화재 및 규제 기준 데이터 ----
SAFETY_STANDARDS = [
    {"standard": "NFPA 855", "region": "미국", "scope": "ESS 설치 및 화재 안전",
     "desc": "ESS 설치 기준 (이격거리, 소방설비, 환기, 폭발 방지). 2023년 개정판에서 실외 ESS 이격거리 강화 및 열폭주 시험 요건 추가.",
     "key_req": "열폭주 전파 시험, 가스 감지, 폭발 방지 환기, 소화 시스템, 비상 대응 계획"},
    {"standard": "UL 9540", "region": "미국/글로벌", "scope": "ESS 제품 안전 인증",
     "desc": "배터리 에너지 저장 시스템 안전 표준. UL 9540A는 열폭주 화재 전파 시험 방법론을 규정.",
     "key_req": "셀→모듈→랙→설치 레벨 4단계 열폭주 시험, 가스 방출량 측정, 연소 생성물 분석"},
    {"standard": "IEC 62933", "region": "글로벌", "scope": "ESS 안전 및 성능",
     "desc": "에너지 저장 시스템의 안전, 성능, 환경 요건. IEC 62933-5-2는 ESS 안전 요건 상세 규정.",
     "key_req": "전기적 안전, 기능 안전(SIL), 환경 시험, 수송 안전, EMC"},
    {"standard": "KS C 8564", "region": "한국", "scope": "ESS 화재 안전",
     "desc": "국내 ESS 화재 안전 기준. 2020년 ESS 화재 사고 이후 대폭 강화. 셀 안전성 시험 + 시스템 레벨 안전 요건.",
     "key_req": "PCS 절연 강화, BMS 이중화, 접지 감시, 온도 모니터링, 소화 설비, 이격거리"},
    {"standard": "AS/NZS 5139", "region": "호주/뉴질랜드", "scope": "ESS 설치 안전",
     "desc": "호주 ESS 설치 안전 기준. 가정용~유틸리티급 ESS 전체 커버. 2024년 개정으로 대형 BESS 요건 강화.",
     "key_req": "설치 위치 제한, 환기 요건, 화재 등급, 비상 차단, 표시 및 라벨링"},
    {"standard": "EN 62619", "region": "EU", "scope": "산업용 리튬이온 배터리 안전",
     "desc": "산업용(ESS 포함) 리튬이온 배터리 안전 요건. CE 마킹 필수. EU Battery Regulation(2027)과 연계.",
     "key_req": "과충전/과방전 보호, 단락 보호, 열 안전, 기계적 안전, 환경 시험"},
]

FIRE_INCIDENTS = [
    {"year": 2017, "location": "한국 (고창)", "cause": "접속 불량/아크", "damage": "시스템 전소", "lesson": "접촉 저항 관리 및 아크 감지 시스템 도입 계기"},
    {"year": 2019, "location": "미국 AZ (McMicken)", "cause": "열폭주 → 가스 축적 → 폭발", "damage": "소방관 부상, 시설 전소", "lesson": "환기 설계 및 가스 감지 의무화(NFPA 855 개정 촉발)"},
    {"year": 2021, "location": "호주 (Victorian Big Battery)", "cause": "냉각 시스템 오작동", "damage": "Tesla Megapack 2대 소손", "lesson": "냉각 시스템 이중화, BMS 알람 즉시 대응 프로토콜"},
    {"year": 2022, "location": "미국 CA (Moss Landing)", "cause": "과열 → 열폭주", "damage": "시스템 정지, 주민 대피", "lesson": "대규모 BESS 열관리 설계 강화, 모듈 간 이격 확대"},
    {"year": 2023, "location": "한국 (나주)", "cause": "BMS 오류/셀 불량 추정", "damage": "컨테이너 전소", "lesson": "BMS 이중화 의무, 셀 수입 검사 강화"},
    {"year": 2024, "location": "미국 CA (Otay Mesa)", "cause": "셀 단락 → 열폭주 전파", "damage": "250MWh급 시설 부분 소손, 11일간 진화", "lesson": "장시간 잔불 대응 프로토콜 정비, 워터미스트 무용성 재평가"},
    {"year": 2025, "location": "미국 CA (Moss Landing 재발)", "cause": "배터리실 화재 (원인 조사중)", "damage": "Vistra 300MW 시설 대규모 소손, 주민 대피", "lesson": "대형 BESS의 배터리실 구획화·격벽 표준화, 보험사 인수 심사 강화"},
    {"year": 2025, "location": "한국 (충북 음성)", "cause": "PCS 절연 열화", "damage": "ESS 컨테이너 1동 전소", "lesson": "PCS 정기 절연저항 모니터링 의무화, KS C 8564 개정 추진"},
    {"year": 2026, "location": "호주 NSW (Bouldercombe)", "cause": "셀 결함 추정 (3건째)", "damage": "Tesla Megapack 1대 소손, 인접 모듈 보호 성공", "lesson": "Megapack 격벽 설계의 화재 격리 효과 입증 — 신규 설계 표준화 가속"},
]

# ---- 배터리 기술 동향 데이터 ----
def _price_range_str(price_dict: dict, ref_year: int) -> str:
    """기준 연도와 이전 연도 가격으로 '$low-high' 문자열 동적 생성."""
    prev = price_dict.get(ref_year - 1)
    curr = price_dict.get(ref_year)
    if prev is None or curr is None:
        return "N/A"
    low, high = sorted([prev, curr])
    return f"${low}-{high}"


BATTERY_TECHNOLOGIES = [
    {"tech": "LFP (리튬인산철)", "chemistry": "LiFePO₄", "status": "주류 상용화",
     "energy_density_wh_kg": "140-170", "cycle_life": "6,000-10,000",
     "cost_per_kwh": "(dynamic — see get_battery_technologies())",
     "pros": "높은 안전성, 긴 수명, 원가 경쟁력, 코발트 무함유",
     "cons": "낮은 에너지 밀도, 저온 성능 저하",
     "outlook": "BESS 시장 지배적 지위 유지. 280Ah+ 대형셀 표준화. LMFP(망간 첨가) 변형으로 에너지 밀도 개선 추진."},
    {"tech": "NMC (니켈망간코발트)", "chemistry": "LiNiMnCoO₂", "status": "상용화 (EV 중심)",
     "energy_density_wh_kg": "200-280", "cycle_life": "3,000-5,000",
     "cost_per_kwh": "(dynamic — see get_battery_technologies())",
     "pros": "높은 에너지 밀도, 높은 출력",
     "cons": "코발트 의존, 열 안정성 LFP 대비 낮음, 높은 원가",
     "outlook": "ESS 시장에서 LFP에 점유율 양보 중. 고에너지 밀도 필요한 공간 제약 프로젝트에서 틈새 활용."},
    {"tech": "나트륨이온 (Na-ion)", "chemistry": "Na₃V₂(PO₄)₃ 등", "status": "초기 상용화",
     "energy_density_wh_kg": "100-140", "cycle_life": "3,000-6,000", "cost_per_kwh": "$30-45 (목표)",
     "pros": "리튬 무함유, 저원가 잠재력, 저온 성능 우수, 풍부한 원재료",
     "cons": "낮은 에너지 밀도, 초기 단계 신뢰성 검증 부족",
     "outlook": "CATL/BYD 양산 돌입(2024~). 단기저장(1-2시간) 및 신흥시장에서 LFP 보완 역할. 2027년 이후 ESS 시장 점유율 10-15% 전망."},
    {"tech": "전고체 배터리", "chemistry": "Li-고체전해질", "status": "R&D/파일럿",
     "energy_density_wh_kg": "350-500", "cycle_life": "5,000+ (목표)", "cost_per_kwh": "$100+ (현재)",
     "pros": "높은 안전성(불연), 높은 에너지 밀도, 넓은 온도 범위",
     "cons": "높은 제조 비용, 계면 저항, 양산 기술 미확립",
     "outlook": "2028-2030년 EV 우선 상용화 예상. ESS 적용은 2030년 이후. Samsung SDI, Toyota 등 선두."},
    {"tech": "바나듐 레독스 흐름전지 (VRFB)", "chemistry": "V²⁺/V³⁺ ↔ V⁴⁺/V⁵⁺", "status": "상용화 (틈새)",
     "energy_density_wh_kg": "15-25", "cycle_life": "20,000+", "cost_per_kwh": "$300-500",
     "pros": "극장수명, 용량/출력 독립 설계, 비인화성, 재활용 용이",
     "cons": "낮은 에너지 밀도, 높은 초기 비용, 바나듐 가격 변동",
     "outlook": "4시간+ 장기저장(LDES) 시장에서 리튬이온 대안. 중국 Dalian 400MW/1.6GWh 가동 시작(2022). 호주·일본 도입 확대."},
    {"tech": "철-공기 배터리", "chemistry": "Fe-Air", "status": "파일럿/데모",
     "energy_density_wh_kg": "80-150", "cycle_life": "조기 단계", "cost_per_kwh": "$20-30 (목표)",
     "pros": "극저원가 잠재력, 풍부한 원재료(철), 100시간+ 저장 가능",
     "cons": "낮은 RTE(45-55%), 대형 풋프린트, 초기 기술",
     "outlook": "Form Energy(미국) 주도. 100시간 저장으로 계절성 저장 시장 타겟. 2025년 첫 상용 프로젝트 착공."},
]

LDES_MARKET = {
    "definition": "4시간 이상 장기 에너지 저장(Long Duration Energy Storage)",
    "base_year": 2025,
    "target_year": 2030,
    "base_size_gwh": 15,
    "target_size_gwh": 120,
    "cagr_pct": 52,
    "key_drivers": [
        "재생에너지 간헐성 증가 → 다일(multi-day) 저장 필요성",
        "석탄/가스 기저 발전 퇴출 → 계통 안정성 확보",
        "미국 DOE LDES 프로그램 ($5B+ 투자)",
        "EU 전략적 에너지 저장 이니셔티브",
    ],
    "competing_techs": [
        {"tech": "리튬이온 (4-8h)", "share_pct": 60, "advantage": "성숙 기술, 검증된 공급망"},
        {"tech": "VRFB (4-12h)", "share_pct": 15, "advantage": "장수명, 용량 확장 용이"},
        {"tech": "압축공기(CAES)", "share_pct": 10, "advantage": "대규모 저장, 지리적 이점"},
        {"tech": "철-공기 (100h+)", "share_pct": 5, "advantage": "극저원가 잠재력"},
        {"tech": "수소/P2G", "share_pct": 10, "advantage": "계절성 저장, 섹터 커플링"},
    ],
}

# ---- 인허가 및 사업 개발 프로세스 데이터 ----
PERMITTING_DATA = {
    "미국": {
        "total_timeline_months": "18-36",
        "grid_connection_wait_months": "24-60",
        "key_permits": ["NEPA 환경영향평가(연방 토지)", "주(State) 에너지 인허가", "카운티/시 건축 허가",
                        "소방서 검토(NFPA 855)", "FERC/ISO 상호연결 신청"],
        "grid_challenge": "PJM/CAISO 상호연결 대기열(Interconnection Queue) 적체 심각. 평균 4-5년 소요. "
                          "FERC Order 2023 개혁으로 개선 기대이나 아직 초기 단계.",
        "land_req_acre_per_mwh": 0.5,
        "tips": "상호연결 신청 조기 진행 필수. Brownfield 부지(폐발전소) 활용 시 인허가 단축. 지역 커뮤니티 수용성 사전 확보.",
    },
    "영국": {
        "total_timeline_months": "12-24",
        "grid_connection_wait_months": "36-84",
        "key_permits": ["Planning Permission (지방의회)", "National Grid 상호연결", "환경영향평가(EIA)",
                        "건축 규정(Building Regulations)", "HSE 안전 검토"],
        "grid_challenge": "그리드 연결 대기시간이 최대 7년+ (영국 최대 과제). "
                          "National Grid 연결 개혁(Connections Reform) 진행 중. 기존 발전소 연결점(Grid Supply Point) 활용이 유리.",
        "land_req_acre_per_mwh": 0.4,
        "tips": "기존 그리드 연결점 확보가 핵심 경쟁 우위. Planning Permission은 50MW 미만 시 지방의회 승인으로 가능.",
    },
    "호주": {
        "total_timeline_months": "12-24",
        "grid_connection_wait_months": "12-36",
        "key_permits": ["Development Approval (주정부)", "AEMO 상호연결", "환경영향평가",
                        "원주민 문화유산 평가", "소방 안전 검토(AS/NZS 5139)"],
        "grid_challenge": "NEM 상호연결 프로세스 비교적 원활하나, 송전 제약(Marginal Loss Factor) 고려 필요. "
                          "REZ(Renewable Energy Zone) 내 프로젝트 우선 연결.",
        "land_req_acre_per_mwh": 0.6,
        "tips": "REZ(신재생 에너지 존) 내 부지 확보 시 인허가 및 그리드 연결 우선권. 원주민 문화유산 평가 조기 착수.",
    },
    "한국": {
        "total_timeline_months": "12-18",
        "grid_connection_wait_months": "6-18",
        "key_permits": ["전기사업 허가(산업통상자원부)", "발전사업 허가", "환경영향평가(대규모)",
                        "건축 허가", "소방 검토(KS C 8564)", "한전 계통연계 협의"],
        "grid_challenge": "상대적으로 짧은 대기 기간이나, 제주도 등 계통 제약 지역에서 연결 거부 사례 증가. "
                          "ESS 의무설치 연계 프로젝트는 인허가 간소화.",
        "land_req_acre_per_mwh": 0.3,
        "tips": "전력거래소 사전 협의 필수. ESS 화재 안전기준(KS C 8564) 충족 증빙 사전 준비. 주민 수용성 확보 중요.",
    },
    "EU": {
        "total_timeline_months": "18-36",
        "grid_connection_wait_months": "12-48",
        "key_permits": ["국가별 에너지 인허가", "환경영향평가(EIA Directive)", "TSO/DSO 상호연결",
                        "건축 허가", "EU Battery Regulation 준수(2027~)"],
        "grid_challenge": "국가별 편차 큼. 독일 비교적 원활, 이탈리아/스페인 3-4년 소요. "
                          "EU 에너지저장 규제 프레임워크 통일 논의 진행 중.",
        "land_req_acre_per_mwh": 0.4,
        "tips": "EU Battery Regulation(2027) 대비 필수 — 탄소발자국 신고, 재활용 요건, 디지털 배터리 여권. 국가별 Fast-track 인허가 활용.",
    },
}

# ---- 프로젝트 파이낸싱 데이터 ----
PROJECT_FINANCING = {
    "structures": [
        {"type": "Non-recourse Project Finance", "leverage": "70-80%", "tenor_yr": "10-18",
         "min_dscr": "1.20-1.35x", "typical_size": "50MW+",
         "desc": "SPV(특수목적법인)를 통한 비소구 금융. BESS 전용 PF 시장 급성장 중. "
                 "장기 Offtake(Tolling/PPA) 확보가 대출 승인의 핵심 요건.",
         "key_lenders": "ING, Natixis, MUFG, Societe Generale, KfW, CEFC(호주)"},
        {"type": "Corporate Finance (On-balance)", "leverage": "N/A", "tenor_yr": "N/A",
         "min_dscr": "N/A", "typical_size": "모든 규모",
         "desc": "개발사/모회사 재무제표 기반 투자. 초기 프로젝트 또는 소규모 BESS에 주로 활용. "
                 "PF 대비 빠른 의사결정이나 자본 효율성 낮음.",
         "key_lenders": "자체 자본, 회사채, 일반 대출"},
        {"type": "Tax Equity (미국)", "leverage": "30-50%", "tenor_yr": "5-10",
         "min_dscr": "N/A", "typical_size": "50MW+",
         "desc": "IRA ITC를 활용한 조세 형평성 투자. Tax Equity 투자자가 ITC 30-50%를 활용하고 "
                 "프로젝트 지분/수익 배분. JP Morgan, Bank of America 등 대형 은행 참여.",
         "key_lenders": "JP Morgan, BofA, Goldman Sachs, US Bank"},
        {"type": "Green Bond / 녹색 채권", "leverage": "100% (채권)", "tenor_yr": "5-15",
         "min_dscr": "N/A", "typical_size": "대규모 포트폴리오",
         "desc": "ESG/녹색 채권 프레임워크 하에서 BESS 프로젝트 자금 조달. "
                 "포트폴리오 레벨에서 다수 프로젝트 번들링. 금리 우대 가능.",
         "key_lenders": "기관투자자, 연기금, 보험사"},
        {"type": "Infrastructure Fund", "leverage": "50-70%", "tenor_yr": "10-25",
         "min_dscr": "N/A", "typical_size": "100MW+",
         "desc": "인프라 펀드를 통한 장기 투자. Blackrock, Brookfield, Macquarie 등 글로벌 인프라 펀드의 "
                 "BESS 투자 급증. COD 이후 자산 인수(Acquisition) 모델 활발.",
         "key_lenders": "Blackrock, Brookfield, Macquarie, Copenhagen Infrastructure Partners"},
    ],
    "bankability_requirements": [
        "장기 Offtake 계약: Tolling/PPA 10년+, 또는 용량시장 계약(T-4 등)",
        "기술 실사: 독립 기술 평가(Independent Engineer Report), Tier 1 셀/PCS 제조사",
        "보험: Property All Risk, Business Interruption, Third Party Liability, Cyber Risk",
        "성능 보증: EPC 사업자 Performance Guarantee, 제조사 용량 Warranty (15-20년)",
        "환경·안전: 환경영향평가 완료, NFPA 855/UL 9540A 등 안전 인증",
        "운영 계획: O&M 계약(LTSA), EMS/최적화 소프트웨어, 보험 갱신 계획",
        "시장 분석: 독립 시장 전문가의 수익 전망(P50/P90), 시나리오 분석",
    ],
    "insurance_coverage": [
        {"type": "Property All Risk (PAR)", "desc": "화재, 자연재해, 기계적 고장 등 자산 손해 보상", "rate": "CAPEX의 0.3-0.8%/yr"},
        {"type": "Business Interruption (BI)", "desc": "사고로 인한 수익 손실 보상. 대기 기간(Deductible) 30-90일", "rate": "예상 수익의 0.5-1.0%/yr"},
        {"type": "Third Party Liability", "desc": "제3자 인적/물적 피해 배상", "rate": "$5M-50M 한도"},
        {"type": "Construction All Risk (CAR)", "desc": "건설 기간 중 사고/손해 보상", "rate": "건설비의 0.5-1.5%"},
        {"type": "Cyber Insurance", "desc": "EMS/SCADA 해킹, 데이터 유출 등 사이버 리스크 보상", "rate": "연간 $50K-200K"},
    ],
}

# ---- EPC 계약 구조 데이터 ----
EPC_CONTRACT_DATA = {
    "contract_types": [
        {"type": "Full Turnkey EPC", "risk_owner": "EPC 사업자",
         "price_structure": "Lump Sum Fixed Price",
         "pros": "발주자 리스크 최소화, 단일 책임(Single Point of Responsibility), PF에 유리",
         "cons": "높은 프리미엄(10-15%), EPC 사업자 마진 포함, 유연성 제한",
         "typical_use": "PF 프로젝트, 첫 진출 시장, 발주자 기술 역량 부족 시",
         "desc": "설계-조달-시공 일괄 도급. 성능 보증 및 일정 보증 포함. BESS 시장에서 가장 보편적 구조."},
        {"type": "EPCM (관리형)", "risk_owner": "발주자 (EPCM 자문)",
         "price_structure": "Cost + Fee / Target Price",
         "pros": "발주자 통제력 강화, 원가 투명성, 조달 유연성",
         "cons": "발주자 리스크 증가, 전문 인력 필요, PF 대출 조건 불리",
         "typical_use": "반복 프로젝트, 발주자 기술 역량 보유 시, 포트폴리오 개발사",
         "desc": "EPC 관리자가 설계/조달/시공을 관리하되 직접 계약 당사자가 아닌 구조. 발주자가 개별 계약 체결."},
        {"type": "Split Contract (분리 발주)", "risk_owner": "발주자 (인터페이스 관리)",
         "price_structure": "각 패키지별 개별 계약",
         "pros": "패키지별 최적 사업자 선정, 원가 절감 잠재력",
         "cons": "인터페이스 리스크, 일정 조율 복잡, 성능 보증 분리",
         "typical_use": "대규모 프로젝트, 전문 셀/PCS 직접 조달 시",
         "desc": "배터리, PCS, BOP(Balance of Plant), 토목/건축을 분리 발주. "
                 "인터페이스 관리 역량이 핵심. Owner's Engineer 활용 권장."},
        {"type": "BOO/BOOT", "risk_owner": "사업자 (BOO) / 이전 (BOOT)",
         "price_structure": "서비스 요금(Capacity Payment)",
         "pros": "발주자 CAPEX 불필요, Off-balance Sheet 가능",
         "cons": "장기 계약 구속, 총 비용 높음, 사업자 수익 마진 포함",
         "typical_use": "중동 정부 프로젝트, 유틸리티 아웃소싱",
         "desc": "Build-Own-Operate: 사업자가 건설·소유·운영. 발주자는 용량 비용만 지급. 중동/아프리카 선호."},
    ],
    "key_commercial_terms": [
        {"term": "Performance Guarantee (PG)", "desc": "용량(MW/MWh), RTE(Round Trip Efficiency), 가용률(Availability) 보증. "
         "미달 시 Liquidated Damages(LD) 적용. 통상 계약 용량 95%+, RTE 85%+, 가용률 97%+."},
        {"term": "Delay LD (지체상금)", "desc": "공사 지연 시 일일 지체상금 부과. 통상 계약금의 0.1-0.5%/일, 상한 10-15%. "
         "BESS는 시장 수익 시작 지연이 직접적 손실이므로 중요."},
        {"term": "Warranty Period", "desc": "EPC Defects Liability Period: 통상 2년. 제조사 셀 Warranty: 10-20년 "
         "(용량 유지율 보증, 일반적으로 10년 80% SOH). PCS Warranty: 5-10년."},
        {"term": "Capacity Warranty", "desc": "제조사가 보증하는 배터리 용량 유지 커브. "
         "Year 10: 80%+ SOH, Year 15: 70%+ SOH가 일반적. Augmentation 비용 부담 주체 명확화 필수."},
        {"term": "Limitation of Liability", "desc": "EPC 사업자 책임 한도. 통상 계약금의 100% (PG LD + Delay LD 합산). "
         "간접 손해(Consequential Damages) 배제 일반적."},
        {"term": "Insurance Requirements", "desc": "CAR(건설 보험), PL(제3자 책임), Professional Indemnity(설계 오류) 필수. "
         "통상 CAPEX의 110%+ 부보. EPC 사업자 부보 의무."},
    ],
    "cost_breakdown": {
        "battery_cells": {"share_pct": 40, "desc": "LFP/NMC 셀 + 모듈화 + BMS"},
        "pcs_inverter": {"share_pct": 15, "desc": "PCS(Power Conversion System) + 변압기"},
        "bop_electrical": {"share_pct": 12, "desc": "케이블, 스위치기어, 접지, SCADA"},
        "bop_civil": {"share_pct": 8, "desc": "기초, 도로, 배수, 펜스, 소방 설비"},
        "ems_software": {"share_pct": 5, "desc": "EMS, 최적화 SW, 통신, 모니터링"},
        "epc_margin_overhead": {"share_pct": 10, "desc": "EPC 마진 + 간접비 + 보험 + 보증"},
        "dev_permitting": {"share_pct": 5, "desc": "개발비, 인허가, 환경 평가, 법률 비용"},
        "contingency": {"share_pct": 5, "desc": "예비비(Contingency) 5-10%"},
    },
}


def get_battery_technologies(ref_year: int = None) -> list:
    """BATTERY_TECHNOLOGIES 사본을 반환하되, LFP/NMC의 cost_per_kwh를 현재 가격 데이터로 동적 치환.

    LFP/NMC는 LFP_CELL_PRICE / NMC_CELL_PRICE 시계열의 (ref_year-1) ~ ref_year 범위로 표시.
    다른 기술(Na-ion, 전고체, VRFB 등)은 정적 값을 유지.
    """
    if ref_year is None:
        ref_year = LATEST_ACTUAL_YEAR
    out = []
    for tech in BATTERY_TECHNOLOGIES:
        item = dict(tech)
        if tech["tech"].startswith("LFP"):
            item["cost_per_kwh"] = _price_range_str(LFP_CELL_PRICE, ref_year)
        elif tech["tech"].startswith("NMC"):
            item["cost_per_kwh"] = _price_range_str(NMC_CELL_PRICE, ref_year)
        out.append(item)
    return out

