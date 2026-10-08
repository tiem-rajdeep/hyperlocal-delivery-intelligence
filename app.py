"""
app.py
------
Hyperlocal Delivery Intelligence – Streamlit Dashboard

A standalone delivery analytics dashboard powered directly by CSV data.
Includes 5 analytical views:
  1. Overview       – Active filter summary, KPI metrics, and high-level distribution
  2. Rider Perf.    – Leaderboard table, speed vs. rating analysis, and qualification filter
  3. Zone Analysis  – City/zone volume breakdown and SLA status classification
  4. Peak Hours     – Order demand and delivery time heatmaps across hours and weekdays
  5. Operations     – Daily order volume trends, weather/traffic impact, and vehicle performance

Run locally:
    streamlit run app.py
"""

import datetime
import html
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Hyperlocal Delivery Intelligence",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Color palette (consistent indigo/purple theme across all charts) ────────
COLORS = {
    "primary":       "#6366F1",   # indigo
    "primary_dark":  "#4F46E5",   # deep indigo
    "primary_light": "#818CF8",   # light indigo
    "purple":        "#8B5CF6",   # violet/purple
    "success":       "#22C55E",   # green
    "warning":       "#F59E0B",   # amber
    "danger":        "#EF4444",   # red
    "neutral":       "#94A3B8",   # slate
    "bg":            "#0F172A",   # dark navy
    "card":          "#1E293B",   # card background
}

PALETTE = [
    "#6366F1", "#8B5CF6", "#A78BFA", "#38BDF8",
    "#22C55E", "#F59E0B", "#F472B6", "#34D399",
]

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Dark theme overrides */
    .stApp { background-color: #0F172A; }
    section[data-testid="stSidebar"] { background-color: #1E293B; }

    /* KPI card style with uniform height */
    .kpi-card {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1rem 0.75rem;
        text-align: center;
        margin-bottom: 0.5rem;
        min-height: 135px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        box-sizing: border-box;
    }
    .kpi-label {
        font-size: 0.74rem;
        font-weight: 600;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        white-space: nowrap;
        margin-bottom: 0.35rem;
    }
    .kpi-value {
        font-size: 1.75rem;
        font-weight: 700;
        line-height: 1.2;
        margin: 0.1rem 0;
    }
    .kpi-caption {
        font-size: 0.78rem;
        color: #94A3B8;
        margin-top: 0.25rem;
        white-space: nowrap;
    }

    /* Active filter summary pill */
    .filter-summary {
        font-size: 0.85rem;
        color: #CBD5E1;
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 0.55rem 0.9rem;
        margin-bottom: 0.85rem;
    }
    .filter-summary b {
        color: #818CF8;
    }

    /* Tight divider spacing */
    hr {
        margin-top: 0.6rem !important;
        margin-bottom: 0.8rem !important;
        border: none !important;
        border-top: 1px solid #334155 !important;
    }

    /* Insight box */
    .insight-box {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border-left: 4px solid #6366F1;
        border-radius: 0 8px 8px 0;
        padding: 1rem 1.2rem;
        margin-top: 1.5rem;
    }
    .insight-title {
        font-size: 0.9rem;
        font-weight: 600;
        color: #818CF8;
        margin-bottom: 0.5rem;
    }
    .insight-text {
        font-size: 0.85rem;
        color: #CBD5E1;
        line-height: 1.6;
    }

    /* Tab styles & indigo accent */
    div[data-baseweb="tab"] button { font-weight: 600; }
    div[data-baseweb="tab-highlight"] { background-color: #6366F1 !important; }

    /* Form controls & slider accent overrides */
    div[data-baseweb="select"] > div:focus-within {
        border-color: #6366F1 !important;
        box-shadow: 0 0 0 1px #6366F1 !important;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #6366F1 !important;
        box-shadow: 0 0 0 1px #6366F1 !important;
    }
    div[data-testid="stSlider"] div[role="slider"] {
        background-color: #6366F1 !important;
        border-color: #6366F1 !important;
    }
    div[data-testid="stSlider"] [data-baseweb="slider"] > div > div:first-child {
        background-color: #6366F1 !important;
    }

    /* Headings */
    h1, h2, h3 { color: #F1F5F9 !important; }
</style>
""", unsafe_allow_html=True)


# ── Data Loading Helper ───────────────────────────────────────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def load_data() -> pd.DataFrame:
    """
    Load cleaned delivery dataset directly from CSV.
    Uses relative pathing for platform independence.
    """
    csv_path = Path(__file__).resolve().parent / "data" / "cleaned_delivery_data.csv"
    if not csv_path.exists():
        st.error(f"❌ Data file not found at: `{csv_path}`")
        return pd.DataFrame()

    df = pd.read_csv(csv_path)

    # Standardize column types and rename for consistency if needed
    if "time_taken_(min)" in df.columns:
        df["time_taken_min"] = pd.to_numeric(df["time_taken_(min)"], errors="coerce")
    else:
        df["time_taken_min"] = pd.to_numeric(df.get("time_taken_min", 0), errors="coerce")

    df["delivery_person_ratings"] = pd.to_numeric(df["delivery_person_ratings"], errors="coerce")
    df["order_hour"] = pd.to_numeric(df["order_hour"], errors="coerce")
    df["is_on_time"] = df["time_taken_min"] <= 30.0

    return df


# ── UI Helper Functions ───────────────────────────────────────────────────────
def kpi_card(icon: str, label: str, value: str, caption: str = "", value_color: str = "#6366F1") -> str:
    """Return HTML for a KPI card with consistent height, icon, label, value, and context caption."""
    caption_html = f'<div class="kpi-caption">{caption}</div>' if caption else '<div class="kpi-caption">&nbsp;</div>'
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{icon} {label}</div>
        <div class="kpi-value" style="color: {value_color};">{value}</div>
        {caption_html}
    </div>
    """


def insight_box(title: str, text: str) -> None:
    """Render a styled key insight box."""
    st.markdown(f"""
    <div class="insight-box">
        <div class="insight-title">💡 Key Insight — {title}</div>
        <div class="insight-text">{text}</div>
    </div>
    """, unsafe_allow_html=True)


def download_csv(df: pd.DataFrame, filename: str) -> None:
    """Add a download-as-CSV button below a table."""
    st.download_button(
        label="⬇️ Download as CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
    )


def empty_state(msg: str = "No orders match the selected filters.") -> None:
    """Display a clean informative message when filtered dataset is empty."""
    st.info(f"ℹ️ {msg}")


# ── Sidebar Filters ───────────────────────────────────────────────────────────
def render_sidebar(df: pd.DataFrame) -> dict:
    st.sidebar.title("🔍 Filters")
    st.sidebar.caption("Changes apply to all pages")

    filters = {}

    # City / Zone filter
    cities = ["All"]
    if "city" in df.columns and not df.empty:
        cities += sorted(df["city"].dropna().unique().tolist())
    filters["city"] = st.sidebar.selectbox("City / Zone", cities)

    # Rider search filter
    filters["rider_search"] = st.sidebar.text_input(
        "Search Rider ID (prefix)",
        value="",
        placeholder="e.g. DEH",
    )

    # Day period filter
    periods = ["All", "Morning", "Lunch", "Afternoon", "Dinner", "Night"]
    filters["period"] = st.sidebar.selectbox("Day Period", periods)

    # Refresh & timestamp control
    if "last_updated" not in st.session_state:
        st.session_state["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    st.sidebar.markdown("---")
    st.sidebar.caption(f"🕒 Last updated: {st.session_state['last_updated']}")
    if st.sidebar.button("🔄 Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.session_state["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.rerun()

    return filters


# ── Filter Application ────────────────────────────────────────────────────────
def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Apply active sidebar filters to dataset."""
    filtered = df.copy()

    if filters["city"] != "All" and "city" in filtered.columns:
        filtered = filtered[filtered["city"] == filters["city"]]

    if filters["rider_search"].strip() and "delivery_person_id" in filtered.columns:
        prefix = filters["rider_search"].strip()
        filtered = filtered[filtered["delivery_person_id"].str.startswith(prefix, na=False)]

    if filters["period"] != "All" and "day_period" in filtered.columns:
        filtered = filtered[filtered["day_period"] == filters["period"]]

    return filtered


# ── PAGE 1: Overview ──────────────────────────────────────────────────────────
def page_overview(df: pd.DataFrame, filters: dict) -> None:
    st.title("Overview")

    # Active filter summary
    city_label = f"City: {html.escape(str(filters['city']))}" if filters["city"] != "All" else "All cities"
    period_label = f"Period: {html.escape(str(filters['period']))}" if filters["period"] != "All" else "All periods"
    rider_prefix = html.escape(filters["rider_search"].strip())
    rider_label = f"Rider prefix: {rider_prefix}" if rider_prefix else "Rider prefix: none"
    filter_summary = f"Showing: {city_label} · {period_label} · {rider_label}"
    st.markdown(f'<div class="filter-summary">🔍 {filter_summary}</div>', unsafe_allow_html=True)

    if df.empty:
        empty_state("No orders match the selected filters.")
        return

    # Calculate metrics
    total_orders = len(df)
    total_riders = df["delivery_person_id"].nunique() if "delivery_person_id" in df.columns else 0
    avg_delivery = df["time_taken_min"].mean() if "time_taken_min" in df.columns else 0.0
    on_time_pct = (df["is_on_time"].sum() / total_orders * 100.0) if total_orders > 0 else 0.0
    avg_rating = df["delivery_person_ratings"].mean() if "delivery_person_ratings" in df.columns else 0.0

    # Festival orders calculation
    if "festival" in df.columns:
        fest_mask = df["festival"].astype(str).str.strip().str.lower().isin(["yes", "1", "true"])
        festival_orders = fest_mask.sum()
    else:
        festival_orders = 0

    fest_pct = (100.0 * festival_orders / total_orders) if total_orders > 0 else 0.0

    # Dynamic status color for On-Time %
    if on_time_pct < 80.0:
        on_time_color = COLORS["danger"]
    elif on_time_pct <= 90.0:
        on_time_color = COLORS["warning"]
    else:
        on_time_color = COLORS["success"]

    # ── KPI Cards Row ─────────────────────────────────────────────────────────
    cols = st.columns(6)
    cards = [
        ("📦", "TOTAL ORDERS", f"{total_orders:,}", "All recorded orders", COLORS["primary"]),
        ("🛵", "TOTAL RIDERS", f"{total_riders:,}", "Active fleet", COLORS["primary"]),
        ("⏱️", "AVG DELIVERY", f"{avg_delivery:.1f} min", "SLA benchmark ≤ 30 min", COLORS["primary"]),
        ("🎯", "ON-TIME %", f"{on_time_pct:.1f}%", "Target: 85%", on_time_color),
        ("⭐", "AVG RATING", f"{avg_rating:.2f}", "Scale: 1.0 - 5.0", COLORS["primary"]),
        ("🎪", "FESTIVAL ORDERS", f"{festival_orders:,}", f"{fest_pct:.1f}% of orders", COLORS["primary"]),
    ]
    for col, (icon, label, value, caption, color) in zip(cols, cards):
        col.markdown(kpi_card(icon, label, value, caption, color), unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)

    # ── City & Period Distribution ───────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Orders by City")
        if "city" in df.columns and not df["city"].dropna().empty:
            city_counts = df["city"].value_counts().reset_index()
            city_counts.columns = ["City", "Orders"]
            fig = px.pie(
                city_counts,
                names="City",
                values="Orders",
                color_discrete_sequence=PALETTE,
                hole=0.45,
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#CBD5E1",
                margin=dict(t=10, b=10, l=10, r=10),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            empty_state("No city distribution available.")

    with col2:
        st.subheader("Orders by Day Period")
        if "day_period" in df.columns and not df["day_period"].dropna().empty:
            period_order = ["Morning", "Lunch", "Afternoon", "Dinner", "Night"]
            period_agg = (
                df.groupby("day_period")
                .agg(
                    total_orders=("id", "count"),
                    avg_delivery_time=("time_taken_min", "mean"),
                )
                .reset_index()
            )
            period_agg["day_period"] = pd.Categorical(
                period_agg["day_period"], categories=period_order, ordered=True
            )
            period_agg = period_agg.sort_values("day_period")

            fig2 = px.bar(
                period_agg,
                x="day_period",
                y="total_orders",
                color="avg_delivery_time",
                color_continuous_scale="Purples",
                labels={
                    "day_period": "Day Period",
                    "total_orders": "Order Volume (count)",
                    "avg_delivery_time": "Avg Time (min)",
                },
            )
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#CBD5E1",
                margin=dict(t=10, b=10, l=10, r=10),
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            empty_state("No day period data available.")

    # ── Speed Distribution Across Riders ─────────────────────────────────────
    st.subheader("Delivery Speed Distribution Across Riders")
    if "delivery_person_id" in df.columns and "time_taken_min" in df.columns:
        rider_speed = (
            df.groupby("delivery_person_id")["time_taken_min"]
            .mean()
            .reset_index()
            .rename(columns={"time_taken_min": "avg_delivery_time"})
        )
        if not rider_speed.empty:
            fig3 = px.histogram(
                rider_speed,
                x="avg_delivery_time",
                nbins=35,
                color_discrete_sequence=[COLORS["primary"]],
                labels={
                    "avg_delivery_time": "Avg Delivery Time (min)",
                    "count": "Rider Count",
                },
            )
            fig3.update_layout(
                yaxis_title="Rider Count",
                xaxis_title="Avg Delivery Time (min)",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#CBD5E1",
                margin=dict(t=10, b=10, l=10, r=10),
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            empty_state("No rider delivery data available.")
    else:
        empty_state("Rider speed data not found.")

    # ── Key Insight ──────────────────────────────────────────────────────────
    insight_box(
        "Overall Performance",
        f"Out of <b>{total_orders:,}</b> total orders, <b>{on_time_pct:.1f}%</b> were delivered within the "
        f"30-minute SLA benchmark. Fleet average delivery time is <b>{avg_delivery:.1f} min</b>. "
        f"Festival-period orders account for <b>{fest_pct:.1f}%</b> of all volume ({festival_orders:,} orders), "
        f"which typically experience congestion and benefit from proactive rider surge allocation."
    )


# ── PAGE 2: Rider Performance ─────────────────────────────────────────────────
def page_rider_performance(df: pd.DataFrame, filters: dict) -> None:
    st.title("🏍️ Rider Performance")

    if df.empty or "delivery_person_id" not in df.columns:
        empty_state("No orders match the selected filters.")
        return

    # Aggregate by rider
    riders = (
        df.groupby("delivery_person_id")
        .agg(
            total_orders=("id", "count"),
            avg_delivery_time=("time_taken_min", "mean"),
            avg_rating=("delivery_person_ratings", "mean"),
            on_time_pct=("is_on_time", lambda s: (s.sum() / len(s)) * 100.0),
            std_delivery_time=("time_taken_min", "std"),
            primary_city=("city", lambda s: s.mode().iloc[0] if not s.mode().empty else "Unknown"),
            primary_vehicle=("type_of_vehicle", lambda s: s.mode().iloc[0] if not s.mode().empty else "Unknown"),
        )
        .reset_index()
        .rename(columns={"delivery_person_id": "rider_id"})
    )
    riders["std_delivery_time"] = riders["std_delivery_time"].fillna(0.0).round(2)
    riders["avg_delivery_time"] = riders["avg_delivery_time"].round(2)
    riders["avg_rating"] = riders["avg_rating"].round(2)
    riders["on_time_pct"] = riders["on_time_pct"].round(2)
    riders["speed_rank"] = riders["avg_delivery_time"].rank(method="min", ascending=True).astype(int)

    # Leaderboard qualification threshold slider
    min_orders = st.slider(
        "Min orders per rider (leaderboard qualification)",
        min_value=1,
        max_value=100,
        value=20,
        step=1,
        help="Filters the leaderboard and performer charts to riders with at least this many orders.",
    )

    qualified_riders = riders[riders["total_orders"] >= min_orders]

    if qualified_riders.empty:
        empty_state(f"No riders have at least {min_orders} orders under active filters. Try lowering the threshold.")
        return

    # ── Top / Bottom Performers ──────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏆 Top 10 Fastest Riders")
        top10 = qualified_riders.nsmallest(10, "avg_delivery_time")[
            ["rider_id", "total_orders", "avg_delivery_time", "on_time_pct", "avg_rating"]
        ].reset_index(drop=True)
        top10.index += 1

        fig = px.bar(
            top10,
            x="avg_delivery_time",
            y="rider_id",
            orientation="h",
            color="on_time_pct",
            color_continuous_scale="Purples",
            labels={
                "avg_delivery_time": "Avg Delivery Time (min)",
                "rider_id": "Rider ID",
                "on_time_pct": "On-Time %",
            },
        )
        fig.update_layout(
            yaxis={"categoryorder": "total ascending"},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#CBD5E1",
            margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🐢 Bottom 10 Slowest Riders")
        bot10 = qualified_riders.nlargest(10, "avg_delivery_time")[
            ["rider_id", "total_orders", "avg_delivery_time", "on_time_pct", "avg_rating"]
        ].reset_index(drop=True)
        bot10.index += 1

        fig2 = px.bar(
            bot10,
            x="avg_delivery_time",
            y="rider_id",
            orientation="h",
            color="avg_delivery_time",
            color_continuous_scale="Reds",
            labels={
                "avg_delivery_time": "Avg Delivery Time (min)",
                "rider_id": "Rider ID",
            },
        )
        fig2.update_layout(
            yaxis={"categoryorder": "total descending"},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#CBD5E1",
            margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Speed vs Rating Scatterplot ──────────────────────────────────────────
    st.subheader("Speed vs Rating — All Riders")
    fig3 = px.scatter(
        qualified_riders,
        x="avg_delivery_time",
        y="avg_rating",
        size="total_orders",
        color="on_time_pct",
        color_continuous_scale="Purples",
        hover_data=["rider_id", "total_orders", "primary_city", "primary_vehicle"],
        labels={
            "avg_delivery_time": "Avg Delivery Time (min)",
            "avg_rating": "Avg Rider Rating (out of 5)",
            "on_time_pct": "On-Time %",
            "total_orders": "Total Orders",
        },
    )
    fig3.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#CBD5E1",
        margin=dict(t=10, b=10, l=10, r=10),
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ── Full Leaderboard Table ───────────────────────────────────────────────
    st.subheader("Full Rider Leaderboard")
    display_cols = [
        "rider_id", "total_orders", "avg_delivery_time",
        "on_time_pct", "avg_rating", "std_delivery_time",
        "primary_city", "primary_vehicle", "speed_rank"
    ]
    show = qualified_riders[display_cols].sort_values("speed_rank")
    st.dataframe(show, use_container_width=True, height=400)
    download_csv(show, "rider_performance.csv")

    # ── Key Insight ──────────────────────────────────────────────────────────
    if len(qualified_riders) > 0:
        best = qualified_riders.nsmallest(1, "avg_delivery_time").iloc[0]
        worst = qualified_riders.nlargest(1, "avg_delivery_time").iloc[0]
        corr = qualified_riders[["avg_delivery_time", "avg_rating"]].corr().iloc[0, 1] if len(qualified_riders) > 1 else 0
        corr_desc = "faster riders tend to be rated higher" if corr < 0 else "speed and rating appear independent"

        insight_box(
            "Rider Analysis",
            f"The fastest rider is <b>{best['rider_id']}</b> with avg "
            f"<b>{best['avg_delivery_time']:.1f} min</b> ({best['on_time_pct']:.0f}% on-time). "
            f"The slowest qualifying rider is <b>{worst['rider_id']}</b> "
            f"at <b>{worst['avg_delivery_time']:.1f} min</b>. "
            f"Correlation between delivery time and rating: <b>{corr:.2f}</b> ({corr_desc})."
        )


# ── PAGE 3: Zone Analysis ─────────────────────────────────────────────────────
def page_zone_analysis(df: pd.DataFrame, filters: dict) -> None:
    st.title("📍 Zone Analysis")

    if df.empty or "city" not in df.columns:
        empty_state("No orders match the selected filters.")
        return

    # Compute zone aggregations
    zones = (
        df.groupby("city")
        .agg(
            total_orders=("id", "count"),
            avg_delivery_time=("time_taken_min", "mean"),
            on_time_pct=("is_on_time", lambda s: (s.sum() / len(s)) * 100.0),
            active_riders=("delivery_person_id", "nunique"),
            avg_rating=("delivery_person_ratings", "mean"),
        )
        .reset_index()
        .rename(columns={"city": "zone"})
    )
    zones["avg_delivery_time"] = zones["avg_delivery_time"].round(2)
    zones["on_time_pct"] = zones["on_time_pct"].round(2)
    zones["avg_rating"] = zones["avg_rating"].round(2)

    # Classify zone status dynamically
    demand_thresh = zones["total_orders"].max() * 0.75 if not zones.empty else 0
    delay_thresh = zones["avg_delivery_time"].mean() * 1.02 if not zones.empty else 0

    def classify_zone(row):
        if row["total_orders"] >= demand_thresh and row["avg_delivery_time"] >= delay_thresh:
            return "Critical Zone"
        elif row["total_orders"] >= demand_thresh:
            return "High Demand"
        elif row["avg_delivery_time"] >= delay_thresh:
            return "High Delay"
        else:
            return "Normal"

    zones["zone_status"] = zones.apply(classify_zone, axis=1)

    if zones.empty:
        empty_state("No zone data available.")
        return

    # ── Zone Charts ───────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Orders by Zone")
        fig = px.bar(
            zones.sort_values("total_orders", ascending=True),
            x="total_orders",
            y="zone",
            orientation="h",
            color="zone_status",
            color_discrete_map={
                "Critical Zone": "#EF4444",
                "High Demand":   "#F59E0B",
                "High Delay":    "#6366F1",
                "Normal":        "#22C55E",
            },
            labels={"total_orders": "Total Orders (count)", "zone": "Zone / City"},
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#CBD5E1",
            margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Avg Delivery Time by Zone")
        fig2 = px.bar(
            zones.sort_values("avg_delivery_time", ascending=False),
            x="zone",
            y="avg_delivery_time",
            color="on_time_pct",
            color_continuous_scale="Purples",
            labels={
                "avg_delivery_time": "Avg Delivery Time (min)",
                "zone": "Zone / City",
                "on_time_pct": "On-Time %",
            },
        )
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#CBD5E1",
            margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Zone Status Summary ───────────────────────────────────────────────────
    st.subheader("Zone Status Summary")
    status_counts = zones["zone_status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Zones"]

    fig3 = px.pie(
        status_counts,
        names="Status",
        values="Zones",
        color_discrete_sequence=["#6366F1", "#8B5CF6", "#F59E0B", "#22C55E", "#EF4444"],
    )
    fig3.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#CBD5E1",
        margin=dict(t=10, b=10, l=10, r=10),
    )

    col3, col4 = st.columns([1, 2])
    with col3:
        st.plotly_chart(fig3, use_container_width=True)
    with col4:
        st.subheader("Zone Detail Table")
        st.dataframe(
            zones[["zone", "total_orders", "avg_delivery_time", "on_time_pct", "active_riders", "avg_rating", "zone_status"]],
            use_container_width=True,
        )
        download_csv(zones, "zone_analysis.csv")

    # ── Key Insight ──────────────────────────────────────────────────────────
    worst_zone = zones.nlargest(1, "avg_delivery_time").iloc[0] if len(zones) else None
    best_zone  = zones.nsmallest(1, "avg_delivery_time").iloc[0] if len(zones) else None
    if worst_zone is not None and best_zone is not None:
        insight_box(
            "Zone Analysis",
            f"<b>{worst_zone['zone']}</b> has the highest avg delivery time at "
            f"<b>{worst_zone['avg_delivery_time']:.1f} min</b> with "
            f"<b>{worst_zone['on_time_pct']:.1f}%</b> on-time deliveries. "
            f"<b>{best_zone['zone']}</b> is the most efficient zone at "
            f"<b>{best_zone['avg_delivery_time']:.1f} min</b>. "
            f"Zones classified as 'High Delay' need priority rider allocation during peak hours."
        )


# ── PAGE 4: Peak Hours ────────────────────────────────────────────────────────
def page_peak_hours(df: pd.DataFrame, filters: dict) -> None:
    st.title("⏰ Peak Hours Analysis")

    if df.empty or "order_hour" not in df.columns:
        empty_state("No orders match the selected filters.")
        return

    hourly = df.dropna(subset=["order_hour"]).copy()
    hourly["order_hour"] = hourly["order_hour"].astype(int)

    if hourly.empty:
        empty_state("No hourly data available.")
        return

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # ── Demand Heatmap ────────────────────────────────────────────────────────
    st.subheader("Order Demand Heatmap — Hour × Day of Week")
    if "day_of_week" in hourly.columns:
        pivot_orders = hourly.pivot_table(
            values="id",
            index="day_of_week",
            columns="order_hour",
            aggfunc="count",
            fill_value=0,
        )
        pivot_orders = pivot_orders.reindex([d for d in day_order if d in pivot_orders.index])

        if not pivot_orders.empty:
            fig = px.imshow(
                pivot_orders,
                color_continuous_scale="Purples",
                labels={"x": "Hour of Day (0-23)", "y": "Day of Week", "color": "Total Orders"},
                aspect="auto",
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#CBD5E1",
                margin=dict(t=10, b=10, l=10, r=10),
            )
            st.plotly_chart(fig, use_container_width=True)

    # ── Delivery Time Heatmap ─────────────────────────────────────────────────
    st.subheader("Avg Delivery Time Heatmap — Hour × Day of Week")
    if "day_of_week" in hourly.columns and "time_taken_min" in hourly.columns:
        pivot_time = hourly.pivot_table(
            values="time_taken_min",
            index="day_of_week",
            columns="order_hour",
            aggfunc="mean",
        )
        pivot_time = pivot_time.reindex([d for d in day_order if d in pivot_time.index])

        if not pivot_time.empty:
            fig2 = px.imshow(
                pivot_time,
                color_continuous_scale="RdYlGn_r",
                labels={"x": "Hour of Day (0-23)", "y": "Day of Week", "color": "Avg Time (min)"},
                aspect="auto",
            )
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#CBD5E1",
                margin=dict(t=10, b=10, l=10, r=10),
            )
            st.plotly_chart(fig2, use_container_width=True)

    # ── Hourly Combined Line/Bar Chart ───────────────────────────────────────
    st.subheader("Orders and Avg Delivery Time by Hour")
    hourly_agg = (
        hourly.groupby("order_hour")
        .agg(
            total_orders=("id", "count"),
            avg_delivery_time=("time_taken_min", "mean"),
        )
        .reset_index()
    )

    if not hourly_agg.empty:
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            x=hourly_agg["order_hour"],
            y=hourly_agg["total_orders"],
            name="Orders",
            marker_color=COLORS["primary"],
            opacity=0.75,
            yaxis="y1",
        ))
        fig3.add_trace(go.Scatter(
            x=hourly_agg["order_hour"],
            y=hourly_agg["avg_delivery_time"],
            name="Avg Time (min)",
            mode="lines+markers",
            line=dict(color=COLORS["warning"], width=2.5),
            yaxis="y2",
        ))
        fig3.update_layout(
            xaxis=dict(title="Hour of Day (0-23)"),
            yaxis=dict(title="Total Orders (count)"),
            yaxis2=dict(title="Avg Delivery Time (min)", overlaying="y", side="right"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#CBD5E1",
            margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(fig3, use_container_width=True)

        # Key Insight
        peak_hr = hourly_agg.nlargest(1, "total_orders").iloc[0]
        slow_hr = hourly_agg.nlargest(1, "avg_delivery_time").iloc[0]
        insight_box(
            "Peak Hours",
            f"The busiest hour is <b>{int(peak_hr['order_hour'])}:00</b> with "
            f"<b>{int(peak_hr['total_orders']):,}</b> orders. "
            f"The slowest hour is <b>{int(slow_hr['order_hour'])}:00</b> with an avg "
            f"delivery time of <b>{slow_hr['avg_delivery_time']:.1f} min</b>. "
            f"Dinner (18:00-21:00) and Night (22:00-23:00) drive peak volume. "
            f"Fleet staging should be increased by ~20% between 19:00 and 21:00."
        )


# ── PAGE 5: Operations Report ─────────────────────────────────────────────────
def page_operations(df: pd.DataFrame, filters: dict) -> None:
    st.title("📊 Operations Report")

    if df.empty:
        empty_state("No orders match the selected filters.")
        return

    # ── Daily Trend ───────────────────────────────────────────────────────────
    st.subheader("Daily Order Volume & On-Time %")
    if "order_date" in df.columns and not df["order_date"].dropna().empty:
        daily = (
            df.groupby("order_date")
            .agg(
                total_orders=("id", "count"),
                avg_delivery_time=("time_taken_min", "mean"),
                on_time_pct=("is_on_time", lambda s: (s.sum() / len(s)) * 100.0),
            )
            .reset_index()
        )
        daily["order_date"] = pd.to_datetime(daily["order_date"], errors="coerce")
        daily = daily.sort_values("order_date").dropna(subset=["order_date"])

        if not daily.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=daily["order_date"],
                y=daily["total_orders"],
                name="Orders",
                marker_color=COLORS["primary"],
                opacity=0.65,
            ))
            fig.add_trace(go.Scatter(
                x=daily["order_date"],
                y=daily["on_time_pct"],
                name="On-Time %",
                mode="lines",
                line=dict(color=COLORS["success"], width=2.5),
                yaxis="y2",
            ))
            fig.update_layout(
                xaxis=dict(title="Order Date"),
                yaxis=dict(title="Total Orders (count)"),
                yaxis2=dict(title="On-Time % (SLA)", overlaying="y", side="right", range=[0, 100]),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#CBD5E1",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(t=10, b=10, l=10, r=10),
            )
            st.plotly_chart(fig, use_container_width=True)
            download_csv(daily, "daily_summary.csv")

    # ── Traffic & Weather Impact ──────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Impact by Traffic Condition")
        if "road_traffic_density" in df.columns and not df["road_traffic_density"].dropna().empty:
            traffic_agg = (
                df.groupby("road_traffic_density")
                .agg(
                    total_orders=("id", "count"),
                    avg_time=("time_taken_min", "mean"),
                )
                .reset_index()
                .rename(columns={"road_traffic_density": "traffic"})
                .sort_values("avg_time", ascending=False)
            )
            fig2 = px.bar(
                traffic_agg,
                x="traffic",
                y="avg_time",
                color="total_orders",
                color_continuous_scale="Purples",
                labels={
                    "traffic": "Traffic Condition",
                    "avg_time": "Avg Delivery Time (min)",
                    "total_orders": "Total Orders (count)",
                },
            )
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#CBD5E1",
                margin=dict(t=10, b=10, l=10, r=10),
            )
            st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.subheader("Impact by Weather Condition")
        if "weather_conditions" in df.columns and not df["weather_conditions"].dropna().empty:
            weather_agg = (
                df.groupby("weather_conditions")
                .agg(
                    total_orders=("id", "count"),
                    avg_time=("time_taken_min", "mean"),
                )
                .reset_index()
                .rename(columns={"weather_conditions": "weather"})
                .sort_values("avg_time", ascending=False)
            )
            fig3 = px.bar(
                weather_agg,
                x="weather",
                y="avg_time",
                color="avg_time",
                color_continuous_scale="Purples",
                labels={
                    "weather": "Weather Condition",
                    "avg_time": "Avg Delivery Time (min)",
                },
            )
            fig3.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#CBD5E1",
                margin=dict(t=10, b=10, l=10, r=10),
            )
            st.plotly_chart(fig3, use_container_width=True)

    # ── Vehicle Performance ───────────────────────────────────────────────────
    st.subheader("Vehicle Type Performance")
    if "type_of_vehicle" in df.columns and not df["type_of_vehicle"].dropna().empty:
        vehicle_agg = (
            df.groupby("type_of_vehicle")
            .agg(
                total_orders=("id", "count"),
                avg_delivery_time=("time_taken_min", "mean"),
                on_time_pct=("is_on_time", lambda s: (s.sum() / len(s)) * 100.0),
            )
            .reset_index()
            .sort_values("avg_delivery_time")
        )
        fig4 = px.bar(
            vehicle_agg,
            x="type_of_vehicle",
            y="avg_delivery_time",
            color="on_time_pct",
            color_continuous_scale="Purples",
            text="total_orders",
            labels={
                "type_of_vehicle": "Vehicle Type",
                "avg_delivery_time": "Avg Delivery Time (min)",
                "on_time_pct": "On-Time %",
            },
        )
        fig4.update_traces(texttemplate="%{text:,} orders", textposition="outside")
        fig4.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#CBD5E1",
            margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(fig4, use_container_width=True)

    # ── Traffic × Weather Combined Table ─────────────────────────────────────
    if "road_traffic_density" in df.columns and "weather_conditions" in df.columns:
        st.subheader("Detailed Traffic × Weather Breakdown")
        tw_agg = (
            df.groupby(["weather_conditions", "road_traffic_density"])
            .agg(
                total_orders=("id", "count"),
                avg_delivery_time=("time_taken_min", "mean"),
                on_time_pct=("is_on_time", lambda s: (s.sum() / len(s)) * 100.0),
            )
            .reset_index()
            .rename(columns={"weather_conditions": "weather", "road_traffic_density": "traffic"})
            .sort_values("avg_delivery_time", ascending=False)
        )
        tw_agg["avg_delivery_time"] = tw_agg["avg_delivery_time"].round(2)
        tw_agg["on_time_pct"] = tw_agg["on_time_pct"].round(2)
        st.dataframe(tw_agg, use_container_width=True)
        download_csv(tw_agg, "traffic_weather_impact.csv")

        worst_combo = tw_agg.iloc[0]
        insight_box(
            "Operations",
            f"The highest delivery friction occurs during <b>{worst_combo['weather']}</b> weather with "
            f"<b>{worst_combo['traffic']}</b> traffic, producing an avg delivery time of "
            f"<b>{worst_combo['avg_delivery_time']:.1f} min</b>. "
            f"Dynamic SLA buffer extensions and localized rider surge incentives are recommended under these conditions."
        )


# ── Main Entry Point ──────────────────────────────────────────────────────────
def main():
    # Header Banner
    st.markdown("""
    <div style="background: linear-gradient(135deg, #6366F1 0%, #0F172A 100%);
                padding: 1.5rem 2rem; border-radius: 12px; margin-bottom: 1rem;">
        <h1 style="color: white; margin: 0; font-size: 1.8rem;">
            🚀 Hyperlocal Delivery Intelligence
        </h1>
        <p style="color: #A5B4FC; margin: 0.3rem 0 0 0; font-size: 0.9rem;">
            Delivery analytics across cities, riders and time periods
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Load standalone CSV dataset
    raw_df = load_data()

    if raw_df.empty:
        st.error("Unable to load delivery dataset. Please ensure `data/cleaned_delivery_data.csv` exists.")
        st.stop()

    # Render sidebar controls & apply global filters
    filters = render_sidebar(raw_df)
    filtered_df = apply_filters(raw_df, filters)

    # Navigation Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "🏍️ Rider Performance",
        "📍 Zone Analysis",
        "⏰ Peak Hours",
        "🔧 Operations",
    ])

    with tab1:
        page_overview(filtered_df, filters)
    with tab2:
        page_rider_performance(filtered_df, filters)
    with tab3:
        page_zone_analysis(filtered_df, filters)
    with tab4:
        page_peak_hours(filtered_df, filters)
    with tab5:
        page_operations(filtered_df, filters)


if __name__ == "__main__":
    main()
