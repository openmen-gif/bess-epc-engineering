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
            desc  = unescape(item.findtext("description", ""))
            desc  = re.sub(r"<[^>]+>", "", desc).strip()
            if title:
                items.append({"title": title, "link": link, "pubDate": pub, "description": desc[:150] + "..."})
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

