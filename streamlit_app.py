import streamlit as st
import pandas as pd
import plotly.express as px

# ============================================
# Page config
# ============================================
st.set_page_config(
    page_title="Canada vs OECD – Inflation & Consumption",
    layout="wide"
)

# ============================================
# COICOP labels (code -> human-readable name)
# ============================================
COICOP_LABELS = {
    "CP01": "Food & Non-Alcoholic Beverages",
    "CP02": "Alcohol & Tobacco",
    "CP03": "Clothing & Footwear",
    "CP04": "Housing, Water, Electricity & Gas",
    "CP041": "Actual Rentals for Housing",
    "CP042": "Imputed Rentals for Housing",
    "CP043": "Maintenance & Repair of Dwellings",
    "CP044": "Water Supply & Misc. Services",
    "CP045": "Electricity, Gas & Other Fuels",
    "CP05": "Furnishings & Household Equipment",
    "CP06": "Health",
    "CP07": "Transport",
    "CP08": "Communication",
    "CP09": "Recreation & Culture",
    "CP10": "Education",
    "CP11": "Restaurants & Hotels",
    "CP12": "Miscellaneous Goods & Services"
}

# Colors
CANADA_RED = "#FF0000"
OECD_BLUE = "#89CFF0"   # pastel blue
CLUSTER_COLORS = {
    0: "#FF6F61",   # pastel red
    1: "#6EC6FF",   # pastel blue
    2: "#98FB98",   # pastel green
    3: "#FFD580"    # pastel yellow
}

# ============================================
# Data loading
# ============================================
@st.cache_data
def load_data():
    clusters = pd.read_csv("cluster_results.csv")
    ts = pd.read_csv("canada_vs_oecd_timeseries.csv")

    # Ensure expected columns exist
    expected_ts_cols = {
        "year", "category",
        "can_cpi", "oecd_cpi",
        "can_exp_share", "oecd_exp_share",
        "can_exp_growth", "oecd_exp_growth"
    }
    missing = expected_ts_cols - set(ts.columns)
    if missing:
        st.error(f"Missing columns in canada_vs_oecd_timeseries.csv: {missing}")
        st.stop()

    # Add readable category labels
    ts["category_label"] = ts["category"].map(COICOP_LABELS).fillna(ts["category"])

    return clusters, ts


clusters, ts = load_data()

# Basic metadata
num_countries = clusters["country"].nunique()
years = sorted(ts["year"].unique())
all_categories = sorted(ts["category"].unique())

# ============================================
# Sidebar – navigation and filters
# ============================================
st.sidebar.title("Navigation")
section = st.sidebar.radio(
    "Go to section:",
    [
        "1. Inflation (CPI) – Canada vs OECD",
        "2. Expenditure Share & Growth",
        "3. Clustering Results"
    ]
)

# Global filters for sections 1 & 2
st.sidebar.markdown("---")
st.sidebar.markdown("### Filters")

selected_categories = st.sidebar.multiselect(
    "Select COICOP categories",
    options=all_categories,
    format_func=lambda x: COICOP_LABELS.get(x, x),
    default=["CP01"] if "CP01" in all_categories else all_categories[:1]
)

year_min = int(min(years))
year_max = int(max(years))

year_range = st.sidebar.slider(
    "Select year range",
    min_value=year_min,
    max_value=year_max,
    value=(max(2020, year_min), year_max)
)

ts_filtered = ts[
    (ts["category"].isin(selected_categories)) &
    (ts["year"].between(year_range[0], year_range[1]))
].copy()

# ============================================
# Overview box
# ============================================
st.title("Canada vs OECD – Inflation and Household Consumption (2020–2024)")

st.success(
    f"**Countries analyzed:** {num_countries}  \n"
    "**Data source:** OECD (Organisation for Economic Co-operation and Development).  \n"
    "The OECD is a group of 38 countries that collaborate on economic policy, "
    "stability, and development. This dashboard compares Canada’s inflation and "
    "household spending patterns with the OECD average and peer countries."
)

st.markdown("---")

# Helper: simple label function for selected categories
def selected_category_labels():
    labs = [COICOP_LABELS.get(c, c) for c in selected_categories]
    return ", ".join(labs)


# ============================================
# Section 1 – Inflation (CPI) Canada vs OECD
# ============================================
if section.startswith("1."):
    st.header("1. Inflation (CPI) – Canada vs OECD")

    if ts_filtered.empty:
        st.info("No data available for the selected categories and year range.")
    else:
        # Prepare data for line chart
        df = ts_filtered.copy()

        plot_df = df.melt(
            id_vars=["year", "category_label"],
            value_vars=["can_cpi", "oecd_cpi"],
            var_name="series",
            value_name="cpi"
        )

        series_names = {
            "can_cpi": "Canada",
            "oecd_cpi": "OECD average"
        }
        plot_df["series"] = plot_df["series"].map(series_names)

        # Line chart – facet by category if more than one
        if len(selected_categories) > 1:
            fig_cpi = px.line(
                plot_df,
                x="year",
                y="cpi",
                color="series",
                facet_col="category_label",
                facet_col_wrap=2,
                labels={
                    "year": "Year",
                    "cpi": "Annual CPI (%)",
                    "series": ""
                },
                title=f"CPI – Canada vs OECD average ({selected_category_labels()})"
            )
        else:
            fig_cpi = px.line(
                plot_df,
                x="year",
                y="cpi",
                color="series",
                labels={
                    "year": "Year",
                    "cpi": "Annual CPI (%)",
                    "series": ""
                },
                title=f"CPI – Canada vs OECD average ({selected_category_labels()})"
            )

        fig_cpi.update_traces(line=dict(width=3))
        fig_cpi.for_each_trace(
            lambda t: t.update(line=dict(color=CANADA_RED))
            if t.name == "Canada"
            else t.update(line=dict(color=OECD_BLUE, dash="dash"))
        )

        st.plotly_chart(fig_cpi, use_container_width=True)

        # -------- Key findings (simple automatic bullets) --------
        st.subheader("Key Findings")

        latest_year = plot_df["year"].max()
        summary_rows = df[df["year"] == latest_year]

        bullets = []
        for _, row in summary_rows.iterrows():
            label = row["category_label"]
            if pd.notna(row["can_cpi"]) and pd.notna(row["oecd_cpi"]):
                if row["can_cpi"] > row["oecd_cpi"]:
                    comp = "above"
                elif row["can_cpi"] < row["oecd_cpi"]:
                    comp = "below"
                else:
                    comp = "similar to"
                bullets.append(
                    f"- In **{label}**, Canada’s CPI in {latest_year} is **{comp}** the OECD average "
                    f"({row['can_cpi']:.1f}% vs {row['oecd_cpi']:.1f}%)."
                )

        if bullets:
            st.markdown("\n".join(bullets))
        else:
            st.markdown("- No clear CPI comparison available for the latest year.")

        # -------- Short conclusion --------
        st.info(
            "Overall, these CPI patterns highlight where inflationary pressure in Canada is "
            "stronger or weaker than the OECD benchmark for the selected spending categories."
        )


# ============================================
# Section 2 – Expenditure share & growth
# ============================================
elif section.startswith("2."):
    st.header("2. Expenditure Share and Growth – Canada vs OECD")

    if ts_filtered.empty:
        st.info("No data available for the selected categories and year range.")
    else:
        df = ts_filtered.copy()
        latest_year = df["year"].max()
        latest = df[df["year"] == latest_year].copy()

        # Ensure we have at least one row
        if latest.empty:
            st.info("No data available for the latest year in the selected range.")
        else:
            # -------- Expenditure share chart --------
            share_df = latest.melt(
                id_vars=["category_label"],
                value_vars=["can_exp_share", "oecd_exp_share"],
                var_name="series",
                value_name="share"
            )
            share_map = {
                "can_exp_share": "Canada",
                "oecd_exp_share": "OECD average"
            }
            share_df["series"] = share_df["series"].map(share_map)

            fig_share = px.bar(
                share_df,
                x="category_label",
                y="share",
                color="series",
                barmode="group",
                labels={
                    "category_label": "COICOP category",
                    "share": "Expenditure share of total",
                    "series": ""
                },
                title=f"Expenditure share in {latest_year} – Canada vs OECD"
            )

            fig_share.for_each_trace(
                lambda t: t.update(marker_color=CANADA_RED)
                if t.name == "Canada"
                else t.update(marker_color=OECD_BLUE)
            )

            st.plotly_chart(fig_share, use_container_width=True)

            # -------- Expenditure growth chart --------
            growth_df = latest.melt(
                id_vars=["category_label"],
                value_vars=["can_exp_growth", "oecd_exp_growth"],
                var_name="series",
                value_name="growth"
            )
            growth_map = {
                "can_exp_growth": "Canada",
                "oecd_exp_growth": "OECD average"
            }
            growth_df["series"] = growth_df["series"].map(growth_map)

            fig_growth = px.bar(
                growth_df,
                x="category_label",
                y="growth",
                color="series",
                barmode="group",
                labels={
                    "category_label": "COICOP category",
                    "growth": "Year-over-year expenditure growth",
                    "series": ""
                },
                title=f"Expenditure growth in {latest_year} – Canada vs OECD"
            )

            fig_growth.for_each_trace(
                lambda t: t.update(marker_color=CANADA_RED)
                if t.name == "Canada"
                else t.update(marker_color=OECD_BLUE)
            )

            st.plotly_chart(fig_growth, use_container_width=True)

            # -------- Key findings --------
            st.subheader("Key Findings")

            bullets = []
            for _, row in latest.iterrows():
                label = row["category_label"]

                # Share comparison
                if pd.notna(row["can_exp_share"]) and pd.notna(row["oecd_exp_share"]):
                    if row["can_exp_share"] > row["oecd_exp_share"]:
                        comp_share = "higher"
                    elif row["can_exp_share"] < row["oecd_exp_share"]:
                        comp_share = "lower"
                    else:
                        comp_share = "similar"
                    bullets.append(
                        f"- In **{label}**, Canada’s expenditure share is **{comp_share}** "
                        f"than the OECD average."
                    )

                # Growth comparison
                if pd.notna(row["can_exp_growth"]) and pd.notna(row["oecd_exp_growth"]):
                    if row["can_exp_growth"] > row["oecd_exp_growth"]:
                        comp_growth = "faster"
                    elif row["can_exp_growth"] < row["oecd_exp_growth"]:
                        comp_growth = "slower"
                    else:
                        comp_growth = "similar"
                    bullets.append(
                        f"  Canada’s spending growth in {label} is **{comp_growth}** "
                        f"than the OECD average in {latest_year}."
                    )

            if bullets:
                st.markdown("\n".join(bullets))
            else:
                st.markdown("- No clear differences in expenditure share or growth were found.")

            # -------- Short conclusion --------
            st.info(
                "These results show how strongly each category contributes to household budgets "
                "in Canada compared with the OECD, and whether Canadian spending is expanding or "
                "contracting faster than the international benchmark."
            )


# ============================================
# Section 3 – Clustering results
# ============================================
elif section.startswith("3."):
    st.header("3. Clustering Results – Countries Similar to Canada")

    if clusters.empty:
        st.info("No clustering results available.")
    else:
        # Cluster counts
        cluster_counts = (
		clusters
    		.groupby("cluster")
    		.size()
    		.reset_index(name="num_countries")
    		.sort_values("cluster")
	)

	col1, col2 = st.columns(2)

	with col1:
    		cluster_counts["cluster_str"] = cluster_counts["cluster"].astype(str)

    		fig_clusters = px.bar(
			cluster_counts,
        		x="cluster",
       	 		y="num_countries",
        		color="cluster_str",
        		color_discrete_map={
            			str(k): v for k, v in CLUSTER_COLORS.items()
        		},
        		labels={
            			"cluster": "Cluster",
            			"num_countries": "Number of countries",
            			"cluster_str": ""
        		},
        		title="Number of countries per cluster"
    		)
    		st.plotly_chart(fig_clusters, use_container_width=True)

        with col2:
            st.markdown("**Countries and their clusters**")
            st.dataframe(
                clusters.sort_values(["cluster", "country"]).reset_index(drop=True),
                use_container_width=True
            )

        # Canada’s cluster
        st.markdown("---")
        st.subheader("Canada’s Position")

        can_row = clusters[clusters["country"] == "CAN"]
        if not can_row.empty:
            can_cluster = int(can_row["cluster"].iloc[0])
            st.write(f"Canada belongs to **cluster {can_cluster}**.")

            peers = (
                clusters[
                    (clusters["cluster"] == can_cluster) &
                    (clusters["country"] != "CAN")
                ]["country"]
                .tolist()
            )

            if peers:
                st.markdown(
                    "Countries in the same cluster as Canada include: " +
                    ", ".join(sorted(peers))
                )
        else:
            st.write("Canada is not present in the clustering results.")

        # Key findings & conclusion
        st.subheader("Key Findings")
        st.markdown(
            "- Clusters group countries with similar inflation dynamics and spending patterns "
            "across COICOP categories.\n"
            "- Canada is grouped with advanced economies that show comparable inflation paths "
            "and expenditure structures since 2020."
        )

        st.info(
            "The clustering analysis provides a high-level view of which OECD countries share "
            "similar inflation and consumption profiles with Canada, complementing the "
            "category-level comparisons in the previous sections."
        )
