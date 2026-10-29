import streamlit as st
try:
    st.set_page_config(page_title="BESS EPC Platform", layout="wide", initial_sidebar_state="auto")
except Exception:
    pass

import plotly.graph_objects as go
from utils.css_loader import apply_custom_css
from utils.auth_helper import require_auth, sidebar_user_info
from utils import engineering_params as EP
from utils import design_model as DM
from utils import site_layout as SL

_KIND = {  # 종류 → (한글, 영문, 색)
    "enc":  ("배터리 인클로저", "Battery enclosure", "#3fb950"),
    "pcs":  ("PCS/MV 스키드", "PCS/MV skid", "#58a6ff"),
    "tr":   ("주변압기 (POI)", "Main transformer (POI)", "#e3b341"),
    "tank": ("소방 수조", "Fire water tank", "#79c0ff"),
}
_SRC = {"p01": "01 프로젝트 설정", "p02": "02 시스템 설계", "p04": "04 전기 BOP", "p05": "05 토목 BOP"}
_SRC_EN = {"p01": "01 Project Setup", "p02": "02 System Eng", "p04": "04 EBOP", "p05": "05 CBOP"}


def run_site_layout_module():
    apply_custom_css()
    require_auth("13")
    sidebar_user_info()
    ko = st.session_state.get("lang", "KO") == "KO"
    L = (lambda k, e: k if ko else e)

    st.caption(L("🛤️ **BESS EPC 워크플로우:** 02 시스템 · 04 전기 · 05 토목 → **[13: 3D 부지 배치]**",
                 "🛤️ **BESS EPC Workflow:** 02 System · 04 EBOP · 05 CBOP → **[13: Site Layout 3D]**"))
    st.title(L("📐 3D 부지 배치", "📐 Site Layout 3D"))
    st.info(L("02·04·05 설계 페이지의 계산값을 그대로 받아 부지 배치를 자동 생성합니다. "
              "설계 페이지에서 값을 바꾸면 이 화면이 따라 바뀝니다.",
              "Builds the site layout directly from the results of design pages 02·04·05. "
              "Change a value there and this view follows."))
    st.caption(L("스크리닝 배치입니다 — 실시공 배치도는 지형·인허가·AHJ 협의로 확정합니다. "
                 "장비 외형(PCS 6.05×2.44 m, 주변압기 8×6 m, 인클로저 높이 2.9 m)은 [가정] 값입니다.",
                 "Screening layout — the construction layout is fixed by terrain, permits and AHJ review. "
                 "Equipment envelopes (PCS 6.05×2.44 m, main TR 8×6 m, enclosure height 2.9 m) are [assumed]."))

    # ── 입력 출처 표 ────────────────────────────────────────────────────────
    inp = DM.layout_inputs()
    stat = {s: DM.status(s) for s in ("system", "ebop", "cbop")}
    sec_of = {"p02": "system", "p04": "ebop", "p05": "cbop"}
    names = {
        "n_enc": L("인클로저 수", "Enclosures"), "n_pcs": L("PCS 스키드 수", "PCS skids"),
        "enc_l": L("인클로저 길이 (m)", "Enclosure length (m)"), "enc_w": L("인클로저 폭 (m)", "Enclosure width (m)"),
        "trench_w": L("트렌치 폭 (m)", "Trench width (m)"), "water_m3": L("소방 수원 (m³)", "Fire water (m³)"),
        "main_tr_mva": L("주변압기 (MVA)", "Main TR (MVA)"), "cable_area_mm2": L("케이블 단면적 (mm²)", "Cable size (mm²)"),
        "target_market": L("목표 시장", "Target market"),
    }
    rows = []
    for k, label in names.items():
        v, src = inp[k]
        if src == "[가정]":
            badge = L("⚪ 미실행", "⚪ not run")
        elif ((sec_of.get(src) and stat[sec_of[src]] == "stale")
              or (k == "n_enc" and (DM.get("cbop") or {}).get("n_enc_basis") == "p05-stale")):
            badge = L("⚠️ 재계산", "⚠️ recompute")
        else:
            badge = "✅"
        shown = "—" if v is None else (f"{v:,.2f}" if isinstance(v, float) else str(v))
        rows.append({L("항목", "Item"): label, L("값", "Value"): shown,
                     L("출처", "Source"): (_SRC if ko else _SRC_EN).get(src, src), L("상태", "Status"): badge})
    with st.expander(L("🔗 설계값 출처 (설계 모델)", "🔗 Design value sources (design model)"),
                     expanded=any(r[L("상태", "Status")] != "✅" for r in rows)):
        st.dataframe(rows, use_container_width=True, hide_index=True)
        st.caption(L("⚪ 미실행 = 해당 설계 페이지를 아직 열지 않아 기본값[가정] 사용 · "
                     "⚠️ 재계산 = 01 입력이 바뀐 뒤 해당 페이지를 다시 열지 않음",
                     "⚪ not run = page not opened yet, default [assumed] used · "
                     "⚠️ recompute = 01 inputs changed since that page last ran"))

    # ── 배치 기준 ──────────────────────────────────────────────────────────
    mk = EP.market_key(inp["target_market"][0])
    sep = EP.SEPARATION_BY_MARKET[mk]
    with st.expander(L("⚙️ 배치 기준 (시장: ", "⚙️ Layout criteria (market: ") + f"{mk})", expanded=False):
        st.caption(f"{sep['src']} {sep['tag']} — " + L("값 소유: bess-fire-engineer", "owner: bess-fire-engineer"))
        c1, c2 = st.columns(2)
        unit_gap = c1.number_input(L("유닛 간 이격 (m)", "Unit separation (m)"), 0.3, 20.0,
                                   float(sep["unit_m"]), 0.1, key=f"sl_gap_{mk}")
        boundary = c2.number_input(L("부지경계 이격 (m)", "Property-line clearance (m)"), 0.0, 50.0,
                                   float(sep["boundary_m"]), 0.5, key=f"sl_bnd_{mk}")
        aisle = c1.number_input(L("블록 행 사이 통로 (m) [가정]", "Aisle between block rows (m) [assumed]"),
                                0.0, 20.0, EP.ACCESS_AISLE_M, 0.5)
        tr_clear = c2.number_input(L("주변압기 이격 (m) [가정]", "Main TR clearance (m) [assumed]"),
                                   0.0, 30.0, EP.TRANSFORMER_CLEARANCE_M, 0.5,
                                   help=L("IEC 61936-1·FM Global DS 5-4 에서 절연유량·내화등급별로 정함 — 조항 확인 전 스크리닝 값",
                                          "Set by IEC 61936-1 / FM Global DS 5-4 per oil volume & fire rating — screening value"))

    lay = SL.build_layout(inp["n_enc"][0], inp["n_pcs"][0], inp["enc_l"][0], inp["enc_w"][0],
                          unit_gap=unit_gap, boundary=boundary, aisle=aisle, tr_clear=tr_clear,
                          trench_w=inp["trench_w"][0], water_m3=inp["water_m3"][0])
    m, chk = lay["metrics"], SL.check_layout(lay)

    # ── 지표 ───────────────────────────────────────────────────────────────
    a, b, c, d = st.columns(4)
    a.metric(L("부지 면적", "Site area"), f"{m['site_area_m2']:,.0f} m²",
             help=f"{m['site_w_m']:.1f} × {m['site_h_m']:.1f} m")
    b.metric(L("인클로저 / PCS", "Enclosures / PCS"), f"{m['n_enc']} / {m['n_pcs']}",
             help=L(f"블록 {m['blocks_cols']}열 × {m['blocks_rows']}행, 블록당 최대 {m['enc_per_block']}기",
                    f"{m['blocks_cols']} × {m['blocks_rows']} blocks, ≤{m['enc_per_block']} per block"))
    c.metric(L("트렌치 총연장", "Total trench"), f"{m['trench_len_m']:,.0f} m")
    d.metric(L("최장 케이블 경로", "Longest cable route"), f"{m['longest_cable_m']:,.1f} m",
             help=L("PCS → 주변압기 직각 경로 길이 (여장·단말 미포함)",
                    "PCS → main TR orthogonal route (no slack/termination allowance)"))

    # ── 3D ────────────────────────────────────────────────────────────────
    view = st.radio(L("시점", "View"), [L("등각", "Isometric"), L("위에서", "Top")], horizontal=True,
                    key="sl_view", label_visibility="collapsed")
    fig = go.Figure()
    for kind, (kn, en, col) in _KIND.items():
        bx = [x for x in lay["boxes"] if x["kind"] == kind]
        if not bx:
            continue
        xs, ys, zs, ii, jj, kk = SL.mesh_arrays(bx)
        hover = []
        for x in bx:
            t_ = x["label"]
            if kind == "pcs":
                t_ += L(f"<br>블록 {x['block']} · 인클로저 {x['n_enc']}기", f"<br>block {x['block']} · {x['n_enc']} enclosures")
            if kind == "tr" and inp["main_tr_mva"][0]:
                t_ += f"<br>{inp['main_tr_mva'][0]} MVA"
            if kind == "tank":
                t_ += f"<br>{m['tank_m3']:.1f} m³"
            hover += [t_] * 8
        fig.add_trace(go.Mesh3d(x=xs, y=ys, z=zs, i=ii, j=jj, k=kk, color=col, opacity=0.9,
                                name=L(kn, en), hovertext=hover, hoverinfo="text", flatshading=True,
                                showlegend=True))
    tx, ty = [], []
    for pl in lay["trench"]:
        tx += [p[0] for p in pl] + [None]
        ty += [p[1] for p in pl] + [None]
    cable = inp["cable_area_mm2"][0]
    fig.add_trace(go.Scatter3d(x=tx, y=ty, z=[0.05 if v is not None else None for v in tx], mode="lines",
                               line=dict(color="#f0883e", width=5),
                               name=L("케이블 트렌치", "Cable trench"),
                               hovertext=L(f"트렌치 폭 {inp['trench_w'][0]:.2f} m", f"trench {inp['trench_w'][0]:.2f} m wide")
                               + (f" · {cable} mm²" if cable else ""), hoverinfo="text"))
    fx = [p[0] for p in lay["fence"]]
    fy = [p[1] for p in lay["fence"]]
    fig.add_trace(go.Scatter3d(x=fx + [None] + fx, y=fy + [None] + fy,
                               z=[0] * len(fx) + [None] + [EP.FENCE_HEIGHT_M] * len(fx), mode="lines",
                               line=dict(color="#8b949e", width=3), name=L("울타리·부지경계", "Fence / boundary"),
                               hoverinfo="skip"))
    w, h = lay["site"]
    zmax = max(w, h) * 0.25
    eye = dict(x=0.0, y=-0.01, z=2.2) if view in ("위에서", "Top") else dict(x=-0.95, y=-1.1, z=0.75)
    fig.update_layout(
        scene=dict(xaxis=dict(title="x (m)", range=[0, w]), yaxis=dict(title="y (m)", range=[0, h]),
                   zaxis=dict(title="z (m)", range=[0, zmax]),
                   aspectmode="manual", aspectratio=dict(x=w / max(w, h), y=h / max(w, h), z=zmax / max(w, h)),
                   camera=dict(eye=eye)),
        paper_bgcolor="rgba(0,0,0,0)", font_color="#c9d1d9", height=480,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", y=-0.02, x=0, font=dict(size=11)),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── 배치 검사 ───────────────────────────────────────────────────────────
    ok = chk["overlaps"] == 0 and chk["unit_ok"] and chk["tr_ok"] and chk["boundary_ok"]
    msg = L(f"겹침 {chk['overlaps']}건 · 유닛 간 최소 {chk['min_unit_gap_m']:.2f} m (기준 {unit_gap:.2f}) · "
            f"주변압기~유닛 최소 {chk['min_tr_gap_m']:.2f} m (기준 {tr_clear:.2f}) · "
            f"부지경계 최소 {chk['min_boundary_m']:.2f} m (기준 {boundary:.2f})",
            f"Overlaps {chk['overlaps']} · min unit gap {chk['min_unit_gap_m']:.2f} m (req. {unit_gap:.2f}) · "
            f"TR-to-unit {chk['min_tr_gap_m']:.2f} m (req. {tr_clear:.2f}) · "
            f"boundary {chk['min_boundary_m']:.2f} m (req. {boundary:.2f})")
    (st.success if ok else st.error)(("✅ " if ok else "❌ ") + msg)
    if not chk["trench_fits"]:
        st.warning(L(f"⚠️ 트렌치 폭 {inp['trench_w'][0]:.2f} m 가 유닛 이격 {unit_gap:.2f} m 보다 넓어 블록 사이 간선이 "
                     "장비 기초와 겹칩니다 — 이격을 넓히거나 05 트렌치(케이블 수·배열)를 재검토하세요.",
                     f"⚠️ Trench width {inp['trench_w'][0]:.2f} m exceeds unit separation {unit_gap:.2f} m — "
                     "branch trenches clash with equipment pads; widen separation or revisit 05 trench design."))
    if m["pcs_clipped"]:
        st.warning(L("⚠️ PCS 스키드 수가 인클로저 수보다 많아 인클로저 수만큼만 배치했습니다 — 02 단위 용량을 확인하세요.",
                     "⚠️ More PCS skids than enclosures — placed one per enclosure; check 02 unit ratings."))

    # ── 04 로 되돌려 보내기 ─────────────────────────────────────────────────
    if st.button(L(f"📏 최장 경로 {m['longest_cable_m']:.1f} m 를 04 케이블 사이징 길이로 적용",
                   f"📏 Apply longest route {m['longest_cable_m']:.1f} m to 04 cable sizing"),
                 use_container_width=True):
        st.session_state["dm_cable_length_m"] = round(m["longest_cable_m"], 1)
        st.success(L("적용했습니다 — 04 전기 BOP › 케이블 탭에서 전압강하 재검증하세요.",
                     "Applied — re-check voltage drop in 04 EBOP › Cable tab."))

    # ── 내보내기·불러오기 ───────────────────────────────────────────────────
    st.markdown("---")
    st.subheader(L("💾 내보내기 / 불러오기", "💾 Export / Import"))
    e1, e2 = st.columns(2)
    e1.download_button(L("설계 모델 JSON", "Design model JSON"),
                       data=DM.export_json(layout_metrics={k: (round(v, 3) if isinstance(v, float) else v)
                                                           for k, v in m.items()}),
                       file_name="bess_design_model.json", mime="application/json", use_container_width=True)
    e2.download_button(L("평면도 DXF (CAD)", "Plan DXF (CAD)"), data=SL.to_dxf(lay),
                       file_name="bess_site_layout.dxf", mime="application/dxf", use_container_width=True)
    if ko:  # 업로더 안내문·버튼은 Streamlit 고정 영문 — 한국어 모드에서만 CSS 로 문구 교체
        st.markdown("""<style>
        [data-testid=stFileUploaderDropzoneInstructions] > div > span,
        [data-testid=stFileUploaderDropzoneInstructions] > div > small,
        [data-testid=stFileUploaderDropzone] button {font-size:0 !important;}
        [data-testid=stFileUploaderDropzoneInstructions] > div > span::after {content:"JSON 파일을 끌어다 놓으세요"; font-size:1rem;}
        [data-testid=stFileUploaderDropzoneInstructions] > div > small::after {content:"파일당 200MB · JSON"; font-size:0.8rem;}
        [data-testid=stFileUploaderDropzone] button::after {content:"파일 선택"; font-size:0.9rem;}
        </style>""", unsafe_allow_html=True)
    up = st.file_uploader(L("설계 모델 JSON 불러오기", "Import design model JSON"), type=["json"],
                          key="sl_import")
    if up is not None and st.session_state.get("_sl_imported") != up.file_id:
        try:
            n = DM.import_json(up.getvalue().decode("utf-8"))
            st.session_state["_sl_imported"] = up.file_id
            st.success(L(f"{n}개 항목을 복원했습니다.", f"Restored {n} items."))
            st.rerun()
        except (ValueError, UnicodeDecodeError, TypeError) as ex:
            st.error(L(f"불러오기 실패: {ex}", f"Import failed: {ex}"))


run_site_layout_module()
