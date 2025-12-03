import streamlit as st
import pandas as pd
import plotly.express as px

# ============================================
# 1. Page config
# ============================================
st.set_page_config(
    page_title="OECD Inflation Dashboard",
    layout="wide"
)

st.title("OECD Inflation & Household Consumption Dashboard")
st.markdown("This dashboard analyzes how inflation has shaped spending patterns in Canada compared to OECD countries (2020–2024).")

# ============================================
# 2. Load data
# ============================================
@st.cache_data
def load_data():
    df_canada = pd.read_csv("canada_vs_oecd_timeseries.csv")
    df_clusters = pd.read_csv("cluster_results.csv")
    return df_canada, df_clusters

canada_oecd, clusters = load_data()

# ============================================
# 3. COICOP category dictionary
# ============================================
CATEGORY_LABELS = {
    "CP01": "Food & Non-Alcoholic Beverages",
    "CP041": "Actual Rentals for Housing",
}

# Pastel-friendly cluster colors
CLUSTER_COLORS = {
    "0": "#AEC6CF",   # pastel blue
    "1": "#FFB3BA",   # pastel red
    "2": "#B5EAD7",   # pastel green
    "3": "#FFDAC1"    # pastel peach
}

# Canada color (red)
CAN_COLOR = "#CC0000"

# ============================================
# Sidebar filters
# ============================================
st.sidebar.header("Filters")

available_cats = sorted(canada_oecd["category"].dropna().unique())
selected_categories = st.sidebar.multiselect(
    "Select COICOP categories",
    options=available_cats,
    format_func=lambda x: CATEGORY_LABELS.get(x, x),
)

if not selected_categories:
    st.warning("Please select at least one COICOP category.")
    st.stop()

# ============================================
# 4. Section: Canada vs OECD summary box
# ============================================
st.subheader("Dataset Overview")

num_countries = clusters["country"].nunique()

st.info(
    f"### OECD countries included: **{num_countries}**  
    Data covers **2020–2024**, using CPI growth and expenditure shares from the OECD COICOP database."
)

# ============================================
# 5. Plot: Canada vs OECD Time Series
# ============================================
st.header("1. Inflation Trends: Canada vs OECD")

filtered = canada_oecd[canada_oecd["category"].isin(selected_categories)]

for cat in selected_categories:
    cat_name = CATEGORY_LABELS.get(cat, cat)

    df_cat = filtered[filtered["category"] == cat]

    fig = px.line(
        df_cat,
        x="year",
        y=["can_cpi", "oecd_cpi"],
        labels={"value": "CPI Annual Avg (%)", "year": "Year"},
        title=f"CPI Trend: {cat_name}"
    )

    # Force Canada red
    fig.for_each_trace(
        lambda t: t.update(line=dict(color=CAN_COLOR)) if "can_cpi" in t.name else None
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        f"**Insight – {cat_name}:**  
        Compare the CPI growth pattern of Canada against the OECD average. Look for years with higher divergence to understand inflation pressure on households."
    )

# ============================================
# 6. Section: Clustering Results
# ============================================
st.header("2. Country Clustering Based on Inflation & Spending Patterns")

# Convert cluster to string for color mapping
clusters["cluster_str"] = clusters["cluster"].astype(str)

# Bar chart of cluster sizes
cluster_counts = (
    clusters.groupby("cluster")
    .size()
    .reset_index(name="num_countries")
    .sort_values("cluster")
)
cluster_counts["cluster_str"] = cluster_counts["cluster"].astype(str)

fig_clusters = px.bar(
    cluster_counts,
    x="cluster",
    y="num_countries",
    color="cluster_str",
    color_discrete_map=CLUSTER_COLORS,
    labels={"cluster": "Cluster", "num_countries": "Number of Countries"},
    title="Number of Countries per Cluster"
)
st.plotly_chart(fig_clusters, use_container_width=True)

st.markdown(
    "**Insight:**  
    Clusters group countries with similar inflation patterns and expenditure structures between 2020–2024.  
    Canada belongs to one of the main clusters with several European economies."
)

# ============================================
# 7. Table showing cluster membership
# ============================================
st.subheader("Cluster Membership by Country")
st.dataframe(clusters.sort_values("cluster").reset_index(drop=True))

# ============================================
# 8. End message
# ============================================
st.markdown("---")
st.markdown("© 2025 – OECD Inflation Study • Streamlit Dashboard")
