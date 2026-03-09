import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.lang_helper import t
from utils.auth_helper import require_auth
from utils.css_loader import apply_custom_css
import utils.market_data as md

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
    curr_yr = 2024
    prev_yr = 2023

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

def render_regional():
    st.subheader(t("mk_reg_title"))
    region_names = list(md.REGIONAL_DATA.keys())
    sel_region = st.selectbox(t("mk_reg_select"), options=region_names)

    r_data = md.REGIONAL_DATA[sel_region]

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
    df_pipe = pd.DataFrame(md.PROJECT_PIPELINE)

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
    st.subheader(t("mk_scen_title"))

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

    st.markdown("**Excel (.xlsx)**")
    if st.button(t("mk_rep_gen"), use_container_width=True, key="btn_prep_excel"):
        with st.spinner("Generating..."):
            import os
            import datetime
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

                pd.DataFrame(md.PROJECT_PIPELINE).to_excel(writer, sheet_name="Pipeline", index=False)
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

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    t("mk_tab_overview"), t("mk_tab_fx"), t("mk_tab_news"), t("mk_tab_regional"),
    t("mk_tab_pipeline"), t("mk_tab_competitor"), t("mk_tab_scenario"), t("mk_tab_report")
])

with tab1: render_overview()
with tab2: render_fx_commodities()
with tab3: render_news()
with tab4: render_regional()
with tab5: render_pipeline()
with tab6: render_competitors()
with tab7: render_scenarios()
with tab8: download_report()
