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

# 3상 교류 전압강하 도체 저항률 (75°C 운전온도 기준, IEC 60287)
# 동(Cu): 2.09e-8 Ω·m, 알루미늄(Al): 3.43e-8 Ω·m
RHO_75C_CU = 2.09e-8
RHO_75C_AL = 3.43e-8
# 단심 삼각배치 케이블 표준 단위길이당 유도 리액턴스 (60Hz 기준 약 0.10 Ω/km, IEC 60502-2)
CABLE_REACTANCE_OHM_PER_KM = 0.10


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


def calc_cable_vdrop(
    v_line_v: float,
    current_a: float,
    length_m: float,
    area_mm2: float,
    is_cu: bool = True,
    power_factor: float = 0.95,
) -> dict:
    """
    3상 선간 전압강하 정밀 산정 (IEC 60287 / IEEE 141 기준).
    ΔV = √3 · I · (L/1000) · (R'·cosφ + X'·sinφ)
    
    MV/대구경 케이블에서는 리액턴스 X 가 저항 R 과 대등하거나 더 커지므로
    저항만 반영 시 전압강하가 과소평가되는 결함을 방지한다.
    """
    rho = RHO_75C_CU if is_cu else RHO_75C_AL
    # 교류 저항 R' (Ω/km) - 표피효과 1.02 반영
    r_ac_km = (rho / (max(area_mm2, 1.0) * 1e-6)) * 1000.0 * 1.02
    x_km = CABLE_REACTANCE_OHM_PER_KM
    
    cos_phi = max(min(power_factor, 1.0), 0.5)
    sin_phi = math.sqrt(max(1.0 - cos_phi**2, 0.0))
    
    # 등가 임피던스 Z' (Ω/km)
    z_eq_km = (r_ac_km * cos_phi) + (x_km * sin_phi)
    
    length_km = length_m / 1000.0
    delta_v = math.sqrt(3.0) * current_a * length_km * z_eq_km
    vdrop_pct = (delta_v / max(v_line_v, 1.0)) * 100.0
    
    return {
        "delta_v": delta_v,
        "vdrop_pct": vdrop_pct,
        "r_ac_km": r_ac_km,
        "x_km": x_km,
        "z_eq_km": z_eq_km,
    }


def vdrop_min_area_mm2(
    v_line_v: float,
    current_a: float,
    length_m: float,
    target_vdrop_pct: float,
    is_cu: bool = True,
    power_factor: float = 0.95,
) -> float:
    """
    목표 전압강하율(%)을 만족하는 최소 단면적(mm²) 역산 (리액턴스 X 고려).
    ΔV = V_line * (vdrop% / 100) = √3 · I · L_km · ( (ρ/S·1.02)·cosφ + X'·sinφ )
    S_min = (ρ_75 · 1.02 · cosφ) / [ ΔV / (√3 · I · L_km) - X' · sinφ ] * 1e6
    """
    target_dv = v_line_v * (target_vdrop_pct / 100.0)
    length_km = length_m / 1000.0
    cos_phi = max(min(power_factor, 1.0), 0.5)
    sin_phi = math.sqrt(max(1.0 - cos_phi**2, 0.0))
    
    denom_imp = target_dv / (math.sqrt(3.0) * max(current_a, 1e-3) * max(length_km, 1e-4))
    r_target = denom_imp - (CABLE_REACTANCE_OHM_PER_KM * sin_phi)
    
    if r_target <= 1e-6:
        # 리액턴스만으로도 허용 전압강하를 초과하는 경우 (병렬 케이블 필요)
        return 9999.0
    
    rho = RHO_75C_CU if is_cu else RHO_75C_AL
    s_m2 = (rho * 1000.0 * 1.02 * cos_phi) / r_target
    return s_m2 * 1e6


# ── 폭발 방산 벤트 (NFPA 68 / NFPA 855 배터리 열폭주 방폭 벤트) ───────────────────
# NFPA 68 (Standard on Explosion Protection by Deflagration Venting)
# 저강도 인클로저(Pred ≤ 0.5 bar)에서 배터리 열폭주 가스(H2/CO/CH4) 폭발 압력 방산 최소 면적
# Av = C · As / √Pred [m²] (C = 방산 계수 약 0.05 bar^0.5, As = 내부 표면적 m²)
DEFLAGRATION_VENT_C = 0.05       # [가정] BESS 배터리 오도가스 혼합기 표준 벤트 계수 (NFPA 68 Table 7.3.3.2)
DEFLAGRATION_P_RED_BAR = 0.10    # [가정] 컨테이너 인클로저 설계 견딤 내압 (약 10 kPa = 0.10 bar)
DEFLAGRATION_MIN_RATIO_M2_M3 = 0.02  # 인클로저 체적당 최소 벤트 비율 (0.02 m²/m³, NFPA 855 권고 하한)


def deflagration_vent_area_m2(
    length_m: float,
    width_m: float,
    height_m: float = 2.9,
    p_red_bar: float = DEFLAGRATION_P_RED_BAR,
) -> dict:
    """
    NFPA 68 기준 인클로저 1기당 소요 폭발 방산 벤트 면적 (Av, m²).
    1) 표면적 기준 Av_surf = C · As / √Pred
    2) 체적비율 기준 Av_vol = V · 0.02 m²/m³
    최종 Av = max(Av_surf, Av_vol)
    """
    vol = length_m * width_m * height_m
    surf_area = 2.0 * (length_m * width_m + length_m * height_m + width_m * height_m)
    
    p_red = max(p_red_bar, 0.02)
    av_surf = (DEFLAGRATION_VENT_C * surf_area) / math.sqrt(p_red)
    av_vol = vol * DEFLAGRATION_MIN_RATIO_M2_M3
    av_req = max(av_surf, av_vol)
    
    # 표준 루프 벤트 패널 크기 (0.6m × 1.2m = 0.72 m² 패널 기준)
    panel_unit_area = 0.72
    panels_req = math.ceil(av_req / panel_unit_area)
    
    return {
        "vent_area_m2": round(av_req, 2),
        "panels_req": panels_req,
        "panel_unit_area_m2": panel_unit_area,
        "volume_m3": round(vol, 1),
        "surface_area_m2": round(surf_area, 1),
        "p_red_bar": p_red,
    }


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


# ── 배터리 증설(Augmentation) 경제성·용량 최적화 모델 ───────────────────────────
def simulate_battery_augmentation(
    project_years: int = 15,
    temp_c: float = 25.0,
    cycles_per_day: float = 1.0,
    dod: float = 0.95,
    required_ac_mwh: float = 400.0,
    eta_discharge: float = 0.938,
    soh_eol_target: float = 0.80,
    cell_cost_per_kwh_usd: float = 85.0,
    annual_cost_decline_pct: float = 4.0,
    discount_rate_pct: float = 6.0,
) -> dict:
    """
    [전략 A] Day-1 올인원(BOL 일괄 오버사이징) vs [전략 B] N차년도 증설(Augmentation) 비교.
    
    [작성 의도]:
    수명말 15~20년 후의 용량 보증을 맞추기 위해 Day-1에 125% 용량을 선시공하면
    초기 CAPEX가 과다해지고 배터리 단가 하락 혜택을 놓치게 됩니다.
    초기 105~110%만 설치하고 SOH 하락 시점(보통 5~7년차)에 부분 증설하는 전략의
    CAPEX 및 순현재가치(NPV) 절감액을 정량 산정합니다.
    """
    # 1. 연도별 단일 팩 잔존 SOH 곡선 (Year 0 ~ project_years)
    years_list = list(range(project_years + 1))
    soh_curve = [
        max(round(soh_pct(temp_c, float(y), cycles_per_day, dod), 2), 50.0)
        for y in years_list
    ]
    eol_soh = soh_curve[-1] / 100.0  # 최종 연도 실제 잔존 SOH 비율
    
    # 2. 기준 필요 DC 용량 (보증 용량을 상시 만족하기 위한 명목 DC 용량)
    # 전략 A (Day-1 올인원): EOL 시점에도 required_ac_mwh 를 공급할 수 있도록 초기 오버사이징
    # EOL 시점 잔존율이 낮을수록 분모가 작아져 초기 설치량이 커진다.
    target_eol_ratio = min(eol_soh, soh_eol_target)
    base_dc_mwh = required_ac_mwh / (eta_discharge * dod)
    strat_a_initial_mwh = base_dc_mwh / max(target_eol_ratio, 0.5)

    # 전략 B (Augmentation): 초기 5년차 수준(SOH 약 82~85%)을 커버하는 용량 선시공 (약 1.15~1.18배)
    # 5~7년차에 도달하여 base_dc_mwh 아래로 떨어질 때 1회 증설
    mid_life_soh = soh_curve[min(5, project_years)] / 100.0
    strat_b_initial_mwh = base_dc_mwh / max(mid_life_soh, 0.75) * 0.98

    # 연도별 용량 추적 및 증설 시점 탐색
    aug_year = None
    aug_mwh = 0.0
    for y in range(1, project_years + 1):
        existing_cap = strat_b_initial_mwh * (soh_curve[y] / 100.0)
        if existing_cap < base_dc_mwh and aug_year is None:
            aug_year = y
            # EOL 시점에 합산 용량이 base_dc_mwh 이상 되도록 잔여 수명 SOH 감안 증설
            rem_years = project_years - aug_year
            aug_pack_eol_soh = soh_pct(temp_c, float(rem_years), cycles_per_day, dod) / 100.0
            deficit_at_eol = max(base_dc_mwh - (strat_b_initial_mwh * eol_soh), base_dc_mwh * 0.1)
            aug_mwh = deficit_at_eol / max(aug_pack_eol_soh, 0.5)
            break

    if aug_year is None:
        aug_year = max(project_years // 2, 5)
        aug_mwh = base_dc_mwh * 0.15
        
    # 3. 연도별 배터리 유효 공급 용량 (MWh)
    strat_a_capacities = []
    strat_b_capacities = []
    for y in years_list:
        # A: 초기 팩 열화
        strat_a_capacities.append(round(strat_a_initial_mwh * (soh_curve[y] / 100.0), 1))
        # B: 초기 팩 열화 + 증설 팩 열화(증설 연도 이후)
        b_cap = strat_b_initial_mwh * (soh_curve[y] / 100.0)
        if y >= aug_year:
            pack_age = y - aug_year
            aug_soh = soh_pct(temp_c, float(pack_age), cycles_per_day, dod) / 100.0
            b_cap += aug_mwh * aug_soh
        strat_b_capacities.append(round(b_cap, 1))

    # 4. 비용 산정 ($ 및 NPV)
    # 단가 ($/MWh) = cell_cost_per_kwh_usd * 1000
    cost_y0 = cell_cost_per_kwh_usd * 1000.0
    cost_aug_year = cost_y0 * ((1.0 - (annual_cost_decline_pct / 100.0)) ** aug_year)
    discount_factor = (1.0 + (discount_rate_pct / 100.0)) ** aug_year
    
    # 전략 A 총 투자비 (Year 0 일시불)
    capex_a = strat_a_initial_mwh * cost_y0
    npv_a = capex_a
    
    # 전략 B 총 투자비 (Year 0 + Year N 증설)
    capex_b_initial = strat_b_initial_mwh * cost_y0
    capex_b_aug = aug_mwh * cost_aug_year
    npv_b = capex_b_initial + (capex_b_aug / discount_factor)
    
    # 절감액 및 절감률
    initial_savings_usd = capex_a - capex_b_initial
    initial_savings_pct = (initial_savings_usd / capex_a) * 100.0
    
    npv_savings_usd = npv_a - npv_b
    npv_savings_pct = (npv_savings_usd / npv_a) * 100.0
    
    return {
        "years": years_list,
        "soh_curve": soh_curve,
        "strat_a_initial_mwh": round(strat_a_initial_mwh, 2),
        "strat_a_capacities": strat_a_capacities,
        "capex_a_usd": round(capex_a, 0),
        "strat_b_initial_mwh": round(strat_b_initial_mwh, 2),
        "strat_b_aug_year": aug_year,
        "strat_b_aug_mwh": round(aug_mwh, 2),
        "strat_b_capacities": strat_b_capacities,
        "capex_b_initial_usd": round(capex_b_initial, 0),
        "capex_b_aug_usd": round(capex_b_aug, 0),
        "npv_a_usd": round(npv_a, 0),
        "npv_b_usd": round(npv_b, 0),
        "initial_savings_usd": round(initial_savings_usd, 0),
        "initial_savings_pct": round(initial_savings_pct, 1),
        "npv_savings_usd": round(npv_savings_usd, 0),
        "npv_savings_pct": round(npv_savings_pct, 1),
        "base_target_dc_mwh": round(base_dc_mwh, 1),
    }


# ── 부지 규모별 소방·하이드란트·번드월·배수 인프라 산정 (CBOP / FBOP) ──────────────
def calc_site_cbop_infrastructure(
    capacity_mwh: float = 100.0,
    power_mw: float = 25.0,
    n_enc: int = 20,
    tr_mva: float = 30.0,
    site_w_m: float = 80.0,
    site_h_m: float = 60.0,
    market: str = "US",
) -> dict:
    """
    사이트 규모(MWh, MW, 인클로저 수, 변압기 용량, 부지 면적)에 따른
    소방 수조, 소화전(Hydrant), 변압기 방유제(Bund Wall), 배수 저류조(Retention Basin),
    소방 펌프실 및 O&M 자재 저장소 규격 정밀 산정.
    
    [적용 규격]:
      - NFPA 855 / NFPA 850: BESS 소방수원 및 변압기 절연유 방유턱 체적
      - NFPA 24 / NFPC 109: 옥외 소화전 간격 (45~50m) 및 방수량 (2구 동시 2시간 = 228 m³)
      - IEEE 980 / IEC 61936-1: 유입변압기 절연유 100% + 소방방수량 + 강우 여유고
      - EPA Stormwater / NFPA 855 §4.4.5: 오염 소화폐수 차집 저류조
    """
    cap_mwh = max(float(capacity_mwh), 1.0)
    p_mw = max(float(power_mw), 0.5)
    enc_cnt = max(int(n_enc), 1)
    mva = max(float(tr_mva if tr_mva else p_mw * 1.15), 5.0)

    # 1. 변압기 오일 방유제(Bund Wall / Oil Retention Basin) 산정
    # 절연유 비체적: 통상 1 MVA 당 약 0.85~0.95 m³ (약 0.75~0.85 톤)
    oil_vol_m3 = mva * 0.90
    # NFPA 850 기준 소방 Deluge 고정방수량 (외표면적 10.2 L/min/m² × 10분)
    fire_deluge_m3 = 120.0 * 10.2 * 10.0 / 1000.0  # 약 12.24 m³
    # 24시간 설계 강우량 (150 mm)
    bund_l, bund_w = 8.0 + 2.4, 6.0 + 2.4  # TR 외형(8×6m) 둘레 사방 1.2m 확장
    bund_area_m2 = bund_l * bund_w          # 10.4m × 8.4m = 87.36 m²
    rain_vol_m3 = bund_area_m2 * 0.150      # 약 13.1 m³
    bund_req_m3 = oil_vol_m3 + fire_deluge_m3 + rain_vol_m3
    # 방유턱 높이 H_bund (최소 0.5m, 통상 0.6~0.9m)
    bund_height_m = max(0.50, round(bund_req_m3 / bund_area_m2, 2))

    # 2. 옥외 소화전(Outdoor Fire Hydrant) 수량 및 간격 산정
    perimeter_m = 2.0 * (site_w_m + site_h_m)
    # NFPA 24 / 855 기준 소화전 간격 45~50m
    hydrant_spacing_m = 45.0
    num_hydrants = max(4, math.ceil(perimeter_m / hydrant_spacing_m))
    # 소화전 방수량: 2구 동시 사용 500 gpm (1,900 L/min) × 120분 = 228 m³
    hydrant_water_m3 = 228.0

    # 3. 소방 수조(Fire Water Tank) 총 수원 산정
    # 컨테이너 고정식 소화설비 (동시 1~2기 방호 120분분)
    fixed_ext_m3 = min(max(enc_cnt * 2.5, 30.0), 90.0)
    total_fire_water_m3 = round((hydrant_water_m3 + fixed_ext_m3) * 1.15, 1)  # 15% 안전여유
    # 수조 치수 (높이 3.0m 기준 평면)
    tank_side_m = round(math.sqrt(total_fire_water_m3 / 3.0), 2)

    # 4. 소방 가압 펌프실(Fire Pump House) 규격
    # 주펌프 + 예비 디젤펌프 + 충압펌프 + 제어반 수용 패키지 컨테이너
    pump_house_dim = (6.05, 2.44, 2.90)  # 표준 20ft 컨테이너 규격

    # 5. 부지 우수 배수 및 소방 오염 폐수 저류조(Retention Basin)
    # NFPA 855 §4.4.5: 방출된 소화폐수(중금속/전해액 함유) 외부 유출 방지용 저류조
    basin_vol_m3 = round(max(total_fire_water_m3 * 0.75, 100.0), 1)
    basin_depth_m = 1.80
    basin_area_m2 = round(basin_vol_m3 / basin_depth_m, 1)
    basin_l = round(math.sqrt(basin_area_m2 * 1.33), 1)
    basin_w = round(basin_area_m2 / basin_l, 1)

    # 6. O&M 예비품 및 특수 자재 보관소(Spare Parts & Tool Storage)
    storage_dim = (6.05, 2.44, 2.90)  # 20ft HC 보관 컨테이너

    return {
        "capacity_mwh": cap_mwh,
        "power_mw": p_mw,
        "num_enclosures": enc_cnt,
        "tr_mva": mva,
        # 번드월 (방유제)
        "bund_oil_vol_m3": round(oil_vol_m3, 1),
        "bund_req_m3": round(bund_req_m3, 1),
        "bund_dim": (round(bund_l, 2), round(bund_w, 2), bund_height_m),
        "bund_area_m2": round(bund_area_m2, 1),
        "bund_height_m": bund_height_m,
        # 소화전
        "perimeter_m": round(perimeter_m, 1),
        "num_hydrants": num_hydrants,
        "hydrant_spacing_m": hydrant_spacing_m,
        "hydrant_water_m3": hydrant_water_m3,
        # 소방수조 및 펌프실
        "fixed_ext_m3": round(fixed_ext_m3, 1),
        "total_fire_water_m3": total_fire_water_m3,
        "tank_side_m": tank_side_m,
        "pump_house_dim": pump_house_dim,
        # 배수 저류조
        "basin_vol_m3": basin_vol_m3,
        "basin_dim": (basin_l, basin_w, basin_depth_m),
        "basin_area_m2": basin_area_m2,
        # 예비품 저장소
        "storage_dim": storage_dim,
    }


# ── 토목·방재 BOP 상세 물량산출(BOQ) 및 개략 공사비(CAPEX) 자동 산출기 ─────────
def calc_cbop_boq_and_cost(
    site_w_m: float = 80.0,
    site_h_m: float = 60.0,
    n_enc: int = 20,
    n_pcs: int = 10,
    pad_l: float = 6.0,
    pad_w: float = 2.4,
    pad_t: float = 0.40,
    trench_len_m: float = 120.0,
    trench_w: float = 0.80,
    trench_d: float = 1.00,
    infra: dict = None,
    market: str = "US",
) -> dict:
    """
    BESS 사이트 기하 및 인프라 설계 기반 토목(CBOP)·소방(FBOP) 상세 물량산출서(BOQ)
    및 시장별 개략 공사비(CAPEX) 자동 집계 엔진.

    5대 공종:
      1) 토공사 (Earthwork): 터파기, 잔토처리/되메우기, 부지정지
      2) 철근콘크리트 (Reinforced Concrete): 패드, 방유턱, 트렌치 타설
      3) 트렌치 커버 및 트레이 (Trench Covers & Cable Tray)
      4) 소방 및 방재 설비 (Fire Protection & Hydrant Loop)
      5) 부대 토목 (Site Civil & Fencing): 외곽 펜스, 자갈 포장, 저류조 차수막
    """
    site_w = max(float(site_w_m), 10.0)
    site_h = max(float(site_h_m), 10.0)
    site_area_m2 = site_w * site_h
    perimeter_m = 2.0 * (site_w + site_h)
    
    enc_cnt = max(int(n_enc), 1)
    pcs_cnt = max(int(n_pcs), 1)
    t_len = max(float(trench_len_m), 10.0)
    
    if infra is None:
        infra = calc_site_cbop_infrastructure(
            capacity_mwh=enc_cnt * 5.0, power_mw=pcs_cnt * 2.5,
            n_enc=enc_cnt, site_w_m=site_w, site_h_m=site_h, market=market
        )

    # ── 1. 콘크리트 체적 계산 (m³) ──
    v_pad_enc = enc_cnt * (pad_l * pad_w * pad_t)
    v_pad_pcs = pcs_cnt * (3.5 * 2.0 * pad_t)
    v_pad_tr = 1.0 * (6.0 * 5.0 * 0.50)  # 변압기 중량 지지 패드
    v_pad_ehouse = 1.0 * (12.2 * 2.44 * pad_t)  # 40ft E-House 패드
    # 방유턱 콘크리트: 둘레 x 벽두께 0.3m x 높이
    bund_h = infra.get("bund_height_m", 0.8)
    bund_dim = infra.get("bund_dim", (10.4, 8.4, bund_h))
    bund_perim = 2.0 * (bund_dim[0] + bund_dim[1])
    v_bund_wall = bund_perim * 0.30 * bund_h
    # 트렌치 콘크리트 구조체 (바닥 150mm + 양측벽 150mm)
    v_trench_conc = t_len * ((trench_w + 0.30) * (trench_d + 0.15) - (trench_w * trench_d))
    
    conc_total_m3 = round(v_pad_enc + v_pad_pcs + v_pad_tr + v_pad_ehouse + v_bund_wall + v_trench_conc, 1)

    # ── 2. 토공량 계산 (m³) ──
    # 패드 하부 터파기 (여유폭 0.6m, 기초 깊이 0.8m)
    v_exc_pads = enc_cnt * (pad_l + 0.6) * (pad_w + 0.6) * 0.8
    v_exc_pads += pcs_cnt * (3.5 + 0.6) * (2.0 + 0.6) * 0.8
    v_exc_pads += 1.0 * (6.0 + 1.0) * (5.0 + 1.0) * 1.0  # TR 터파기
    v_exc_pads += 1.0 * (12.2 + 0.8) * (2.44 + 0.8) * 0.8  # E-House
    # 트렌치 터파기 (터파기 폭 trench_w + 0.4m, 깊이 trench_d + 0.2m)
    v_exc_trench = t_len * (trench_w + 0.40) * (trench_d + 0.20)
    # 비상 저류조 터파기 (저류조 체적 + 15% 여유)
    basin_m3 = infra.get("basin_vol_m3", 150.0)
    v_exc_basin = basin_m3 * 1.15
    
    excav_total_m3 = round(v_exc_pads + v_exc_trench + v_exc_basin, 1)
    backfill_total_m3 = round(max(0.0, excav_total_m3 - conc_total_m3), 1)

    # ── 3. 방재 및 소방 물량 ──
    tank_m3 = infra.get("total_fire_water_m3", 200.0)
    num_hydrants = infra.get("num_hydrants", 6)
    basin_area_m2 = infra.get("basin_area_m2", 120.0)
    # 소화전 환상 링 배관 (부지 둘레 기준 연장)
    fire_pipe_len_m = round(perimeter_m * 0.95, 1)

    # ── 4. 단가 테이블 (USD 기준, 실무 EPC 기준 단가) ──
    # 한국 원화 환산 시 1,350원/USD 적용 가능
    rates = {
        "site_grading_m2": 6.5,       # 부지 정지 및 롤러 다짐 ($/m²)
        "excavation_m3": 28.0,        # 토사/풍화암 터파기 및 상차 ($/m³)
        "backfill_m3": 14.0,          # 양질토 되메우기 및 다짐 ($/m³)
        "conc_pad_m3": 380.0,         # 인클로저/PCS RC 슬래브 (24MPa+철근+거푸집) ($/m³)
        "conc_tr_bund_m3": 440.0,     # TR 고강도 패드 및 방유벽 콘크리트 ($/m³)
        "conc_trench_m3": 360.0,      # 케이블 트렌치 콘크리트 타설 ($/m³)
        "trench_grating_m": 125.0,    # HDG 스틸 그레이팅 커버 ($/m)
        "fire_tank_m3": 220.0,        # 원통형 볼트조립 소방 수조 본체 ($/m³)
        "fire_pump_package": 65000.0, # 소방 가압펌프실 패키지 (주펌프+디젤예비+컨테이너, 1식)
        "hydrant_ea": 3500.0,         # 옥외 소화전 세트 (지상식 소화전 + PIV) ($/ea)
        "fire_pipe_m": 115.0,         # D150/D200 지하 매설 주철관 ($/m)
        "basin_liner_m2": 32.0,       # 비상 저류조 HDPE 차수막 및 집수 유수지 ($/m²)
        "fence_m": 85.0,              # 외곽 보안 펜스 (H=2.4m + 3열 유자선) ($/m)
        "gravel_paving_m2": 18.0,     # 부지 쇄석(자갈) 포장 t=100mm ($/m²)
    }

    # ── 5. 세부 BOQ 품목 산출 ──
    gravel_area_m2 = round(max(site_area_m2 * 0.45, 200.0), 1)  # 설비/도로 외 쇄석 포장
    qty_pad_conc = round(v_pad_enc + v_pad_pcs + v_pad_ehouse, 1)
    qty_tr_bund_conc = round(v_pad_tr + v_bund_wall, 1)
    qty_trench_conc = round(v_trench_conc, 1)

    items = [
        # [공종 1: 토공사]
        {"category": "토공사 (Earthwork)", "item": "부지 정지 및 롤러 다짐", "spec": "표토제거 및 95% 다짐도",
         "qty": round(site_area_m2, 1), "unit": "m²", "unit_cost": rates["site_grading_m2"],
         "cost_usd": round(round(site_area_m2, 1) * rates["site_grading_m2"])},
        {"category": "토공사 (Earthwork)", "item": "구조물 및 트렌치 터파기", "spec": "기초/트렌치/저류조 터파기 (토사 80%, 암 20%)",
         "qty": excav_total_m3, "unit": "m³", "unit_cost": rates["excavation_m3"],
         "cost_usd": round(excav_total_m3 * rates["excavation_m3"])},
        {"category": "토공사 (Earthwork)", "item": "되메우기 및 잔토처리", "spec": "구조물 주변 층다짐 및 잉여토 반출",
         "qty": backfill_total_m3, "unit": "m³", "unit_cost": rates["backfill_m3"],
         "cost_usd": round(backfill_total_m3 * rates["backfill_m3"])},

        # [공종 2: 철근콘크리트 공사]
        {"category": "철근콘크리트 (Concrete)", "item": "인클로저/PCS/E-House 기초 패드", "spec": "fck=24MPa, 철근 D13/D16 복배근, t=0.4m",
         "qty": qty_pad_conc, "unit": "m³", "unit_cost": rates["conc_pad_m3"],
         "cost_usd": round(qty_pad_conc * rates["conc_pad_m3"])},
        {"category": "철근콘크리트 (Concrete)", "item": "주변압기 패드 및 오일 방유벽", "spec": "fck=30MPa 내유콘크리트, 방유턱 H=" + f"{bund_h}m",
         "qty": qty_tr_bund_conc, "unit": "m³", "unit_cost": rates["conc_tr_bund_m3"],
         "cost_usd": round(qty_tr_bund_conc * rates["conc_tr_bund_m3"])},
        {"category": "철근콘크리트 (Concrete)", "item": "케이블 트렌치 콘크리트 구조체", "spec": "fck=24MPa, 바닥/벽체 t=0.15m",
         "qty": qty_trench_conc, "unit": "m³", "unit_cost": rates["conc_trench_m3"],
         "cost_usd": round(qty_trench_conc * rates["conc_trench_m3"])},

        # [공종 3: 트렌치 커버 및 트레이]
        {"category": "트렌치 커버 (Trench Cover)", "item": "트렌치 HDG 스틸 그레이팅 커버", "spec": "차량 하중 고려 T-20 중하중용 용융아연도금",
         "qty": round(t_len, 1), "unit": "m", "unit_cost": rates["trench_grating_m"],
         "cost_usd": round(round(t_len, 1) * rates["trench_grating_m"])},

        # [공종 4: 소방 및 방재 설비]
        {"category": "소방/방재 설비 (Firefighting)", "item": "소방 수조 본체 및 기초", "spec": f"볼트조립식 원통형 수조 {tank_m3} m³ (NFPA 855)",
         "qty": round(tank_m3, 1), "unit": "m³", "unit_cost": rates["fire_tank_m3"],
         "cost_usd": round(round(tank_m3, 1) * rates["fire_tank_m3"])},
        {"category": "소방/방재 설비 (Firefighting)", "item": "소방 가압펌프실 패키지", "spec": "주펌프(전기)+예비(디젤)+충압 20ft 컨테이너 일체형",
         "qty": 1.0, "unit": "식", "unit_cost": rates["fire_pump_package"],
         "cost_usd": round(1.0 * rates["fire_pump_package"])},
        {"category": "소방/방재 설비 (Firefighting)", "item": "옥외 소화전 세트", "spec": "지상식 2구 옥외소화전 + PIV 밸브 (NFPA 24)",
         "qty": float(num_hydrants), "unit": "ea", "unit_cost": rates["hydrant_ea"],
         "cost_usd": round(float(num_hydrants) * rates["hydrant_ea"])},
        {"category": "소방/방재 설비 (Firefighting)", "item": "소방 링루프 지하 매설 배관", "spec": "D150/D200 덕타일 주철관(K9) 매설",
         "qty": fire_pipe_len_m, "unit": "m", "unit_cost": rates["fire_pipe_m"],
         "cost_usd": round(fire_pipe_len_m * rates["fire_pipe_m"])},
        {"category": "소방/방재 설비 (Firefighting)", "item": "비상 배수 저류조 및 차수막", "spec": f"소화폐수 차집 유수지 {basin_m3} m³, HDPE 차수막 1.5mm",
         "qty": basin_area_m2, "unit": "m²", "unit_cost": rates["basin_liner_m2"],
         "cost_usd": round(basin_area_m2 * rates["basin_liner_m2"])},

        # [공종 5: 부대 토목 및 울타리]
        {"category": "부대 토목 (Site Works)", "item": "외곽 보안 울타리 및 출입문", "spec": "H=2.4m 능형망 + 상부 3열 Y형 유자철선 + 슬라이딩게이트",
         "qty": round(perimeter_m, 1), "unit": "m", "unit_cost": rates["fence_m"],
         "cost_usd": round(round(perimeter_m, 1) * rates["fence_m"])},
        {"category": "부대 토목 (Site Works)", "item": "부지 쇄석(자갈) 포장", "spec": "잡초 방지 부직포 + 쇄석 t=100mm 포장",
         "qty": gravel_area_m2, "unit": "m²", "unit_cost": rates["gravel_paving_m2"],
         "cost_usd": round(gravel_area_m2 * rates["gravel_paving_m2"])},
    ]

    total_capex_usd = sum(it["cost_usd"] for it in items)
    
    # 공종별 소계 집계
    cat_summary = {}
    for it in items:
        cat = it["category"]
        cat_summary[cat] = cat_summary.get(cat, 0.0) + it["cost_usd"]

    return {
        "items": items,
        "cat_summary": cat_summary,
        "total_capex_usd": total_capex_usd,
        "total_capex_krw": round(total_capex_usd * 1350.0),
        "quantities": {
            "site_area_m2": site_area_m2,
            "perimeter_m": perimeter_m,
            "excavation_total_m3": excav_total_m3,
            "backfill_total_m3": backfill_total_m3,
            "concrete_total_m3": conc_total_m3,
            "trench_len_m": t_len,
            "fire_water_m3": tank_m3,
            "num_hydrants": num_hydrants,
            "fire_pipe_m": fire_pipe_len_m,
            "bund_wall_m3": round(v_bund_wall, 1),
            "basin_m3": basin_m3,
        }
    }


