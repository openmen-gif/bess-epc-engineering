import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.lang_helper import t
from utils.auth_helper import require_auth
from utils.css_loader import apply_custom_css
from utils import theme  # bess_dark 템플릿 등록 — px 차트 다크·브랜드 colorway 자동 적용
import utils.market_data as md
from utils.data_fetchers import get_live_us_capacity_or_fallback

apply_custom_css()
require_auth()

def _format_number(n, decimals=1):
    if n >= 1_000_000:
        return f"{n/1_000_000:,.{decimals}f}M"
    elif n >= 1_000:
        return f"{n/1_000:,.{decimals}f}K"
    return f"{n:,.{decimals}f}"

def render_overview():
    st.subheader(t("mk_ov_title"))

    # KPIs
    curr_yr = md.LATEST_ACTUAL_YEAR
    prev_yr = curr_yr - 1
    st.caption(f"📅 {t('mk_ov_basis')}: {curr_yr}년 실적 (vs {prev_yr})")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        val = md.GLOBAL_CAPACITY_GWH.get(curr_yr, 0)
        prev = md.GLOBAL_CAPACITY_GWH.get(prev_yr, 1)
        st.metric(label=t("mk_ov_cap"), value=f"{val}", delta=f"{((val-prev)/prev)*100:.1f}% YoY")
    with c2:
        val = md.GLOBAL_MARKET_VALUE_B_USD.get(curr_yr, 0)
        prev = md.GLOBAL_MARKET_VALUE_B_USD.get(prev_yr, 1)
        st.metric(label=t("mk_ov_val"), value=f"${val}", delta=f"{((val-prev)/prev)*100:.1f}% YoY")
    with c3:
        val = md.LFP_CELL_PRICE.get(curr_yr, 0)
        prev = md.LFP_CELL_PRICE.get(prev_yr, 1)
        st.metric(label=t("mk_ov_lfp"), value=f"${val}", delta=f"{((val-prev)/prev)*100:.1f}% YoY", delta_color="inverse")
    with c4:
        val = md.SYSTEM_CAPEX.get(curr_yr, 0)
        prev = md.SYSTEM_CAPEX.get(prev_yr, 1)
        st.metric(label=t("mk_ov_capex"), value=f"${val}", delta=f"{((val-prev)/prev)*100:.1f}% YoY", delta_color="inverse")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        cap_lbl = t("mk_ov_cap_gwh")
        df_cap = pd.DataFrame({
            "Year": md.YEARS,
            cap_lbl: [md.GLOBAL_CAPACITY_GWH[y] for y in md.YEARS]
        })
        fig1 = px.bar(df_cap, x="Year", y=cap_lbl, title=t("mk_ov_growth"), text=cap_lbl)
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        lfp_lbl = t("mk_ov_lfp_kwh")
        nmc_lbl = t("mk_ov_nmc_kwh")
        capex_lbl = t("mk_ov_capex_kwh")
        df_price = pd.DataFrame({
            "Year": md.YEARS,
            lfp_lbl: [md.LFP_CELL_PRICE[y] for y in md.YEARS],
            nmc_lbl: [md.NMC_CELL_PRICE[y] for y in md.YEARS],
            capex_lbl: [md.SYSTEM_CAPEX[y] for y in md.YEARS]
        })
        fig2 = px.line(df_price, x="Year", y=[lfp_lbl, nmc_lbl, capex_lbl],
                       title=t("mk_ov_price_trend"), markers=True)
        st.plotly_chart(fig2, use_container_width=True)

def render_news():
    st.subheader(t("mk_news_title"))

    col_cat, col_btn = st.columns([4, 1])
    with col_cat:
        selected_category = st.selectbox(
            t("mk_news_cat"),
            options=list(md.RSS_FEEDS.keys()),
            index=0
        )
    with col_btn:
        st.write("")  # spacing
        if st.button(t("mk_news_refresh"), use_container_width=True):
            md.clear_rss_cache()

    feed_data = md.fetch_rss_feed(selected_category)
    items = feed_data.get("items", [])
    last_sync = feed_data.get("timestamp")

    if last_sync:
        st.caption(f"{t('mk_news_sync')}: {last_sync.strftime('%Y-%m-%d %H:%M:%S')}")

    if not items:
        st.info(t("mk_news_empty"))
    else:
        news_cols = st.columns(3)
        for i, item in enumerate(items):
            col_idx = i % 3
            with news_cols[col_idx]:
                with st.container(border=True):
                    st.markdown(f"**[{item['title']}]({item['link']})**")
                    st.caption(item['pubDate'])
                    st.markdown(f"<div style='font-size:0.85em; color:gray;'>{item['description']}</div>", unsafe_allow_html=True)

    # ── Recent Market Commentary (RSS 자동 추출) ─────────────────────
    st.markdown("---")
    st.markdown(f"### {t('mk_commentary_title')}")
    try:
        _commentary = md.extract_market_commentary(max_items=8)
    except Exception as _ce:
        _commentary = []
        st.warning(f"인용 추출 오류: {_ce}")
    if not _commentary:
        st.info(t("mk_commentary_empty"))
    else:
        for _c in _commentary:
            _figs = " · ".join(f"`{f}`" for f in _c["figures"])
            with st.container(border=True):
                st.markdown(f"{_figs}")
                st.markdown(f"**[{_c['title']}]({_c['url']})**")
                st.caption(f"{_c.get('source', '')} · {_c.get('pub_date', '')}")

def render_regional():
    st.subheader(t("mk_reg_title"))
    region_names = list(md.REGIONAL_DATA.keys())
    sel_region = st.selectbox(t("mk_reg_select"), options=region_names)

    r_data = md.REGIONAL_DATA[sel_region]

    # 미국 선택 시 EIA 라이브 데이터 시도 → 성공하면 배너 표시 + installed 값 오버레이
    _live_us = None
    if sel_region == "미국":
        _snapshot_gwh = r_data["installed_gwh"].get(md.LATEST_ACTUAL_YEAR, 0)
        _live_us = get_live_us_capacity_or_fallback(_snapshot_gwh)
        if _live_us["is_live"]:
            st.success(
                f"{t('mk_live_us_capacity')}: **{_live_us['value_gwh']:.1f} GWh** "
                f"(EIA {_live_us['as_of_str']} 기준 · 출처: {_live_us['source']})"
            )
        elif _live_us["error"]:
            st.info(f"{t('mk_live_fallback')} _{_live_us['error']}_")

    c1, c2, c3 = st.columns(3)
    c1.metric(t("mk_reg_share"), f"{r_data['market_share_pct']}%")
    c2.metric(t("mk_reg_pipeline"), f"{r_data['pipeline_gwh']} GWh")
    c3.metric(t("mk_reg_avg_size"), f"{r_data['avg_project_size_mwh']} MWh")

    st.markdown("---")
    c_left, c_right = st.columns(2)
    with c_left:
        st.markdown(t("mk_reg_drivers"))
        for driver in r_data['key_drivers']:
            st.markdown(f"- {driver}")
        st.markdown(f"{t('mk_reg_revenue')} {r_data['revenue_model']}")

    with c_right:
        st.markdown(t("mk_reg_policy"))
        for p in r_data['policy']:
            st.markdown(f"- {p}")
        st.markdown(f"{t('mk_reg_players')} {', '.join(r_data['key_players'])}")

    # Regional Growth Chart
    installed_lbl = t("mk_reg_installed")
    years = sorted(list(r_data['installed_gwh'].keys()))
    df_reg = pd.DataFrame({
        "Year": years,
        installed_lbl: [r_data['installed_gwh'][y] for y in years]
    })
    fig = px.bar(df_reg, x="Year", y=installed_lbl, title=f"{sel_region} — {t('mk_reg_chart')}")
    st.plotly_chart(fig, use_container_width=True)

def render_pipeline():
    st.subheader(t("mk_pipe_title"))
    df_pipe = pd.DataFrame(md.project_pipeline_with_status())

    # Filters
    c1, c2 = st.columns(2)
    all_lbl = t("mk_pipe_all")
    regions = [all_lbl] + list(df_pipe['region'].unique())
    statuses = [all_lbl] + list(df_pipe['status'].unique())

    sel_r = c1.selectbox(t("mk_pipe_region"), regions)
    sel_s = c2.selectbox(t("mk_pipe_status"), statuses)

    if sel_r != all_lbl:
        df_pipe = df_pipe[df_pipe['region'] == sel_r]
    if sel_s != all_lbl:
        df_pipe = df_pipe[df_pipe['status'] == sel_s]

    st.dataframe(df_pipe, use_container_width=True, hide_index=True)

def render_competitors():
    st.subheader(t("mk_comp_title"))
    df_comp = pd.DataFrame(md.COMPETITORS)
    st.dataframe(df_comp, use_container_width=True, hide_index=True)

    fig = px.scatter(df_comp, x="market_share_pct", y="capacity_gwh", text="name",
                     size="revenue_b_usd", color="country", title=t("mk_comp_chart"))
    fig.update_traces(textposition='top center')
    st.plotly_chart(fig, use_container_width=True)

def render_scenarios():
    _scen_keys = sorted(next(iter(md.SCENARIOS.values()))["capacity_gwh"].keys())
    _scen_range = f"({_scen_keys[0]}-{_scen_keys[-1]})" if _scen_keys else ""
    st.subheader(f"{t('mk_scen_title')} {_scen_range}".strip())

    sel_scenario = st.radio(t("mk_scen_select"), options=list(md.SCENARIOS.keys()), horizontal=True)
    s_data = md.SCENARIOS[sel_scenario]

    st.info(f"**{sel_scenario}:** {s_data['description']}")
    st.metric("CAGR (%)", f"{s_data['cagr_pct']}%")

    years = sorted(list(s_data['capacity_gwh'].keys()))
    df_scen = pd.DataFrame({
        "Year": years,
        "Capacity (GWh)": [s_data['capacity_gwh'][y] for y in years],
        "Market Value (B$)": [s_data['market_value_b'][y] for y in years],
        "Cell Price ($/kWh)": [s_data['cell_price'][y] for y in years]
    })

    fig = px.bar(df_scen, x="Year", y="Capacity (GWh)", title=f"{sel_scenario} — {t('mk_scen_proj')}")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df_scen, use_container_width=True, hide_index=True)

def render_fx_commodities():
    st.subheader(t("mk_fx_title"))
    st.caption(t("mk_fx_caption"))

    col_fx, col_cmd = st.columns(2)

    with col_fx:
        st.markdown(t("mk_fx_rates"))
        fx = md.fetch_exchange_rates()
        if "error" in fx:
            st.warning(f"{t('mk_fx_err')}: {fx['error']}")
        else:
            fx_pairs = [
                ("USD/KRW", fx.get("USD_KRW"), "🇰🇷"),
                ("USD/JPY", fx.get("USD_JPY"), "🇯🇵"),
                ("USD/EUR", fx.get("USD_EUR"), "🇪🇺"),
                ("USD/CNY", fx.get("USD_CNY"), "🇨🇳"),
                ("USD/GBP", fx.get("USD_GBP"), "🇬🇧"),
                ("USD/AUD", fx.get("USD_AUD"), "🇦🇺"),
            ]
            r1 = st.columns(3)
            r2 = st.columns(3)
            for i, (pair, val, flag) in enumerate(fx_pairs):
                col = r1[i] if i < 3 else r2[i - 3]
                if val is not None:
                    fmt = f"{val:,.2f}" if val > 10 else f"{val:.4f}"
                    col.metric(f"{flag} {pair}", fmt)
                else:
                    col.metric(f"{flag} {pair}", "N/A")
        if fx.get("timestamp"):
            st.caption(f"{t('mk_fx_updated')}: {fx['timestamp'].strftime('%Y-%m-%d %H:%M')}")

    with col_cmd:
        st.markdown(t("mk_cmd_title"))
        cmd = md.fetch_commodity_prices()
        c1, c2 = st.columns(2)
        c1.metric(t("mk_cmd_brent"), f"${cmd['brent_crude_usd']}/bbl" if cmd['brent_crude_usd'] else "N/A")
        c2.metric(t("mk_cmd_wti"), f"${cmd['wti_crude_usd']}/bbl" if cmd['wti_crude_usd'] else "N/A")

        c3, c4 = st.columns(2)
        c3.metric(t("mk_cmd_lithium"), f"${cmd['lithium_carbonate_usd_ton']:,}/ton" if cmd['lithium_carbonate_usd_ton'] else "N/A")
        c4.metric(t("mk_cmd_copper"), f"${cmd['copper_usd_ton']:,}/ton" if cmd['copper_usd_ton'] else "N/A")

        st.metric(t("mk_cmd_nickel"), f"${cmd['nickel_usd_ton']:,}/ton" if cmd['nickel_usd_ton'] else "N/A")

        if cmd.get("source"):
            st.caption(f"Source: {cmd['source']} | {cmd['timestamp'].strftime('%Y-%m-%d %H:%M')}")

    st.markdown("---")
    st.markdown(t("mk_impact_title"))
    st.info(t("mk_impact_body"))


def download_report():
    st.subheader(t("mk_rep_title"))

    # ── Section 1: Comprehensive Word Report ──────────────────────────
    st.markdown(f"### {t('mk_rep_section_word')}")
    with st.container(border=True):
        st.markdown(t("mk_crep_desc"))
        st.markdown(t("mk_crep_contents"))

        col_w, col_p = st.columns(2)
        with col_w:
            if st.button(t("mk_crep_gen_word"), use_container_width=True, key="btn_gen_word"):
                with st.spinner(t("mk_crep_generating")):
                    try:
                        from utils._report_local import generate_word_report
                        word_path = generate_word_report()
                        with open(word_path, "rb") as f:
                            st.session_state["dl_word_bytes"] = f.read()
                            st.session_state["dl_word_name"] = word_path.split("\\")[-1] if "\\" in word_path else word_path.split("/")[-1]
                        st.success(t("mk_rep_done"))
                    except Exception as e:
                        st.error(f"{t('mk_crep_err')}: {e}")

        with col_p:
            if st.button(t("mk_crep_gen_pdf"), use_container_width=True, key="btn_gen_pdf"):
                with st.spinner(t("mk_crep_generating")):
                    try:
                        from utils._report_local import generate_pdf_report
                        pdf_path = generate_pdf_report()
                        with open(pdf_path, "rb") as f:
                            st.session_state["dl_pdf_bytes"] = f.read()
                            st.session_state["dl_pdf_name"] = pdf_path.split("\\")[-1] if "\\" in pdf_path else pdf_path.split("/")[-1]
                        st.success(t("mk_rep_done"))
                    except Exception as e:
                        st.error(f"{t('mk_crep_err')}: {e}")

        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            if st.session_state.get("dl_word_bytes"):
                st.download_button(
                    label=t("mk_crep_dl_word"),
                    data=st.session_state["dl_word_bytes"],
                    file_name=st.session_state.get("dl_word_name", "BESS_Market_Report.docx"),
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    key="dl_word_btn"
                )
        with dl_col2:
            if st.session_state.get("dl_pdf_bytes"):
                st.download_button(
                    label=t("mk_crep_dl_pdf"),
                    data=st.session_state["dl_pdf_bytes"],
                    file_name=st.session_state.get("dl_pdf_name", "BESS_Market_Report.pdf"),
                    mime="application/pdf",
                    use_container_width=True,
                    key="dl_pdf_btn"
                )

    st.markdown("---")

    # ── Section 2: Excel Data Export ──────────────────────────────────
    st.markdown(f"### {t('mk_rep_section_excel')}")
    with st.container(border=True):
        if st.button(t("mk_rep_gen"), use_container_width=True, key="btn_prep_excel"):
            with st.spinner("Generating..."):
                import os
                import datetime
                if os.path.isdir("/data"):
                    out_dir = "/data/output_reports"
                else:
                    out_dir = os.path.join(os.path.dirname(__file__), "..", "output_reports")
                os.makedirs(out_dir, exist_ok=True)
                timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                file_path = os.path.join(out_dir, f"BESS_Market_Report_{timestamp}.xlsx")

                with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
                    pd.DataFrame({
                        "Year": md.YEARS,
                        "Capacity (GWh)": [md.GLOBAL_CAPACITY_GWH[y] for y in md.YEARS],
                        "Market Value (B$)": [md.GLOBAL_MARKET_VALUE_B_USD[y] for y in md.YEARS],
                        "LFP Price ($/kWh)": [md.LFP_CELL_PRICE[y] for y in md.YEARS],
                        "CAPEX ($/kWh)": [md.SYSTEM_CAPEX[y] for y in md.YEARS],
                    }).to_excel(writer, sheet_name="Overview", index=False)

                    pd.DataFrame(md.project_pipeline_with_status()).to_excel(writer, sheet_name="Pipeline", index=False)
                    pd.DataFrame(md.COMPETITORS).to_excel(writer, sheet_name="Competitors", index=False)

                st.session_state["dl_excel_path"] = file_path
                st.success(t("mk_rep_done"))

        if "dl_excel_path" in st.session_state and st.session_state["dl_excel_path"]:
            p = st.session_state["dl_excel_path"]
            with open(p, "rb") as f:
                st.download_button(
                    label=t("mk_rep_dl"),
                    data=f.read(),
                    file_name=p.split("\\")[-1] if "\\" in p else p.split("/")[-1],
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="dl_excel_btn"
                )

st.title(t("mk_title"))
st.markdown(t("mk_subtitle"))

# ── 데이터 신선도 배너 ─────────────────────────────────────────────
_fresh = md.get_data_freshness_summary()
_live_count = len(_fresh["live_sections"])
_static_count = len(_fresh["all_sections"]) - _live_count
_oldest = _fresh["oldest_section"]
_oldest_str = f"{_oldest[1]} ({_oldest[0]})" if _oldest else "—"

with st.container(border=True):
    c1, c2, c3 = st.columns([2, 2, 3])
    c1.markdown(f"**{t('mk_freshness_snapshot')}**: `{_fresh['snapshot_as_of']}`")
    c2.markdown(f"**{t('mk_freshness_live')}**: {_live_count}건 · **{t('mk_freshness_static')}**: {_static_count}건")
    c3.markdown(f"**{t('mk_freshness_oldest')}**: `{_oldest_str}`")
    st.caption(t("mk_freshness_disclaimer"))

    with st.expander(t("mk_freshness_expand"), expanded=False):
        _df_fresh = pd.DataFrame([
            {
                t("mk_freshness_section"): s["label"],
                t("mk_freshness_as_of"): s["as_of"],
                t("mk_freshness_source"): s["source"],
                t("mk_freshness_type"): s["type"],
                t("mk_freshness_note"): s.get("note", ""),
            }
            for s in _fresh["all_sections"]
        ])
        st.dataframe(_df_fresh, use_container_width=True, hide_index=True)

def render_infra_map():
    """🗺️ OpenInfraMap 안내 카드 + 지역 바로가기.

    OpenInfraMap이 X-Frame-Options/CSP frame-ancestors 헤더로 iframe 임베드를 차단하므로
    페이지 내 직접 렌더링은 불가. 대신 안내 카드 + 대형 새 탭 버튼 + 자주 보는 지역 바로가기 제공.

    Source: https://openinframap.org/ (Russ Garrett, MIT License)
    Data:   OpenStreetMap contributors (ODbL)
    """
    st.subheader(t("mk_infra_title"))
    st.caption(t("mk_infra_caption"))

    # Legend + tip cards
    col_l, col_r = st.columns([1, 1])
    with col_l:
        st.info(t("mk_infra_legend"))
    with col_r:
        st.success(t("mk_infra_tip"))

    # World-overview default URL (user-specified: zoom=2, lat=26, lon=12)
    INFRA_MAP_URL = "https://openinframap.org/#2/26/12"

    # Hero card — embed-blocked notice + large open-in-new-tab button
    st.markdown(
        f'<div style="text-align:center; padding:28px 16px; margin:14px 0; '
        f'background:linear-gradient(135deg,#1E3A5F 0%,#2E75B6 100%); '
        f'border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.15);">'
        f'<div style="color:#FFFFFF; font-size:14px; margin-bottom:16px; opacity:0.92; line-height:1.5;">'
        f'{t("mk_infra_blocked")}</div>'
        f'<a href="{INFRA_MAP_URL}" target="_blank" rel="noopener" '
        f'style="display:inline-block; padding:14px 36px; background:#FFFFFF; color:#1E3A5F; '
        f'border-radius:8px; text-decoration:none; font-weight:800; font-size:16px; '
        f'box-shadow:0 2px 8px rgba(0,0,0,0.20);">'
        f'{t("mk_infra_open")}</a>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Region quick-links (BESS 사업 관심 지역 8건)
    st.markdown(f"#### {t('mk_infra_regions')}")
    REGIONS = [
        ("🇰🇷 한국 / Korea",          "https://openinframap.org/#7/36.5/127.8"),
        ("🇯🇵 일본 / Japan",          "https://openinframap.org/#5/36.0/138.0"),
        ("🇨🇳 중국 / China",          "https://openinframap.org/#4/35.0/105.0"),
        ("🇮🇳 인도 / India",          "https://openinframap.org/#5/22.0/79.0"),
        ("🇦🇪 UAE",                   "https://openinframap.org/#7/24.0/54.0"),
        ("🇪🇺 EU 중부 / Central EU",  "https://openinframap.org/#5/50.0/10.0"),
        ("🇺🇸 미국 텍사스 / Texas",   "https://openinframap.org/#6/31.5/-99.0"),
        ("🇦🇺 호주 / Australia",      "https://openinframap.org/#4/-25.0/134.0"),
    ]
    cols = st.columns(4)
    for i, (label, url) in enumerate(REGIONS):
        with cols[i % 4]:
            st.markdown(
                f'<a href="{url}" target="_blank" rel="noopener" '
                f'style="display:block; padding:14px 10px; margin:6px 0; '
                f'background:rgba(46,117,182,0.10); border:1px solid rgba(46,117,182,0.35); '
                f'border-radius:8px; text-decoration:none; color:inherit; '
                f'text-align:center; font-weight:600; font-size:13px; line-height:1.4;">'
                f'{label}</a>',
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.caption(t("mk_infra_source"))


tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    t("mk_tab_overview"), t("mk_tab_fx"), t("mk_tab_news"), t("mk_tab_regional"),
    t("mk_tab_pipeline"), t("mk_tab_competitor"), t("mk_tab_scenario"),
    t("mk_tab_infra"), t("mk_tab_report")
])

with tab1: render_overview()
with tab2: render_fx_commodities()
with tab3: render_news()
with tab4: render_regional()
with tab5: render_pipeline()
with tab6: render_competitors()
with tab7: render_scenarios()
with tab8: render_infra_map()
with tab9: download_report()
