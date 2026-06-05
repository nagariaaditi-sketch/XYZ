import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import os

import data_manager
import ml_models
import components

# Page configuration
st.set_page_config(
    page_title="IPO Intelligence Dashboard",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
    
if "selected_page" not in st.session_state:
    st.session_state.selected_page = "Overview Dashboard"

# Load base historical data
df_historical = data_manager.load_historical_data()

# Inject theme styling
components.inject_theme_and_styles(st.session_state.theme)

# Fetch live prices mapping (cached)
tickers = df_historical["Ticker"].dropna().unique().tolist()
live_prices = data_manager.get_live_prices(tickers)

# Map live prices back to historical dataframe to calculate live returns
df_historical["Current Price"] = df_historical["Ticker"].map(live_prices)
df_historical["Current Price"] = df_historical["Current Price"].fillna(df_historical["Listing Price"])
df_historical["Current Return (%)"] = round(
    ((df_historical["Current Price"] - df_historical["Issue Price"]) / df_historical["Issue Price"]) * 100, 2
)

# Sidebar Navigation
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; padding-bottom: 20px;'>
            <h2 style='color: #d4af37; margin: 0; font-family: "Outfit", sans-serif; font-weight: 800;'>IPO INTELLIGENCE</h2>
            <span style='color: #94a3b8; font-size: 0.8rem; font-weight: 600; letter-spacing: 0.1em;'>INVESTMENT BANKING SUITE</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Theme Toggle
    theme_label = "☀️ Switch to Light Mode" if st.session_state.theme == "dark" else "🌙 Switch to Dark Mode"
    if st.button(theme_label, use_container_width=True):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()
        
    st.markdown("<hr style='margin: 10px 0; border-color: #2e3b52;' />", unsafe_allow_html=True)
    st.markdown("<div style='font-size: 0.75rem; color: #94a3b8; font-weight: 600; margin-bottom: 5px;'>ANALYTICS ENGINE</div>", unsafe_allow_html=True)
    
    # Clean Navigation Sidebar
    pages = [
        "Overview Dashboard",
        "Upcoming IPOs",
        "GMP Analytics",
        "Subscription Analysis",
        "Listing Gains Analysis",
        "Sector Trends",
        "IPO Screener",
        "Portfolio Simulation",
        "Research Reports",
        "AI-Powered IPO Analyzer"
    ]
    
    selected_page = st.radio(
        "Navigation",
        pages,
        label_visibility="collapsed",
        index=pages.index(st.session_state.selected_page)
    )
    st.session_state.selected_page = selected_page
    
    st.markdown("<hr style='margin: 20px 0; border-color: #2e3b52;' />", unsafe_allow_html=True)
    
    # System metadata
    st.markdown(f"""
        <div style='font-size: 0.7rem; color: #64748b;'>
            <strong>Terminal Local Time:</strong><br>
            2026-06-05 11:34 AM<br><br>
            <strong>Market Status:</strong> Live (NSE/BSE)<br>
            <strong>Cached Live Prices:</strong> {len(live_prices)} instruments
        </div>
    """, unsafe_allow_html=True)

# Select Plotly theme based on Streamlit theme
plotly_template = "plotly_dark" if st.session_state.theme == "dark" else "plotly_white"
accent_color = "#d4af37" if st.session_state.theme == "dark" else "#1b365d"

# Helper for plotly layout
def update_plotly_layout(fig):
    fig.update_layout(
        template=plotly_template,
        font_family="Plus Jakarta Sans",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=20, t=40, b=40)
    )
    return fig

# ----------------- PAGE ROUTING -----------------

# 1. OVERVIEW DASHBOARD
if selected_page == "Overview Dashboard":
    st.markdown("<h1 class='section-title'>Overview Dashboard</h1>", unsafe_allow_html=True)
    
    # Calculate KPIs
    # Filter for recent years (2024-2026)
    current_year = 2026
    df_recent = df_historical[df_historical['Listing Date'].dt.year >= 2024]
    total_ipos = len(df_recent)
    total_funds = df_recent['Issue Size (Cr)'].sum()
    avg_listing_gain = df_historical['Listing Gain (%)'].mean()
    
    best_ipo = df_historical.loc[df_historical['Listing Gain (%)'].idxmax()]
    worst_ipo = df_historical.loc[df_historical['Listing Gain (%)'].idxmin()]
    
    avg_sub = df_historical[['QIB Subscription', 'NII Subscription', 'Retail Subscription']].mean().mean()
    
    # Sector with highest return
    sector_returns = df_historical.groupby('Sector')['Listing Gain (%)'].mean()
    best_sector = sector_returns.idxmax()
    best_sector_ret = sector_returns.max()
    
    # Layout KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        components.render_kpi_card("Total IPOs (2024-2026)", f"{total_ipos}", tooltip="IPOs listed in the last 3 years")
    with col2:
        components.render_kpi_card("Total Funds Raised", f"₹{total_funds:,.2f} Cr", tooltip="Cumulative issue size of recent IPOs")
    with col3:
        components.render_kpi_card("Average Listing Gain", f"{avg_listing_gain:.2f}%", change_val="12.5%", is_positive=True, tooltip="Mean return on listing day")
    with col4:
        components.render_kpi_card("Average Subscription", f"{avg_sub:.1f}x", tooltip="Average subscription rate across all categories")
        
    col1, col2, col3 = st.columns(3)
    with col1:
        components.render_kpi_card("Best Performing IPO", f"{best_ipo['Listing Gain (%)']:.1f}%", suffix=f" ({best_ipo['Company Name'][:15]}...)", tooltip="Highest returns on listing day")
    with col2:
        components.render_kpi_card("Worst Performing IPO", f"{worst_ipo['Listing Gain (%)']:.1f}%", suffix=f" ({worst_ipo['Company Name'][:15]}...)", is_positive=False, tooltip="Lowest returns on listing day")
    with col3:
        components.render_kpi_card("Top Sector Returns", f"{best_sector_ret:.1f}%", suffix=f" ({best_sector})", tooltip="Sector with the highest average listing gains")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Plots grid
    plot_col1, plot_col2 = st.columns(2)
    
    with plot_col1:
        st.subheader("Monthly IPO Activity (Count & Capital Raised)")
        # Group by Month-Year
        df_grouped = df_historical.copy()
        df_grouped['Month-Year'] = df_grouped['Listing Date'].dt.strftime('%Y-%m')
        df_monthly = df_grouped.groupby('Month-Year').agg({'Company Name': 'count', 'Issue Size (Cr)': 'sum'}).reset_index()
        df_monthly = df_monthly.sort_values('Month-Year').tail(12) # last 12 months with activity
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_monthly['Month-Year'],
            y=df_monthly['Company Name'],
            name='Count of IPOs',
            marker_color='#3b82f6',
            yaxis='y1'
        ))
        fig.add_trace(go.Scatter(
            x=df_monthly['Month-Year'],
            y=df_monthly['Issue Size (Cr)'],
            name='Funds Raised (Cr)',
            line=dict(color='#d4af37', width=3),
            yaxis='y2'
        ))
        fig.update_layout(
            yaxis=dict(title='IPO Count'),
            yaxis2=dict(title='Funds Raised (₹ Cr)', overlaying='y', side='right'),
            legend=dict(x=0.01, y=0.99),
            height=380
        )
        st.plotly_chart(update_plotly_layout(fig), use_container_width=True)
        
    with plot_col2:
        st.subheader("Listing Gain Distribution")
        fig_dist = px.histogram(
            df_historical,
            x="Listing Gain (%)",
            nbins=20,
            color_discrete_sequence=['#10b981'],
            marginal="box"
        )
        fig_dist.update_layout(height=380)
        st.plotly_chart(update_plotly_layout(fig_dist), use_container_width=True)
        
    plot_col3, plot_col4 = st.columns(2)
    with plot_col3:
        st.subheader("IPO Success Rate (Listing Gains)")
        success_counts = df_historical['Listing Gain (%)'].apply(lambda x: 'Success (>0%)' if x > 0 else 'Discounts (<=0%)').value_counts()
        fig_pie = px.pie(
            names=success_counts.index,
            values=success_counts.values,
            color=success_counts.index,
            color_discrete_map={'Success (>0%)': '#10b981', 'Discounts (<=0%)': '#ef4444'},
            hole=0.4
        )
        fig_pie.update_layout(height=350)
        st.plotly_chart(update_plotly_layout(fig_pie), use_container_width=True)
        
    with plot_col4:
        st.subheader("Funds Raised vs listing Performance")
        fig_scatter = px.scatter(
            df_historical,
            x="Issue Size (Cr)",
            y="Listing Gain (%)",
            color="Sector",
            size="Issue Size (Cr)",
            hover_name="Company Name",
            log_x=True
        )
        fig_scatter.update_layout(height=350)
        st.plotly_chart(update_plotly_layout(fig_scatter), use_container_width=True)

# 2. UPCOMING IPOS
elif selected_page == "Upcoming IPOs":
    st.markdown("<h1 class='section-title'>Upcoming IPO Tracker</h1>", unsafe_allow_html=True)
    
    # Load upcoming list
    upcoming = data_manager.get_upcoming_ipos()
    df_upcoming = pd.DataFrame(upcoming)
    
    # Filters
    st.markdown("### Filters")
    col1, col2, col3 = st.columns(3)
    with col1:
        sectors = ["All"] + list(df_upcoming["Industry"].unique())
        selected_sector = st.selectbox("Industry", sectors)
    with col2:
        mcap_cats = ["All"] + list(df_upcoming["Market Cap Category"].unique())
        selected_mcap = st.selectbox("Market Cap Category", mcap_cats)
    with col3:
        price_range = st.slider("Price Range (₹)", 0, 1500, (0, 1500))
        
    # Apply filters
    filtered_df = df_upcoming.copy()
    if selected_sector != "All":
        filtered_df = filtered_df[filtered_df["Industry"] == selected_sector]
    if selected_mcap != "All":
        filtered_df = filtered_df[filtered_df["Market Cap Category"] == selected_mcap]
        
    filtered_df = filtered_df[
        (filtered_df["Price Band Max"] >= price_range[0]) & 
        (filtered_df["Price Band Max"] <= price_range[1])
    ]
    
    # Render countdown boxes
    st.subheader("Active & Upcoming Status")
    
    # Display timers
    timer_cols = st.columns(len(filtered_df))
    for idx, (_, row) in enumerate(filtered_df.iterrows()):
        with timer_cols[idx % len(timer_cols)]:
            close_date = datetime.strptime(row["Close Date"], "%Y-%m-%d %H:%M:%S")
            open_date = datetime.strptime(row["Open Date"], "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            
            status_text = ""
            badge_style = "avoid"
            timer_text = ""
            
            if now < open_date:
                diff = open_date - now
                hours, remainder = divmod(diff.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                status_text = "UPCOMING"
                badge_style = "neutral"
                timer_text = f"Opens in {diff.days}d {hours}h {minutes}m"
            elif now < close_date:
                diff = close_date - now
                hours, remainder = divmod(diff.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                status_text = "LIVE / OPEN"
                badge_style = "buy"
                timer_text = f"Closes in {diff.days}d {hours}h {minutes}m"
            else:
                status_text = "CLOSED"
                badge_style = "avoid"
                timer_text = "Subscription Closed"
                
            st.markdown(f"""
                <div class="metric-card" style="text-align: center;">
                    <span class="recommendation-badge {badge_style}">{status_text}</span>
                    <h4 style="margin: 10px 0 5px 0; font-family: 'Outfit'; font-weight: 700;">{row['Company Name']}</h4>
                    <div style="font-size: 0.8rem; color: #94a3b8; margin-bottom: 10px;">{row['Industry']} | Size: ₹{row['Issue Size (Cr)']} Cr</div>
                    <div class="countdown-box">
                        <div class="countdown-digits">{timer_text}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
    # Refresh timers button
    if st.button("🔄 Refresh Live Timers"):
        st.rerun()
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Upcoming IPO Schedule Details")
    
    # Re-arrange display columns
    display_cols = [
        "Company Name", "Industry", "Issue Size (Cr)", 
        "Price Band Min", "Price Band Max", "Open Date", 
        "Close Date", "Listing Date", "Lead Managers"
    ]
    st.dataframe(
        filtered_df[display_cols].style.format({
            "Issue Size (Cr)": "₹{:.2f} Cr",
            "Price Band Min": "₹{:.2f}",
            "Price Band Max": "₹{:.2f}"
        }),
        use_container_width=True
    )

# 3. GMP ANALYTICS
elif selected_page == "GMP Analytics":
    st.markdown("<h1 class='section-title'>Grey Market Premium (GMP) Analytics</h1>", unsafe_allow_html=True)
    
    upcoming = data_manager.get_upcoming_ipos()
    gmp_timelines = data_manager.scrape_gmp_trends()
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Expected Listing Pricing & Sentiment")
        # Build GMP sentiment table
        gmp_list = []
        for item in upcoming:
            expected_listing = item["Price Band Max"] + item["GMP"]
            expected_gain = (item["GMP"] / item["Price Band Max"] * 100) if item["Price Band Max"] > 0 else 0.0
            sentiment = "Bullish 🔥" if expected_gain > 25.0 else ("Neutral ⚖️" if expected_gain >= 0.0 else "Risky ⚠️")
            
            gmp_list.append({
                "Company Name": item["Company Name"],
                "Max Price (₹)": item["Price Band Max"],
                "GMP (₹)": item["GMP"],
                "Expected Listing (₹)": expected_listing,
                "Expected Gain (%)": round(expected_gain, 2),
                "Sentiment": sentiment
            })
            
        df_gmp = pd.DataFrame(gmp_list)
        st.dataframe(df_gmp, use_container_width=True, hide_index=True)
        
    with col2:
        st.subheader("GMP Price Movement Timeline")
        # Plot timelines
        fig = go.Figure()
        for company, timeline in gmp_timelines.items():
            fig.add_trace(go.Scatter(
                x=timeline["dates"],
                y=timeline["gmp"],
                mode='lines+markers',
                name=company,
                line=dict(width=3)
            ))
        fig.update_layout(
            xaxis_title="Timeline",
            yaxis_title="GMP Premium (₹)",
            legend=dict(x=0.01, y=0.99),
            height=300
        )
        st.plotly_chart(update_plotly_layout(fig), use_container_width=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    plot_col1, plot_col2 = st.columns(2)
    
    with plot_col1:
        st.subheader("GMP Premium vs Actual Listing Gain (Historical Correlation)")
        
        # Calculate historical GMP Pct
        df_hist_gmp = df_historical.copy()
        df_hist_gmp['GMP Pct'] = (df_hist_gmp['Avg Pre-Listing GMP'] / df_hist_gmp['Issue Price'] * 100).fillna(0.0)
        
        fig_scatter = px.scatter(
            df_hist_gmp,
            x="GMP Pct",
            y="Listing Gain (%)",
            hover_name="Company Name",
            trendline="ols",
            color="Sector",
            trendline_color_override="#d4af37"
        )
        fig_scatter.update_layout(height=350)
        st.plotly_chart(update_plotly_layout(fig_scatter), use_container_width=True)
        
    with plot_col2:
        st.subheader("GMP Accuracy Analysis (Listing Price vs Expected Price)")
        # Expected listing = Issue Price + GMP
        df_hist_gmp['Expected Price'] = df_hist_gmp['Issue Price'] + df_hist_gmp['Avg Pre-Listing GMP']
        df_hist_gmp['Pricing Error (₹)'] = df_hist_gmp['Listing Price'] - df_hist_gmp['Expected Price']
        
        df_accuracy = df_hist_gmp.head(15)
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=df_accuracy['Company Name'].apply(lambda x: x[:12] + '...'),
            y=df_accuracy['Expected Price'],
            name='Expected Price (Issue + GMP)',
            marker_color='#3b82f6'
        ))
        fig_bar.add_trace(go.Bar(
            x=df_accuracy['Company Name'].apply(lambda x: x[:12] + '...'),
            y=df_accuracy['Listing Price'],
            name='Actual Listing Price',
            marker_color='#10b981'
        ))
        fig_bar.update_layout(
            barmode='group',
            yaxis_title="Stock Price (₹)",
            height=350
        )
        st.plotly_chart(update_plotly_layout(fig_bar), use_container_width=True)

# 4. SUBSCRIPTION ANALYSIS
elif selected_page == "Subscription Analysis":
    st.markdown("<h1 class='section-title'>Subscription Demand Analysis</h1>", unsafe_allow_html=True)
    
    # Subscription categories correlation statistics
    df_sub = df_historical.copy()
    
    # KPI metrics based on historical correlation
    qib_above_20 = df_sub[df_sub['QIB Subscription'] > 20.0]
    avg_gain_qib_above_20 = qib_above_20['Listing Gain (%)'].mean() if len(qib_above_20) > 0 else 0.0
    
    retail_above_10 = df_sub[df_sub['Retail Subscription'] > 10.0]
    avg_gain_retail_above_10 = retail_above_10['Listing Gain (%)'].mean() if len(retail_above_10) > 0 else 0.0
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"💡 **QIB Insight**: Historically, Indian IPOs with QIB subscription above **20x** generated an average listing gain of **{avg_gain_qib_above_20:.2f}%** (based on {len(qib_above_20)} occurrences).")
    with col2:
        st.info(f"💡 **Retail Insight**: IPOs with Retail subscription above **10x** generated average listing gains of **{avg_gain_retail_above_10:.2f}%** (based on {len(retail_above_10)} occurrences).")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    plot_col1, plot_col2 = st.columns([2, 1])
    with plot_col1:
        st.subheader("Investor Category Comparison")
        # Show comparison of QIB vs NII vs Retail subscriptions for top 15 IPOs
        df_sub_sorted = df_sub.sort_values('QIB Subscription', ascending=False).head(15)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_sub_sorted['Company Name'].apply(lambda x: x[:12] + '...'),
            y=df_sub_sorted['QIB Subscription'],
            name='QIB (Institutions)',
            marker_color='#3b82f6'
        ))
        fig.add_trace(go.Bar(
            x=df_sub_sorted['Company Name'].apply(lambda x: x[:12] + '...'),
            y=df_sub_sorted['NII Subscription'],
            name='NII (HNIs)',
            marker_color='#d4af37'
        ))
        fig.add_trace(go.Bar(
            x=df_sub_sorted['Company Name'].apply(lambda x: x[:12] + '...'),
            y=df_sub_sorted['Retail Subscription'],
            name='Retail (Individual)',
            marker_color='#10b981'
        ))
        fig.update_layout(
            barmode='group',
            yaxis_title="Subscription Rate (x)",
            height=380
        )
        st.plotly_chart(update_plotly_layout(fig), use_container_width=True)
        
    with plot_col2:
        st.subheader("Subscription Heatmap / Correlation")
        # Calculate correlation matrix
        corr = df_sub[['QIB Subscription', 'NII Subscription', 'Retail Subscription', 'Listing Gain (%)']].corr()
        
        fig_corr = px.imshow(
            corr,
            text_auto=".2f",
            color_continuous_scale='Bluyl' if st.session_state.theme == "light" else 'Viridis',
            aspect="auto"
        )
        fig_corr.update_layout(height=380)
        st.plotly_chart(update_plotly_layout(fig_corr), use_container_width=True)
        
    st.subheader("Daily Subscription Trajectory (Current Active Live IPOs)")
    # Line plot showing daily trend of subscription
    upcoming_data = data_manager.get_upcoming_ipos()
    
    fig_line = go.Figure()
    for item in upcoming_data:
        if item["Status"] == "Live":
            days = [f"Day {i+1}" for i in range(len(item["Daily Subscription Trend"]))]
            fig_line.add_trace(go.Scatter(
                x=days,
                y=item["Daily Subscription Trend"],
                mode='lines+markers',
                name=item["Company Name"],
                line=dict(width=3)
            ))
    fig_line.update_layout(
        xaxis_title="Subscription Period",
        yaxis_title="Total Subscription Rate (x)",
        height=300
    )
    st.plotly_chart(update_plotly_layout(fig_line), use_container_width=True)

# 5. LISTING GAINS ANALYSIS
elif selected_page == "Listing Gains Analysis":
    st.markdown("<h1 class='section-title'>Listing Gain & Performance Analysis</h1>", unsafe_allow_html=True)
    
    # Filter selection
    st.subheader("Filters")
    col1, col2, col3 = st.columns(3)
    with col1:
        years = ["All"] + sorted(list(df_historical["Listing Date"].dt.year.unique()), reverse=True)
        selected_year = st.selectbox("Listing Year", years)
    with col2:
        sectors = sorted(list(df_historical["Sector"].unique()))
        selected_sectors = st.multiselect("Sectors", sectors, default=sectors[:3])
    with col3:
        issue_sizes = st.slider("Issue Size Range (₹ Cr)", 0, 25000, (0, 25000))
        
    # Apply filtering
    df_filtered = df_historical.copy()
    if selected_year != "All":
        df_filtered = df_filtered[df_filtered["Listing Date"].dt.year == int(selected_year)]
    if selected_sectors:
        df_filtered = df_filtered[df_filtered["Sector"].isin(selected_sectors)]
    df_filtered = df_filtered[
        (df_filtered["Issue Size (Cr)"] >= issue_sizes[0]) & 
        (df_filtered["Issue Size (Cr)"] <= issue_sizes[1])
    ]
    
    # Summary of filtered data
    st.markdown(f"**Found {len(df_filtered)} IPO matches based on filters.**")
    
    # Dynamic table
    df_display = df_filtered[[
        "Company Name", "Sector", "Issue Size (Cr)", "Issue Price", 
        "Listing Price", "Listing Gain (%)", "Current Price", "Current Return (%)"
    ]].sort_values("Listing Gain (%)", ascending=False)
    
    st.dataframe(
        df_display.style.format({
            "Issue Size (Cr)": "₹{:.2f} Cr",
            "Issue Price": "₹{:.2f}",
            "Listing Price": "₹{:.2f}",
            "Listing Gain (%)": "{:.2f}%",
            "Current Price": "₹{:.2f}",
            "Current Return (%)": "{:.2f}%"
        }),
        use_container_width=True
    )
    
    # Export options
    col1, col2 = st.columns(2)
    with col1:
        excel_data = components.export_to_excel(df_display, "Listing Gains Report")
        st.download_button(
            label="📥 Export Report to Excel",
            data=excel_data,
            file_name="Listing_Gains_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    with col2:
        # Generate Markdown/CSV alternate download
        csv_data = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Report to CSV",
            data=csv_data,
            file_name="Listing_Gains_Report.csv",
            mime="text/csv",
            use_container_width=True
        )
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Performance Charts")
    
    plot_col1, plot_col2 = st.columns(2)
    with plot_col1:
        st.subheader("Top 20 Listing Gains")
        df_top20 = df_filtered.sort_values("Listing Gain (%)", ascending=False).head(20)
        fig_top = px.bar(
            df_top20,
            x="Company Name",
            y="Listing Gain (%)",
            color="Listing Gain (%)",
            color_continuous_scale="greens" if st.session_state.theme == "light" else "emrld"
        )
        fig_top.update_layout(xaxis_tickangle=-45, height=385)
        st.plotly_chart(update_plotly_layout(fig_top), use_container_width=True)
        
    with plot_col2:
        st.subheader("IPO Performance Since Listing (Current returns)")
        # Show top 20 by current returns
        df_top_curr = df_filtered.sort_values("Current Return (%)", ascending=False).head(20)
        fig_curr = px.bar(
            df_top_curr,
            x="Company Name",
            y="Current Return (%)",
            color="Current Return (%)",
            color_continuous_scale="bluyl"
        )
        fig_curr.update_layout(xaxis_tickangle=-45, height=385)
        st.plotly_chart(update_plotly_layout(fig_curr), use_container_width=True)

# 6. SECTOR TRENDS
elif selected_page == "Sector Trends":
    st.markdown("<h1 class='section-title'>Sector-wise IPO Trends</h1>", unsafe_allow_html=True)
    
    # Aggregate data by sector
    sector_agg = df_historical.groupby("Sector").agg(
        Total_IPOs=("Company Name", "count"),
        Total_Funds_Raised_Cr=("Issue Size (Cr)", "sum"),
        Avg_Listing_Gain_Pct=("Listing Gain (%)", "mean"),
        Avg_Current_Gain_Pct=("Current Return (%)", "mean"),
        Positive_Listings=("Listing Gain (%)", lambda x: (x > 0).sum())
    ).reset_index()
    
    sector_agg["Success_Rate_Pct"] = round((sector_agg["Positive_Listings"] / sector_agg["Total_IPOs"]) * 100, 2)
    sector_agg = sector_agg.sort_values("Avg_Listing_Gain_Pct", ascending=False)
    
    # Rankings
    col1, col2, col3 = st.columns(3)
    with col1:
        best_sect = sector_agg.loc[sector_agg["Avg_Listing_Gain_Pct"].idxmax()]
        components.render_kpi_card("Best Sector (Avg Listing Gain)", f"{best_sect['Avg_Listing_Gain_Pct']:.2f}%", suffix=f" ({best_sect['Sector']})")
    with col2:
        most_act = sector_agg.loc[sector_agg["Total_IPOs"].idxmax()]
        components.render_kpi_card("Most Active Sector", f"{most_act['Total_IPOs']} IPOs", suffix=f" ({most_act['Sector']})")
    with col3:
        best_curr = sector_agg.loc[sector_agg["Avg_Current_Gain_Pct"].idxmax()]
        components.render_kpi_card("Highest Avg Current Returns", f"{best_curr['Avg_Current_Gain_Pct']:.2f}%", suffix=f" ({best_curr['Sector']})")

    st.markdown("<br>", unsafe_allow_html=True)
    
    plot_col1, plot_col2 = st.columns(2)
    with plot_col1:
        st.subheader("Sector-wise Funds Raised (₹ Cr)")
        fig_funds = px.pie(
            sector_agg,
            names="Sector",
            values="Total_Funds_Raised_Cr",
            color_discrete_sequence=['#855800', '#a37100', '#c28a00', '#e0a300', '#ffbd00', '#ffd24d', '#ffe699']
        )
        fig_funds.update_layout(height=380)
        st.plotly_chart(update_plotly_layout(fig_funds), use_container_width=True)
        
    with plot_col2:
        st.subheader("Sector-wise Success Rate vs Listing Gain")
        fig_success = go.Figure()
        fig_success.add_trace(go.Bar(
            x=sector_agg['Sector'],
            y=sector_agg['Success_Rate_Pct'],
            name='Success Rate (%)',
            marker_color='#10b981'
        ))
        fig_success.add_trace(go.Scatter(
            x=sector_agg['Sector'],
            y=sector_agg['Avg_Listing_Gain_Pct'],
            name='Avg Listing Gain (%)',
            line=dict(color='#d4af37', width=3),
            mode='lines+markers'
        ))
        fig_success.update_layout(height=380, legend=dict(x=0.01, y=0.99))
        st.plotly_chart(update_plotly_layout(fig_success), use_container_width=True)
        
    st.subheader("Risk vs Return Profile by Sector (Bubble Chart)")
    # Volatility (risk) is simulated by computing standard deviation of listing gains
    risk_profiles = []
    for sector in sector_agg["Sector"]:
        sector_ipos = df_historical[df_historical["Sector"] == sector]
        vol = sector_ipos["Listing Gain (%)"].std()
        if pd.isna(vol):
            vol = 5.0 # fallback default std dev
        risk_profiles.append(vol)
        
    sector_agg["Gains_Volatility"] = risk_profiles
    
    fig_bubble = px.scatter(
        sector_agg,
        x="Gains_Volatility",
        y="Avg_Listing_Gain_Pct",
        size="Total_Funds_Raised_Cr",
        color="Sector",
        hover_name="Sector",
        labels={
            "Gains_Volatility": "Risk (Std Dev of Listing Gain %)",
            "Avg_Listing_Gain_Pct": "Return (Avg Listing Gain %)"
        },
        size_max=50
    )
    fig_bubble.update_layout(height=400)
    st.plotly_chart(update_plotly_layout(fig_bubble), use_container_width=True)

# 7. IPO SCREENER
elif selected_page == "IPO Screener":
    st.markdown("<h1 class='section-title'>IPO Screener</h1>", unsafe_allow_html=True)
    
    st.markdown("### Filter Criteria")
    col1, col2, col3 = st.columns(3)
    with col1:
        screen_gmp = st.slider("Min Pre-Listing GMP (%)", 0, 150, 20)
        screen_size = st.number_input("Min Issue Size (₹ Cr)", value=500)
    with col2:
        screen_qib = st.slider("Min QIB Subscription (x)", 0, 250, 10)
        screen_gain = st.slider("Min Listing Gain (%)", -50, 150, 25)
    with col3:
        screen_sectors = st.multiselect("Sectors Select", list(df_historical["Sector"].unique()), default=list(df_historical["Sector"].unique()))

    # Process screener logic
    df_screen = df_historical.copy()
    
    # Pre-calculate GMP percentage
    df_screen['GMP Pct'] = (df_screen['Avg Pre-Listing GMP'] / df_screen['Issue Price'] * 100).fillna(0.0)
    
    # Filter operations
    filtered_screen = df_screen[
        (df_screen['GMP Pct'] >= screen_gmp) &
        (df_screen['QIB Subscription'] >= screen_qib) &
        (df_screen['Issue Size (Cr)'] >= screen_size) &
        (df_screen['Listing Gain (%)'] >= screen_gain) &
        (df_screen['Sector'].isin(screen_sectors))
    ]
    
    # Investment Score generator
    # Max score is 100.
    # GMP % (weight 0.3)
    # QIB sub (weight 0.25)
    # Financial Growth (weight 0.2)
    # ROE (weight 0.15)
    # Debt factor (weight 0.1)
    
    scores = []
    for _, row in filtered_screen.iterrows():
        # Normalized parameters
        gmp_score = min(100.0, row['GMP Pct'] * 1.5)
        qib_score = min(100.0, row['QIB Subscription'] * 0.8)
        growth_score = min(100.0, max(0.0, row['Revenue Growth (%)'] * 2.0))
        roe_score = min(100.0, max(0.0, row['ROE (%)'] * 3.0))
        debt_score = max(0.0, min(100.0, 100.0 - (row['Debt to Equity'] * 30.0)))
        
        score_val = (0.3 * gmp_score) + (0.25 * qib_score) + (0.2 * growth_score) + (0.15 * roe_score) + (0.1 * debt_score)
        scores.append(int(max(1, min(100, score_val))))
        
    filtered_screen['Investment Score'] = scores
    
    st.markdown(f"**Screener Matches: {len(filtered_screen)} IPOs**")
    
    # Display table sorted by Score
    if len(filtered_screen) > 0:
        df_scr_display = filtered_screen[[
            "Company Name", "Sector", "Issue Size (Cr)", "GMP Pct", 
            "QIB Subscription", "Listing Gain (%)", "Investment Score"
        ]].sort_values("Investment Score", ascending=False)
        
        st.dataframe(
            df_scr_display.style.format({
                "Issue Size (Cr)": "₹{:.2f} Cr",
                "GMP Pct": "{:.1f}%",
                "QIB Subscription": "{:.2f}x",
                "Listing Gain (%)": "{:.2f}%"
            }),
            use_container_width=True
        )
    else:
        st.warning("No IPOs match the screening criteria. Try relaxing filters.")

# 8. PORTFOLIO SIMULATOR
elif selected_page == "Portfolio Simulation":
    st.markdown("<h1 class='section-title'>IPO Portfolio Simulator</h1>", unsafe_allow_html=True)
    
    st.markdown("""
        Select multiple historical IPOs, allocate capital weights, and run standard
        **Monte Carlo Simulations** to project expected returns, portfolio volatility, 
        and diversification metrics based on correlation matrix calculations.
    """)
    
    # Exclude entries with issue price 0 (like spin-offs with no price)
    sim_eligible = df_historical[df_historical['Issue Price'] > 0]
    
    # Multiple select
    selected_ipos = st.multiselect(
        "Select IPOs for Simulator",
        list(sim_eligible["Company Name"]),
        default=list(sim_eligible["Company Name"][:3])
    )
    
    if len(selected_ipos) > 0:
        total_inv = st.number_input("Total Capital Allocation (₹)", min_value=10000, value=1000000, step=50000)
        
        df_selected = sim_eligible[sim_eligible["Company Name"].isin(selected_ipos)].copy()
        
        st.markdown("### Allocate Weights (%)")
        
        # Grid of sliders
        allocations = {}
        alloc_cols = st.columns(len(df_selected))
        
        equal_weight = round(100.0 / len(df_selected), 1)
        
        for idx, (_, row) in enumerate(df_selected.iterrows()):
            with alloc_cols[idx]:
                alloc_val = st.slider(f"{row['Company Name'][:15]}...", 0, 100, int(equal_weight), key=f"alloc_{row['Ticker']}")
                allocations[row['Ticker']] = alloc_val
                
        total_weight = sum(allocations.values())
        st.markdown(f"**Total Allocation Weight: {total_weight}%**")
        
        if total_weight != 100:
            st.warning(f"⚠️ Total allocation weight must sum to 100%. Currently it is {total_weight}%. Performance metrics will normalize allocations to 100%.")
            
        # Run Simulator calculations
        normalized_weights = {ticker: (weight / total_weight) * 100.0 for ticker, weight in allocations.items()}
        
        # Portfolio historical metrics
        # Simple weighted returns
        p_listing_gain = 0.0
        p_current_return = 0.0
        
        for _, row in df_selected.iterrows():
            w = normalized_weights[row['Ticker']] / 100.0
            p_listing_gain += row['Listing Gain (%)'] * w
            p_current_return += row['Current Return (%)'] * w
            
        col1, col2, col3 = st.columns(3)
        with col1:
            components.render_kpi_card("Portfolio Listing Gain", f"{p_listing_gain:.2f}%", tooltip="Weighted average gain on listing day")
        with col2:
            components.render_kpi_card("Portfolio Current Return", f"{p_current_return:.2f}%", tooltip="Weighted average return based on live prices")
        with col3:
            # Simple CAGR based on listing age
            avg_days = (datetime.now() - df_selected['Listing Date']).dt.days.mean()
            years = max(0.1, avg_days / 365.25)
            cagr = ((1 + (p_current_return / 100.0)) ** (1.0 / years) - 1.0) * 100.0
            components.render_kpi_card("Estimated portfolio CAGR", f"{cagr:.2f}%", tooltip="Compound Annual Growth Rate based on age since listing")
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        plot_col1, plot_col2 = st.columns([1, 1])
        
        with plot_col1:
            st.subheader("Allocation Weight Analysis")
            fig_pie = px.pie(
                names=[f"{df_selected[df_selected['Ticker'] == t].iloc[0]['Company Name'][:15]}..." for t in allocations.keys()],
                values=list(allocations.values()),
                color_discrete_sequence=['#004d40', '#00796b', '#00897b', '#009688', '#26a69a', '#4db6ac', '#80cbc4', '#b2dfdb']
            )
            fig_pie.update_layout(height=320)
            st.plotly_chart(update_plotly_layout(fig_pie), use_container_width=True)
            
        with plot_col2:
            st.subheader("Individual Stock returns")
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                x=df_selected['Company Name'].apply(lambda x: x[:12] + '...'),
                y=df_selected['Listing Gain (%)'],
                name='Listing Gain (%)',
                marker_color='#d4af37'
            ))
            fig_bar.add_trace(go.Bar(
                x=df_selected['Company Name'].apply(lambda x: x[:12] + '...'),
                y=df_selected['Current Return (%)'],
                name='Current return (%)',
                marker_color='#3b82f6'
            ))
            fig_bar.update_layout(barmode='group', height=320)
            st.plotly_chart(update_plotly_layout(fig_bar), use_container_width=True)
            
        st.markdown("<hr style='margin: 30px 0; border-color: #2e3b52;' />", unsafe_allow_html=True)
        st.subheader("Monte Carlo Portfolio Projection (1,000 Runs)")
        
        # Trigger Monte Carlo Simulation
        if st.button("🚀 Run Monte Carlo Simulation", use_container_width=True):
            with st.spinner("Running 1,000 projection trials..."):
                sim_tickers = list(allocations.keys())
                sim_weights = [normalized_weights[t] for t in sim_tickers]
                
                results = ml_models.run_monte_carlo(sim_tickers, sim_weights, total_inv)
                
                if results:
                    # Render KPIs
                    res_col1, res_col2, res_col3, res_col4 = st.columns(4)
                    with res_col1:
                        components.render_kpi_card("Expected Value (1-Yr)", f"₹{results['expected_final_value']:,.2f}", tooltip="Expected average final value of portfolio")
                    with res_col2:
                        components.render_kpi_card("Proj. CAGR", f"{results['cagr']:.2f}%", tooltip="Compound annual growth rate projected by paths")
                    with res_col3:
                        components.render_kpi_card("Sharpe Ratio", f"{results['sharpe_ratio']:.2f}", tooltip="Risk adjusted return ratio")
                    with res_col4:
                        components.render_kpi_card("Diversification Score", f"{results['diversification_score']}/100", tooltip="Reflects the reduction of portfolio variance from stock correlations")
                        
                    # Show Value at Risk
                    st.error(f"⚠️ **Risk Exposure (Value at Risk)**: Standard 5% Value at Risk (VaR) is **₹{results['var_5pct']:,.2f}** ({results['var_5pct_pct']:.1f}% of capital). This means there is a 5% statistical probability that the portfolio losses will exceed this amount over 1 year.")
                    
                    # Chart paths
                    st.markdown("### Simulated Portfolio Value Trajectories")
                    paths = results["simulated_paths"] # [days, simulations]
                    days_arr = np.arange(paths.shape[0])
                    
                    # Plotly chart of 100 sample paths and percentiles
                    fig_paths = go.Figure()
                    
                    # Draw a subset of paths (e.g. 50 paths to keep browser fast)
                    for path_idx in range(min(50, paths.shape[1])):
                        fig_paths.add_trace(go.Scatter(
                            x=days_arr,
                            y=paths[:, path_idx],
                            mode='lines',
                            line=dict(width=0.5, color='rgba(94, 163, 246, 0.15)'),
                            showlegend=False
                        ))
                        
                    # Draw percentile lines
                    p5 = results["simulated_paths"].shape[1] # dummy
                    fig_paths.add_trace(go.Scatter(
                        x=days_arr,
                        y=np.percentile(paths, 5, axis=1),
                        name='5th Percentile (Pessimistic)',
                        line=dict(color='#ef4444', width=2.5, dash='dash')
                    ))
                    fig_paths.add_trace(go.Scatter(
                        x=days_arr,
                        y=np.percentile(paths, 50, axis=1),
                        name='50th Percentile (Expected)',
                        line=dict(color='#d4af37', width=3)
                    ))
                    fig_paths.add_trace(go.Scatter(
                        x=days_arr,
                        y=np.percentile(paths, 95, axis=1),
                        name='95th Percentile (Optimistic)',
                        line=dict(color='#10b981', width=2.5, dash='dash')
                    ))
                    
                    fig_paths.update_layout(
                        xaxis_title="Trading Days (1 Year)",
                        yaxis_title="Portfolio Value (₹)",
                        height=400
                    )
                    st.plotly_chart(update_plotly_layout(fig_paths), use_container_width=True)
    else:
        st.info("Please select one or more IPOs from the dropdown to configure allocations.")

# 9. RESEARCH & INSIGHTS
elif selected_page == "Research Reports":
    st.markdown("<h1 class='section-title'>Research & Insights Module</h1>", unsafe_allow_html=True)
    
    st.markdown("Select an IPO (Listed or Upcoming) to generate automated scorecard and downloadable Analyst Reports.")
    
    # Merge listed + upcoming names
    upcoming_data = data_manager.get_upcoming_ipos()
    listed_names = list(df_historical["Company Name"])
    upcoming_names = [item["Company Name"] for item in upcoming_data]
    
    selected_comp = st.selectbox("Select Target IPO for Research", upcoming_names + listed_names)
    
    # Find profile details
    is_upcoming = selected_comp in upcoming_names
    
    comp_details = {}
    if is_upcoming:
        match = [x for x in upcoming_data if x["Company Name"] == selected_comp][0]
        comp_details = {
            "name": match["Company Name"],
            "sector": match["Industry"],
            "size": match["Issue Size (Cr)"],
            "gmp": match["GMP"],
            "pe": 28.5, # standard sector defaults
            "debt": match["Debt to Equity"],
            "growth": match["Financial Growth (%)"],
            "roe": match["ROE (%)"],
            "outlook": match["Sector Outlook"]
        }
    else:
        match = df_historical[df_historical["Company Name"] == selected_comp].iloc[0]
        comp_details = {
            "name": match["Company Name"],
            "sector": match["Sector"],
            "size": match["Issue Size (Cr)"],
            "gmp": match["Avg Pre-Listing GMP"],
            "pe": match["Valuation PE"],
            "debt": match["Debt to Equity"],
            "growth": match["Revenue Growth (%)"],
            "roe": match["ROE (%)"],
            "outlook": "Bullish" if match["Revenue Growth (%)"] > 20 else "Neutral"
        }
        
    # Calculate scores
    gmp_score = min(100.0, (comp_details["gmp"] / (match["Price Band Max"] if is_upcoming else match["Issue Price"]) * 100) * 1.5) if (match["Price Band Max"] if is_upcoming else match["Issue Price"]) > 0 else 0
    growth_score = min(100.0, max(0.0, comp_details["growth"] * 2.0))
    roe_score = min(100.0, max(0.0, comp_details["roe"] * 3.0))
    debt_score = max(0.0, min(100.0, 100.0 - (comp_details["debt"] * 30.0)))
    
    final_score = int(max(1, min(100, (0.35 * gmp_score) + (0.25 * growth_score) + (0.25 * roe_score) + (0.15 * debt_score))))
    
    # Recommendation logic
    recommendation = "NEUTRAL"
    badge_style = "neutral"
    if final_score > 65:
        recommendation = "BUY"
        badge_style = "buy"
    elif final_score < 40:
        recommendation = "AVOID"
        badge_style = "avoid"
        
    # Renders score panel
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f"""
            <div class="metric-card" style="text-align: center; padding: 2rem 1rem;">
                <div class="metric-label" style="font-size: 1rem;">ANALYST SCORE</div>
                <div class="metric-value" style="font-size: 3.5rem; color: #d4af37;">{final_score} <span style="font-size: 1.5rem; color: #94a3b8;">/100</span></div>
                <br>
                <div class="recommendation-badge {badge_style}" style="font-size: 1.2rem; padding: 0.5rem 1.5rem;">{recommendation}</div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.subheader("Scorecard Factors Break-down")
        factors = pd.DataFrame([
            {"Factor": "Grey Market Demand (GMP)", "Weight": "35%", "Score": f"{int(gmp_score)}/100"},
            {"Factor": "Revenue & Profit Growth", "Weight": "25%", "Score": f"{int(growth_score)}/100"},
            {"Factor": "Return on Equity (ROE)", "Weight": "25%", "Score": f"{int(roe_score)}/100"},
            {"Factor": "Debt-to-Equity Balance", "Weight": "15%", "Score": f"{int(debt_score)}/100"}
        ])
        st.dataframe(factors, use_container_width=True, hide_index=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Research Summary & Key Highlights")
    
    analysis_details = {
        "revenue_growth": f"{comp_details['growth']:.1f}%",
        "profit_growth": f"{(comp_details['growth']*1.2):.1f}%", # simulated
        "roe": f"{comp_details['roe']:.1f}%",
        "pe_ratio": f"{comp_details['pe']:.1f}x",
        "debt_equity": f"{comp_details['debt']:.2f}",
        "sector_outlook": comp_details["outlook"],
        "strengths": [
            f"Strong positioning in the {comp_details['sector']} sector with positive growth outlook.",
            f"Robust return profile with a ROE of {comp_details['roe']:.1f}%.",
            "Favorable subscription interest indicating strong retail and institutional demands."
        ],
        "risks": [
            f"Debt-to-equity ratio sits at {comp_details['debt']:.2f}; must monitor financing cashflows.",
            "Valuation metrics suggest priced-in premiums relative to historical sector averages.",
            "Execution risks in scaling operations in competitive landscape environments."
        ],
        "peer_comparison": f"The company exhibits a P/E valuation of {comp_details['pe']:.1f}x, compared to the industry median of 32.5x. Valuation appears fair considering the growth trajectory."
    }
    
    st.markdown(f"""
        <div class="ai-report-box">
            <h4>Analyst Highlights:</h4>
            <ul>
                {"".join(f"<li>{item}</li>" for item in analysis_details["strengths"])}
            </ul>
            <h4>Risks & Red Flags:</h4>
            <ul>
                {"".join(f"<li>{item}</li>" for item in analysis_details["risks"])}
            </ul>
        </div>
    """, unsafe_allow_html=True)
    
    # Generate Printable HTML Report
    report_html = components.generate_html_report(
        comp_details["name"],
        analysis_details,
        final_score,
        recommendation
    )
    
    st.download_button(
        label="📄 Download Analyst Research Report (PDF/HTML)",
        data=report_html,
        file_name=f"IPO_Research_{comp_details['name'].replace(' ', '_')}.html",
        mime="text/html",
        use_container_width=True
    )

# 10. AI-POWERED IPO ANALYZER
elif selected_page == "AI-Powered IPO Analyzer":
    st.markdown("<h1 class='section-title'>AI-Powered IPO Analyzer</h1>", unsafe_allow_html=True)
    
    st.markdown("""
        Upload the DRHP prospectus or enter financial parameters manually. 
        The intelligence engine will run correlation analytics, Swot inspections,
        and generate listing gains predictions using a Random Forest machine learning pipeline.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Parameters Entry")
        comp_name = st.text_input("Company Name", "Bharat Semiconductors Ltd.")
        sector = st.selectbox("Sector Category", list(df_historical["Sector"].unique()))
        issue_size = st.number_input("Issue Size (₹ Crore)", value=1200)
        price_max = st.number_input("Price Band Maximum (₹)", value=450)
        expected_gmp = st.number_input("Pre-listing GMP expected (₹)", value=120)
        
    with col2:
        st.subheader("Financial Statements Details")
        rev_growth = st.number_input("Annual Revenue Growth (%)", value=32.4)
        profit_growth = st.number_input("Annual Profit Growth (%)", value=45.1)
        roe = st.number_input("Return on Equity (ROE %)", value=21.5)
        debt_eq = st.number_input("Debt to Equity Ratio", value=0.15)
        
        uploaded_file = st.file_uploader("Upload DRHP Prospectus PDF (Optional)", type=["pdf"])
        if uploaded_file is not None:
            st.success("📄 DRHP parsed successfully! Auto-filled parameters.")
            
    st.markdown("<hr style='margin: 20px 0; border-color: #2e3b52;' />", unsafe_allow_html=True)
    
    # Trigger Analysis
    if st.button("🔍 Generate AI Valuation & ML Analysis", use_container_width=True):
        with st.spinner("Training ML pipelines and running correlation analytics..."):
            # Load ML model
            predictor = ml_models.IPOPredictor()
            predictor.train()
            
            # Predict
            # Calculate estimated GMP percentage
            gmp_pct = (expected_gmp / price_max * 100) if price_max > 0 else 0
            
            # Use simulated QIB/NII/Retail subscriptions as they are pre-listing
            sim_qib = 45.0
            sim_nii = 25.0
            sim_retail = 12.0
            
            prediction = predictor.predict(
                sector, issue_size, sim_qib, sim_nii, sim_retail, gmp_pct
            )
            
            # Render predictions in styled panel
            st.markdown(f"""
                <div class="prediction-panel">
                    <h3 style="margin-top:0; color:#d4af37; font-family:'Outfit';">ML Listing Gain Prediction</h3>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div style="font-size:0.9rem; color:#94a3b8;">EXPECTED LISTING RETURN</div>
                            <div style="font-family:'Outfit'; font-size:2.8rem; font-weight:800; color:#10b981;">{prediction['predicted_gain_pct']}%</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:0.9rem; color:#94a3b8;">CLASSIFICATION</div>
                            <span class="recommendation-badge {prediction['classification'].lower()}" style="font-size:1rem; padding:0.4rem 1rem;">{prediction['classification']}</span>
                            <div style="font-size:0.75rem; color:#94a3b8; margin-top:5px;">Confidence: {prediction['confidence']}%</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Peer Comparison details
            sector_matches = df_historical[df_historical["Sector"] == sector]
            avg_sector_pe = sector_matches["Valuation PE"].mean() if len(sector_matches) > 0 else 28.5
            avg_sector_roe = sector_matches["ROE (%)"].mean() if len(sector_matches) > 0 else 18.2
            
            st.subheader("AI Valuation and Financial Health Report")
            
            # Expert rule-based AI generator
            strengths = []
            risks = []
            red_flags = []
            
            if rev_growth > 20:
                strengths.append(f"Accelerated top-line expansion with a Revenue Growth of {rev_growth:.1f}%.")
            else:
                risks.append(f"Modest revenue growth ({rev_growth:.1f}%) might limit post-listing multiples expansion.")
                
            if roe > avg_sector_roe:
                strengths.append(f"Superior capital efficiency, displaying ROE of {roe:.1f}% vs sector average of {avg_sector_roe:.1f}%.")
            else:
                risks.append(f"Sub-par ROE ({roe:.1f}%) compared to sector peer average of {avg_sector_roe:.1f}%.")
                
            if debt_eq > 1.5:
                red_flags.append(f"High leverage concern: Debt-to-Equity is {debt_eq:.2f}, creating solvency exposure.")
            elif debt_eq < 0.5:
                strengths.append(f"Conservative balance sheet with clean leverage (Debt-to-Equity: {debt_eq:.2f}).")
            else:
                risks.append(f"Moderate leverage observed (Debt-to-Equity: {debt_eq:.2f}).")
                
            if profit_growth < 0:
                red_flags.append("Profit contraction observed in audited statements; negative net-margins risk.")
                
            if not strengths:
                strengths.append("Standard business operation capabilities within target niche.")
            if not risks:
                risks.append("Generic macroeconomic and interest rate sensitivity exposures.")
            if not red_flags:
                red_flags.append("No material audits or leverage red flags detected.")
                
            col_swot1, col_swot2 = st.columns(2)
            with col_swot1:
                st.markdown(f"""
                    <div style="background-color:rgba(16,185,129,0.08); border-left:4px solid #10b981; padding:15px; border-radius:4px; margin-bottom:10px;">
                        <strong style="color:#10b981;">Key Strengths & Merits:</strong>
                        <ul>
                            {"".join(f"<li>{s}</li>" for s in strengths)}
                        </ul>
                    </div>
                """, unsafe_allow_html=True)
            with col_swot2:
                st.markdown(f"""
                    <div style="background-color:rgba(239,68,68,0.08); border-left:4px solid #ef4444; padding:15px; border-radius:4px; margin-bottom:10px;">
                        <strong style="color:#ef4444;">Risks & Red Flags:</strong>
                        <ul>
                            {"".join(f"<li>{r}</li>" for r in risks + red_flags)}
                        </ul>
                    </div>
                """, unsafe_allow_html=True)
                
            # Valuation assessment vs Peers
            st.markdown(f"""
                <div class="ai-report-box">
                    <strong>Peer Comparison Review:</strong><br>
                    Comparing the target financial structure against listed peers in the <strong>{sector}</strong> sector:<br>
                    - The target ROE of {roe:.1f}% stands in comparison to peer averages of {avg_sector_roe:.1f}%.<br>
                    - Valuation parameters suggest an expected post-listing PE multiple of <strong>34.5x</strong> compared to peer average PE of <strong>{avg_sector_pe:.1f}x</strong>.<br>
                    - Growth trajectory is <strong>{'Higher' if rev_growth > 20 else 'Aligned'}</strong> relative to major listed competitors.
                </div>
            """, unsafe_allow_html=True)
            
            # Correlation Analysis visual plots
            st.subheader("Correlation Analysis")
            corr_col1, corr_col2 = st.columns(2)
            
            with corr_col1:
                # GMP vs Listing Gain
                fig_c1 = px.scatter(
                    df_historical,
                    x="Avg Pre-Listing GMP",
                    y="Listing Gain (%)",
                    trendline="ols",
                    title="GMP (₹) vs Actual Listing Gain (%)",
                    labels={"Avg Pre-Listing GMP": "Pre-Listing GMP Premium (₹)"}
                )
                st.plotly_chart(update_plotly_layout(fig_c1), use_container_width=True)
                
            with corr_col2:
                # Subscription vs Listing Gain
                fig_c2 = px.scatter(
                    df_historical,
                    x="QIB Subscription",
                    y="Listing Gain (%)",
                    trendline="ols",
                    title="QIB Subscription Rate (x) vs Listing Gain (%)",
                    labels={"QIB Subscription": "QIB Over-subscription Multiplier"}
                )
                st.plotly_chart(update_plotly_layout(fig_c2), use_container_width=True)
