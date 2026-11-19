"""Exercise result-bearing Streamlit pages, including branches hidden by default."""
import json
import re
from pathlib import Path

import numpy as np
import pytest
from streamlit.testing.v1 import AppTest


def page(name, lang="KO"):
    a = AppTest.from_file(f"pages/{name}", default_timeout=120)
    a.session_state["auth_user"] = "tester"
    a.session_state["auth_role"] = "admin"
    a.session_state["lang"] = lang
    return a.run()


def scene(a, name):
    assert not a.exception, [e.value for e in a.exception]
    html = next(i.proto.srcdoc for i in a.get("iframe") if 'id="scene-data"' in i.proto.srcdoc)
    Path("output_reports/viewer").mkdir(parents=True, exist_ok=True)
    Path(f"output_reports/viewer/page-{name}.html").write_text(html, encoding="utf-8")
    return json.loads(re.search(r'<script id="scene-data" type="application/json">(.*?)</script>', html, re.S)[1])


@pytest.mark.parametrize("role,expected", [(0,"thermal"),(1,"structure"),(2,"smoke")])
def test_analysis_result_branches(role, expected):
    a = page("03_3D_Simulation.py", "EN")
    a.selectbox[0].select_index(role).run()
    data = scene(a, expected)
    assert data["mode"] == expected
    assert len(data["times"]) >= 31
    if expected == "structure":
        assert max(abs(v) for v in data["eccentricities"]) > .1
        assert not np.allclose(data["fields"][0], data["fields"][1])
    if expected == "smoke":
        assert len(data["plume"]) == len(data["times"])
        assert data["layers"][-1] < data["size"][2]


def test_container_after_actual_solver_run():
    a = page("09_Container_Thermal.py")
    next(b for b in a.button if "시뮬레이션 실행" in b.label).click().run()
    data = scene(a, "container")
    assert data["mode"] == "thermal" and data["airflow"]
    np.testing.assert_allclose(data["fields"][-1], a.session_state["thermal_snapshots"][-1], atol=.001)
    assert len(data["boxes"]) == len(a.session_state["thermal_sources"])


def test_fire_after_actual_solver_run():
    a = page("10_Fire_Spread.py")
    next(b for b in a.button if "시뮬레이션 실행" in b.label).click().run()
    data = scene(a, "fire")
    assert data["mode"] == "fire"
    assert data["states"] == np.asarray(a.session_state["fire_result"]["state_frames"]).tolist()
    np.testing.assert_allclose(data["fields"], a.session_state["fire_result"]["T_frames"], atol=.001)


def test_ebop_cable_reactance_and_exact_vdrop():
    """IEC 60287 / IEEE 141 리액턴스 포함 전압강하 산정 검증."""
    from utils import engineering_params as EP

    # 22.9kV, 200A, 100m, 185mm² 동선, 역률 0.95
    res = EP.calc_cable_vdrop(
        v_line_v=22900.0,
        current_a=200.0,
        length_m=100.0,
        area_mm2=185.0,
        is_cu=True,
        power_factor=0.95,
    )
    # 리액턴스(0.10) 및 도체 저항이 양수이며 전압강하율이 유효 범위 내
    assert 0.0 < res["vdrop_pct"] < 3.0
    assert res["z_eq_km"] > res["r_ac_km"] * 0.95  # 리액턴스 기여 확인

    # 목표 전압강하 3% 기준 최소 단면적 역산
    min_area = EP.vdrop_min_area_mm2(
        v_line_v=22900.0,
        current_a=200.0,
        length_m=100.0,
        target_vdrop_pct=3.0,
        is_cu=True,
        power_factor=0.95,
    )
    assert 1.0 < min_area < 50.0  # 100m 22.9kV 200A 에서는 작은 단면적으로도 전압강하 만족


def test_cbop_nfpa68_deflagration_vent():
    """NFPA 68 방폭 방산구 면적 산정 검증."""
    from utils import engineering_params as EP

    # 20ft 컨테이너 (6.05 × 2.44 × 2.9m)
    vent = EP.deflagration_vent_area_m2(length_m=6.05, width_m=2.44, height_m=2.9)
    assert vent["vent_area_m2"] > 0.5
    assert vent["panels_req"] >= 1
    assert vent["volume_m3"] > 40.0


def test_battery_augmentation_simulation():
    """배터리 증설 시뮬레이터 정량 지표 검증."""
    from utils import engineering_params as EP

    res = EP.simulate_battery_augmentation(
        project_years=15,
        temp_c=25.0,
        cycles_per_day=1.0,
        dod=0.95,
        required_ac_mwh=400.0,
        eta_discharge=0.938,
        soh_eol_target=0.80,
    )
    # 초기 CAPEX 절감 및 NPV 절감이 양수여야 함
    assert res["initial_savings_pct"] > 5.0  # 초기 CAPEX 최소 5% 이상 절감
    assert res["npv_savings_usd"] > 0.0     # 생애주기 NPV 기준 절감 달성
    assert 1 <= res["strat_b_aug_year"] <= 15
    assert len(res["soh_curve"]) == 16
    assert res["strat_a_initial_mwh"] > res["strat_b_initial_mwh"]


def test_site_layout_ehouse_and_switchgear_integration():
    """스위치기어 및 제어실 E-House 3D 부지 배치 및 이격거리 정량 검증."""
    from utils import site_layout as SL

    # 1. 중앙 집중형 + E-House 포함
    lay_cf = SL.build_layout(12, 3, water_m3=100.0, topology="center_fed", tr_pos="center", include_ehouse=True)
    chk_cf = SL.check_layout(lay_cf)

    assert chk_cf["overlaps"] == 0
    assert chk_cf["unit_ok"] is True
    assert chk_cf["tr_ok"] is True
    assert chk_cf["boundary_ok"] is True
    assert lay_cf["metrics"]["include_ehouse"] is True
    assert lay_cf["metrics"]["ehouse_m2"] > 25.0  # 40ft HC 약 29.7m²

    # E-House 박스 존재 및 치수 확인 (12.19 × 2.44 × 2.9m)
    eh_boxes = [b for b in lay_cf["boxes"] if b["kind"] == "ehouse"]
    assert len(eh_boxes) == 1
    eh = eh_boxes[0]
    assert eh["dx"] == 12.19
    assert eh["dy"] == 2.44
    assert eh["dz"] == 2.9
    assert "E-HOUSE" in eh["label"]

    # 트렌치가 E-House 중심까지 연결되었는지 확인
    eh_cx = eh["x"] + eh["dx"] / 2.0
    trench_pts = [pt for seg in lay_cf["trench"] for pt in seg]
    assert any(abs(pt[0] - eh_cx) < 1e-3 for pt in trench_pts)

    # 2. 외곽 모서리 배치형(corner) 검증
    lay_corner = SL.build_layout(12, 3, water_m3=80.0, tr_pos="corner", include_ehouse=True)
    chk_corner = SL.check_layout(lay_corner)
    assert chk_corner["overlaps"] == 0
    assert chk_corner["tr_ok"] is True
    assert chk_corner["boundary_ok"] is True

    # 3. 미포함 옵션(include_ehouse=False) 하위 호환성 검증
    lay_no_eh = SL.build_layout(12, 3, include_ehouse=False)
    assert not any(b["kind"] == "ehouse" for b in lay_no_eh["boxes"])
    assert lay_no_eh["metrics"]["ehouse_m2"] == 0.0


def test_site_cbop_infrastructure_sizing_and_layout():
    """사이트 규모별 소방·하이드란트·번드월·배수 인프라 산정 및 3D 배치 검증."""
    from utils import engineering_params as EP
    from utils import site_layout as SL

    # 1. 사이트 규모별 엔지니어링 계산 검증 (100MW / 400MWh)
    infra = EP.calc_site_cbop_infrastructure(
        capacity_mwh=400.0,
        power_mw=100.0,
        n_enc=80,
        tr_mva=120.0,
        site_w_m=120.0,
        site_h_m=90.0,
    )
    # 변압기 방유제 체적 (120 MVA × 0.9 + deluge + rain > 120 m³)
    assert infra["bund_req_m3"] > 120.0
    assert infra["bund_height_m"] >= 0.5
    # 소화전: 둘레 420m / 45m 간격 -> 최소 8기 이상
    assert infra["num_hydrants"] >= 8
    # 소방 수조 용량: 소화전 228m³ + 고정식 소화 + 여유 -> 300m³ 이상
    assert infra["total_fire_water_m3"] > 300.0
    # 배수 저류조: 소화폐수 차집 200m³ 이상
    assert infra["basin_vol_m3"] >= 200.0

    # 2. 3D 부지 배치 기하 및 겹침 제약 검증
    lay = SL.build_layout(
        20, 5, water_m3=infra["total_fire_water_m3"],
        topology="center_fed", tr_pos="center",
        include_ehouse=True, include_infra=True
    )
    chk = SL.check_layout(lay)

    # 불변 규칙: 겹침 0, 단위 이격거리 및 경계 이격 준수
    assert chk["overlaps"] == 0
    assert chk["unit_ok"] is True
    assert chk["tr_ok"] is True
    assert chk["boundary_ok"] is True

    # 신규 인프라 박스 종류 확인
    kinds = set(b["kind"] for b in lay["boxes"])
    assert {"bund", "hydrant", "pump_house", "storage", "basin", "ehouse", "tr", "enc", "pcs"}.issubset(kinds)
    assert lay["metrics"]["num_hydrants"] >= 4
    assert lay["metrics"]["bund_area_m2"] > 80.0


def test_cbop_boq_and_capex_sizing():
    """토목(CBOP)·소방(FBOP) 상세 물량산출(BOQ) 및 CAPEX 자동 집계 검증."""
    from utils import engineering_params as EP

    boq = EP.calc_cbop_boq_and_cost(
        site_w_m=90.0,
        site_h_m=70.0,
        n_enc=24,
        n_pcs=6,
        pad_l=6.2,
        pad_w=2.5,
        pad_t=0.40,
        trench_len_m=150.0,
        trench_w=0.80,
        trench_d=1.00,
    )

    # 1. 수량 검증 (정량적 수치 및 물리 단위)
    q = boq["quantities"]
    assert q["site_area_m2"] == 6300.0
    assert q["perimeter_m"] == 320.0
    assert q["concrete_total_m3"] > 100.0   # 패드 + 방유벽 + 트렌치
    assert q["excavation_total_m3"] > q["concrete_total_m3"]  # 터파기량이 콘크리트보다 커야 함
    assert q["backfill_total_m3"] > 0.0
    assert q["num_hydrants"] >= 6
    assert q["fire_water_m3"] >= 150.0

    # 2. 공종별 및 총 공사비 정합성 검증
    items = boq["items"]
    assert len(items) >= 10
    for it in items:
        assert it["qty"] > 0.0
        assert it["unit_cost"] > 0.0
        assert abs(it["cost_usd"] - round(it["qty"] * it["unit_cost"])) <= 2.0  # 반올림 오차 이내

    assert boq["total_capex_usd"] > 200000.0  # 최소 20만 달러 이상
    assert boq["total_capex_krw"] == round(boq["total_capex_usd"] * 1350.0)
    assert len(boq["cat_summary"]) >= 5
    assert sum(boq["cat_summary"].values()) == boq["total_capex_usd"]


def test_hydrant_fire_coverage_verification():
    """소화전 40m 유효 방수 반경 (Coverage) 검증 및 3D 기하 생성 테스트."""
    from utils import site_layout as SL

    lay = SL.build_layout(
        16, 4,
        water_m3=200.0,
        topology="center_fed",
        tr_pos="center",
        include_ehouse=True,
        include_infra=True
    )

    # 1. 소화전 40m 커버리지 분석
    cov = SL.check_fire_coverage(lay, radius_m=40.0)
    assert cov["all_covered"] is True
    assert cov["coverage_pct"] == 100.0
    assert cov["total_assets"] >= 20  # 인클로저 16 + PCS 4 + TR 1 + E-House 1
    assert len(cov["uncovered"]) == 0
    assert 0.0 < cov["max_dist_m"] <= 40.0
    assert 0.0 < cov["avg_dist_m"] < cov["max_dist_m"]

    # 2. 3D Plotly 링 및 돔 기하 생성 함수 검증
    cx, cy, cz = SL.hydrant_coverage_circles(lay, radius_m=40.0)
    assert len(cx) > 0
    assert len(cx) == len(cy) == len(cz)
    assert None in cx  # 소화전 간 트레이스 분리용 None 포함 확인

    dxs, dys, dzs, dii, djj, dkk = SL.hydrant_coverage_dome_mesh(lay, radius_m=40.0)
    assert len(dxs) > 0
    assert len(dii) > 0
    assert len(dxs) == len(dys) == len(dzs)
    assert len(dii) == len(djj) == len(dkk)


def test_power_block_allocation_and_site_area_optimization():
    """PCS 대당 배터리 파워블록 연계 및 부지 총면적 최소화 전역 최적화 검증."""
    from utils import site_layout as SL

    # 1. 20개 배터리 + 5개 PCS (1:4 비율)
    lay = SL.build_layout(
        20, 5,
        topology="center_fed",
        tr_pos="center",
        include_ehouse=True,
        include_infra=True
    )

    # 파워 블록(Power Block: 1 PCS + N Battery) 구획 정보 검증
    pb_list = lay.get("power_blocks", [])
    assert len(pb_list) == 5
    for i, pb in enumerate(pb_list):
        assert pb["block"] == i + 1
        assert pb["n_enc"] == 4  # 20 // 5 = 4기씩 정확히 연계
        assert pb["pcs_label"] == f"PCS-{i + 1:02d}"
        assert pb["dx"] > 0 and pb["dy"] > 0

    assert lay["metrics"]["power_blocks_count"] == 5
    assert lay["metrics"]["enc_per_pcs_ratio"] == 4.0

    # 2. PCS와 배터리 인클로저 형상/치수 차별화 검증
    pcs_boxes = [b for b in lay["boxes"] if b["kind"] == "pcs"]
    enc_boxes = [b for b in lay["boxes"] if b["kind"] == "enc"]
    assert len(pcs_boxes) == 5
    assert len(enc_boxes) == 20

    # PCS는 배터리 컨테이너(2.9m)와 구분되는 2.4m 높이
    assert pcs_boxes[0]["dz"] == 2.40
    assert enc_boxes[0]["dz"] == 2.90

    # 3. 부지 기하 제약 검증 (최적화 후에도 겹침 0 및 이격거리 충족)
    chk = SL.check_layout(lay)
    assert chk["overlaps"] == 0
    assert chk["unit_ok"] is True
    assert chk["tr_ok"] is True
    assert chk["boundary_ok"] is True
    assert lay["metrics"]["site_area_m2"] > 0


def test_hydrant_central_reinforcement_and_100pct_coverage():
    """대형 부지에서 중앙 사각지대 해소를 위한 내부 소화전 자동 보강 및 40m 100% 커버리지 검증."""
    from utils import site_layout as SL

    # 대형 40 배터리 + 10 PCS 배치 (부지 폭 90m 이상)
    lay = SL.build_layout(40, 10, include_infra=True)

    # 1. 소화전 목록에 외곽뿐 아니라 중앙 소화전(HYDRANT-C01 등)이 자동 보강되었는지 확인
    hydrants = [b for b in lay["boxes"] if b["kind"] == "hydrant"]
    c_hydrants = [h for h in hydrants if "HYDRANT-C" in h["label"]]
    assert len(hydrants) >= 4

    # 2. 모든 주요 설비가 소화전 반경 40m 내에 100% 포괄되는지 검증
    cov = SL.check_fire_coverage(lay, radius_m=40.0)
    assert cov["coverage_pct"] == 100.0
    assert cov["all_covered"] is True
    assert len(cov["uncovered"]) == 0
    assert cov["max_dist_m"] <= 40.0


def test_heavy_equipment_simulation():
    """50T 크레인 인양 반경 및 3.5T 지게차 회전 반경 시뮬레이션 검증."""
    from utils import site_layout as SL

    lay = SL.build_layout(24, 6, include_infra=True)
    res = SL.heavy_equipment_simulation(lay)

    # 1. 50T 크레인 스테이션 및 인양 반경 20m, 아우트리거 7.5m 확인
    assert len(res["crane_stations"]) >= 2
    assert res["crane_radius_m"] == 20.0
    assert res["outrigger_size_m"] == 7.5
    assert res["crane_coverage_pct"] >= 90.0

    # 2. 지게차 통로 폭 3.5m 및 회전 반경 3.8m 검증
    assert res["forklift_turning_radius_m"] == 3.8
    assert res["forklift_min_aisle_m"] == 3.5
    assert res["site_aisle_m"] >= res["forklift_min_aisle_m"]
    assert res["aisle_margin_m"] >= 0.0
    assert res["forklift_pass"] is True
    assert res["all_pass"] is True

    # 3. 3D 기하 좌표 생성 검증
    c_xs, c_ys, c_zs = res["crane_circles"]
    assert len(c_xs) > 0
    assert None in c_xs
    o_xs, o_ys, o_zs = res["outrigger_boxes"]
    assert len(o_xs) > 0


def test_multiview_dxf_generation():
    """12개 전문 레이어, 평면도, 단면도(A-A, B-B), 표제란이 포함된 전문가 수준 DXF 검증."""
    from utils import site_layout as SL

    lay = SL.build_layout(16, 4, include_infra=True)
    dxf_str = SL.to_dxf(lay, multi_view=True)

    # 1. DXF 기본 구조 및 단위(Meters)
    assert "AC1009" in dxf_str
    assert "$INSUNITS" in dxf_str

    # 2. 12개 전문 엔지니어링 레이어 포함 여부
    assert "C-PAD-CONC" in dxf_str
    assert "C-TRENCH" in dxf_str
    assert "C-FENCE" in dxf_str
    assert "E-BESS-ENC" in dxf_str
    assert "E-PCS-SKID" in dxf_str
    assert "E-MAIN-TR" in dxf_str
    assert "F-HYDRANT" in dxf_str
    assert "DIM-MAJOR" in dxf_str
    assert "SECTION-AA" in dxf_str
    assert "SECTION-BB" in dxf_str
    assert "TITLE-BLOCK" in dxf_str

    # 3. 단면도(Section A-A, Section B-B) 레이블 및 지표면(GL) 표기 확인
    assert "SECTION A-A" in dxf_str
    assert "SECTION B-B" in dxf_str
    assert "GL ±0.00" in dxf_str

    # 4. 표준 표제란 메타데이터 확인
    assert "PROJECT: UTILITY-SCALE BESS EPC PROJECT" in dxf_str
    assert "DWG NO: DWG-BESS-EPC-001" in dxf_str
    assert "SCALE: 1:100" in dxf_str


def test_create_section_figures():
    """2D 공학 정밀 횡단면도 (Section A-A, Section B-B) Plotly 생성 검증."""
    from utils import site_layout as SL

    lay = SL.build_layout(12, 3, include_infra=True)
    fig_a, fig_b = SL.create_section_figures(lay)

    # Section A-A 트레이스 검증
    assert fig_a is not None
    assert len(fig_a.data) >= 5  # GL선, 패드, 배터리, 트렌치, PCS 등
    assert "Section A-A" in fig_a.layout.title.text

    # Section B-B 트레이스 검증
    assert fig_b is not None
    assert len(fig_b.data) >= 4  # GL선, 방유벽, 변압기 기초, TR 본체, 소방도로 등
    assert "Section B-B" in fig_b.layout.title.text







