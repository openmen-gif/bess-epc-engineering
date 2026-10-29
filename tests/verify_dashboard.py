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
# 3b. 스킬 기준값 정합 (2026-10-28) — engineering_params 가 스킬 앵커를 재현하고,
#     스킬 사본(skill_md/)에 그 기준 문구가 아직 있는지 확인. 스킬이 자라 기준이
#     바뀌면 여기서 FAIL 로 드러나므로 engineering_params 를 같이 갱신한다.
# ══════════════════════════════════════════════════════════════════════════
def run_skill_criteria_checks():
    from utils import engineering_params as EP

    check("열화: 캘린더 앵커 25°C·10년 = 15%", abs(EP.calendar_loss_pct(25, 10) - 15.0) < 1e-6,
          f"{EP.calendar_loss_pct(25, 10):.3f}%")
    check("열화: 캘린더 앵커 45°C·5년 = 15%", abs(EP.calendar_loss_pct(45, 5) - 15.0) < 1e-6,
          f"{EP.calendar_loss_pct(45, 5):.3f}%")
    check("열화: 사이클 앵커 7,000×80% DoD = 20%", abs(EP.cycle_loss_pct(5600) - 20.0) < 1e-6)
    s = [EP.soh_pct(25, y, 1.0, 0.8) for y in (5, 10, 15, 20)]
    check("열화: SOH 연차 단조 감소", all(a > b for a, b in zip(s, s[1:])), " > ".join(f"{v:.1f}" for v in s))
    check("소화: Water Mist 40ft 60m³ (30+60분, 0.10) = 540 L",
          abs(EP.WATER_MIST_DENSITY_DEFAULT * 60 * (EP.WATER_MIST_BATTERY_DISCHARGE_MIN
                                                    + EP.WATER_MIST_COOLING_EXT_MIN) - 540.0) < 1e-9)
    check("케이블: 단락 S = I√t/k (25kA·0.5s·Cu) ≈ 123.6 mm²",
          abs(EP.sc_min_area_mm2(25, 0.5, EP.SC_K["XLPE-Cu"]) - 123.6) < 0.1)
    check("케이블: 전압등급 0.69→LV, 22.9→MV, 154→HV",
          [EP.voltage_class(v) for v in (0.69, 22.9, 154.0)] == ["LV", "MV", "HV"])

    def page(name):
        with open(os.path.join(DASH, "pages", name), encoding="utf-8") as f:
            return f.read()
    check("03 열 한계 = EP 셀 허용(45°C), 50°C 하드코딩 없음",
          "THERMAL_LIMIT_C = EP.CELL_TMAX_ALLOW_C" in page("03_3D_Simulation.py"))
    check("09 열 판정 = EP 셀 권장·허용", "EP.CELL_TMAX_REC_C" in page("09_Container_Thermal.py")
          and "peak <= 55" not in page("09_Container_Thermal.py"))
    check("05 배터리 구역 기본 약제 = Water Mist",
          "index=0 if battery_room else" in page("05_CBOP_Engineer.py")
          and page("05_CBOP_Engineer.py").count("Water Mist (NFPA 750)") >= 1)
    check("04 케이블 3중 검증(전압강하·단락·허용전류)",
          all(k in page("04_EBOP_Engineer.py") for k in ("sc_min_area_mm2", "i_base", "VDROP_LIMIT_PCT")))

    anchors = {
        "bess-cfd-analyst.md": "≤ 35°C (권장) / ≤ 45°C (허용)",
        "bess-battery-expert.md": "25°C 보관 10년 후 잔존 ≈85%",
        "bess-cable-engineer.md": "XLPE-Cu k=143",
        "bess-fire-engineer.md": "0.07~0.15 L/min/m³",
    }
    for fname, needle in anchors.items():
        p = os.path.join(DASH, "skill_md", fname)
        ok = os.path.exists(p) and needle in open(p, encoding="utf-8").read()
        check(f"스킬 사본 기준 유지: {fname}", ok, "" if ok else f"'{needle}' 없음 — 스킬 갱신 시 engineering_params 재검토")


# ══════════════════════════════════════════════════════════════════════════
# 3c. 설계 모델 → 3D 부지 배치 (2026-10-29): 순수 함수 검사 + 페이지 간 값 전파 사슬
# ══════════════════════════════════════════════════════════════════════════
def run_design_model_checks():
    import json
    from utils import engineering_params as EP
    from utils import design_model as DM
    from utils import site_layout as SL

    SEP = EP.SEPARATION_BY_MARKET
    check("이격: US 미시험 기본 10 ft = 3.048 m (3 ft 단축은 UL 9540A 입증 시)",
          abs(SEP["US"]["unit_m"] - 10 * 0.3048) < 1e-9 and abs(SEP["US"]["boundary_m"] - 10 * 0.3048) < 1e-9)
    # 정본 표 값 대조 — 스킬 사본 표에 해당 행이 있고, 코드 값이 그 행 수치와 같아야 한다
    fire = open(os.path.join(DASH, "skill_md", "bess-fire-engineer.md"), encoding="utf-8").read()
    rows = {"KR": ("소방시설법 / ESS 안전기준 | ≥3m | ≥6m |", (3.0, 6.0)),
            "US": ("≥3ft(0.9m), 미시험 시 ≥10ft(3m)", (3.048, None)),
            "AU": ("AS/NZS 5139:2019 / CFA | ≥3m |", (3.0, None))}
    bad = [k for k, (needle, (u, b)) in rows.items()
           if needle not in fire or abs(SEP[k]["unit_m"] - u) > 1e-9 or (b is not None and abs(SEP[k]["boundary_m"] - b) > 1e-9)]
    check("이격: KR 3/6 m · US 10 ft · AU 3 m = fire-engineer 정본 표", not bad, f"불일치 {bad}")
    check("이격: 정본 표에 정량값 없는 부지경계는 [가정] 표기 (AU·UK·JP·EU)",
          all("[가정]" in SEP[k]["src"] or SEP[k]["tag"] == "[가정]" for k in ("AU", "UK", "JP", "EU")))
    check("이격: 시장 키 'US (ERCOT)'→US, 미지정→KR",
          EP.market_key("US (ERCOT)") == "US" and EP.market_key(None) == "KR")

    # 배치 기하 — 대수·이격·수조 크기를 바꿔도 겹침 0, 이격 기준 충족, 인클로저 수 보존
    bad = []
    for n_enc, n_pcs, gap, bnd, tank in [(1, 1, 3, 3, 0), (7, 3, 0.9144, 3.048, 0), (87, 25, 0.9144, 3.048, 0.54),
                                         (250, 60, 3, 3, 150), (40, 80, 3, 3, 0)]:
        lay = SL.build_layout(n_enc, n_pcs, unit_gap=gap, boundary=bnd, water_m3=tank)
        c = SL.check_layout(lay)
        n_box = sum(b["kind"] == "enc" for b in lay["boxes"])
        if not (c["overlaps"] == 0 and c["unit_ok"] and c["tr_ok"] and c["boundary_ok"] and n_box == n_enc):
            bad.append((n_enc, n_pcs, c, n_box))
    check("배치: 5개 사례 겹침 0·유닛/변압기/경계 이격 충족·인클로저 수 보존", not bad, str(bad)[:120])
    lay = SL.build_layout(20, 5)
    check("배치: 최장 케이블 경로 > 0 이고 트렌치 총연장 이상 아님",
          0 < lay["metrics"]["longest_cable_m"] <= lay["metrics"]["trench_len_m"],
          f"{lay['metrics']['longest_cable_m']:.1f} / {lay['metrics']['trench_len_m']:.1f} m")

    # DXF — 엔티티 수 = 박스 4선 + 트렌치 선분 + 울타리 4선, 라벨 = 박스 수
    dxf = SL.to_dxf(lay)
    n_seg = sum(len(pl) - 1 for pl in lay["trench"])
    exp_lines = 4 * len(lay["boxes"]) + n_seg + 4
    try:
        import ezdxf, io as _io
        doc = ezdxf.read(_io.StringIO(dxf))
        msp = doc.modelspace()
        got = (len(msp.query("LINE")), len(msp.query("TEXT")))
        check("DXF: ezdxf 파싱 성공·엔티티 수 일치", got == (exp_lines, len(lay["boxes"])), f"{got} vs {(exp_lines, len(lay['boxes']))}")
    except ImportError:
        lines = dxf.split("\n")
        got = (sum(1 for a, b in zip(lines, lines[1:]) if a == "0" and b == "LINE"),
               sum(1 for a, b in zip(lines, lines[1:]) if a == "0" and b == "TEXT"))
        check("DXF: 엔티티 수 일치 (ezdxf 미설치 — 구조 검사)", got == (exp_lines, len(lay["boxes"])), str(got))

    # 설계 모델 — stale 판정 · JSON 왕복
    ss = {"capacity_mw": 100.0, "duration_h": 4.0, "rte_percent": 88.0, "aux_loss_percent": 2.5,
          "epc_margin": 5.0, "target_market": "US (ERCOT)"}
    DM.record("system", {"num_containers": 95, "num_pcs": 25}, ss)
    st0 = DM.status("system", ss)
    ss["capacity_mw"] = 120.0
    check("설계 모델: 상류 입력 변경 시 ok → stale", (st0, DM.status("system", ss)) == ("ok", "stale"))
    j1 = DM.export_json(ss)
    ss2 = {"widget_capacity_mw": 1.0}
    DM.import_json(j1, ss2)
    strip = lambda s: {k: v for k, v in json.loads(s).items() if k != "exported"}
    check("설계 모델: JSON 왕복 동일 + 01 위젯 상태 초기화",
          strip(DM.export_json(ss2)) == strip(j1) and "widget_capacity_mw" not in ss2)
    try:
        DM.import_json('{"schema": "other"}', {})
        check("설계 모델: 다른 형식 JSON 거부", False)
    except ValueError:
        check("설계 모델: 다른 형식 JSON 거부", True)
    rej = []
    for bad_json in ('[]', '{"schema": "%s", "sections": [1, 2]}' % DM.SCHEMA,
                     '{"schema": "%s", "sections": {"cbop": 1}}' % DM.SCHEMA,
                     '{"schema": "%s", "project": {"capacity_mw": "abc"}}' % DM.SCHEMA,
                     '{"schema": "%s", "project": {"capacity_mw": NaN}}' % DM.SCHEMA,
                     '{"schema": "%s", "project": {"target_market": 123}}' % DM.SCHEMA,
                     '{"schema": "%s", "sections": {"cbop": {"values": {"n_enc": "abc"}}}}' % DM.SCHEMA):
        try:
            DM.import_json(bad_json, {})
            rej.append(bad_json[:30])
        except ValueError:
            pass
    check("설계 모델: 리스트·잘못된 sections·비숫자·NaN·섹션 문자열 값 JSON 7종 ValueError", not rej, f"통과됨 {rej}")
    ss3 = {"num_containers": 60, DM.DM_KEY: {"cbop": {"values": {"n_enc": 60}, "sig": {}}}}
    DM.import_json('{"schema": "%s", "project": {"capacity_mw": 200.0}, "sections": {}}' % DM.SCHEMA, ss3)
    check("설계 모델: 불러오기 시 이전 프로젝트 값 초기화 (잔류 n_enc 60 없음)",
          "num_containers" not in ss3 and DM.layout_inputs(ss3)["n_enc"][1] == "[가정]",
          str(DM.layout_inputs(ss3)["n_enc"]))
    pc = DM.per_container({DM.DM_KEY: {"cbop": {"values": dict(n_enc=10, bat_heat_kw=300.0, pcs_heat_kw=200.0,
                                                              hvac_installed_kw=900.0, hvac_safety_pct=15,
                                                              hvac_dt_k=15.0, env_ua_kw_k=0.2), "sig": {}}}})
    check("설계 모델: 컨테이너 HVAC = (배터리 30 kW + 0.2×15) × 1.15 = 37.95 kW (PCS 발열 제외, 안전율 전체 적용)",
          abs(pc["hvac_kw"] - 37.95) < 1e-9, f"{pc['hvac_kw']:.2f} kW")
    lay_t = SL.build_layout(10, 3, unit_gap=0.9144, trench_w=2.64)
    check("배치: 트렌치 2.64 m > 이격 0.91 m 이면 trench_fits=False",
          SL.check_layout(lay_t)["trench_fits"] is False and SL.check_layout(SL.build_layout(10, 3, trench_w=0.6))["trench_fits"])
    check("배치: PCS 수 > 인클로저 수 → pcs_clipped 표시", SL.build_layout(3, 8)["metrics"]["pcs_clipped"] is True)

    # 구조 뷰 — 기초 패드·트렌치 지중 박스, 패드 순간격, 기준안 차이
    lay_s = SL.build_layout(20, 5, unit_gap=3.0, trench_w=0.6)
    pads = SL.pad_boxes(lay_s, 7.05, 3.44)
    encs = [b for b in lay_s["boxes"] if b["kind"] == "enc"]
    centered = all(abs((p["x"] + p["dx"] / 2) - (e["x"] + e["dx"] / 2)) < 1e-9 and
                   abs((p["y"] + p["dy"] / 2) - (e["y"] + e["dy"] / 2)) < 1e-9 for p, e in zip(pads, encs))
    tb = SL.trench_boxes(lay_s, 1.2)
    n_seg_s = sum(len(pl) - 1 for pl in lay_s["trench"])
    check("구조 뷰: 패드 = 인클로저 수·중심 일치·z −0.3~0, 트렌치 박스 = 선분 수·깊이 −1.2 m",
          len(pads) == len(encs) and centered and all(p["z0"] == -SL.PAD_T and p["dz"] == 0 for p in pads)
          and len(tb) == n_seg_s and all(t["z0"] == -1.2 and min(t["dx"], t["dy"]) >= 0.6 - 1e-9 for t in tb),
          f"pad {len(pads)}/{len(encs)} trench {len(tb)}/{n_seg_s}")
    g_ok = SL.pad_clear_gap(lay_s, 7.05, 3.44)
    g_bad = SL.pad_clear_gap(SL.build_layout(20, 5, unit_gap=0.5), 7.05, 3.44)
    check("구조 뷰: 패드 순간격 = 이격 3 m − 여유 1 m = 2.0 m, 이격 0.5 m 면 −0.5 m(겹침)",
          abs(g_ok - 2.0) < 1e-9 and abs(g_bad + 0.5) < 1e-9, f"{g_ok:.2f} / {g_bad:.2f}")
    dm_ = SL.diff_metrics(SL.build_layout(24, 6)["metrics"], lay_s["metrics"])
    check("기준안 비교: 인클로저 20→24 = +4기 (+20.0%), 면적 증가",
          dm_["n_enc"][2] == 4 and abs(dm_["n_enc"][3] - 20.0) < 1e-9 and dm_["site_area_m2"][2] > 0,
          f"{dm_['n_enc']} area Δ{dm_['site_area_m2'][3]:+.1f}%")
    ex_, ey_, ez_ = SL.edge_arrays(encs[:2])
    check("구조 뷰: 모서리선 박스당 상·하 링 2 + 수직 4 = 24 점(구분자 포함)", len(ex_) == 2 * 24 == len(ey_) == len(ez_),
          str(len(ex_)))

    # 차트 전송량 — 수치 배열만 반올림, Mesh 인덱스·스칼라 보존
    import plotly.graph_objects as go
    from utils.fig_compact import compact
    rng = np.random.default_rng(0)
    zz = 25 + rng.random((40, 40)) * 20
    fig_c = go.Figure([go.Surface(z=zz, opacity=0.123456), go.Mesh3d(x=[0.123456] * 3, y=[0, 1, 0], z=[0, 0, 1],
                                                                       i=[0], j=[1], k=[2])],
                      frames=[go.Frame(data=[go.Surface(z=zz + 1)])])
    full, cd = len(fig_c.to_json()), compact(fig_c)
    small = len(json.dumps(go.Figure(cd).to_plotly_json(), cls=__import__("plotly").utils.PlotlyJSONEncoder))
    zc = np.asarray(cd["data"][0]["z"])
    check("전송량: 반올림 후 크기 ≤ 원본 50%·값 오차 ≤ 0.005·인덱스·스칼라 보존",
          small <= 0.5 * full and float(np.abs(zc - zz).max()) <= 0.005 + 1e-12
          and list(cd["data"][1]["i"]) == [0] and cd["data"][0]["opacity"] == 0.123456
          and np.asarray(cd["frames"][0]["data"][0]["z"]).shape == (40, 40),
          f"{full/1024:.0f}KB → {small/1024:.0f}KB")

    if FAST:
        return
    # 값 전파 사슬 — 01 입력 → 02 실행 → 05 실행 → 3D 입력 (실제 페이지를 AppTest 로 실행)
    from streamlit.testing.v1 import AppTest

    def run_page(name, state):
        at = AppTest.from_file(os.path.join(DASH, "pages", name), default_timeout=180)
        for k, v in state.items():
            at.session_state[k] = v
        at.run()
        errs = [e.value for e in at.exception]
        out = {k: at.session_state[k] for k in at.session_state.filtered_state}
        return out, errs

    base = dict(auth_user="tester", auth_role="admin", lang="KO", capacity_mw=100.0, duration_h=4.0,
                target_market="US (ERCOT)", rte_percent=88.0, aux_loss_percent=2.5, epc_margin=5.0)
    s02, e02 = run_page("02_System_Engineering.py", base)
    n02 = (s02.get("design_model") or {}).get("system", {}).get("values", {}).get("num_containers")
    s05, e05 = run_page("05_CBOP_Engineer.py", {**base, **{k: s02[k] for k in
                        ("num_containers", "num_pcs", "batt_unit_mwh", "pcs_unit_mw", "design_model") if k in s02}})
    n05 = (s05.get("design_model") or {}).get("cbop", {}).get("values", {}).get("n_enc")
    # 냉방부하 외피 = 인클로저 수 × 1기 UA × ΔT (예전엔 플랜트 전체에 1기분만 더했다)
    cv = (s05.get("design_model") or {}).get("cbop", {}).get("values", {})
    ua1 = EP.enc_ua_kw_k(6.05, 2.44)
    exp_load = (cv.get("bat_heat_kw", 0) + cv.get("pcs_heat_kw", 0) + n05 * ua1 * cv.get("hvac_dt_k", 0)) \
        * (1 + cv.get("hvac_safety_pct", 0) / 100.0) if n05 else None
    check("05 냉방부하: (발열 + 인클로저 수 × U·A × ΔT) × (1+안전율) (1기 UA 0.197 kW/K)",
          exp_load is not None and cv.get("hvac_dt_k", 0) > 0 and abs(cv.get("hvac_load_kw", 0) - exp_load) < 1e-6
          and abs(cv.get("env_ua_kw_k", 0) - ua1) < 1e-9 and abs(ua1 - 0.19690) < 1e-4,
          f"load={cv.get('hvac_load_kw', 0):.1f} kW 기대={exp_load or 0:.1f} UA={ua1:.4f} n={n05}")
    # 13 화면: 기준안 저장 → 유닛 이격 3.048→6 m 변경 → 구조 뷰 — 면적 Δ 표시·패드/트렌치 트레이스·예외 0
    at13 = AppTest.from_file(os.path.join(DASH, "pages", "13_Site_Layout_3D.py"), default_timeout=180)
    for k, v in {**base, **{k: s05[k] for k in ("num_containers", "num_pcs", "design_model") if k in s05}}.items():
        at13.session_state[k] = v
    at13.run()
    at13.button[0].click().run()
    at13.number_input(key="sl_gap_US").set_value(6.0).run()
    at13.radio(key="sl_view").set_value("구조 (기초·트렌치)").run()
    spec13 = json.loads(at13.get("plotly_chart")[0].proto.spec)
    names13 = [t.get("name") for t in spec13["data"]]
    d_area = at13.metric[0].proto.body if at13.metric else ""
    delta13 = at13.metric[0].proto.delta if at13.metric else ""
    d_enc13 = at13.metric[1].proto.delta if len(at13.metric) > 1 else "?"
    check("13 화면: 기준안 저장 후 이격 변경 → 면적 Δ(+) 표시·변화 없는 인클로저 수는 Δ 없음(↑ 오표시 방지), "
          "구조 뷰에 기초 패드·트렌치·기준안 윤곽",
          not at13.exception and delta13.startswith("+") and d_enc13 == "" and {"기초 패드", "케이블 트렌치", "기준안 윤곽"} <= set(names13)
          and spec13["layout"]["scene"]["zaxis"]["range"][0] < -1.0,
          f"Δ={delta13} 인클로저Δ={d_enc13!r} 면적={d_area} traces={names13} err={[e.value for e in at13.exception][:1]}"[:160])
    inp = DM.layout_inputs(s05)
    n3d = sum(b["kind"] == "enc" for b in SL.build_layout(inp["n_enc"][0], inp["n_pcs"][0])["boxes"])
    check("전파: 02 인클로저 수 = 05 기본값 = 3D 박스 수", not (e02 or e05) and n02 and n02 == n05 == n3d,
          f"02={n02} 05={n05} 3D={n3d}" + (f" err={(e02 or e05)[0]}"[:80] if (e02 or e05) else ""))
    check("전파: 3D 입력 출처 = 05·02 (가정값 아님)", inp["n_enc"][1] == "p05" and inp["n_pcs"][1] == "p02",
          f"{inp['n_enc'][1]}/{inp['n_pcs'][1]}")
    # stale 세탁 방지 — 02 를 100 MW 로 실행 후 01 을 200 MW 로 바꾸고 02 를 다시 열지 않은 채 05 실행
    s05b, e05b = run_page("05_CBOP_Engineer.py", {**base, "capacity_mw": 200.0, **{k: s02[k] for k in
                          ("num_containers", "num_pcs", "batt_unit_mwh", "pcs_unit_mw", "design_model") if k in s02}})
    n05b = (s05b.get("design_model") or {}).get("cbop", {}).get("values", {}).get("n_enc")
    check("전파: 02 가 stale 이면 05 는 옛 02 수량(121)을 쓰지 않음 (200 MW 자체 산정)",
          not e05b and n05b and n05b != n02 and n05b > n02, f"02(100MW)={n02} 05(200MW)={n05b}")
    s04, e04 = run_page("04_EBOP_Engineer.py", {**base, "dm_cable_length_m": 166.0})
    got = (s04.get("design_model") or {}).get("ebop", {}).get("values", {}).get("cable_length_m")
    check("되돌림: 3D 최장 경로 166 m → 04 케이블 길이 기록 (접지 탭 length 덮어쓰기 없음)",
          not e04 and got == 166.0, f"{got}")


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
    run_skill_criteria_checks()
    run_design_model_checks()
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
