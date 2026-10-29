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
TANK_H = 3.0


def _counts(n_enc, n_pcs):
    base, rem = divmod(n_enc, n_pcs)
    return [base + (1 if i < rem else 0) for i in range(n_pcs)]


def build_layout(n_enc, n_pcs, enc_l=6.05, enc_w=2.44, unit_gap=3.0, boundary=3.0,
                 aisle=6.0, tr_clear=5.0, trench_w=0.6, water_m3=0.0) -> dict:
    n_enc = max(int(n_enc), 1)
    pcs_clipped = int(n_pcs) > n_enc            # PCS 가 인클로저보다 많으면 블록이 빈다 → 인클로저 수로 제한
    n_pcs = max(min(int(n_pcs), n_enc), 1)
    pcs_l, pcs_w, pcs_h = PCS_DIM
    tr_l, tr_w, tr_h = TR_DIM
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
    band = max(tr_w, tank_side)                      # 남측 띠 깊이 — 큰 수조가 이격대를 침범하지 않게
    y_trunk = b + band + tr_clear / 2.0
    y_arr = b + band + tr_clear
    x_arr = b

    boxes, trench = [], []
    tr_x, tr_y = b, b
    tr_cx = tr_x + tr_l / 2.0
    boxes.append(dict(kind="tr", label="MAIN-TR", x=tr_x, y=tr_y, dx=tr_l, dy=tr_w, dz=tr_h))
    if tank_side:
        boxes.append(dict(kind="tank", label="FIRE-WATER", x=tr_x + tr_l + tr_clear, y=b,
                          dx=tank_side, dy=tank_side, dz=TANK_H))

    runs, branch_top = [], {}
    k_enc = 0
    for i, cnt in enumerate(counts):
        r, c = divmod(i, cols)
        bx = x_arr + c * (block_len + unit_gap)
        by = y_arr + r * (block_dep + row_gap)
        for j in range(cnt):
            k_enc += 1
            boxes.append(dict(kind="enc", label=f"ENC-{k_enc:03d}", x=bx + j * (enc_l + unit_gap), y=by,
                              dx=enc_l, dy=enc_w, dz=ENC_H, block=i + 1))
        px = bx + block_len - pcs_l
        boxes.append(dict(kind="pcs", label=f"PCS-{i + 1:02d}", x=px, y=by, dx=pcs_l, dy=pcs_w, dz=pcs_h,
                          block=i + 1, n_enc=cnt))
        x_br = bx + block_len + unit_gap / 2.0       # 블록 오른쪽 이격대에 간선
        y_pcs = by + pcs_w / 2.0
        trench.append([(px + pcs_l, y_pcs), (x_br, y_pcs)])      # PCS → 간선
        branch_top[c] = max(branch_top.get(c, 0.0), y_pcs)
        run = (x_br - (px + pcs_l)) + (y_pcs - y_trunk) + abs(x_br - tr_cx) + (y_trunk - (tr_y + tr_w))
        runs.append(run)
    branch_x = {c: x_arr + c * (block_len + unit_gap) + block_len + unit_gap / 2.0 for c in branch_top}
    for c, ytop in branch_top.items():
        trench.append([(branch_x[c], y_trunk), (branch_x[c], ytop)])
    x_far = max(branch_x.values())
    trench.append([(tr_cx, tr_y + tr_w), (tr_cx, y_trunk), (x_far, y_trunk)])  # 주변압기 인입 + trunk

    site_w = max(x_arr + arr_w + unit_gap, tr_x + tr_l + (tr_clear + tank_side if tank_side else 0)) + b
    site_h = y_arr + arr_h + b
    trench_len = sum(math.dist(p, q) for pl in trench for p, q in zip(pl, pl[1:]))

    return dict(
        boxes=boxes, trench=trench, trench_w=trench_w,
        fence=[(0.0, 0.0), (site_w, 0.0), (site_w, site_h), (0.0, site_h), (0.0, 0.0)],
        site=(site_w, site_h),
        metrics=dict(
            site_area_m2=site_w * site_h, site_w_m=site_w, site_h_m=site_h,
            trench_len_m=trench_len, longest_cable_m=max(runs), n_enc=n_enc, n_pcs=n_pcs,
            blocks_cols=cols, blocks_rows=rows, enc_per_block=per, tank_m3=water_m3,
            pcs_clipped=pcs_clipped,
        ),
        params=dict(unit_gap=unit_gap, boundary=boundary, aisle=aisle, tr_clear=tr_clear,
                    enc_l=enc_l, enc_w=enc_w),
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
    """겹침 수, 유닛(인클로저·PCS) 간 최소 이격, 변압기~유닛 최소 이격, 부지경계 최소 이격."""
    boxes = layout["boxes"]
    p = layout["params"]
    d = _edge_gaps(boxes)
    a = np.array([[b["x"], b["y"], b["x"] + b["dx"], b["y"] + b["dy"]] for b in boxes])
    ox = np.minimum(a[:, None, 2], a[None, :, 2]) - np.maximum(a[:, None, 0], a[None, :, 0])
    oy = np.minimum(a[:, None, 3], a[None, :, 3]) - np.maximum(a[:, None, 1], a[None, :, 1])
    ov = (ox > 1e-9) & (oy > 1e-9)
    np.fill_diagonal(ov, False)
    kinds = np.array([b["kind"] for b in boxes])
    unit = np.isin(kinds, ("enc", "pcs"))
    tr = kinds == "tr"
    w, h = layout["site"]
    to_fence = min(min(b["x"], b["y"], w - b["x"] - b["dx"], h - b["y"] - b["dy"]) for b in boxes)
    min_unit = float(d[np.ix_(unit, unit)].min()) if unit.sum() > 1 else float("inf")
    min_tr = float(d[np.ix_(tr, unit)].min()) if tr.any() else float("inf")
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
        xs += [x0, x1, x1, x0, x0, x1, x1, x0]
        ys += [y0, y0, y1, y1, y0, y0, y1, y1]
        zs += [0, 0, 0, 0, z1, z1, z1, z1]
        o = 8 * n
        ii += [o + v for v in _I]
        jj += [o + v for v in _J]
        kk += [o + v for v in _K]
    return xs, ys, zs, ii, jj, kk


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
