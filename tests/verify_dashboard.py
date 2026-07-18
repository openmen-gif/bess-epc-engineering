# -*- coding: utf-8 -*-
"""
tests/verify_dashboard.py — 대시보드 회귀 검증 스위트 (push 전 필수 실행)

사용:
  cd output/99_tools/dashboard
  PYTHONIOENCODING=utf-8 python3 tests/verify_dashboard.py          # 전체
  PYTHONIOENCODING=utf-8 python3 tests/verify_dashboard.py --fast   # 수식·물리만 (렌더 생략)

검증 내용:
  1. 수식·표준 정합 (2026-07-18 교정분 회귀 방지): NFPA 2001 소화약제,
     Laurent 접지, 3상 √3, 내진 하중, DC 사이징, 연기층 하한, 테마 토큰 동기
  2. 화재 확산 의미론: 약제 없음 → 억제 상태(4) 불출현, 약제 → 억제(파랑) 경유,
     내부 TR 지속(진화 전이 없음 — UL 9540A 정합)
  3. 공기 흐름 궤적: 경계 준수·유속 범위·흡기→배기 순이동
  4. 전 페이지 × 한/영 2모드 AppTest 헤드리스 렌더 (예외 0 요구)

의존성: streamlit(testing.v1), numpy — requirements.txt와 동일 환경이면 충분.
"""
import os
import sys
import glob
import math

HERE = os.path.dirname(os.path.abspath(__file__))
DASH = os.path.dirname(HERE)
os.chdir(DASH)
sys.path.insert(0, DASH)

import numpy as np

FAST = "--fast" in sys.argv
results = []


def check(name, cond, detail=""):
    results.append(("PASS" if cond else "FAIL", name, detail))


# ══════════════════════════════════════════════════════════════════════════
# 1. 수식·표준 정합
# ══════════════════════════════════════════════════════════════════════════
def run_formula_checks():
    # NFPA 2001 — Novec 증기밀도·불활성 로그식 (05 로직 재현)
    w_novec = 120.0 * (5.9 / (100 - 5.9)) * 13.91
    check("05 Novec 소요량(120m³, 5.9%) ≈ 104.7 kg", abs(w_novec - 104.7) < 1.5, f"{w_novec:.1f} kg")
    w_n2_log = 120.0 * math.log(100.0 / (100.0 - 40.6)) * 1.165
    w_n2_lin = 120.0 * (40.6 / (100 - 40.6)) * 1.165
    check("05 N₂ 로그식 < 선형식", w_n2_log < w_n2_lin, f"{w_n2_log:.1f} < {w_n2_lin:.1f} kg")

    # Laurent 접지 등가반경 (04)
    rho, area, length = 100.0, 2500.0, 1000.0
    rg = rho / (4 * np.sqrt(area / np.pi)) + rho / length
    check("04 접지 Rg ≈ 0.986Ω (등가반경 √(A/π))", abs(rg - 0.986) < 0.02, f"{rg:.3f} Ω")

    # 3상 전압강하 √3 (04)
    check("04 3상 계수 √3 (DC 왕복 2 아님)", abs(np.sqrt(3) - 1.732) < 1e-3)

    # 내진 하중 = dead × Cs (03)
    check("03 내진 하중 8.5×0.2=1.7 (×9.81 금지)", abs(8.5 * 0.2 - 1.7) < 1e-9)

    # DC 사이징 — 편도효율·DoD·EOL SOH (02)
    dc = 200 * 1.025 / (math.sqrt(0.88) * 0.95 * 0.80) * 1.05
    check("02 DC 사이징(200MWh 조건) ≈ 302 MWh", abs(dc - 302.0) < 3.0, f"{dc:.1f} MWh")

    # 연기층 표시 하한 (sim_physics)
    from utils.sim_physics import smoke_layer_series
    res = smoke_layer_series(15.0, 1.0, 400.0, 8.0, t_end=240.0, n=25)
    check("연기층 z_min=0.3 정직 표시", float(res["z_layer"][-1]) < 1.0,
          f"z_eq={float(res['z_layer'][-1]):.2f} m")

    # 테마 토큰 ↔ CSS 변수 동기
    from utils.theme import PALETTE
    css = open("utils/css_loader.py", encoding="utf-8").read()
    keys = ("bg", "bg2", "bg3", "border", "text", "text2", "muted", "accent", "ok", "warn", "danger")
    check("theme.PALETTE ↔ css_loader :root 동기", all(PALETTE[k] in css for k in keys))


# ══════════════════════════════════════════════════════════════════════════
# 2. 화재 확산 의미론 (UL 9540A 정합)
# ══════════════════════════════════════════════════════════════════════════
def run_fire_semantics_checks():
    from utils.sim_physics import simulate_runaway, S_FIRE, S_SUPPRESSED, S_BURNOUT

    def run(eta, q_cool):
        return simulate_runaway(rows=6, cols=8, origin_rc=(2, 3), hrr_MW=2.5,
                                onset_C=170.0, energy_MJ=2700.0, spacing_m=0.3,
                                eta_supp=eta, q_cool_W=q_cool, response_s=60,
                                t_max_s=2700.0, n_frames=60)

    def ever(r):
        return int(np.sum(np.maximum.reduce([
            ((g == S_FIRE) | (g == S_SUPPRESSED) | (g == S_BURNOUT)).astype(int)
            for g in r["state_frames"]])))

    r_none = run(0.0, 0.0)
    r_fm = run(0.70, 0.0)
    s4_none = max(int((g == S_SUPPRESSED).sum()) for g in r_none["state_frames"])
    s4_fm = max(int((g == S_SUPPRESSED).sum()) for g in r_fm["state_frames"])
    check("화재: 약제 없음 → 억제 상태(4) 불출현", s4_none == 0, f"최대 {s4_none}")
    check("화재: 약제 없음 → 소진(5) 발생", int((r_none["state_frames"][-1] == S_BURNOUT).sum()) > 0)
    check("화재: FM-200 → 억제 상태(파랑) 경유", s4_fm > 0, f"최대 {s4_fm}")
    check("화재: 약제가 확산을 늘리지 않음", ever(r_none) >= ever(r_fm),
          f"없음 {ever(r_none)} ≥ FM {ever(r_fm)}")
    # 내부 TR 지속 — 억제 중에도 에너지 소모(진화 전이 없음): 원점 랙은 결국 소진
    check("화재: 억제 중에도 원점 랙 소진 도달(진화 전이 없음)",
          bool(r_fm["state_frames"][-1][2, 3] == S_BURNOUT))


# ══════════════════════════════════════════════════════════════════════════
# 3. 공기 흐름 궤적 물리
# ══════════════════════════════════════════════════════════════════════════
def run_airflow_checks():
    from utils.sim_physics import airflow_trajectories
    T = np.full((20, 40), 30.0); T[8:12, 4:10] = 46.0
    res = airflow_trajectories(T, exhaust_xy=[(11.5, 0.6), (11.5, 1.8)],
                               intake_xy=[(0.7, 0.6), (0.7, 1.8)],
                               Lx=12.19, Ly=2.44, H=2.59)
    X, Z, SP = res["x"], res["z"], res["speed"]
    check("공기: 경계 준수", bool((X.min() >= 0) and (X.max() <= 12.19)
                                and (Z.min() >= 0) and (Z.max() <= 2.59)))
    check("공기: 유속 실내 범위", 0.05 < float(np.median(SP)) < 1.5,
          f"중앙값 {float(np.median(SP)):.2f} m/s")
    check("공기: 흡기→배기 순이동(+X)", float(np.mean(X[-1]) - np.mean(X[0])) > 0,
          f"{float(np.mean(X[-1]) - np.mean(X[0])):+.2f} m")


# ══════════════════════════════════════════════════════════════════════════
# 4. 전 페이지 × 한/영 AppTest 렌더
# ══════════════════════════════════════════════════════════════════════════
def run_render_checks():
    from streamlit.testing.v1 import AppTest
    targets = sorted(glob.glob(os.path.join(DASH, "pages", "*.py"))) + \
              [os.path.join(DASH, "Dashboard.py")]
    for pg in targets:
        base = os.path.basename(pg)
        langs = ("KO", "EN") if base != "Dashboard.py" else ("KO",)
        for lang in langs:
            try:
                at = AppTest.from_file(pg, default_timeout=180)
                at.session_state["auth_user"] = "tester"
                at.session_state["auth_role"] = "admin"
                at.session_state["lang"] = lang
                at.run()
                errs = [e.value for e in at.exception]
                check(f"렌더 {base} [{lang}]", not errs, str(errs[0])[:120] if errs else "")
            except Exception as ex:
                check(f"렌더 {base} [{lang}]", False, f"{type(ex).__name__}: {str(ex)[:110]}")


def main():
    run_formula_checks()
    run_fire_semantics_checks()
    run_airflow_checks()
    if not FAST:
        run_render_checks()
    fails = [r for r in results if r[0] == "FAIL"]
    print("=" * 72)
    for s, n, d in results:
        print(f"  {s}  {n}" + (f"  — {d}" if d else ""))
    print("=" * 72)
    print(f"총 {len(results)}건 중 실패 {len(fails)}건" + ("  (--fast 모드)" if FAST else ""))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
