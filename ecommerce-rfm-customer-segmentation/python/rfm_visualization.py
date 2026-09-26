"""
rfm_visualization.py
---------------------
Reads outputs/customer_segments.csv (produced by the SQL pipeline in
sql/03-05) and produces three portfolio-ready charts plus a short,
data-driven business-insights text file.

Charts:
  1. Customer count by segment            (outputs/charts/segment_distribution.png)
  2. Revenue by segment                   (outputs/charts/revenue_by_segment.png)
  3. Recency vs Monetary scatter, colored (outputs/charts/recency_vs_monetary.png)
     by segment

This script does NOT recompute RFM logic -- all numbers come straight
from the SQL output, so every figure here is traceable back to
sql/03_rfm_analysis.sql / 04_customer_segmentation.sql.
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEGMENTS_CSV = ROOT / "outputs" / "customer_segments.csv"
CHARTS_DIR = ROOT / "outputs" / "charts"
INSIGHTS_PATH = ROOT / "outputs" / "business_insights.md"

SEGMENT_ORDER = [
    "High Value", "Loyal Customer", "Potential Loyalist",
    "New Customer", "At Risk", "Churned", "Low Value",
]
SEGMENT_COLORS = {
    "High Value": "#1F3864", "Loyal Customer": "#2E75B6",
    "Potential Loyalist": "#9DC3E6", "New Customer": "#70AD47",
    "At Risk": "#ED7D31", "Churned": "#C00000", "Low Value": "#A6A6A6",
}


def load_data() -> pd.DataFrame:
    df = pd.read_csv(SEGMENTS_CSV)
    return df


def chart_segment_distribution(df: pd.DataFrame):
    counts = df["segment"].value_counts().reindex(SEGMENT_ORDER).dropna()
    colors = [SEGMENT_COLORS[s] for s in counts.index]

    fig, ax = plt.subplots(figsize=(9, 5.5))
    bars = ax.bar(counts.index, counts.values, color=colors)
    ax.set_title("Customer Segment Distribution", fontsize=14, fontweight="bold")
    ax.set_xlabel("Segment")
    ax.set_ylabel("Number of Customers")
    ax.tick_params(axis="x", rotation=30)
    for bar, val in zip(bars, counts.values):
        ax.annotate(f"{int(val):,}", (bar.get_x() + bar.get_width() / 2, val),
                    textcoords="offset points", xytext=(0, 4), ha="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "segment_distribution.png", dpi=150)
    plt.close(fig)


def chart_revenue_by_segment(df: pd.DataFrame):
    revenue = df.groupby("segment")["monetary"].sum().reindex(SEGMENT_ORDER).dropna()
    colors = [SEGMENT_COLORS[s] for s in revenue.index]

    fig, ax = plt.subplots(figsize=(9, 5.5))
    bars = ax.bar(revenue.index, revenue.values / 1000, color=colors)
    ax.set_title("Total Revenue by Customer Segment", fontsize=14, fontweight="bold")
    ax.set_xlabel("Segment")
    ax.set_ylabel("Total Revenue (£ thousands)")
    ax.tick_params(axis="x", rotation=30)
    for bar, val in zip(bars, revenue.values):
        ax.annotate(f"£{val/1000:,.0f}K", (bar.get_x() + bar.get_width() / 2, val / 1000),
                    textcoords="offset points", xytext=(0, 4), ha="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "revenue_by_segment.png", dpi=150)
    plt.close(fig)


def chart_recency_vs_monetary(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(9, 6))
    for seg in SEGMENT_ORDER:
        sub = df[df["segment"] == seg]
        if sub.empty:
            continue
        ax.scatter(sub["recency"], sub["monetary"], s=14, alpha=0.55,
                   color=SEGMENT_COLORS[seg], label=seg)
    ax.set_yscale("log")
    ax.set_title("Recency vs. Monetary Value by Segment", fontsize=14, fontweight="bold")
    ax.set_xlabel("Recency (days since last purchase)")
    ax.set_ylabel("Monetary Value (£, log scale)")
    ax.legend(title="Segment", fontsize=8, title_fontsize=9, loc="upper right")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "recency_vs_monetary.png", dpi=150)
    plt.close(fig)


def generate_insights(df: pd.DataFrame) -> str:
    total_customers = len(df)
    total_revenue = df["monetary"].sum()

    by_seg = df.groupby("segment").agg(
        customers=("customer_id", "count"),
        revenue=("monetary", "sum"),
        avg_monetary=("monetary", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_recency=("recency", "mean"),
    )
    by_seg["pct_customers"] = 100 * by_seg["customers"] / total_customers
    by_seg["pct_revenue"] = 100 * by_seg["revenue"] / total_revenue

    hv = by_seg.loc["High Value"]
    at_risk = by_seg.loc["At Risk"]
    churned = by_seg.loc["Churned"]
    top10_revenue = df.nlargest(10, "monetary")["monetary"].sum()

    lines = []
    lines.append("# Key Business Insights\n")
    lines.append(
        f"1. **High Value** customers are {hv['pct_customers']:.1f}% of the customer "
        f"base ({int(hv['customers']):,} customers) but generate {hv['pct_revenue']:.1f}% "
        f"of total revenue (£{hv['revenue']:,.0f}) — classic 80/20-style concentration.\n"
    )
    lines.append(
        f"2. **At Risk** customers ({int(at_risk['customers']):,} customers, "
        f"{at_risk['pct_customers']:.1f}% of the base) have historically generated "
        f"£{at_risk['revenue']:,.0f} in revenue ({at_risk['pct_revenue']:.1f}% of total) "
        f"with an average spend of £{at_risk['avg_monetary']:,.0f} each, but haven't "
        f"purchased in {at_risk['avg_recency']:.0f} days on average — this is the "
        f"single highest-value group to target with a win-back campaign.\n"
    )
    lines.append(
        f"3. The top 10 customers by revenue alone contribute £{top10_revenue:,.0f} "
        f"({100*top10_revenue/total_revenue:.1f}% of total revenue), underscoring how "
        f"concentrated this business's revenue is among a small number of accounts.\n"
    )
    lines.append(
        f"4. **Churned** customers make up the largest single segment "
        f"({int(churned['customers']):,} customers, {churned['pct_customers']:.1f}% of "
        f"the base) but only {churned['pct_revenue']:.1f}% of revenue, with an average "
        f"recency of {churned['avg_recency']:.0f} days — most were low-value to begin "
        f"with (avg spend £{churned['avg_monetary']:,.0f}), so win-back spend is better "
        f"directed at **At Risk** customers than at this group.\n"
    )
    lines.append(
        f"5. Recommendation: prioritize retention offers for the {int(at_risk['customers']):,} "
        f"**At Risk** customers (high historical value, lapsing now) over broad campaigns "
        f"aimed at the larger but lower-value **Churned** segment, and protect the "
        f"**High Value** segment's experience since it drives the majority of revenue "
        f"from a minority of the customer base.\n"
    )
    return "\n".join(lines)


def main():
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    df = load_data()

    chart_segment_distribution(df)
    chart_revenue_by_segment(df)
    chart_recency_vs_monetary(df)

    insights = generate_insights(df)
    INSIGHTS_PATH.write_text(insights)

    print("Charts written to", CHARTS_DIR)
    print("Insights written to", INSIGHTS_PATH)
    print("\n" + insights)


if __name__ == "__main__":
    main()
