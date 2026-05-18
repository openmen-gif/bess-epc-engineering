"""data_fetchers.py — 외부 공개 데이터 소스에서 라이브 BESS 데이터 fetch.

현재 지원:
- fetch_eia_us_battery_capacity(): EIA API로 미국 BESS 총 운영 용량(MW) 조회

설계 원칙:
- 모든 fetch는 try/except로 감싸 실패 시 None 반환 (fallback 가능하게).
- streamlit cache_data로 결과 캐싱 (TTL 6시간).
- API 키는 EIA_API_KEY 환경변수에서 읽음. 없으면 None 반환 (스냅샷 fallback).
- 응답은 표준화된 dict 구조로 반환:
    {"value": float, "unit": str, "as_of": datetime, "source": str, "error": Optional[str]}
"""
import logging
import os
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone
import streamlit as st

_log = logging.getLogger(__name__)

EIA_API_BASE = "https://api.eia.gov/v2"
EIA_TIMEOUT_SEC = 15

# EIA 시리즈 ID (월별 미국 배터리 저장 운영 용량, MW)
# https://www.eia.gov/electricity/data/browser/#/topic/0?agg=2,0,1&fuel=01g&geo=g
# Form EIA-860M monthly survey of utility-scale battery storage.
EIA_SERIES_BATTERY_MW = "electricity/operating-generator-capacity/data/"

# 출처 라벨 (대시보드/보고서에 표시)
EIA_SOURCE_LABEL = "U.S. EIA Form EIA-860M (Operating Battery Storage)"


def _eia_api_key() -> str | None:
    """Get EIA API key from env. EIA requires a free key for v2 API."""
    key = os.environ.get("EIA_API_KEY", "").strip()
    return key if key else None


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def fetch_eia_us_battery_capacity() -> dict:
    """미국 배터리 저장 총 운영 용량 (MW)을 EIA에서 fetch.

    Returns:
        {
            "value_mw": float | None,
            "value_gwh_est": float | None,  # MW * 4시간 가정한 추정 GWh
            "as_of": datetime | None,
            "source": str,
            "error": str | None,
        }
    """
    result = {
        "value_mw": None,
        "value_gwh_est": None,
        "as_of": None,
        "source": EIA_SOURCE_LABEL,
        "error": None,
    }

    key = _eia_api_key()
    if not key:
        result["error"] = "EIA_API_KEY 환경변수가 설정되지 않음 (https://www.eia.gov/opendata/register.php 무료 발급)"
        return result

    # EIA v2: operating generator capacity, filter to battery technology, US total
    params = {
        "api_key": key,
        "frequency": "monthly",
        "data[0]": "nameplate-capacity-mw",
        "facets[technology][]": "Batteries",
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": 12,  # last 12 months
    }
    url = f"{EIA_API_BASE}/{EIA_SERIES_BATTERY_MW}?{urllib.parse.urlencode(params, doseq=True)}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BESS-EPC-Dashboard/1.0"})
        with urllib.request.urlopen(req, timeout=EIA_TIMEOUT_SEC) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        rows = data.get("response", {}).get("data", [])
        if not rows:
            result["error"] = "EIA 응답에 데이터 행 없음"
            return result

        # 최신 월 데이터 (sort desc로 첫 행)
        latest = rows[0]
        period = latest.get("period")  # "YYYY-MM"
        # 동일 month의 모든 plant 합산 (US 전체)
        target_period = period
        total_mw = 0.0
        for r in rows:
            if r.get("period") != target_period:
                continue
            try:
                total_mw += float(r.get("nameplate-capacity-mw") or 0)
            except (TypeError, ValueError):
                continue

        if total_mw <= 0:
            # 데이터는 있었으나 합산이 0 — facet이 plant 단위가 아닐 수 있음
            try:
                total_mw = float(latest.get("nameplate-capacity-mw") or 0)
            except (TypeError, ValueError):
                total_mw = 0.0

        if total_mw <= 0:
            result["error"] = "EIA 응답 파싱 후 유효한 용량값을 얻지 못함"
            return result

        # 평균 duration 가정 (미국 BESS 평균 ~3.5시간, 보수적으로 4시간 적용)
        # 정확한 GWh는 EIA 별도 시리즈에서 가져와야 하므로 추정치로 표시
        gwh_est = total_mw * 4.0 / 1000.0  # MW * 4h / 1000 = GWh

        try:
            as_of_dt = datetime.strptime(period, "%Y-%m").replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            as_of_dt = datetime.now(timezone.utc)

        result["value_mw"] = round(total_mw, 1)
        result["value_gwh_est"] = round(gwh_est, 2)
        result["as_of"] = as_of_dt
        return result

    except urllib.error.HTTPError as e:
        result["error"] = f"EIA HTTP {e.code}: {e.reason}"
        return result
    except urllib.error.URLError as e:
        result["error"] = f"EIA URL error: {e.reason}"
        return result
    except (json.JSONDecodeError, KeyError) as e:
        result["error"] = f"EIA 응답 파싱 실패: {e}"
        return result
    except Exception as e:
        _log.exception("Unexpected error fetching EIA data")
        result["error"] = f"예기치 못한 오류: {e}"
        return result


def get_live_us_capacity_or_fallback(snapshot_gwh: float | int) -> dict:
    """라이브 fetch 시도 → 실패 시 스냅샷 값으로 fallback.

    Args:
        snapshot_gwh: market_data.REGIONAL_DATA["미국"]["installed_gwh"][curr_year] 같은 fallback 값

    Returns:
        {
            "value_gwh": float,
            "is_live": bool,
            "as_of_str": str,   # 표시용 ("2026-04" 또는 "snapshot")
            "source": str,
            "error": str | None,
        }
    """
    live = fetch_eia_us_battery_capacity()
    if live["value_gwh_est"] is not None and live["error"] is None:
        return {
            "value_gwh": live["value_gwh_est"],
            "is_live": True,
            "as_of_str": live["as_of"].strftime("%Y-%m") if live["as_of"] else "live",
            "source": live["source"],
            "error": None,
        }
    return {
        "value_gwh": float(snapshot_gwh),
        "is_live": False,
        "as_of_str": "snapshot",
        "source": "market_data.py snapshot",
        "error": live.get("error"),
    }
