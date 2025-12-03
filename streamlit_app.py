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

st.title("Canada vs OECD – Inflation and Household Consumption (2020–2024)")

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

# Colors
CAN_COLOR = "#CC0000"  # Canada red
OECD_COLOR = "#7EC8E3"  # light blue

CLUSTER_COLORS = {
    "0": "#AEC6CF",   # pastel blue
    "1": "#FFB3BA",   # pastel red
    "2": "#B5EAD7",   # pastel green
    "3": "#FFDAC1"    # pastel peach
}

# ============================================
# 4. Sidebar – navigation & filters
# ============================================
st.sidebar.header("Navigation")

section = st.sidebar.radio(
    "Go to section:",
    (
        "1. Inflation (CPI) – Canada vs OECD",
        "2. Expenditure Share & Growth – Canada vs OECD",
        "3. Clustering Results"
    )
)

st.sidebar.markdown("---")
st.sidebar.header("Filters")

available_cats = sorted(canada_oecd["category"].dropna().unique())

selected_categories = st.sidebar.multiselect(
    "Select COICOP categories",
    options=available_cats,
    format_func=lambda x: CATEGORY_LABELS.get(x, x),
)

min_year = int(canada_oecd["year"].min())
max_year = int(canada_oecd["year"].max())

year_range = st.sidebar.slider(
    "Select year range",
    min_year,
    max_year,
    (min_year, max_year),
)

if not selected_categories:
    st.warning("Please select at least one COICOP category in the sidebar.")
    st.stop()

# Filter once and reuse
df_filtered = canada_oecd[
    (canada_oecd["category"].isin(selected_categories)) &
    (canada_oecd["year"] >= year_range[0]) &
    (canada_oecd["year"] <= year_range[1])
].copy()

# ============================================
# 5. Overview box (always visible)
# ============================================
st.subheader("Dataset Overview")

num_countries = clusters["country"].nunique()

st.info(
    f"""
**Countries analyzed:** {num_countries}  
**Data source:** OECD (Organisation for Economic Co-operation and Development).  

The OECD is a group of countries that collaborate on economic policy, stability, and development.  
This dashboard compares Canada's inflation and household spending patterns with the OECD average and peer countries.
"""
)

st.markdown("---")

# ============================================
# 6. Section 1 – Inflation (CPI) Canada vs OECD
# ============================================
if section.startswith("1."):
    st.header("1. Inflation (CPI) – Canada vs OECD")

    for cat in selected_categories:
        cat_name = CATEGORY_LABELS.get(cat, cat)
        df_cat = df_filtered[df_filtered["category"] == cat].copy()

        if df_cat.empty:
            st.warning(f"No CPI data available for {cat_name} in the selected year range.")
            continue

        # Line chart – CPI Canada vs OECD
        fig = px.line(
            df_cat,
            x="year",
            y=["can_cpi", "oecd_cpi"],
            labels={"value": "CPI annual average (%)", "year": "Year", "variable": ""},
            title=f"CPI – Canada vs OECD average ({cat_name})",
        )

        # Force colors
        for trace in fig.data:
            if trace.name == "can_cpi":
                trace.update(line=dict(color=CAN_COLOR))
                trace.name = "Canada"
            elif trace.name == "oecd_cpi":
                trace.update(line=dict(color=OECD_COLOR))
                trace.name = "OECD average"

        st.plotly_chart(fig, use_container_width=True)

        # Simple analytical insight using latest year in range
        latest_year = int(df_cat["year"].max())
        latest_row = df_cat[df_cat["year"] == latest_year].iloc[0]
        can_val = latest_row["can_cpi"]
        oecd_val = latest_row["oecd_cpi"]

        if pd.isna(can_val) or pd.isna(oecd_val):
            relation = "cannot be directly compared due to missing data"
            insight_text = f"In {latest_year}, CPI for {cat_name} {relation}."
        else:
            if can_val > oecd_val:
                relation = "above"
            elif can_val < oecd_val:
                relation = "below"
            else:
                relation = "very close to"

            insight_text = (
                f"In **{latest_year}**, Canada's CPI for **{cat_name}** is "
                f"**{relation}** the OECD average "
                f"({can_val:.1f}% vs {oecd_val:.1f}%)."
            )

        st.markdown(f"**Key finding – {cat_name}:** {insight_text}")

    st.info(
        "Overall, these CPI patterns highlight where inflationary pressure in Canada is "
        "stronger or weaker than the OECD benchmark for the selected spending categories."
    )

# ============================================
# 7. Section 2 – Expenditure share & growth
# ============================================
elif section.startswith("2."):
    st.header("2. Expenditure Share and Growth – Canada vs OECD")

    latest_year = year_range[1]
    df_last = df_filtered[df_filtered["year"] == latest_year].copy()

    if df_last.empty:
        st.warning("No expenditure data available for the selected year range.")
    else:
        # ---------- Expenditure share ----------
        share_rows = []
        for _, row in df_last.iterrows():
            cat = row["category"]
            cat_name = CATEGORY_LABELS.get(cat, cat)

            share_rows.append(
                {"category": cat_name, "group": "Canada", "value": row["can_exp_share"]}
            )
            share_rows.append(
                {"category": cat_name, "group": "OECD average", "value": row["oecd_exp_share"]}
            )

        df_share = pd.DataFrame(share_rows)

        fig_share = px.bar(
            df_share,
            x="category",
            y="value",
            color="group",
            barmode="group",
            labels={"value": "Expenditure share of total", "category": "COICOP category"},
            title=f"Expenditure share in {latest_year} – Canada vs OECD",
            color_discrete_map={"Canada": CAN_COLOR, "OECD average": OECD_COLOR},
        )
        st.plotly_chart(fig_share, use_container_width=True)

        # ---------- Expenditure growth ----------
        growth_rows = []
        for _, row in df_last.iterrows():
            cat = row["category"]
            cat_name = CATEGORY_LABELS.get(cat, cat)

            growth_rows.append(
                {"category": cat_name, "group": "Canada", "value": row["can_exp_growth"]}
            )
            growth_rows.append(
                {"category": cat_name, "group": "OECD average", "value": row["oecd_exp_growth"]}
            )

        df_growth = pd.DataFrame(growth_rows)

        fig_growth = px.bar(
            df_growth,
            x="category",
            y="value",
            color="group",
            barmode="group",
            labels={"value": "Year-over-year expenditure growth", "category": "COICOP category"},
            title=f"Expenditure growth in {latest_year} – Canada vs OECD",
            color_discrete_map={"Canada": CAN_COLOR, "OECD average": OECD_COLOR},
        )
        st.plotly_chart(fig_growth, use_container_width=True)

        # ---------- Text insights ----------
        lines = []
        for _, row in df_last.iterrows():
            cat = row["category"]
            cat_name = CATEGORY_LABELS.get(cat, cat)

            share_can = row["can_exp_share"]
            share_oecd = row["oecd_exp_share"]
            growth_can = row["can_exp_growth"]
            growth_oecd = row["oecd_exp_growth"]

            # Relation for share
            if pd.isna(share_can) or pd.isna(share_oecd):
                share_rel = "cannot be compared due to missing data"
            elif share_can > share_oecd:
                share_rel = "a **higher expenditure share** than the OECD average"
            elif share_can < share_oecd:
                share_rel = "a **lower expenditure share** than the OECD average"
            else:
                share_rel = "a **similar expenditure share** to the OECD average"

            # Relation for growth
            if pd.isna(growth_can) or pd.isna(growth_oecd):
                growth_rel = "growth cannot be compared due to missing data"
            elif growth_can > growth_oecd:
                growth_rel = "spending is growing **faster** than the OECD average"
            elif growth_can < growth_oecd:
                growth_rel = "spending is growing **slower** than the OECD average"
            else:
                growth_rel = "spending is growing at a **similar pace** to the OECD average"

            bullet = (
                f"- In **{cat_name}**, Canada shows {share_rel}, and "
                f"{growth_rel} in {latest_year}."
            )
            lines.append(bullet)

        if lines:
            summary_md = "**Key Findings (latest year)**\n\n" + "\n".join(lines)
            st.markdown(summary_md)

        st.info(
            "These results show how strongly each category contributes to household budgets "
            "in Canada compared with the OECD, and whether Canadian spending is expanding "
            "or contracting faster than the international benchmark."
        )

# ============================================
# 8. Section 3 – Clustering results
# ============================================
elif section.startswith("3."):
    st.header("3. Clustering Results – Countries Similar to Canada")

    # Prepare cluster info
    clusters["cluster_str"] = clusters["cluster"].astype(str)

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
        labels={"cluster": "Cluster", "num_countries": "Number of countries", "cluster_str": ""},
        title="Number of countries per cluster",
    )
    st.plotly_chart(fig_clusters, use_container_width=True)

    # Canada cluster + peers
    canada_cluster_row = clusters[clusters["country"] == "CAN"]
    if not canada_cluster_row.empty:
        canada_cluster = int(canada_cluster_row["cluster"].iloc[0])
        peers = clusters[clusters["cluster"] == canada_cluster]["country"].tolist()

        st.markdown(
            f"Canada belongs to **cluster {canada_cluster}**, "
            f"together with **{len(peers)}** countries."
        )

        st.markdown("**Countries in the same cluster as Canada:**")
        st.write(", ".join(sorted(peers)))
    else:
        st.warning("Canada is not present in the clustering results.")

    st.subheader("Cluster Membership by Country")
    st.dataframe(clusters.sort_values("cluster").reset_index(drop=True))

    st.info(
        "Clusters group countries with similar inflation and expenditure patterns for the "
        "selected COICOP categories between 2020 and 2024. Countries in the same cluster "
        "as Canada can be seen as its closest peers in terms of recent inflation and "
        "household consumption dynamics."
    )

# ============================================
# 9. Footer
# ============================================
st.markdown("---")
st.markdown("© 2025 – OECD Inflation Study • Streamlit Dashboard")
