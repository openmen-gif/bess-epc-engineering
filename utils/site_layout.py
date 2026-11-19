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
PCS_DIM = (6.05, 2.44, 2.9)   # [가정] PCS/MV 스키드
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

    # 정사각형에 가장 가까운 블록 열 수
    best = None
    for c in range(1, n_pcs + 1):
        r = math.ceil(n_pcs / c)
        w = c * block_len + (c - 1) * unit_gap
        h = r * block_dep + (r - 1) * row_gap
        score = abs(math.log(w / h))
        if best is None or score < best[0]:
            best = (score, c, r, w, h)
    _, cols, rows, arr_w, arr_h = best

    tank_side = math.sqrt(water_m3 / TANK_H) if water_m3 > 0 else 0.0
    b = boundary
    band = max(tr_w + (1.2 if include_infra else 0.0), tank_side, (eh_w if include_ehouse else 0.0))  # 남측 띠 깊이 — 방유제/대형 설비 이격대 침범 방지
    y_trunk = b + band + tr_clear / 2.0
    y_arr = b + band + tr_clear
    x_arr = b

    south_eq_w = tr_l + (tr_clear + eh_l if include_ehouse else 0.0) + (tr_clear + tank_side if tank_side else 0.0)
    if include_infra:
        south_eq_w += (2.5 + pump_l) + (2.5 + st_l) + 2.4
    site_w_est = max(x_arr + arr_w + unit_gap, 2 * b + south_eq_w) + b
    site_w = site_w_est

    boxes, trench = [], []

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
        # 변의 길이가 50m를 넘으면 중간 소화전 추가
        if site_w > 50.0:
            hydrant_pts.append((site_w / 2.0 - 0.2, 0.6))
            hydrant_pts.append((site_w / 2.0 - 0.2, site_h - 1.0))
        if site_h > 50.0:
            hydrant_pts.append((0.6, site_h / 2.0 - 0.2))
            hydrant_pts.append((site_w - 1.0, site_h / 2.0 - 0.2))

        for h_idx, (hx, hy) in enumerate(hydrant_pts, 1):
            boxes.append(dict(kind="hydrant", label=f"HYDRANT-{h_idx:02d}",
                              x=hx, y=hy, dx=0.40, dy=0.40, dz=0.85))
        num_hydrants = len(hydrant_pts)

    trench_len = sum(math.dist(p, q) for pl in trench for p, q in zip(pl, pl[1:]))

    dc_max = max(dc_runs_all) if dc_runs_all else 0.0
    dc_min = min(dc_runs_all) if dc_runs_all else 0.0
    dc_imbalance = dc_max - dc_min

    return dict(
        boxes=boxes, trench=trench, trench_w=trench_w,
        fence=[(0.0, 0.0), (site_w, 0.0), (site_w, site_h), (0.0, site_h), (0.0, 0.0)],
        site=(site_w, site_h),
        metrics=dict(
            site_area_m2=site_w * site_h, site_w_m=site_w, site_h_m=site_h,
            trench_len_m=trench_len, longest_cable_m=max(runs), n_enc=n_enc, n_pcs=n_pcs,
            blocks_cols=cols, blocks_rows=rows, enc_per_block=per, tank_m3=water_m3,
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


# ── DXF R12 (ASCII) — 외부 의존성 없이 평면도 출력 ──────────────────────────────────
_LAYER = {"enc": "BESS-ENC", "pcs": "BESS-PCS", "tr": "BESS-TR", "tank": "FIRE-WATER"}


def to_dxf(layout) -> str:
    """평면도 DXF(R12). 레이어: 장비 종류별 + TRENCH + FENCE + LABEL. 단위 m."""
    out = ["0", "SECTION", "2", "HEADER", "9", "$ACADVER", "1", "AC1009",
           "9", "$INSUNITS", "70", "6", "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES"]

    def line(layer, p, q):
        out.extend(["0", "LINE", "8", layer, "10", f"{p[0]:.3f}", "20", f"{p[1]:.3f}", "30", "0.0",
                    "11", f"{q[0]:.3f}", "21", f"{q[1]:.3f}", "31", "0.0"])

    def text(layer, p, h, s):
        out.extend(["0", "TEXT", "8", layer, "10", f"{p[0]:.3f}", "20", f"{p[1]:.3f}", "30", "0.0",
                    "40", f"{h:.3f}", "1", s])

    for b in layout["boxes"]:
        lay = _LAYER.get(b["kind"], "0")
        x0, y0, x1, y1 = b["x"], b["y"], b["x"] + b["dx"], b["y"] + b["dy"]
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
        for p, q in zip(pts, pts[1:]):
            line(lay, p, q)
        text("LABEL", (x0 + 0.2, y0 + 0.2), min(0.6, b["dy"] / 3), b["label"])
    for pl in layout["trench"]:
        for p, q in zip(pl, pl[1:]):
            line("TRENCH", p, q)
    f = layout["fence"]
    for p, q in zip(f, f[1:]):
        line("FENCE", p, q)
    out.extend(["0", "ENDSEC", "0", "EOF"])
    return "\n".join(out) + "\n"


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

