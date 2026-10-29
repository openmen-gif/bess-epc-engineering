# -*- coding: utf-8 -*-
"""
engineering_params.py — 페이지가 판정에 쓰는 기술 기준값의 단일 출처.

각 값 옆의 근거는 스킬 정본(01_BESS사업/00_Skill_MD/*.md, 앱 사본은 skill_md/)의 파일:섹션이다.
스킬이 자라 기준이 바뀌면 이 파일만 고치고, tests/verify_dashboard.py 의 기준값 회귀가
페이지 판정과 이 값이 어긋나지 않았는지 확인한다. (2026-10-28 신설)
"""
import math

# ── 열관리 판정 (bess-cfd-analyst.md "배터리 열관리 해석 — 공냉" 표) ─────────────
CELL_TMAX_REC_C = 35.0      # 셀 최고온도 권장 상한
CELL_TMAX_ALLOW_C = 45.0    # 셀 최고온도 허용 상한 (초과 시 Fail)
CELL_DT_RACK_MAX_C = 5.0    # 랙 내 셀 간 온도 편차 ΔT_cell 상한
RACK_DT_MAX_C = 3.0         # 랙 간 온도 편차 ΔT_rack 상한
CONTAINER_MEAN_TARGET_C = (20.0, 25.0)  # 컨테이너 내부 평균온도 HVAC 제어 목표

# ── 케이블 사이징 (bess-cable-engineer.md "1. 케이블 사이징·선정") ────────────────
# 전압강하 판정은 케이블 스킬(소유 도메인) 값 — ebop 스킬의 "MV 5%·LV 3%" 표기와 상충 중(스킬 정리 대상)
VDROP_LIMIT_PCT = {"LV": 5.0, "MV": 3.0, "HV": 2.0}
AMPACITY_DESIGN_MARGIN = 1.25   # I_base×∏k ≥ 1.25·I_load 권고 (U ≤ 0.8)
# 단열 단락내량 계수 k — IEC 60364-4-43 Table 43A (도체)
SC_K = {"XLPE-Cu": 143.0, "XLPE-Al": 94.0, "PVC-Cu": 115.0}


def voltage_class(kv_ll: float) -> str:
    """선간전압(kV) → 전압 등급. LV ≤1 kV, MV ≤35 kV, 그 이상 HV."""
    if kv_ll <= 1.0:
        return "LV"
    if kv_ll <= 35.0:
        return "MV"
    return "HV"


def sc_min_area_mm2(i_sc_ka: float, t_s: float, k: float) -> float:
    """단열 단락내량 S_min = I·√t / k [mm²] (I in A)."""
    return i_sc_ka * 1000.0 * math.sqrt(t_s) / k


# ── 소화설비 (bess-fire-engineer.md "3. 소화 시스템 설계") ─────────────────────────
# 배터리 컨테이너 = Water Mist(NFPA 750) 기본, Clean Agent 는 PCS실·EMS실용
WATER_MIST_DENSITY_LPM_M3 = (0.07, 0.15)   # 고압 기준 방출밀도 범위, 실시험 인증값 우선
WATER_MIST_DENSITY_DEFAULT = 0.10
WATER_MIST_MIN_DISCHARGE_MIN = 10.0        # NFPA 750 최소
WATER_MIST_BATTERY_DISCHARGE_MIN = 30.0    # 배터리 화재 권장
WATER_MIST_COOLING_EXT_MIN = 60.0          # 냉각 연장 (스킬 예시: 30분 + 60분 = 540 L @ 60 m³)
FM200_GWP = 3220


# ── 냉방부하 외피 취득열 (bess-cbop-engineer.md "HVAC 냉방 부하 산정 공식" Q_envelope = U·A·ΔT) ──
# 스킬 공식은 U 값을 특정하지 않는다 — 단열 패널 컨테이너 스크리닝 값
ENC_U_W_M2K = 2.5       # [가정] 외피 열관류율
ENC_HEIGHT_M = 2.9      # [가정] 20ft HC 인클로저 높이 (site_layout.ENC_H 와 동일)


def enc_ua_kw_k(length_m: float, width_m: float, height_m: float = ENC_HEIGHT_M) -> float:
    """인클로저 1기 외피 U·A [kW/K] — A = 6면 표면적 (20ft 6.05×2.44×2.9 → 78.8 m² → 0.197 kW/K)."""
    area = 2.0 * (length_m * width_m + length_m * height_m + width_m * height_m)
    return ENC_U_W_M2K * area / 1000.0


# ── 부지 배치 이격 (값 소유: bess-fire-engineer "시장별 이격거리 기준", 배치 반영: bess-cbop-engineer) ──
# 이격은 UL 9540A 시험 결과·AHJ·보험사 요건으로 가감되는 값 — 여기 값은 스크리닝 기본값이다.
# tag: "" = 스킬 표 명시값, "[요확인]" = 조건부(시험·위험물·국가별) 값이라 현장 확인 필요,
#      "[가정]" = 스킬 표에 정량값이 없어(State별·조례별 상이 등) 보수값을 대입한 항목 포함
SEPARATION_BY_MARKET = {
    # 정본: bess-fire-engineer.md "시장별 이격거리 기준" 표 (bess-cbop-engineer.md "이격거리 기준" 표와 교차)
    "US": dict(unit_m=3.048, boundary_m=3.048, tag="[요확인]",
               src="NFPA 855 §4.1.4 — UL 9540A 미시험 시 ≥10 ft(3 m), 시험 입증 시 ≥3 ft(0.9 m)까지 단축 · "
                   "부지경계 FM Global 10 ft(3 m)"),
    "KR": dict(unit_m=3.0, boundary_m=6.0, tag="",
               src="소방청·KFI ESS 화재안전기준 — 컨테이너 간 ≥3 m · 부지경계 ≥6 m (2층 이상 건물 ≥9 m)"),
    "AU": dict(unit_m=3.0, boundary_m=3.0, tag="[가정]",
               src="AS/NZS 5139:2019 컨테이너 간 ≥3 m · 부지경계는 State별 상이 → 3 m [가정]"),
    "UK": dict(unit_m=3.0, boundary_m=3.0, tag="[가정]",
               src="NFCC BESS Guidance 2023 ≥3 m 권고 · 부지경계는 화재위험평가 기반 → 3 m [가정]"),
    "JP": dict(unit_m=3.0, boundary_m=3.0, tag="[요확인]",
               src="消防法·危険物令 ≥3 m(위험물 보유 시) · 부지경계는 조례별 상이 → 3 m [가정]"),
    "EU": dict(unit_m=5.0, boundary_m=5.0, tag="[요확인]",
               src="국가 소방법 ≥3~5 m(국가별) → 보수값 5 m · 부지경계 국가별 상이 → 5 m [가정]"),
}
# 변압기 이격은 IEC 61936-1·FM Global DS 5-4 에서 절연유량·내화등급별로 정한다(fire-engineer) — 값 미특정
TRANSFORMER_CLEARANCE_M = 5.0           # [가정] 조항·값 확인 전 스크리닝 값
ACCESS_AISLE_M = 6.0                    # [가정] 블록 행 사이 소방·유지보수 차량 통로
FENCE_HEIGHT_M = 2.1                    # bess-cbop-engineer 울타리 높이 ≥2.1 m 권장


def market_key(target_market: str) -> str:
    """'US (ERCOT)' → 'US'. 미지정·미지원은 KR."""
    m = str(target_market or "").upper()
    for k in SEPARATION_BY_MARKET:
        if m.startswith(k):
            return k
    return "KR"


# ── 운영 KPI (bess-data-analyst.md 재사용 지식 "운영 KPI 정량 임계 세트") ────────────
# 계약 성능보증 값이 있으면 그것이 우선 — 미제공 시 [가정]
KPI_AVAILABILITY_MIN_PCT = 97.0
KPI_RTE_MIN_PCT = {"LFP": 85.0, "NMC": 87.0}
SOH_EOL_PCT = 80.0


# ── 열화 모델 (bess-battery-expert.md "열화·수명 모델") ─────────────────────────────
# 총 열화 = 캘린더 + 사이클 (선형 가산). 스킬 앵커:
#   캘린더: 25°C 10년 → 잔존 85%, 45°C 5년 → 잔존 85%   (Arrhenius)
#   사이클: LFP 80% DoD 에서 EOL 80% 까지 ≈7,000 사이클  (throughput, Q ∝ N^z, z≈0.5~1)
#   불확실성 ±3%
# [가정] 캘린더 시간 지수 0.5(√t) — 스킬에 지수 명시 없음. 두 앵커로 A·Ea 를 역산한다.
CAL_TIME_EXP = 0.5
_ANCHOR_A = (25.0, 10.0, 15.0)   # (°C, 년, 손실 %)
_ANCHOR_B = (45.0, 5.0, 15.0)
CYC_ANCHOR_EFC = 7000 * 0.80     # 7,000 사이클 × 80% DoD = 5,600 EFC
CYC_ANCHOR_LOSS_PCT = 20.0
CYC_EXP_DEFAULT = 0.75           # [가정] z 범위 0.5~1 의 중앙값
DEGRADATION_UNCERTAINTY_PCT = 3.0

_R = 8.314462618  # J/(mol·K)


def _calendar_fit():
    (t1, y1, l1), (t2, y2, l2) = _ANCHOR_A, _ANCHOR_B
    k1 = l1 / (y1 ** CAL_TIME_EXP)
    k2 = l2 / (y2 ** CAL_TIME_EXP)
    T1, T2 = t1 + 273.15, t2 + 273.15
    ea = _R * math.log(k2 / k1) / (1.0 / T1 - 1.0 / T2)   # J/mol
    a = k1 * math.exp(ea / (_R * T1))
    return a, ea


CAL_A, CAL_EA_J_MOL = _calendar_fit()


def calendar_loss_pct(temp_c: float, years: float) -> float:
    k = CAL_A * math.exp(-CAL_EA_J_MOL / (_R * (temp_c + 273.15)))
    return k * max(years, 0.0) ** CAL_TIME_EXP


def cycle_loss_pct(efc: float, z: float = CYC_EXP_DEFAULT) -> float:
    return CYC_ANCHOR_LOSS_PCT * (max(efc, 0.0) / CYC_ANCHOR_EFC) ** z


def soh_pct(temp_c: float, years: float, cycles_per_day: float, dod: float,
            z: float = CYC_EXP_DEFAULT) -> float:
    """SOH(%) = 100 − 캘린더 손실 − 사이클 손실. EFC = 사이클 수 × DoD."""
    efc = cycles_per_day * 365.0 * years * dod
    return 100.0 - calendar_loss_pct(temp_c, years) - cycle_loss_pct(efc, z)
