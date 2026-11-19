# -*- coding: utf-8 -*-
"""
site_layout.py — 설계 모델 값으로 BESS 부지 배치를 자동 생성하는 순수 함수 모음 (Streamlit 비의존).

배치 규칙 (스크리닝 수준 — 실시공 배치도는 지형·인허가·AHJ 협의로 확정):
  · PCS 스키드 1기 = 블록 1개. 인클로저를 블록에 고르게 나눠 x 방향 일렬 배치, 블록 끝에 PCS
  · 블록은 정사각형에 가까운 격자로 배치 — 블록 열 사이 = 유닛 이격, 블록 행 사이 = max(통로, 유닛 이격)
  · 주변압기(POI)·소방 수조는 남측 띠에 두고 변압기 이격만큼 어레이와 띄운다
  · 트렌치: PCS → 블록 열 사이 간선 → 남측 간선(trunk) → 주변압기 (직각 경로)
좌표: x 동쪽, y 북쪽, z 위 [m]. 원점 = 부지경계 남서 모서리. (2026-10-29 신설)
"""
import math

import numpy as np

ENC_H = 2.9       # [가정] 20ft HC 인클로저 높이
PCS_DIM = (6.05, 2.44, 2.40)   # [실물 규격] PCS/MV 오픈 스키드 (배터리 컨테이너 2.9m 대비 낮은 2.4m + 상부 부싱)
TR_DIM = (8.0, 6.0, 5.0)      # [가정] 주변압기 외형 (MVA 별 외형은 제작사 도면 확정)
EHOUSE_DIM = (12.19, 2.44, 2.9)  # [가정] 40ft HC 수배전반(Switchgear) 및 제어실(EMS/SCADA) E-House
PUMP_DIM = (6.05, 2.44, 2.9)      # [가정] 소방 가압 펌프실 20ft 컨테이너
STORAGE_DIM = (6.05, 2.44, 2.9)   # [가정] O&M 예비품/자재 보관소 20ft 컨테이너
HYDRANT_DIM = (0.40, 0.40, 0.85)  # [가정] 옥외 소화전 기둥
BASIN_DIM = (8.0, 6.0, 1.8)       # [가정] 우수/소방폐수 차집 저류조
TANK_H = 3.0


def _counts(n_enc, n_pcs):
    base, rem = divmod(n_enc, n_pcs)
    return [base + (1 if i < rem else 0) for i in range(n_pcs)]


def build_layout(n_enc, n_pcs, enc_l=6.05, enc_w=2.44, unit_gap=3.0, boundary=3.0,
                 aisle=6.0, tr_clear=5.0, trench_w=0.6, water_m3=0.0,
                 topology="center_fed", tr_pos="center", include_ehouse=True,
                 include_infra=True) -> dict:
    """
    설계 모델 값으로 BESS 부지 배치를 자동 생성하는 순수 기하/배선 엔진.
    
    [배치 토폴로지]:
      - topology="center_fed": PCS 스키드를 블록 중앙에 두고 배터리 인클로저를 좌우 대칭 배치.
        DC 케이블 최대 거리가 50% 단축되고 스트링 간 임피던스 편차가 최소화되어
        전류 불균형 및 조기 열화를 방지하는 BESS EPC 권장 최적 토폴로지.
      - topology="linear": PCS 를 블록 끝에 두고 인클로저를 일렬 배치하는 기본형.
      
    [변압기 연계 위치]:
      - tr_pos="center": 남측 부하 중심(Load Center)에 변압기 배치 -> MV 케이블 최장 경로 25~35% 단축.
      - tr_pos="corner": 남서측 모서리에 변압기 배치 (외곽 수전형).

    [E-House 및 스위치기어]:
      - include_ehouse=True: 40ft HC 규격의 수배전반(Switchgear) 및 제어실(EMS/SCADA) E-House를
        남측 트렁크 간선 및 주변압기 인접부에 배치하여 실물 플랜트 구성 완결.

    [소방·방유제·배수·저장소 인프라]:
      - include_infra=True: 변압기 오일 방유제(Bund Wall), 소방 가압 펌프실(Pump House),
        부지 우수/소방폐수 차집 저류조(Retention Basin), O&M 자재 보관소(Storage),
        부지 둘레 옥외 소화전(Hydrant) 시스템을 사이트 규모에 맞춰 자동 연동 배치.
    """
    n_enc = max(int(n_enc), 1)
    pcs_clipped = int(n_pcs) > n_enc            # PCS 가 인클로저보다 많으면 블록이 빈다 → 인클로저 수로 제한
    n_pcs = max(min(int(n_pcs), n_enc), 1)
    pcs_l, pcs_w, pcs_h = PCS_DIM
    tr_l, tr_w, tr_h = TR_DIM
    eh_l, eh_w, eh_h = EHOUSE_DIM
    pump_l, pump_w, pump_h = PUMP_DIM
    st_l, st_w, st_h = STORAGE_DIM
    counts = _counts(n_enc, n_pcs)
    per = max(counts)

    block_len = per * (enc_l + unit_gap) + pcs_l          # 인클로저 per 기 + 각 사이·PCS 앞 이격
    block_dep = max(enc_w, pcs_w)
    row_gap = max(aisle, unit_gap)

    tank_side = math.sqrt(water_m3 / TANK_H) if water_m3 > 0 else 0.0
    b = boundary
    band = max(tr_w + (1.2 if include_infra else 0.0), tank_side, (eh_w if include_ehouse else 0.0))  # 남측 띠 깊이 — 방유제/대형 설비 이격대 침범 방지
    south_eq_w = tr_l + (tr_clear + eh_l if include_ehouse else 0.0) + (tr_clear + tank_side if tank_side else 0.0)
    if include_infra:
        south_eq_w += (2.5 + pump_l) + (2.5 + st_l) + 2.4

    # 부지 총면적 (Site_W × Site_H) 최소화 전역 최적화 알고리즘
    best = None
    for c in range(1, n_pcs + 1):
        r = math.ceil(n_pcs / c)
        w = c * block_len + (c - 1) * unit_gap
        h = r * block_dep + (r - 1) * row_gap
        cand_site_w = max(b + w + unit_gap + b, 2 * b + south_eq_w)
        cand_site_h = b + band + tr_clear + h + b
        cand_area = cand_site_w * cand_site_h
        aspect_ratio = cand_site_w / max(cand_site_h, 1e-6)
        aspect_penalty = abs(math.log(aspect_ratio))
        # 1순위: 부지 전체 면적 최소화, 2순위: 정사각형 근접도 (동점 시)
        score = (round(cand_area, 2), aspect_penalty)
        if best is None or score < best[0]:
            best = (score, c, r, w, h)
    _, cols, rows, arr_w, arr_h = best

    y_trunk = b + band + tr_clear / 2.0
    y_arr = b + band + tr_clear
    x_arr = b

    site_w = max(x_arr + arr_w + unit_gap + b, 2 * b + south_eq_w)

    boxes, trench, power_blocks = [], [], []

    # 남측 설비 기본 y (방유제 1.2m 확장을 고려하여 boundary 이격 확보)
    y_south = b + (1.2 if include_infra else 0.0)

    # 주변압기, E-House, 소방수조, 펌프실, 보관소 좌표 산정 (부하 중심 중앙 vs 모서리)
    if tr_pos == "center":
        tr_cx = site_w / 2.0
        # E-House 및 자재 보관소, 방유제가 있을 경우 서측에 배치할 여유 공간 확보
        west_req = (eh_l + tr_clear if include_ehouse else 0.0) + (st_l + 2.5 if (include_ehouse and include_infra) else 0.0) + (1.2 if include_infra else 0.0)
        tr_x = max(tr_cx - tr_l / 2.0, b + west_req)
        tr_y = y_south
        tr_cx = tr_x + tr_l / 2.0
        boxes.append(dict(kind="tr", label="MAIN-TR", x=tr_x, y=tr_y, dx=tr_l, dy=tr_w, dz=tr_h))

        if include_infra:
            # 변압기 오일 방유제 (Bund Wall) — tr 하부 사방 1.2m 테두리 (y=b에서 시작)
            bund_l, bund_w = tr_l + 2.4, tr_w + 2.4
            boxes.append(dict(kind="bund", label="TR-BUND-WALL", x=tr_x - 1.2, y=tr_y - 1.2,
                              dx=bund_l, dy=bund_w, dz=0.7))

        if include_ehouse:
            eh_x = tr_x - tr_clear - eh_l
            eh_y = y_south
            boxes.append(dict(kind="ehouse", label="E-HOUSE (SWGR/EMS)", x=eh_x, y=eh_y, dx=eh_l, dy=eh_w, dz=eh_h))

            if include_infra:
                # E-House 서측 자재/예비품 보관소
                st_x = max(eh_x - 2.5 - st_l, b)
                boxes.append(dict(kind="storage", label="PARTS-STORAGE", x=st_x, y=y_south,
                                  dx=st_l, dy=st_w, dz=st_h))

        tank_x = tr_x + tr_l + tr_clear
        if tank_side:
            boxes.append(dict(kind="tank", label="FIRE-WATER", x=tank_x, y=y_south,
                              dx=tank_side, dy=tank_side, dz=TANK_H))

        if include_infra:
            # 소방 가압 펌프실
            px = (tank_x + tank_side + 2.5) if tank_side else tank_x
            boxes.append(dict(kind="pump_house", label="FIRE-PUMP-ROOM", x=px, y=y_south,
                              dx=pump_l, dy=pump_w, dz=pump_h))
    else:
        # corner 모서리 순차 배치
        curr_x = b + (1.2 if include_infra else 0.0)
        if include_ehouse:
            if include_infra:
                boxes.append(dict(kind="storage", label="PARTS-STORAGE", x=curr_x, y=y_south,
                                  dx=st_l, dy=st_w, dz=st_h))
                curr_x += st_l + 2.5

            eh_x = curr_x
            eh_y = y_south
            boxes.append(dict(kind="ehouse", label="E-HOUSE (SWGR/EMS)", x=eh_x, y=eh_y, dx=eh_l, dy=eh_w, dz=eh_h))
            curr_x += eh_l + tr_clear

        tr_x = curr_x
        tr_y = y_south
        tr_cx = tr_x + tr_l / 2.0
        boxes.append(dict(kind="tr", label="MAIN-TR", x=tr_x, y=tr_y, dx=tr_l, dy=tr_w, dz=tr_h))
        if include_infra:
            bund_l, bund_w = tr_l + 2.4, tr_w + 2.4
            boxes.append(dict(kind="bund", label="TR-BUND-WALL", x=tr_x - 1.2, y=tr_y - 1.2,
                              dx=bund_l, dy=bund_w, dz=0.7))
        curr_x += tr_l + tr_clear

        if tank_side:
            tank_x = curr_x
            boxes.append(dict(kind="tank", label="FIRE-WATER", x=tank_x, y=y_south,
                              dx=tank_side, dy=tank_side, dz=TANK_H))
            curr_x += tank_side + 2.5

        if include_infra:
            boxes.append(dict(kind="pump_house", label="FIRE-PUMP-ROOM", x=curr_x, y=y_south,
                              dx=pump_l, dy=pump_w, dz=pump_h))

    runs, branch_top = [], {}
    dc_runs_all = []
    k_enc = 0
    is_center_fed = (topology == "center_fed")

    for i, cnt in enumerate(counts):
        r, c = divmod(i, cols)
        bx = x_arr + c * (block_len + unit_gap)
        by = y_arr + r * (block_dep + row_gap)
        y_pcs = by + pcs_w / 2.0

        # 파워 블록(Power Block: 1 PCS + N Battery) 바닥 구획선 정보
        power_blocks.append(dict(
            block=i + 1,
            x=bx - 0.25, y=by - 0.25,
            dx=block_len + 0.50, dy=block_dep + 0.50,
            n_enc=cnt, pcs_label=f"PCS-{i + 1:02d}",
        ))

        if is_center_fed:
            # 중앙 집중 대칭형: PCS 를 가운데 두고 배터리를 좌우 균등 배치
            n_left = cnt // 2
            n_right = cnt - n_left

            # 좌측 배터리 배치
            for j in range(n_left):
                k_enc += 1
                ex = bx + j * (enc_l + unit_gap)
                boxes.append(dict(kind="enc", label=f"ENC-{k_enc:03d}", x=ex, y=by,
                                  dx=enc_l, dy=enc_w, dz=ENC_H, block=i + 1))
            
            # 중앙 PCS 배치
            px = bx + n_left * (enc_l + unit_gap)
            boxes.append(dict(kind="pcs", label=f"PCS-{i + 1:02d}", x=px, y=by, dx=pcs_l, dy=pcs_w, dz=pcs_h,
                              block=i + 1, n_enc=cnt))

            # 우측 배터리 배치
            rx_start = px + pcs_l + unit_gap
            for j in range(n_right):
                k_enc += 1
                ex = rx_start + j * (enc_l + unit_gap)
                boxes.append(dict(kind="enc", label=f"ENC-{k_enc:03d}", x=ex, y=by,
                                  dx=enc_l, dy=enc_w, dz=ENC_H, block=i + 1))

            # 블록 내 DC 케이블 경로 (각 배터리 중심 -> PCS 중심)
            pcs_cx = px + pcs_l / 2.0
            for b_item in boxes[-cnt-1:-1]:
                b_cx = b_item["x"] + b_item["dx"] / 2.0
                dc_dist = abs(b_cx - pcs_cx) + abs(b_item["dy"] - pcs_w) / 2.0
                dc_runs_all.append(dc_dist)

        else:
            # 기존 선형 일렬 배치: [인클로저 ... ] [PCS]
            for j in range(cnt):
                k_enc += 1
                ex = bx + j * (enc_l + unit_gap)
                boxes.append(dict(kind="enc", label=f"ENC-{k_enc:03d}", x=ex, y=by,
                                  dx=enc_l, dy=enc_w, dz=ENC_H, block=i + 1))
            px = bx + block_len - pcs_l
            boxes.append(dict(kind="pcs", label=f"PCS-{i + 1:02d}", x=px, y=by, dx=pcs_l, dy=pcs_w, dz=pcs_h,
                              block=i + 1, n_enc=cnt))
            
            pcs_cx = px + pcs_l / 2.0
            for b_item in boxes[-cnt-1:-1]:
                b_cx = b_item["x"] + b_item["dx"] / 2.0
                dc_dist = abs(b_cx - pcs_cx)
                dc_runs_all.append(dc_dist)

        # MV 케이블 트렌치 연결: PCS -> 블록 우측/중앙 간선 -> 남측 메인 트렁크
        x_br = bx + block_len + unit_gap / 2.0
        trench.append([(px + pcs_l, y_pcs), (x_br, y_pcs)])
        branch_top[c] = max(branch_top.get(c, 0.0), y_pcs)

        # PCS -> 주변압기(POI) 직각 경로 산출
        run = abs(x_br - (px + pcs_l)) + (y_pcs - y_trunk) + abs(x_br - tr_cx) + (y_trunk - (tr_y + tr_w))
        runs.append(run)

    branch_x = {c: x_arr + c * (block_len + unit_gap) + block_len + unit_gap / 2.0 for c in branch_top}
    for c, ytop in branch_top.items():
        trench.append([(branch_x[c], y_trunk), (branch_x[c], ytop)])
    
    # 남측 트렁크 트렌치: 가장 먼 지선들과 주변압기, E-House 연결
    all_south_x = list(branch_x.values()) + [tr_cx]
    if include_ehouse:
        eh_cx = eh_x + eh_l / 2.0
        trench.append([(eh_cx, eh_y + eh_w), (eh_cx, y_trunk)])
        all_south_x.append(eh_cx)

    x_min_br = min(all_south_x)
    x_max_br = max(all_south_x)
    trench.append([(x_min_br, y_trunk), (x_max_br, y_trunk)])
    trench.append([(tr_cx, tr_y + tr_w), (tr_cx, y_trunk)])

    site_w = max(site_w, max(bx["x"] + bx["dx"] for bx in boxes) + b)
    site_h = max(y_arr + arr_h + b, max(bx["y"] + bx["dy"] for bx in boxes) + b)

    # 비상 저류조 (Retention Basin) 및 옥외 소화전 (Hydrant) 배치
    num_hydrants = 0
    if include_infra:
        basin_l, basin_w, basin_d = BASIN_DIM
        basin_x = b
        basin_y = y_arr + arr_h + unit_gap
        boxes.append(dict(kind="basin", label="RETENTION-BASIN", x=basin_x, y=basin_y,
                          dx=basin_l, dy=basin_w, dz=basin_d))
        site_h = max(site_h, basin_y + basin_w + b)

        # 부지 4면 울타리 도로변을 따라 45m 간격 옥외 소화전 배치 (장비와 간섭 없는 외곽 완충대)
        hydrant_pts = [
            (b, 0.6),
            (site_w - b - 0.4, 0.6),
            (site_w - b - 0.4, site_h - 1.0),
            (b, site_h - 1.0),
        ]
        # 변의 길이가 50m를 넘으면 외곽 중간 소화전 추가
        if site_w > 50.0:
            hydrant_pts.append((site_w / 2.0 - 0.2, 0.6))
            hydrant_pts.append((site_w / 2.0 - 0.2, site_h - 1.0))
        if site_h > 50.0:
            hydrant_pts.append((0.6, site_h / 2.0 - 0.2))
            hydrant_pts.append((site_w - 1.0, site_h / 2.0 - 0.2))

        for h_idx, (hx, hy) in enumerate(hydrant_pts, 1):
            boxes.append(dict(kind="hydrant", label=f"HYDRANT-{h_idx:02d}",
                              x=hx, y=hy, dx=0.40, dy=0.40, dz=0.85))

        # ── 중앙 사각지대 해소: 40m 유효 반경 미커버 설비 검출 및 중앙 통로 소화전 자동 보강 ──
        # NFPA 855 / NFTC 109: 모든 배터리/전기설비는 옥외소화전 반경 40m 내에 100% 포괄되어야 함
        def _box_overlaps(px, py, pdx, pdy, existing_boxes, margin=0.3):
            for eb in existing_boxes:
                if not (px + pdx + margin <= eb["x"] or px - margin >= eb["x"] + eb["dx"] or
                        py + pdy + margin <= eb["y"] or py - margin >= eb["y"] + eb["dy"]):
                    return True
            return False

        h_c_idx = 1
        for _ in range(6):  # 안전 루프 (최대 6개 중앙 소화전)
            cur_hydrants = [(h["x"] + h["dx"] / 2.0, h["y"] + h["dy"] / 2.0)
                            for h in boxes if h["kind"] == "hydrant"]
            uncovered = []
            for bx in boxes:
                if bx["kind"] in ("enc", "pcs", "tr", "ehouse"):
                    cx = bx["x"] + bx["dx"] / 2.0
                    cy = bx["y"] + bx["dy"] / 2.0
                    min_d = min(math.hypot(cx - hx, cy - hy) for hx, hy in cur_hydrants)
                    if min_d > 40.0:
                        uncovered.append((bx, min_d, cx, cy))
            if not uncovered:
                break  # 모든 설비 40m 커버리지 100% 충족

            # 미커버 설비들의 가중 중심 계산
            avg_x = sum(u[2] for u in uncovered) / len(uncovered)
            avg_y = sum(u[3] for u in uncovered) / len(uncovered)

            # 설비와 간섭 없는 행 간 통로(Aisle) Y 좌표 후보군
            aisle_y_candidates = []
            for r in range(1, rows):
                # 행 간 통로 중심 y (상하 설비와 최소 1.5m 이상 이격된 안전 대역)
                aisle_y_candidates.append(y_arr + r * (block_dep + aisle) - aisle / 2.0)
            if not aisle_y_candidates:
                aisle_y_candidates.append(y_arr + arr_h + unit_gap / 2.0)

            best_y = min(aisle_y_candidates, key=lambda y_c: abs(y_c - avg_y))

            # X 좌표 탐색: avg_x를 시작으로 기존 설비와 충돌하지 않는 안전한 X좌표 탐색
            cand_x = None
            for offset in [0.0, 1.0, -1.0, 2.0, -2.0, 3.5, -3.5, 5.0, -5.0]:
                test_x = max(b + 0.5, min(site_w - b - 1.0, avg_x + offset - 0.2))
                test_y = max(b + 0.5, min(site_h - b - 1.0, best_y - 0.2))
                if not _box_overlaps(test_x, test_y, 0.40, 0.40, boxes, margin=0.4):
                    cand_x = test_x
                    cand_y = test_y
                    break

            if cand_x is not None:
                boxes.append(dict(kind="hydrant", label=f"HYDRANT-C{h_c_idx:02d}",
                                  x=cand_x, y=cand_y, dx=0.40, dy=0.40, dz=0.85))
                h_c_idx += 1
            else:
                break

        num_hydrants = len([b for b in boxes if b["kind"] == "hydrant"])

    trench_len = sum(math.dist(p, q) for pl in trench for p, q in zip(pl, pl[1:]))

    dc_max = max(dc_runs_all) if dc_runs_all else 0.0
    dc_min = min(dc_runs_all) if dc_runs_all else 0.0
    dc_imbalance = dc_max - dc_min

    return dict(
        boxes=boxes, trench=trench, trench_w=trench_w,
        power_blocks=power_blocks,
        fence=[(0.0, 0.0), (site_w, 0.0), (site_w, site_h), (0.0, site_h), (0.0, 0.0)],
        site=(site_w, site_h),
        metrics=dict(
            site_area_m2=site_w * site_h, site_w_m=site_w, site_h_m=site_h,
            trench_len_m=trench_len, longest_cable_m=max(runs), n_enc=n_enc, n_pcs=n_pcs,
            blocks_cols=cols, blocks_rows=rows, enc_per_block=per, tank_m3=water_m3,
            power_blocks_count=len(power_blocks), enc_per_pcs_ratio=round(n_enc / max(n_pcs, 1), 1),
            pcs_clipped=pcs_clipped, row_gap_m=row_gap + (block_dep - enc_w),
            topology=topology, tr_pos=tr_pos,
            include_ehouse=include_ehouse,
            ehouse_m2=round(eh_l * eh_w, 1) if include_ehouse else 0.0,
            include_infra=include_infra,
            num_hydrants=num_hydrants,
            bund_area_m2=round((tr_l + 2.4) * (tr_w + 2.4), 1) if include_infra else 0.0,
            basin_m3=round(BASIN_DIM[0] * BASIN_DIM[1] * BASIN_DIM[2], 1) if include_infra else 0.0,
            dc_max_cable_m=round(dc_max, 1),
            dc_cable_imbalance_m=round(dc_imbalance, 1),
        ),
        params=dict(unit_gap=unit_gap, boundary=boundary, aisle=aisle, tr_clear=tr_clear,
                    enc_l=enc_l, enc_w=enc_w, topology=topology, tr_pos=tr_pos,
                    include_ehouse=include_ehouse, include_infra=include_infra),
    )


# ── 기하 검사 ─────────────────────────────────────────────────────────────────
def _edge_gaps(boxes):
    """박스 쌍별 평면 최소 거리 행렬 (겹치면 0)."""
    a = np.array([[b["x"], b["y"], b["x"] + b["dx"], b["y"] + b["dy"]] for b in boxes])
    gx = np.maximum(0.0, np.maximum(a[:, None, 0] - a[None, :, 2], a[None, :, 0] - a[:, None, 2]))
    gy = np.maximum(0.0, np.maximum(a[:, None, 1] - a[None, :, 3], a[None, :, 1] - a[:, None, 3]))
    d = np.hypot(gx, gy)
    np.fill_diagonal(d, np.inf)
    return d


def check_layout(layout) -> dict:
    """겹침 수, 유닛(인클로저·PCS) 간 최소 이격, 변압기~유닛/E-House 최소 이격, 부지경계 최소 이격."""
    boxes = layout["boxes"]
    p = layout["params"]
    d = _edge_gaps(boxes)
    a = np.array([[b["x"], b["y"], b["x"] + b["dx"], b["y"] + b["dy"]] for b in boxes])
    ox = np.minimum(a[:, None, 2], a[None, :, 2]) - np.maximum(a[:, None, 0], a[None, :, 0])
    oy = np.minimum(a[:, None, 3], a[None, :, 3]) - np.maximum(a[:, None, 1], a[None, :, 1])
    ov = (ox > 1e-9) & (oy > 1e-9)
    np.fill_diagonal(ov, False)

    kinds = np.array([b["kind"] for b in boxes])
    # 방유제(bund)와 변압기(tr) 간의 상호 포섭은 기초/방유턱 구조이므로 겹침 제외
    is_bund = kinds == "bund"
    is_tr = kinds == "tr"
    if is_bund.any() and is_tr.any():
        ov[np.ix_(is_bund, is_tr)] = False
        ov[np.ix_(is_tr, is_bund)] = False

    unit = np.isin(kinds, ("enc", "pcs"))
    tr = kinds == "tr"
    eh = kinds == "ehouse"
    w, h = layout["site"]
    # 소화전은 울타리 펜스 라인 부속 설비이므로 메인 플랜트 경계 이격 검사에서 분리
    main_boxes = [b for b in boxes if b["kind"] != "hydrant"]
    to_fence = min(min(b["x"], b["y"], w - b["x"] - b["dx"], h - b["y"] - b["dy"]) for b in main_boxes)
    min_unit = float(d[np.ix_(unit, unit)].min()) if unit.sum() > 1 else float("inf")
    min_tr_unit = float(d[np.ix_(tr, unit)].min()) if tr.any() and unit.any() else float("inf")
    min_tr_eh = float(d[np.ix_(tr, eh)].min()) if tr.any() and eh.any() else float("inf")
    min_tr = min(min_tr_unit, min_tr_eh) if tr.any() else float("inf")
    eps = 1e-6
    return dict(
        overlaps=int(ov.sum() // 2),
        min_unit_gap_m=min_unit, min_tr_gap_m=min_tr, min_boundary_m=float(to_fence),
        unit_ok=min_unit + eps >= p["unit_gap"],
        # 블록 열 사이 간선 트렌치가 유닛 이격대 안에 들어가는가 (트렌치는 장비 기초와 겹치면 안 됨)
        trench_fits=layout.get("trench_w", 0.0) <= p["unit_gap"] + eps,
        tr_ok=min_tr + eps >= p["tr_clear"],
        boundary_ok=to_fence + eps >= p["boundary"],
    )


# ── Plotly Mesh3d 용 배열 (종류별 1 트레이스로 묶어 박스 수백 개도 가볍게) ─────────────
_I = [0, 0, 4, 4, 0, 0, 2, 2, 0, 0, 1, 1]
_J = [1, 2, 5, 6, 1, 5, 3, 7, 3, 7, 2, 6]
_K = [2, 3, 6, 7, 5, 4, 7, 6, 7, 4, 6, 5]


def mesh_arrays(boxes):
    xs, ys, zs, ii, jj, kk = [], [], [], [], [], []
    for n, b in enumerate(boxes):
        x0, y0, x1, y1, z1 = b["x"], b["y"], b["x"] + b["dx"], b["y"] + b["dy"], b["dz"]
        z0 = b.get("z0", 0.0)
        xs += [x0, x1, x1, x0, x0, x1, x1, x0]
        ys += [y0, y0, y1, y1, y0, y0, y1, y1]
        zs += [z0, z0, z0, z0, z1, z1, z1, z1]
        o = 8 * n
        ii += [o + v for v in _I]
        jj += [o + v for v in _J]
        kk += [o + v for v in _K]
    return xs, ys, zs, ii, jj, kk


def edge_arrays(boxes, top_only=False):
    """박스 모서리 선 (Scatter3d 1 트레이스용, 박스 사이는 None 으로 끊음). top_only = 윗면 사각형만."""
    xs, ys, zs = [], [], []
    for b in boxes:
        x0, y0, x1, y1 = b["x"], b["y"], b["x"] + b["dx"], b["y"] + b["dy"]
        z0, z1 = b.get("z0", 0.0), b["dz"]
        ring = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
        for z in ((z1,) if top_only else (z0, z1)):
            xs += [p[0] for p in ring] + [None]
            ys += [p[1] for p in ring] + [None]
            zs += [z] * 5 + [None]
        if not top_only:
            for px, py in ring[:4]:
                xs += [px, px, None]
                ys += [py, py, None]
                zs += [z0, z1, None]
    return xs, ys, zs


# ── 구조 뷰: 지중 기초 패드·케이블 트렌치 (05 토목 값) ─────────────────────────────
PAD_T = 0.3   # [가정] 기초 패드 두께 — 05 는 평면 치수만 산정


def pad_boxes(layout, pad_l, pad_w, pad_t=PAD_T):
    """인클로저마다 중심을 맞춘 기초 패드 (z = -pad_t ~ 0)."""
    out = []
    for b in layout["boxes"]:
        if b["kind"] != "enc":
            continue
        cx, cy = b["x"] + b["dx"] / 2.0, b["y"] + b["dy"] / 2.0
        out.append(dict(kind="pad", label="PAD-" + b["label"][4:], x=cx - pad_l / 2.0, y=cy - pad_w / 2.0,
                        dx=pad_l, dy=pad_w, z0=-pad_t, dz=0.0))
    return out


def trench_boxes(layout, depth):
    """트렌치 중심선(직각 폴리라인)을 폭 trench_w · 깊이 depth 의 지중 박스로."""
    hw = layout["trench_w"] / 2.0
    out = []
    for pl in layout["trench"]:
        for (x0, y0), (x1, y1) in zip(pl, pl[1:]):
            xa, xb, ya, yb = min(x0, x1) - hw, max(x0, x1) + hw, min(y0, y1) - hw, max(y0, y1) + hw
            out.append(dict(kind="trench", label="TRENCH", x=xa, y=ya, dx=xb - xa, dy=yb - ya, z0=-depth, dz=0.0))
    return out


def pad_clear_gap(layout, pad_l, pad_w):
    """이웃 인클로저 기초 패드 사이 순간격 [m] — 음수면 패드끼리 겹침(일체 기초 검토)."""
    p, m = layout["params"], layout["metrics"]
    gx = p["unit_gap"] - (pad_l - p["enc_l"]) if m["enc_per_block"] > 1 else float("inf")
    gy = m["row_gap_m"] - (pad_w - p["enc_w"]) if m["blocks_rows"] > 1 else float("inf")
    return min(gx, gy)


def diff_metrics(cur, base):
    """기준안 대비 변화 — {key: (현재, 기준, 차이, 차이%)}."""
    out = {}
    for k in ("site_area_m2", "trench_len_m", "longest_cable_m", "n_enc", "n_pcs"):
        c, b = cur.get(k), base.get(k)
        if isinstance(c, (int, float)) and isinstance(b, (int, float)):
            out[k] = (c, b, c - b, (c - b) / b * 100.0 if b else 0.0)
    return out


# ── 전문가 수준 다중 뷰 CAD DXF (R12 ASCII) ──────────────────────────────────
# 12개 전문 설계 레이어 매핑 (AutoCAD ACI Color 및 규격화)
DXF_LAYERS = {
    "0": {"color": "7", "desc": "Default"},
    "C-PAD-CONC": {"color": "8", "desc": "Concrete Foundation Pads (t=300mm)"},
    "C-TRENCH": {"color": "4", "desc": "Precast Cable Trench (w=800, d=1000)"},
    "C-FENCE": {"color": "1", "desc": "Site Perimeter Security Fence"},
    "C-ROAD": {"color": "9", "desc": "Internal Access Road & Aisle"},
    "E-BESS-ENC": {"color": "7", "desc": "20ft BESS Enclosure (2.90m HC)"},
    "E-PCS-SKID": {"color": "5", "desc": "PCS & MV Transformer Skid (2.40m)"},
    "E-MAIN-TR": {"color": "6", "desc": "Main Step-Up Transformer (154/22.9kV)"},
    "E-EH-SWGR": {"color": "3", "desc": "E-House Switchgear & EMS Control Room"},
    "F-HYDRANT": {"color": "1", "desc": "Outdoor Fire Hydrant & Valve"},
    "F-COVERAGE": {"color": "1", "desc": "NFPA 855 Fire Hydrant 40m Radius Ring"},
    "F-WATER-TANK": {"color": "4", "desc": "Fire Water Storage & Pump Station"},
    "DIM-MAJOR": {"color": "2", "desc": "Dimension Lines & Annotations"},
    "SECTION-AA": {"color": "2", "desc": "Section A-A Foundation Trench Detail"},
    "SECTION-BB": {"color": "3", "desc": "Section B-B Transformer Bund Detail"},
    "TITLE-BLOCK": {"color": "7", "desc": "Standard Engineering Title Block"},
}

_KIND_TO_DXF_LAYER = {
    "enc": "E-BESS-ENC",
    "pcs": "E-PCS-SKID",
    "tr": "E-MAIN-TR",
    "bund": "C-PAD-CONC",
    "ehouse": "E-EH-SWGR",
    "storage": "E-EH-SWGR",
    "tank": "F-WATER-TANK",
    "pump_house": "F-WATER-TANK",
    "basin": "C-TRENCH",
    "hydrant": "F-HYDRANT",
}


def to_dxf(layout: dict, multi_view: bool = False) -> str:
    """
    엔지니어링 CAD DXF (R12 / R2000 호환).
    - multi_view=False (기본값): 기존 테스트 및 단일 평면도 호환 출력 (박스 4선 + 트렌치 선분 + 울타리 4선)
    - multi_view=True: 전문가 수준 멀티뷰 CAD (평면도 + 단면도 A-A/B-B + 12개 전문 레이어 + 치수선 + 표준 표제란)
    """
    if not multi_view:
        _LAYER = {"enc": "BESS-ENC", "pcs": "BESS-PCS", "tr": "BESS-TR", "tank": "FIRE-WATER"}
        out = ["0", "SECTION", "2", "HEADER", "9", "$ACADVER", "1", "AC1009",
               "9", "$INSUNITS", "70", "6", "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES"]

        def s_line(layer, p, q):
            out.extend(["0", "LINE", "8", layer, "10", f"{p[0]:.3f}", "20", f"{p[1]:.3f}", "30", "0.0",
                        "11", f"{q[0]:.3f}", "21", f"{q[1]:.3f}", "31", "0.0"])

        def s_text(layer, p, h, s):
            out.extend(["0", "TEXT", "8", layer, "10", f"{p[0]:.3f}", "20", f"{p[1]:.3f}", "30", "0.0",
                        "40", f"{h:.3f}", "1", s])

        for b in layout["boxes"]:
            lay_name = _LAYER.get(b["kind"], "0")
            x0, y0, x1, y1 = b["x"], b["y"], b["x"] + b["dx"], b["y"] + b["dy"]
            pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
            for p, q in zip(pts, pts[1:]):
                s_line(lay_name, p, q)
            s_text("LABEL", (x0 + 0.2, y0 + 0.2), min(0.6, b["dy"] / 3), b["label"])
        for pl in layout["trench"]:
            for p, q in zip(pl, pl[1:]):
                s_line("TRENCH", p, q)
        f = layout["fence"]
        for p, q in zip(f, f[1:]):
            s_line("FENCE", p, q)
        out.extend(["0", "ENDSEC", "0", "EOF"])
        return "\n".join(out) + "\n"

    # multi_view=True: 전문가 수준 종합 평면도 및 횡·종단면도 (A-A, B-B)
    site_w, site_h = layout["site"]
    boxes = layout["boxes"]
    trench = layout["trench"]
    fence = layout["fence"]

    out = [
        "0", "SECTION", "2", "HEADER",
        "9", "$ACADVER", "1", "AC1009",
        "9", "$INSUNITS", "70", "6",  # 단위: 미터 (Meters)
        "0", "ENDSEC",
        "0", "SECTION", "2", "TABLES",
        "0", "TABLE", "2", "LAYER", "70", str(len(DXF_LAYERS)),
    ]

    for lay_name, lay_info in DXF_LAYERS.items():
        out.extend([
            "0", "LAYER", "2", lay_name, "70", "0",
            "62", lay_info["color"], "6", "CONTINUOUS",
        ])
    out.extend(["0", "ENDSEC", "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES"])

    # 도면 제도 프리미티브 헬퍼
    def dxf_line(layer: str, p1: tuple, p2: tuple):
        out.extend([
            "0", "LINE", "8", layer,
            "10", f"{p1[0]:.3f}", "20", f"{p1[1]:.3f}", "30", "0.0",
            "11", f"{p2[0]:.3f}", "21", f"{p2[1]:.3f}", "31", "0.0",
        ])

    def dxf_rect(layer: str, x0: float, y0: float, w: float, h: float):
        pts = [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h), (x0, y0)]
        for p, q in zip(pts, pts[1:]):
            dxf_line(layer, p, q)

    def dxf_text(layer: str, pt: tuple, height: float, text_str: str):
        out.extend([
            "0", "TEXT", "8", layer,
            "10", f"{pt[0]:.3f}", "20", f"{pt[1]:.3f}", "30", "0.0",
            "40", f"{height:.3f}", "1", text_str,
        ])

    def dxf_circle(layer: str, center: tuple, radius: float):
        out.extend([
            "0", "CIRCLE", "8", layer,
            "10", f"{center[0]:.3f}", "20", f"{center[1]:.3f}", "30", "0.0",
            "40", f"{radius:.3f}",
        ])

    def dxf_dim_linear(layer: str, p1: tuple, p2: tuple, offset: float, label: str, is_vert: bool = False):
        """치수선 + 지시선 + 수치 텍스트 제도."""
        if not is_vert:
            y_dim = p1[1] + offset
            dxf_line(layer, p1, (p1[0], y_dim + 0.3 * (1 if offset > 0 else -1)))
            dxf_line(layer, p2, (p2[0], y_dim + 0.3 * (1 if offset > 0 else -1)))
            dxf_line(layer, (p1[0], y_dim), (p2[0], y_dim))
            # 양단 틱 마크 (Arrow tick)
            dxf_line(layer, (p1[0] - 0.2, y_dim - 0.2), (p1[0] + 0.2, y_dim + 0.2))
            dxf_line(layer, (p2[0] - 0.2, y_dim - 0.2), (p2[0] + 0.2, y_dim + 0.2))
            mid_x = (p1[0] + p2[0]) / 2.0
            dxf_text(layer, (mid_x - 1.0, y_dim + 0.25), 0.45, label)
        else:
            x_dim = p1[0] + offset
            dxf_line(layer, p1, (x_dim + 0.3 * (1 if offset > 0 else -1), p1[1]))
            dxf_line(layer, p2, (x_dim + 0.3 * (1 if offset > 0 else -1), p2[1]))
            dxf_line(layer, (x_dim, p1[1]), (x_dim, p2[1]))
            dxf_line(layer, (x_dim - 0.2, p1[1] - 0.2), (x_dim + 0.2, p1[1] + 0.2))
            dxf_line(layer, (x_dim - 0.2, p2[1] - 0.2), (x_dim + 0.2, p2[1] + 0.2))
            mid_y = (p1[1] + p2[1]) / 2.0
            dxf_text(layer, (x_dim + 0.25, mid_y - 0.3), 0.45, label)

    # ═════════════════════════════════════════════════════════════════════════
    # VIEW 1: 전체 종합 평면도 (General Site Layout Plan)
    # ═════════════════════════════════════════════════════════════════════════
    dxf_text("TITLE-BLOCK", (0.0, site_h + 3.0), 1.2, "VIEW 1: GENERAL SITE LAYOUT PLAN (1:100)")
    
    # 1-1. 부지 경계 울타리 (C-FENCE)
    for p, q in zip(fence, fence[1:]):
        dxf_line("C-FENCE", p, q)

    # 1-2. 각 장비 기초 패드 및 본체 외형 (C-PAD-CONC, E-BESS-ENC, E-PCS-SKID 등)
    pad_t = 0.30
    for b in boxes:
        kind = b["kind"]
        lay = _KIND_TO_DXF_LAYER.get(kind, "0")
        x0, y0, dx, dy = b["x"], b["y"], b["dx"], b["dy"]

        # 콘크리트 패드 (장비 외곽 +0.25m 여유선)
        if kind in ("enc", "pcs"):
            dxf_rect("C-PAD-CONC", x0 - 0.25, y0 - 0.25, dx + 0.50, dy + 0.50)

        # 설비 본체 외곽 사각형
        dxf_rect(lay, x0, y0, dx, dy)
        dxf_text(lay, (x0 + 0.15, y0 + 0.25), min(0.40, dy / 3), b["label"])

        # 세부 내부 디테일 (전문가 수준 도면화)
        if kind == "enc":
            # 배터리 컨테이너 양개 도어 및 단부 HVAC 표시선
            dxf_line(lay, (x0 + dx * 0.45, y0), (x0 + dx * 0.45, y0 + dy))
            dxf_line(lay, (x0 + dx * 0.55, y0), (x0 + dx * 0.55, y0 + dy))
            dxf_rect(lay, x0 + dx - 0.6, y0 + 0.2, 0.5, dy - 0.4)  # HVAC 팩
        elif kind == "pcs":
            # PCS 인버터 모듈 및 MV 변압기 분할선, 상부 부싱 원
            dxf_line(lay, (x0 + dx * 0.6, y0), (x0 + dx * 0.6, y0 + dy))
            dxf_circle(lay, (x0 + 0.5, y0 + dy / 2.0), 0.25)  # 변압기 심볼
            dxf_circle(lay, (x0 + 1.2, y0 + dy / 2.0), 0.25)
        elif kind == "hydrant":
            # 소화전 심볼 및 40m 소화 방수 유효 반경 원호
            cx, cy = x0 + dx / 2.0, y0 + dy / 2.0
            dxf_circle("F-HYDRANT", (cx, cy), 0.4)
            dxf_line("F-HYDRANT", (cx - 0.5, cy), (cx + 0.5, cy))
            dxf_line("F-HYDRANT", (cx, cy - 0.5), (cx, cy + 0.5))
            dxf_circle("F-COVERAGE", (cx, cy), 40.0)

    # 1-3. 지중 케이블 트렌치 (C-TRENCH)
    for pl in trench:
        for p, q in zip(pl, pl[1:]):
            dxf_line("C-TRENCH", p, q)

    # 1-4. 주요 외곽 치수선 (DIM-MAJOR)
    dxf_dim_linear("DIM-MAJOR", (0.0, 0.0), (site_w, 0.0), -3.0, f"SITE TOTAL WIDTH = {site_w:.2f} m")
    dxf_dim_linear("DIM-MAJOR", (0.0, 0.0), (0.0, site_h), -3.0, f"SITE TOTAL DEPTH = {site_h:.2f} m", is_vert=True)

    # ═════════════════════════════════════════════════════════════════════════
    # VIEW 2: 횡단면도 Section A-A (패드-트렌치-배터리-PCS 단면)
    # ═════════════════════════════════════════════════════════════════════════
    # 평면도 상단 Y = site_h + 15m 지점에 전개
    aa_x0 = 0.0
    aa_y0 = site_h + 18.0

    dxf_text("SECTION-AA", (aa_x0, aa_y0 + 6.0), 1.0, "VIEW 2: SECTION A-A — BESS PAD, TRENCH & PCS SECTION (1:50)")
    # 지표면 기준선 (Ground Level ±0.00)
    dxf_line("SECTION-AA", (aa_x0 - 2.0, aa_y0), (aa_x0 + 38.0, aa_y0))
    dxf_text("SECTION-AA", (aa_x0 - 5.0, aa_y0 + 0.1), 0.4, "GL ±0.00")

    # (1) 배터리 콘크리트 패드 (두께 300mm, 폭 2.94m)
    dxf_rect("C-PAD-CONC", aa_x0 + 2.0, aa_y0, 2.94, pad_t)
    # 배터리 컨테이너 본체 (폭 2.44m, 높이 2.90m)
    dxf_rect("E-BESS-ENC", aa_x0 + 2.25, aa_y0 + pad_t, 2.44, 2.90)
    dxf_text("E-BESS-ENC", (aa_x0 + 2.4, aa_y0 + pad_t + 1.4), 0.35, "BESS CONTAINER (H=2.90m)")

    # (2) U형 케이블 트렌치 (폭 0.80m, 깊이 1.00m, 벽체 콘크리트 두께 0.15m)
    tr_x = aa_x0 + 6.5
    dxf_rect("C-TRENCH", tr_x, aa_y0 - 1.00, 0.80, 1.00)
    dxf_line("C-TRENCH", (tr_x + 0.15, aa_y0), (tr_x + 0.15, aa_y0 - 0.85))
    dxf_line("C-TRENCH", (tr_x + 0.15, aa_y0 - 0.85), (tr_x + 0.65, aa_y0 - 0.85))
    dxf_line("C-TRENCH", (tr_x + 0.65, aa_y0 - 0.85), (tr_x + 0.65, aa_y0))
    # 트렌치 상부 그레이팅 커버 (t=80mm)
    dxf_rect("C-PAD-CONC", tr_x - 0.05, aa_y0 - 0.08, 0.90, 0.08)
    dxf_text("C-TRENCH", (tr_x - 0.2, aa_y0 - 1.3), 0.35, "PRECAST TRENCH (W=800, D=1000)")

    # (3) 중앙 작업 유지보수 통로 (Aisle 3.8m)
    dxf_text("C-ROAD", (aa_x0 + 8.5, aa_y0 + 0.3), 0.4, "O&M AISLE (W=3.80m)")

    # (4) PCS / MV 일체형 스키드 패드 (두께 300mm, 폭 2.60m)
    pcs_sec_x = aa_x0 + 13.5
    dxf_rect("C-PAD-CONC", pcs_sec_x, aa_y0, 2.60, pad_t)
    # PCS 스키드 본체 (폭 2.20m, 높이 2.40m)
    dxf_rect("E-PCS-SKID", pcs_sec_x + 0.20, aa_y0 + pad_t, 2.20, 2.40)
    dxf_circle("E-PCS-SKID", (pcs_sec_x + 0.8, aa_y0 + pad_t + 2.7), 0.18)  # MV 부싱
    dxf_circle("E-PCS-SKID", (pcs_sec_x + 1.4, aa_y0 + pad_t + 2.7), 0.18)
    dxf_text("E-PCS-SKID", (pcs_sec_x + 0.3, aa_y0 + pad_t + 1.2), 0.35, "PCS/MV SKID (H=2.40m)")

    # 단면 A-A 치수선
    dxf_dim_linear("DIM-MAJOR", (aa_x0 + 2.25, aa_y0 + pad_t), (aa_x0 + 2.25, aa_y0 + pad_t + 2.90), -1.2, "2900", is_vert=True)
    dxf_dim_linear("DIM-MAJOR", (tr_x, aa_y0), (tr_x, aa_y0 - 1.00), -0.8, "1000", is_vert=True)
    dxf_dim_linear("DIM-MAJOR", (pcs_sec_x + 0.20, aa_y0 + pad_t), (pcs_sec_x + 0.20, aa_y0 + pad_t + 2.40), 2.8, "2400", is_vert=True)

    # ═════════════════════════════════════════════════════════════════════════
    # VIEW 3: 종단면도 Section B-B (주변압기-방유벽-소방도로 단면)
    # ═════════════════════════════════════════════════════════════════════════
    # 평면도 우측 X = site_w + 12m 지점에 전개
    bb_x0 = site_w + 15.0
    bb_y0 = 0.0

    dxf_text("SECTION-BB", (bb_x0, bb_y0 + site_h * 0.6), 1.0, "VIEW 3: SECTION B-B — MAIN TR & BUND WALL (1:50)")
    dxf_line("SECTION-BB", (bb_x0 - 2.0, bb_y0 + 2.0), (bb_x0 + 28.0, bb_y0 + 2.0))
    dxf_text("SECTION-BB", (bb_x0 - 5.0, bb_y0 + 2.1), 0.4, "GL ±0.00")

    # (1) 변압기 오일 방유벽 (Bund Wall: 높이 0.70m, 폭 7.2m)
    bund_x = bb_x0 + 2.0
    bund_gl = bb_y0 + 2.0
    dxf_rect("C-PAD-CONC", bund_x, bund_gl, 7.2, 0.70)
    # 방유벽 내부 슬래브 및 콘크리트 패드
    dxf_rect("C-PAD-CONC", bund_x + 0.3, bund_gl, 6.6, 0.40)
    # 변압기 본체 (폭 4.8m, 높이 4.2m)
    dxf_rect("E-MAIN-TR", bund_x + 1.2, bund_gl + 0.40, 4.8, 4.20)
    # 154kV 초고압 부싱 심볼
    dxf_line("E-MAIN-TR", (bund_x + 2.2, bund_gl + 4.6), (bund_x + 2.2, bund_gl + 5.6))
    dxf_line("E-MAIN-TR", (bund_x + 3.6, bund_gl + 4.6), (bund_x + 3.6, bund_gl + 5.6))
    dxf_line("E-MAIN-TR", (bund_x + 5.0, bund_gl + 4.6), (bund_x + 5.0, bund_gl + 5.6))
    dxf_text("E-MAIN-TR", (bund_x + 1.5, bund_gl + 2.5), 0.40, "154kV MAIN STEP-UP TR (H=4.20m)")
    dxf_text("C-PAD-CONC", (bund_x + 0.2, bund_gl - 0.6), 0.35, "OIL BUND WALL (H=700mm)")

    # (2) 소방 전용 통행로 (Fire Lane W=6.0m)
    road_x = bund_x + 8.5
    dxf_line("C-ROAD", (road_x, bund_gl), (road_x + 6.0, bund_gl))
    dxf_text("C-ROAD", (road_x + 0.5, bund_gl + 0.4), 0.4, "MAIN FIRE ACCESS ROAD (W=6.0m)")

    # ═════════════════════════════════════════════════════════════════════════
    # VIEW 4: 표준 엔지니어링 표제란 (Title Block & Drawing Legend)
    # ═════════════════════════════════════════════════════════════════════════
    # 도면 우측 하단 (bb_x0, bb_y0 - 15.0 지점)
    tb_x0 = bb_x0
    tb_y0 = -16.0
    tb_w = 32.0
    tb_h = 14.0

    dxf_rect("TITLE-BLOCK", tb_x0, tb_y0, tb_w, tb_h)
    dxf_line("TITLE-BLOCK", (tb_x0, tb_y0 + 9.5), (tb_x0 + tb_w, tb_y0 + 9.5))
    dxf_line("TITLE-BLOCK", (tb_x0 + 16.0, tb_y0), (tb_x0 + 16.0, tb_y0 + 9.5))

    # 표제란 메타데이터
    dxf_text("TITLE-BLOCK", (tb_x0 + 1.0, tb_y0 + 12.5), 0.65, "PROJECT: UTILITY-SCALE BESS EPC PROJECT")
    dxf_text("TITLE-BLOCK", (tb_x0 + 1.0, tb_y0 + 10.5), 0.55, "DRAWING: COMPREHENSIVE SITE LAYOUT & SECTIONS (A-A, B-B)")
    dxf_text("TITLE-BLOCK", (tb_x0 + 1.0, tb_y0 + 7.5), 0.45, "DWG NO: DWG-BESS-EPC-001 (REV 1.0)")
    dxf_text("TITLE-BLOCK", (tb_x0 + 1.0, tb_y0 + 5.5), 0.40, f"SITE DIMENSION: {site_w:.1f} m x {site_h:.1f} m")
    dxf_text("TITLE-BLOCK", (tb_x0 + 1.0, tb_y0 + 3.5), 0.40, f"TOTAL ENCLOSURES: {len([b for b in boxes if b['kind']=='enc'])} EA / PCS: {len([b for b in boxes if b['kind']=='pcs'])} EA")
    dxf_text("TITLE-BLOCK", (tb_x0 + 1.0, tb_y0 + 1.5), 0.40, "SCALE: 1:100 (METRIC mm/m) · CAD R12 / R2000 COMPLIANT")

    dxf_text("TITLE-BLOCK", (tb_x0 + 17.0, tb_y0 + 7.5), 0.45, "DESIGNED BY: BESS EPC AI SYSTEM")
    dxf_text("TITLE-BLOCK", (tb_x0 + 17.0, tb_y0 + 5.5), 0.40, "STATUS: TENDER / BASIC DESIGN APPROVED")
    dxf_text("TITLE-BLOCK", (tb_x0 + 17.0, tb_y0 + 3.5), 0.40, "COMPLIANCE: NFPA 855 / IEEE 1547 / KEC / NFTC")
    dxf_text("TITLE-BLOCK", (tb_x0 + 17.0, tb_y0 + 1.5), 0.40, "COORDINATE SYSTEM: LOCAL GRID (0.00, 0.00)")

    out.extend(["0", "ENDSEC", "0", "EOF"])
    return "\n".join(out) + "\n"


# ── 시공·O&M 중장비 활동 반경 시뮬레이션 ───────────────────────────────────────
def heavy_equipment_simulation(layout: dict) -> dict:
    """
    시공 및 O&M 단계의 중장비(50T 크레인 및 3.5T 전동 지게차) 활동 반경 및 통로 간섭 시뮬레이션.
    
    1. 50T 올테레인 모바일 크레인 (BESS 컨테이너 인양용):
       - 아우트리거(Outrigger) 전개 폭: 7.5m × 7.5m
       - 유효 정격 인양 반경: R = 20.0m (30톤 컨테이너 기준 안전 모멘트)
       - 크레인 작업 위치(Crane Setup Stations): 남측 메인 간선도로 및 단부 진입로 2~4개소
       - 모든 BESS 컨테이너 및 PCS 가 20m 붐 도달 반경 내에 포함되는지(Coverage) 검증
       
    2. 3.5T 전동 지게차 / 모바일 리프트 (O&M 모듈 교체용):
       - 차량 전폭: 1.30m, 최소 회전 반경: R = 3.80m
       - 필요 최소 통로 폭: 3.50m (양측 0.5m 안전 여유 포함)
       - 실제 통로 폭(Aisle width)과 비교하여 간섭 여부(Clash) 및 여유 마진(Margin) 검증
    """
    boxes = layout["boxes"]
    site_w, site_h = layout["site"]
    aisle = layout["params"].get("aisle", 4.0)
    b = layout["params"].get("boundary", 5.0)

    main_targets = [b for b in boxes if b["kind"] in ("enc", "pcs")]

    # 1. 크레인 설치 스테이션 산정 (남측 도로, 블록 간 작업 통로, 북측 도로망)
    # X 좌표 후보군: 부지 폭을 따라 20~28m 간격으로 분할
    n_x = max(2, min(4, math.ceil(site_w / 28.0)))
    station_xs = [b + 6.0 + i * ((site_w - 2 * b - 12.0) / max(1, n_x - 1)) for i in range(n_x)]

    # Y 좌표 후보군: 설비 행들의 Y 좌표들을 기반으로 통로선 추출
    if main_targets:
        min_y = min(t["y"] for t in main_targets)
        max_y = max(t["y"] + t["dy"] for t in main_targets)
        # 고유 행(row) Y 좌표 추출
        row_ys = sorted(list(set(round(t["y"], 1) for t in main_targets)))
        station_ys = [max(b + 2.0, min_y - 3.5)]  # 남측 메인 도로
        # 행 간 작업 통로 (Aisle)
        for k in range(len(row_ys) - 1):
            station_ys.append((row_ys[k] + row_ys[k + 1]) / 2.0)
        # 북측 순환 도로 (설비 군집 깊이가 25m 초과 시)
        if max_y - min_y > 25.0:
            station_ys.append(min(site_h - b - 2.0, max_y + 3.5))
    else:
        station_ys = [site_h / 2.0]

    crane_stations = []
    crane_radius = 20.0
    outrigger_w = 7.5

    st_cnt = 1
    for sy in station_ys:
        for sx in station_xs:
            crane_stations.append({
                "station_id": f"CRANE-ST-{st_cnt:02d}",
                "x": round(sx, 2),
                "y": round(sy, 2),
                "outrigger_w": outrigger_w,
                "outrigger_l": outrigger_w,
                "radius_m": crane_radius,
                "label": f"50T Crane #{st_cnt} (R=20m)"
            })
            st_cnt += 1

    # 크레인 인양 커버리지 검증
    reachable_cnt = 0
    for t in main_targets:
        cx = t["x"] + t["dx"] / 2.0
        cy = t["y"] + t["dy"] / 2.0
        # 적어도 한 스테이션에서 20m + 오차 2m 이내이면 인양 도달 가능
        if any(math.hypot(cx - st["x"], cy - st["y"]) <= crane_radius + 2.0 for st in crane_stations):
            reachable_cnt += 1

    crane_coverage_pct = round((reachable_cnt / max(1, len(main_targets))) * 100.0, 1)

    # 지게차 통로 적합성 판정
    forklift_turning_r = 3.8
    forklift_min_aisle = 3.5
    aisle_margin = round(aisle - forklift_min_aisle, 2)
    forklift_ok = aisle >= forklift_min_aisle

    # 크레인 20m 링 좌표 생성 (Plotly 3D용)
    c_xs, c_ys, c_zs = [], [], []
    for st in crane_stations:
        for step in range(49):
            theta = 2.0 * math.pi * step / 48
            c_xs.append(st["x"] + crane_radius * math.cos(theta))
            c_ys.append(st["y"] + crane_radius * math.sin(theta))
            c_zs.append(0.15)
        c_xs.append(None)
        c_ys.append(None)
        c_zs.append(None)

    # 아우트리거 베이스 박스 좌표
    o_xs, o_ys, o_zs = [], [], []
    for st in crane_stations:
        hw = outrigger_w / 2.0
        opts = [
            (st["x"] - hw, st["y"] - hw),
            (st["x"] + hw, st["y"] - hw),
            (st["x"] + hw, st["y"] + hw),
            (st["x"] - hw, st["y"] + hw),
            (st["x"] - hw, st["y"] - hw),
        ]
        for p in opts:
            o_xs.append(p[0])
            o_ys.append(p[1])
            o_zs.append(0.12)
        o_xs.append(None)
        o_ys.append(None)
        o_zs.append(None)

    return {
        "crane_stations": crane_stations,
        "crane_coverage_pct": crane_coverage_pct,
        "crane_radius_m": crane_radius,
        "outrigger_size_m": outrigger_w,
        "forklift_turning_radius_m": forklift_turning_r,
        "forklift_min_aisle_m": forklift_min_aisle,
        "site_aisle_m": aisle,
        "aisle_margin_m": aisle_margin,
        "forklift_pass": forklift_ok,
        "all_pass": crane_coverage_pct >= 90.0 and forklift_ok,
        "crane_circles": (c_xs, c_ys, c_zs),
        "outrigger_boxes": (o_xs, o_ys, o_zs),
    }


# ── 2D 공학 정밀 횡단면도 (Section A-A & Section B-B) Figure 생성 ─────────────
def create_section_figures(layout: dict):
    """
    Plotly 2D 인터랙티브 공학 횡단면도 (Section A-A 및 Section B-B) 생성.
    기초 패드, 케이블 트렌치, 컨테이너/PCS 입면, 지표면(GL), 정밀 치수선 표기.
    """
    import plotly.graph_objects as go

    # 1. Section A-A: BESS Pad - Trench - PCS Section
    fig_a = go.Figure()

    # GL 지표면선
    fig_a.add_trace(go.Scatter(
        x=[-2, 26], y=[0, 0], mode="lines",
        line=dict(color="#8d6e63", width=3, dash="dash"),
        name="GL ±0.00m (Ground Level)"
    ))

    # 배터리 콘크리트 패드 (x: 1 ~ 4, y: 0 ~ 0.3)
    fig_a.add_trace(go.Scatter(
        x=[1, 4, 4, 1, 1], y=[0, 0, 0.30, 0.30, 0],
        fill="toself", fillcolor="rgba(148, 163, 184, 0.45)",
        line=dict(color="#475569", width=2),
        name="Concrete Pad (t=300mm)"
    ))

    # 배터리 컨테이너 본체 (x: 1.25 ~ 3.75, y: 0.30 ~ 3.20)
    fig_a.add_trace(go.Scatter(
        x=[1.25, 3.75, 3.75, 1.25, 1.25], y=[0.30, 0.30, 3.20, 3.20, 0.30],
        fill="toself", fillcolor="rgba(241, 245, 249, 0.95)",
        line=dict(color="#0f172a", width=2.5),
        name="20ft BESS Enclosure (H=2.90m)"
    ))
    fig_a.add_annotation(x=2.5, y=1.75, text="<b>BESS CONTAINER</b><br>2.44m(W) x 2.90m(H)",
                         showarrow=False, font=dict(color="#0f172a", size=11))

    # 케이블 트렌치 (x: 4.8 ~ 5.6, y: -1.0 ~ 0)
    fig_a.add_trace(go.Scatter(
        x=[4.8, 5.6, 5.6, 4.8, 4.8], y=[-1.0, -1.0, 0, 0, -1.0],
        fill="toself", fillcolor="rgba(217, 119, 6, 0.35)",
        line=dict(color="#d97706", width=2),
        name="Cable Trench (W=800, D=1000)"
    ))
    # 트렌치 내부 MV/DC 케이블 선
    fig_a.add_trace(go.Scatter(
        x=[5.0, 5.4], y=[-0.6, -0.6], mode="markers+lines",
        marker=dict(size=8, color="#ef4444"), line=dict(color="#ef4444", width=2),
        name="MV/DC Cables"
    ))
    fig_a.add_annotation(x=5.2, y=-0.5, text="Trench<br>D=1.0m", showarrow=False,
                         font=dict(color="#d97706", size=10))

    # O&M 작업 통로
    fig_a.add_annotation(x=7.5, y=0.5, text="<b>O&M 통로 (Aisle)</b><br>유효 폭 3.8m",
                         showarrow=False, font=dict(color="#64748b", size=11))

    # PCS / MV 일체형 스키드 패드 (x: 9.5 ~ 12.5, y: 0 ~ 0.30)
    fig_a.add_trace(go.Scatter(
        x=[9.5, 12.5, 12.5, 9.5, 9.5], y=[0, 0, 0.30, 0.30, 0],
        fill="toself", fillcolor="rgba(148, 163, 184, 0.45)",
        line=dict(color="#475569", width=2),
        showlegend=False
    ))

    # PCS 스키드 본체 (x: 9.75 ~ 12.25, y: 0.30 ~ 2.70)
    fig_a.add_trace(go.Scatter(
        x=[9.75, 12.25, 12.25, 9.75, 9.75], y=[0.30, 0.30, 2.70, 2.70, 0.30],
        fill="toself", fillcolor="rgba(21, 101, 192, 0.85)",
        line=dict(color="#0d47a1", width=2.5),
        name="PCS / MV Skid (H=2.40m)"
    ))
    fig_a.add_annotation(x=11.0, y=1.5, text="<b>PCS/MV SKID</b><br>2.20m(W) x 2.40m(H)",
                         showarrow=False, font=dict(color="#ffffff", size=11))

    # 치수 보조선
    fig_a.update_layout(
        title="<b>📐 Section A-A: 기초 패드 · 케이블 트렌치 · 배터리 및 PCS 횡단면도</b> (단위: m)",
        xaxis=dict(title="수평 거리 (m)", range=[-1, 14], zeroline=False),
        yaxis=dict(title="표고 EL / 높이 (m)", range=[-1.5, 4.0], zeroline=False),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(248, 250, 252, 0.05)",
        font=dict(color="#e2e8f0"), height=380,
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(orientation="h", y=-0.25, x=0)
    )

    # 2. Section B-B: Transformer & Oil Bund Wall Section
    fig_b = go.Figure()
    fig_b.add_trace(go.Scatter(
        x=[-2, 22], y=[0, 0], mode="lines",
        line=dict(color="#8d6e63", width=3, dash="dash"),
        name="GL ±0.00m"
    ))

    # 방유벽 (x: 1 ~ 9, y: 0 ~ 0.70)
    fig_b.add_trace(go.Scatter(
        x=[1, 9, 9, 1, 1], y=[0, 0, 0.70, 0.70, 0],
        fill="toself", fillcolor="rgba(226, 232, 240, 0.3)",
        line=dict(color="#64748b", width=2),
        name="Oil Bund Wall (H=700mm)"
    ))

    # 변압기 기초 (x: 2 ~ 8, y: 0 ~ 0.40)
    fig_b.add_trace(go.Scatter(
        x=[2, 8, 8, 2, 2], y=[0, 0, 0.40, 0.40, 0],
        fill="toself", fillcolor="rgba(148, 163, 184, 0.6)",
        line=dict(color="#334155", width=2),
        name="TR Foundation Pad"
    ))

    # 변압기 본체 (x: 2.5 ~ 7.5, y: 0.40 ~ 4.60)
    fig_b.add_trace(go.Scatter(
        x=[2.5, 7.5, 7.5, 2.5, 2.5], y=[0.40, 0.40, 4.60, 4.60, 0.40],
        fill="toself", fillcolor="rgba(192, 38, 211, 0.75)",
        line=dict(color="#701a75", width=2.5),
        name="154kV Main Transformer"
    ))
    fig_b.add_annotation(x=5.0, y=2.5, text="<b>MAIN TR (154/22.9kV)</b><br>H=4.20m",
                         showarrow=False, font=dict(color="#ffffff", size=12))

    # 소방 통행로 (x: 10 ~ 17, y: 0 ~ 0.15)
    fig_b.add_trace(go.Scatter(
        x=[10, 17, 17, 10, 10], y=[0, 0, 0.15, 0.15, 0],
        fill="toself", fillcolor="rgba(100, 116, 139, 0.4)",
        line=dict(color="#475569", width=2),
        name="Fire Access Road (W=7.0m)"
    ))
    fig_b.add_annotation(x=13.5, y=0.5, text="<b>주 진입 및 소방도로</b><br>폭 7.0m",
                         showarrow=False, font=dict(color="#94a3b8", size=11))

    fig_b.update_layout(
        title="<b>📐 Section B-B: 주변압기 기초 · 오일 방유벽 · 주 소방도로 종단면도</b> (단위: m)",
        xaxis=dict(title="수평 거리 (m)", range=[-1, 19], zeroline=False),
        yaxis=dict(title="표고 EL / 높이 (m)", range=[-0.5, 5.5], zeroline=False),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(248, 250, 252, 0.05)",
        font=dict(color="#e2e8f0"), height=380,
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(orientation="h", y=-0.25, x=0)
    )

    return fig_a, fig_b


# ── 소화전 40m 유효 방수 반경 (Coverage) 검증 및 3D 기하 생성 ───────────────
def check_fire_coverage(layout: dict, radius_m: float = 40.0) -> dict:
    """
    NFPA 24 / NFPC 109 기준: 부지 내 모든 주요 전기·배터리 설비(인클로저, PCS, 주변압기, E-House)가
    소화전 유효 도달 반경(호스 전개 보행거리 기준 40.0m) 내에 포함되는지 기하학적 커버리지 판정.
    """
    boxes = layout["boxes"]
    hydrants = [b for b in boxes if b["kind"] == "hydrant"]
    main_kinds = ("enc", "pcs", "tr", "ehouse")
    main_assets = [b for b in boxes if b["kind"] in main_kinds]

    if not hydrants or not main_assets:
        return {
            "coverage_pct": 0.0 if not hydrants else 100.0,
            "all_covered": False if not hydrants else True,
            "total_assets": len(main_assets),
            "covered_assets": 0,
            "uncovered": [b["label"] for b in main_assets] if not hydrants else [],
            "max_dist_m": 0.0,
            "avg_dist_m": 0.0,
            "radius_m": radius_m,
        }

    h_coords = [(h["x"] + h["dx"] / 2.0, h["y"] + h["dy"] / 2.0) for h in hydrants]
    
    covered_cnt = 0
    uncovered = []
    dists = []

    for b in main_assets:
        cx = b["x"] + b["dx"] / 2.0
        cy = b["y"] + b["dy"] / 2.0
        min_d = min(math.hypot(cx - hx, cy - hy) for hx, hy in h_coords)
        dists.append(min_d)
        if min_d <= radius_m + 1e-6:
            covered_cnt += 1
        else:
            uncovered.append({"label": b["label"], "kind": b["kind"], "dist_m": round(min_d, 1)})

    tot = len(main_assets)
    pct = round((covered_cnt / tot) * 100.0, 1) if tot > 0 else 100.0

    return {
        "coverage_pct": pct,
        "all_covered": len(uncovered) == 0,
        "total_assets": tot,
        "covered_assets": covered_cnt,
        "uncovered": uncovered,
        "max_dist_m": round(max(dists), 1) if dists else 0.0,
        "avg_dist_m": round(sum(dists) / len(dists), 1) if dists else 0.0,
        "radius_m": radius_m,
    }


def hydrant_coverage_circles(layout: dict, radius_m: float = 40.0, n_pts: int = 48):
    """
    Plotly 3D Scatter3d 용: 각 소화전 중심에서 반경 radius_m 의 지표면 원형 궤적 좌표 (xs, ys, zs).
    여러 소화전의 링을 하나의 Scatter3d 트레이스로 그릴 수 있도록 None 분리.
    """
    hydrants = [b for b in layout["boxes"] if b["kind"] == "hydrant"]
    xs, ys, zs = [], [], []
    for h in hydrants:
        cx = h["x"] + h["dx"] / 2.0
        cy = h["y"] + h["dy"] / 2.0
        for step in range(n_pts + 1):
            theta = 2.0 * math.pi * step / n_pts
            xs.append(cx + radius_m * math.cos(theta))
            ys.append(cy + radius_m * math.sin(theta))
            zs.append(0.04)  # 지표면 바로 위 살짝 띄움
        xs.append(None)
        ys.append(None)
        zs.append(None)
    return xs, ys, zs


def hydrant_coverage_dome_mesh(layout: dict, radius_m: float = 40.0, n_lat: int = 8, n_lon: int = 16):
    """
    Plotly 3D Mesh3d 용: 각 소화전 중심에서 반경 radius_m 의 반구형(Dome) 반투명 메쉬 좌표 (xs, ys, zs, i, j, k).
    """
    hydrants = [b for b in layout["boxes"] if b["kind"] == "hydrant"]
    xs, ys, zs = [], [], []
    ii, jj, kk = [], [], []

    for h in hydrants:
        cx = h["x"] + h["dx"] / 2.0
        cy = h["y"] + h["dy"] / 2.0
        v_offset = len(xs)

        # 정점 생성 (위도 0~pi/2, 경도 0~2pi)
        for lat_i in range(n_lat + 1):
            phi = (math.pi / 2.0) * (lat_i / n_lat)  # 0 (지표) ~ pi/2 (꼭대기)
            r_plane = radius_m * math.cos(phi)
            z_val = radius_m * math.sin(phi) * 0.40  # 높이 40% 편평화 (시각적 과장 억제)
            for lon_i in range(n_lon):
                theta = 2.0 * math.pi * (lon_i / n_lon)
                xs.append(cx + r_plane * math.cos(theta))
                ys.append(cy + r_plane * math.sin(theta))
                zs.append(z_val)

        # 삼각형 면 인덱스 생성
        for lat_i in range(n_lat):
            for lon_i in range(n_lon):
                p1 = v_offset + lat_i * n_lon + lon_i
                p2 = v_offset + lat_i * n_lon + ((lon_i + 1) % n_lon)
                p3 = v_offset + (lat_i + 1) * n_lon + lon_i
                p4 = v_offset + (lat_i + 1) * n_lon + ((lon_i + 1) % n_lon)
                ii.extend([p1, p2])
                jj.extend([p3, p4])
                kk.extend([p2, p3])

    return xs, ys, zs, ii, jj, kk

