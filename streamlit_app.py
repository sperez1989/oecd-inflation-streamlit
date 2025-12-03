import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Canada vs OECD – Inflation and Household Consumption",
    layout="wide"
)

@st.cache_data
def load_data():
    clusters = pd.read_csv("cluster_results.csv")
    ts = pd.read_csv("canada_vs_oecd_timeseries.csv")
    return clusters, ts

clusters, ts = load_data()

st.title("Canada vs OECD – Inflation and Household Consumption (2020–2024)")

st.markdown(
    "This dashboard compares Canada’s inflation and household consumption patterns "
    "with other OECD countries, using CPI and COICOP-based expenditure data."
)

st.markdown("---")

categories = sorted(ts["category"].dropna().unique().tolist())
years = sorted(ts["year"].dropna().unique().tolist())

col_filter1, col_filter2 = st.columns(2)
with col_filter1:
    selected_category = st.selectbox("Select COICOP category", categories)
with col_filter2:
    year_range = st.slider(
        "Select year range",
        min_value=int(min(years)),
        max_value=int(max(years)),
        value=(2020, int(max(years)))
    )

ts_filt = ts[
    (ts["category"] == selected_category) &
    (ts["year"].between(year_range[0], year_range[1]))
]

st.subheader("Time series: Canada vs OECD average (CPI)")

if ts_filt.empty:
    st.info("No data available for this category and year range.")
else:
    fig_cpi = px.line(
        ts_filt,
        x="year",
        y=["can_cpi", "oecd_cpi"],
        labels={"value": "Annual CPI (%)", "year": "Year", "variable": "Series"},
        title=f"Annual CPI – Canada vs OECD average ({selected_category})"
    )
    st.plotly_chart(fig_cpi, use_container_width=True)

st.subheader("Canada vs OECD – Expenditure share and growth")

if not ts_filt.empty:
    latest_year = ts_filt["year"].max()
    latest = ts_filt[ts_filt["year"] == latest_year].iloc[0]

    col1, col2 = st.columns(2)

    with col1:
        fig_share = px.bar(
            x=["Canada", "OECD average"],
            y=[latest["can_exp_share"], latest["oecd_exp_share"]],
            labels={"x": "", "y": "Expenditure share"},
            title=f"Expenditure share in {latest_year} ({selected_category})"
        )
        st.plotly_chart(fig_share, use_container_width=True)

    with col2:
        fig_growth = px.bar(
            x=["Canada", "OECD average"],
            y=[latest["can_exp_growth"], latest["oecd_exp_growth"]],
            labels={"x": "", "y": "YoY expenditure growth"},
            title=f"Expenditure growth in {latest_year} ({selected_category})"
        )
        st.plotly_chart(fig_growth, use_container_width=True)

st.markdown("---")
st.subheader("Cluster assignment by country")

cluster_counts = clusters["cluster"].value_counts().reset_index()
cluster_counts.columns = ["cluster", "num_countries"]

col_a, col_b = st.columns(2)

with col_a:
    fig_clusters = px.bar(
        cluster_counts,
        x="cluster",
        y="num_countries",
        title="Number of countries per cluster",
        labels={"cluster": "Cluster", "num_countries": "Countries"}
    )
    st.plotly_chart(fig_clusters, use_container_width=True)

with col_b:
    st.markdown("Countries and their clusters")
    st.dataframe(clusters.sort_values(["cluster", "country"]), use_container_width=True)

st.markdown("**Canada’s cluster:**")
can_row = clusters[clusters["country"] == "CAN"]
if not can_row.empty:
    st.write(f"Canada belongs to cluster: `{int(can_row['cluster'].iloc[0])}`")
else:
    st.write("Canada not found in cluster_results.csv")
