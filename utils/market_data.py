import urllib.request
import xml.etree.ElementTree as ET
from html import unescape
import re
from datetime import datetime
import streamlit as st

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
        print(f"RSS fetch failed [{url}]: {e}")
        return []

@st.cache_data(ttl=1800)
def fetch_rss_feed(category, max_items=6, timeout=12):
    """Try each RSS source in order until we get results."""
    urls = RSS_FEEDS.get(category, [])
    if isinstance(urls, str):
        urls = [urls]
    for url in urls:
        items = _fetch_one_rss(url, max_items, timeout)
        if items:
            return {"items": items, "timestamp": datetime.now(), "source": url}
    return {"items": [], "timestamp": datetime.now(), "source": None}

def clear_rss_cache():
    """Clear the Streamlit cache for RSS feeds to force a refresh."""
    fetch_rss_feed.clear()

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

    # Fallback: hardcoded recent reference values (updated periodically)
    if result["brent_crude_usd"] is None:
        result["brent_crude_usd"] = 72.5
        result["wti_crude_usd"] = 68.8
        result["source"] = "reference (offline)"
    if result["wti_crude_usd"] is None:
        result["wti_crude_usd"] = round(result["brent_crude_usd"] * 0.95, 2)

    # Lithium / Copper / Nickel — reference values (real-time requires paid API)
    result["lithium_carbonate_usd_ton"] = 11500
    result["copper_usd_ton"] = 9200
    result["nickel_usd_ton"] = 16800
    return result


# ============================================================
# 시장 데이터 (Built-in Defaults)
# ============================================================

YEARS = [2022, 2023, 2024, 2025, 2026, 2027]
YEAR_LABELS = ["2022", "2023", "2024", "2025", "2026E", "2027F"]

# ---- 글로벌 시장 규모 (GWh) ----
GLOBAL_CAPACITY_GWH = {
    2022: 45,
    2023: 75,
    2024: 130,
    2025: 200,
    2026: 280,
    2027: 370,
}

# ---- 글로벌 시장 규모 (억 달러) ----
GLOBAL_MARKET_VALUE_B_USD = {
    2022: 18.0,
    2023: 30.0,
    2024: 46.0,
    2025: 65.0,
    2026: 88.0,
    2027: 115.0,
}

# ---- 배터리 셀 가격 $/kWh (LFP 기준) ----
LFP_CELL_PRICE = {
    2022: 80,
    2023: 62,
    2024: 50,
    2025: 43,
    2026: 37,
    2027: 32,
}

# ---- 시스템 CAPEX $/kWh ----
SYSTEM_CAPEX = {
    2022: 380,
    2023: 320,
    2024: 265,
    2025: 235,
    2026: 205,
    2027: 180,
}

# ---- NMC 셀 가격 $/kWh (참고) ----
NMC_CELL_PRICE = {
    2022: 120,
    2023: 98,
    2024: 82,
    2025: 70,
    2026: 60,
    2027: 52,
}

# ---- 지역별 데이터 ----
REGIONAL_DATA = {
    "한국": {
        "name_en": "South Korea",
        "installed_gwh": {2022: 1.5, 2023: 2.5, 2024: 4.0, 2025: 6.5, 2026: 9.5, 2027: 13.0},
        "pipeline_gwh": 25.0,
        "market_share_pct": 4.5,
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
        "installed_gwh": {2022: 2.0, 2023: 3.0, 2024: 4.5, 2025: 7.0, 2026: 10.5, 2027: 14.5},
        "pipeline_gwh": 30.0,
        "market_share_pct": 5.0,
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
        "installed_gwh": {2022: 12.0, 2023: 20.0, 2024: 32.0, 2025: 50.0, 2026: 72.0, 2027: 100.0},
        "pipeline_gwh": 180.0,
        "market_share_pct": 31.0,
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
        "installed_gwh": {2022: 3.0, 2023: 5.0, 2024: 8.0, 2025: 13.0, 2026: 18.5, 2027: 25.0},
        "pipeline_gwh": 50.0,
        "market_share_pct": 7.5,
        "key_drivers": [
            "석탄발전 퇴출 가속화",
            "NEM(National Electricity Market) 변동성",
            "대규모 VPP(Virtual Power Plant)",
            "주택용 태양광+ESS 보급",
            "2030 재생에너지 82% 목표",
        ],
        "revenue_model": "FCAS(주파수조정), 에너지 차익거래, 용량결제, VPP, 네트워크 지원",
        "policy": [
            "Capacity Investment Scheme",
            "ARENA 보조금 프로그램",
            "NEM 용량시장 도입 논의",
            "각 주별 재생에너지 목표",
            "가정용 배터리 보조금",
        ],
        "key_players": ["Neoen", "AGL Energy", "Origin Energy", "Tesla", "Sungrow"],
        "avg_project_size_mwh": 300,
        "growth_rate_pct": 45,
    },
    "영국": {
        "name_en": "United Kingdom",
        "installed_gwh": {2022: 2.5, 2023: 4.0, 2024: 6.5, 2025: 10.0, 2026: 14.5, 2027: 20.0},
        "pipeline_gwh": 40.0,
        "market_share_pct": 6.0,
        "key_drivers": [
            "2035 전력 탈탄소화 목표",
            "풍력(해상) 확대에 따른 유연성 수요",
            "보조서비스 수익 모델 다양화",
            "Cap & Floor 수익 안정 메커니즘",
            "EFR/DC/DM/FFR 시장 성장",
        ],
        "revenue_model": "Dynamic Containment, FFR, T-4 용량시장, 에너지 차익거래, Balancing Mechanism",
        "policy": [
            "Net Zero Strategy 2050",
            "Contracts for Difference (CfD)",
            "용량시장 (Capacity Market T-4)",
            "REMA (전력시장개혁) 검토",
            "그리드 연결 대기시간 개선",
        ],
        "key_players": ["Gresham House", "Gore Street", "Harmony Energy", "Zenobe", "EDF"],
        "avg_project_size_mwh": 100,
        "growth_rate_pct": 40,
    },
    "EU": {
        "name_en": "European Union",
        "installed_gwh": {2022: 5.0, 2023: 8.0, 2024: 13.0, 2025: 20.0, 2026: 30.0, 2027: 42.0},
        "pipeline_gwh": 80.0,
        "market_share_pct": 13.0,
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
        "installed_gwh": {2022: 0.5, 2023: 1.0, 2024: 2.5, 2025: 5.0, 2026: 9.0, 2027: 14.0},
        "pipeline_gwh": 35.0,
        "market_share_pct": 3.5,
        "key_drivers": [
            "사우디 Vision 2030 (50% RE 목표)",
            "UAE Net Zero 2050",
            "대규모 태양광+ESS 프로젝트",
            "피크 수요 관리 (냉방 부하)",
            "석유 의존도 탈피 전략",
        ],
        "revenue_model": "PPA/BOO 모델, 피크 저감, 태양광+ESS 하이브리드, 정부 프로젝트 입찰",
        "policy": [
            "사우디 NREP (재생에너지 프로그램)",
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
COMPETITORS = [
    {"name": "CATL", "country": "중국", "type": "셀/시스템", "market_share_pct": 28.0, "revenue_b_usd": 12.5, "capacity_gwh": 55, "strength": "LFP 원가 경쟁력, 대규모 생산능력", "weakness": "지정학적 리스크, 서비스 네트워크"},
    {"name": "BYD", "country": "중국", "type": "셀/시스템", "market_share_pct": 18.0, "revenue_b_usd": 8.2, "capacity_gwh": 35, "strength": "수직 계열화, Blade Battery 안전성", "weakness": "미국 시장 진입 장벽"},
    {"name": "Samsung SDI", "country": "한국", "type": "셀", "market_share_pct": 6.5, "revenue_b_usd": 3.8, "capacity_gwh": 12, "strength": "NMC 기술력, 미국/유럽 공장", "weakness": "LFP 라인업 후발"},
    {"name": "LG Energy Solution", "country": "한국", "type": "셀", "market_share_pct": 5.5, "revenue_b_usd": 3.2, "capacity_gwh": 10, "strength": "글로벌 생산 네트워크, 기술 다양성", "weakness": "ESS 전용 투자 제한적"},
    {"name": "Tesla (Megapack)", "country": "미국", "type": "시스템", "market_share_pct": 12.0, "revenue_b_usd": 6.0, "capacity_gwh": 25, "strength": "브랜드, 소프트웨어 통합, Autobidder", "weakness": "높은 가격, 납기 지연"},
    {"name": "Fluence", "country": "미국", "type": "시스템", "market_share_pct": 8.0, "revenue_b_usd": 3.5, "capacity_gwh": 16, "strength": "SW 플랫폼(Mosaic), Siemens/AES 백업", "weakness": "수익성 미확보"},
    {"name": "Sungrow", "country": "중국", "type": "PCS/시스템", "market_share_pct": 7.0, "revenue_b_usd": 2.8, "capacity_gwh": 14, "strength": "PCS 기술, 가격 경쟁력", "weakness": "브랜드 인지도 (서방)"},
    {"name": "Wärtsilä", "country": "핀란드", "type": "시스템", "market_share_pct": 3.5, "revenue_b_usd": 1.5, "capacity_gwh": 7, "strength": "EPC 경험, GEMS 플랫폼", "weakness": "셀 외부 조달 의존"},
    {"name": "Honeywell", "country": "미국", "type": "시스템/SW", "market_share_pct": 2.0, "revenue_b_usd": 0.9, "capacity_gwh": 4, "strength": "산업용 제어 기술, 브랜드 신뢰", "weakness": "ESS 전문성 후발"},
    {"name": "EVE Energy", "country": "중국", "type": "셀", "market_share_pct": 5.0, "revenue_b_usd": 2.2, "capacity_gwh": 10, "strength": "LFP 대형셀 경쟁력, 가격", "weakness": "글로벌 트랙레코드"},
]

# ---- 시나리오 분석 데이터 ----
SCENARIOS = {
    "보수적 (Conservative)": {
        "description": "글로벌 경기 둔화, 정책 지연, 공급망 불안정",
        "capacity_gwh": {2024: 95, 2025: 130, 2026: 170, 2027: 210, 2028: 255, 2029: 300, 2030: 360},
        "market_value_b": {2024: 36, 2025: 45, 2026: 55, 2027: 66, 2028: 78, 2029: 90, 2030: 105},
        "cell_price": {2024: 58, 2025: 52, 2026: 47, 2027: 43, 2028: 40, 2029: 38, 2030: 36},
        "cagr_pct": 21,
    },
    "기본 (Base)": {
        "description": "현재 정책 유지, 기술 발전 지속, 안정적 성장",
        "capacity_gwh": {2024: 100, 2025: 150, 2026: 200, 2027: 260, 2028: 340, 2029: 430, 2030: 550},
        "market_value_b": {2024: 38, 2025: 52, 2026: 68, 2027: 85, 2028: 108, 2029: 135, 2030: 170},
        "cell_price": {2024: 55, 2025: 48, 2026: 42, 2027: 37, 2028: 33, 2029: 30, 2030: 27},
        "cagr_pct": 33,
    },
    "낙관적 (Optimistic)": {
        "description": "강력한 정책 지원, 기술 혁신 가속, 수요 폭증",
        "capacity_gwh": {2024: 105, 2025: 165, 2026: 240, 2027: 340, 2028: 470, 2029: 630, 2030: 850},
        "market_value_b": {2024: 40, 2025: 58, 2026: 80, 2027: 108, 2028: 145, 2029: 190, 2030: 250},
        "cell_price": {2024: 53, 2025: 45, 2026: 38, 2027: 32, 2028: 27, 2029: 24, 2030: 21},
        "cagr_pct": 42,
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

