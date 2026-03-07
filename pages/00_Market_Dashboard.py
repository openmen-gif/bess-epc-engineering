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
    st.subheader(t("hp_market_trends_title") if t("hp_market_trends_title") != "hp_market_trends_title" else "📈 Global BESS Market Overview")
    
    # KPIs
    curr_yr = 2024
    prev_yr = 2023
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        val = md.GLOBAL_CAPACITY_GWH.get(curr_yr, 0)
        prev = md.GLOBAL_CAPACITY_GWH.get(prev_yr, 1)
        st.metric(label="Global Installed Capacity (GWh)", value=f"{val}", delta=f"{((val-prev)/prev)*100:.1f}% YoY")
    with c2:
        val = md.GLOBAL_MARKET_VALUE_B_USD.get(curr_yr, 0)
        prev = md.GLOBAL_MARKET_VALUE_B_USD.get(prev_yr, 1)
        st.metric(label="Market Value (Billion USD)", value=f"${val}", delta=f"{((val-prev)/prev)*100:.1f}% YoY")
    with c3:
        val = md.LFP_CELL_PRICE.get(curr_yr, 0)
        prev = md.LFP_CELL_PRICE.get(prev_yr, 1)
        st.metric(label="LFP Cell Price ($/kWh)", value=f"${val}", delta=f"{((val-prev)/prev)*100:.1f}% YoY", delta_color="inverse")
    with c4:
        val = md.SYSTEM_CAPEX.get(curr_yr, 0)
        prev = md.SYSTEM_CAPEX.get(prev_yr, 1)
        st.metric(label="System CAPEX ($/kWh)", value=f"${val}", delta=f"{((val-prev)/prev)*100:.1f}% YoY", delta_color="inverse")

    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        # Market Growth Chart
        df_cap = pd.DataFrame({
            "Year": md.YEARS,
            "Capacity (GWh)": [md.GLOBAL_CAPACITY_GWH[y] for y in md.YEARS]
        })
        fig1 = px.bar(df_cap, x="Year", y="Capacity (GWh)", title="Global BESS Market Growth", text="Capacity (GWh)")
        st.plotly_chart(fig1, use_container_width=True)
        
    with col2:
        # Price Trends Chart
        df_price = pd.DataFrame({
            "Year": md.YEARS,
            "LFP Cell ($/kWh)": [md.LFP_CELL_PRICE[y] for y in md.YEARS],
            "NMC Cell ($/kWh)": [md.NMC_CELL_PRICE[y] for y in md.YEARS],
            "System CAPEX ($/kWh)": [md.SYSTEM_CAPEX[y] for y in md.YEARS]
        })
        fig2 = px.line(df_price, x="Year", y=["LFP Cell ($/kWh)", "NMC Cell ($/kWh)", "System CAPEX ($/kWh)"], 
                       title="Battery Price & System CAPEX Trends", markers=True)
        st.plotly_chart(fig2, use_container_width=True)

def render_news():
    st.subheader("📰 Real-time Market News")
    
    col_cat, col_btn = st.columns([4, 1])
    with col_cat:
        selected_category = st.selectbox(
            "Select News Category",
            options=list(md.RSS_FEEDS.keys()),
            index=0
        )
    with col_btn:
        st.write("") # spacing
        if st.button("🔄 Refresh Data", use_container_width=True):
            md.clear_rss_cache()
            
    feed_data = md.fetch_rss_feed(selected_category)
    items = feed_data.get("items", [])
    last_sync = feed_data.get("timestamp")
    
    if last_sync:
        st.caption(f"Last Sync: {last_sync.strftime('%Y-%m-%d %H:%M:%S')}")
        
    if not items:
        st.info("No news available for this category.")
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
    st.subheader("🌍 Regional Analysis")
    region_names = list(md.REGIONAL_DATA.keys())
    sel_region = st.selectbox("Select Region", options=region_names)
    
    r_data = md.REGIONAL_DATA[sel_region]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Market Share", f"{r_data['market_share_pct']}%")
    c2.metric("Pipeline Capacity", f"{r_data['pipeline_gwh']} GWh")
    c3.metric("Avg. Project Size", f"{r_data['avg_project_size_mwh']} MWh")
    
    st.markdown("---")
    c_left, c_right = st.columns(2)
    with c_left:
        st.markdown("##### Key Drivers")
        for driver in r_data['key_drivers']:
            st.markdown(f"- {driver}")
        st.markdown(f"**Revenue Model:** {r_data['revenue_model']}")
        
    with c_right:
        st.markdown("##### Key Policies")
        for p in r_data['policy']:
            st.markdown(f"- {p}")
        st.markdown(f"**Key Players:** {', '.join(r_data['key_players'])}")
        
    # Regional Growth Chart
    years = sorted(list(r_data['installed_gwh'].keys()))
    df_reg = pd.DataFrame({
        "Year": years,
        "Installed (GWh)": [r_data['installed_gwh'][y] for y in years]
    })
    fig = px.bar(df_reg, x="Year", y="Installed (GWh)", title=f"{sel_region} Installed Capacity Trend")
    st.plotly_chart(fig, use_container_width=True)

def render_pipeline():
    st.subheader("🏗️ Major Project Pipeline")
    df_pipe = pd.DataFrame(md.PROJECT_PIPELINE)
    
    # Filters
    c1, c2 = st.columns(2)
    regions = ["All"] + list(df_pipe['region'].unique())
    statuses = ["All"] + list(df_pipe['status'].unique())
    
    sel_r = c1.selectbox("Filter by Region", regions)
    sel_s = c2.selectbox("Filter by Status", statuses)
    
    if sel_r != "All":
        df_pipe = df_pipe[df_pipe['region'] == sel_r]
    if sel_s != "All":
        df_pipe = df_pipe[df_pipe['status'] == sel_s]
        
    st.dataframe(df_pipe, use_container_width=True, hide_index=True)

def render_competitors():
    st.subheader("🏢 Competitor Analysis")
    df_comp = pd.DataFrame(md.COMPETITORS)
    st.dataframe(df_comp, use_container_width=True, hide_index=True)
    
    fig = px.scatter(df_comp, x="market_share_pct", y="capacity_gwh", text="name", 
                     size="revenue_b_usd", color="country", title="Competitor Landscape")
    fig.update_traces(textposition='top center')
    st.plotly_chart(fig, use_container_width=True)

def render_scenarios():
    st.subheader("🔮 Scenario Forecast (2024-2030)")
    
    sel_scenario = st.radio("Select Scenario", options=list(md.SCENARIOS.keys()), horizontal=True)
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
    
    fig = px.bar(df_scen, x="Year", y="Capacity (GWh)", title=f"{sel_scenario} Capacity Projection")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df_scen, use_container_width=True, hide_index=True)

def download_report():
    st.subheader("📥 Download Market Report")
    
    st.markdown("**Excel (.xlsx)**")
    if st.button("📄 Generate Excel Report", use_container_width=True, key="btn_prep_excel"):
        with st.spinner("Generating Excel report..."):
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
            st.success("✅ 생성 완료")

    if "dl_excel_path" in st.session_state and st.session_state["dl_excel_path"]:
        p = st.session_state["dl_excel_path"]
        with open(p, "rb") as f:
            st.download_button(
                label="⬇️ Download Full Excel Report",
                data=f.read(),
                file_name=p.split("\\")[-1] if "\\" in p else p.split("/")[-1],
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="dl_excel_btn"
            )

st.title("📈 BESS Market Dashboard")
st.markdown("Global ESS market data, price trends, project pipelines, market size forecasts, competitive landscape, and real-time news feeds.")

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Overview", "📰 News Feed", "🌍 Regional Analysis", 
    "🏗️ Project Pipeline", "🏢 Competitors", "🔮 Scenarios", "📥 Reports"
])

with tab1: render_overview()
with tab2: render_news()
with tab3: render_regional()
with tab4: render_pipeline()
with tab5: render_competitors()
with tab6: render_scenarios()
with tab7: download_report()
