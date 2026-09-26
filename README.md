# E-commerce Customer Segmentation using RFM Analysis

A SQL-first data analytics project that segments e-commerce customers using
**RFM (Recency, Frequency, Monetary) analysis**, so the business knows
exactly who its best customers are, who's about to churn, and where
retention effort is best spent.

## Project Overview

Every e-commerce business has the same underlying question buried in its
transaction log: *which customers actually matter?* RFM analysis answers
this without machine learning or guesswork — it scores every customer on
three simple, business-intuitive dimensions:

- **Recency** — how recently did they buy?
- **Frequency** — how often do they buy?
- **Monetary** — how much do they spend?

Combining these three scores produces customer segments (High Value, At
Risk, Churned, etc.) that marketing and retention teams can act on
immediately — e.g. "spend the retention budget on At Risk customers, not
on customers who were never valuable to begin with."

## Business Problem

The business has ~780K cleaned transaction records and no systematic way
to tell a first-time £20 buyer from a customer who has spent £500,000
across 400 orders. Marketing spend and retention effort are being applied
uniformly instead of where they'd have the most impact. This project
builds the segmentation needed to fix that.

## Objectives

1. Clean and prepare raw transaction data for analysis
2. Calculate Recency, Frequency, and Monetary metrics per customer in SQL
3. Score and segment customers using SQL window functions and `CASE` logic
4. Rank customers by value and identify at-risk/high-value groups
5. Answer concrete business questions about segment size, revenue
   contribution, and behavior
6. Visualize the results and summarize actionable business insights

## Dataset

- **Source**: [Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii)
  (UCI Machine Learning Repository) — also mirrored on
  [Kaggle](https://www.kaggle.com/datasets/mashlyn/online-retail-ii-uci).
  Transactions from a UK-based online gift retailer.
- **Raw records**: 1,067,371 line items across two workbook sheets (FY2009-2010, FY2010-2011)
- **Date range**: 2009-12-01 to 2011-12-09
- **Columns**: Invoice, StockCode, Description, Quantity, InvoiceDate, Price, Customer ID, Country
- **Limitations**: ~23% of rows have no Customer ID (guest/unlinked
  transactions) and are excluded, since RFM is inherently customer-level.
  The raw file is not committed to this repo (see `.gitignore`) because it's
  45MB+ and redistribution isn't guaranteed — download it from the link
  above and place it at `data/raw/online_retail.xlsx` to reproduce.

## Data Cleaning

Implemented in [`python/data_cleaning.py`](python/data_cleaning.py). Rules applied, in order:

| # | Rule | Why |
|---|---|---|
| 1 | Drop rows with missing `Customer ID` | RFM is customer-level; unattributed transactions can't be scored |
| 2 | Drop rows with missing `Description` | Data-quality consistency; usually co-occurs with other bad rows |
| 3 | Drop cancelled invoices (`Invoice` starting with `C`) | Returns/refunds, not purchases — would distort Frequency & Monetary |
| 4 | Drop `Quantity <= 0` | Returns/adjustments, not real purchases |
| 5 | Drop `Price <= 0` | Free items / stock corrections, not sales |
| 6 | Drop exact duplicate rows | Duplicate scans/re-exports |
| 7 | Parse `InvoiceDate`, drop unparsable rows | Recency requires a valid date |
| 8 | Compute `Revenue = Quantity × Price` | Needed for the Monetary metric |

**Result**: 1,067,371 raw rows → 779,425 cleaned rows (26.98% removed),
covering **5,878 unique customers** across **36,969 unique invoices**.

## RFM Methodology

In plain business terms:

- **Recency** — days since a customer's last order. Lower = better (they're
  still actively shopping).
- **Frequency** — number of distinct orders placed. Higher = better (they
  keep coming back).
- **Monetary** — total amount spent. Higher = better (they're worth more).

Each metric is split into quintiles (`NTILE(5)`) across the whole customer
base, giving every customer an R, F, and M score from 1 (worst) to 5
(best) — Recency is inverted so *most recent* = score 5. The three scores
sum to an `rfm_score` (3-15) and combine into an `rfm_segment_code` like
`"555"` for easy filtering.

## SQL Techniques Used

- **CTEs** (`WITH ... AS`) to break the RFM calculation into readable steps
  instead of one giant nested query
- **Window functions**: `NTILE(5)` for quintile scoring, `RANK()` for
  revenue/frequency leaderboards (`OVER (ORDER BY ...)`)
- **`CASE` statements** for multi-condition business segmentation logic
- **`GROUP BY` / `HAVING`** for aggregation and data-quality checks
- **Date functions** (`JULIANDAY`, `DATE(..., '+1 day')`) for recency math
- **Materialized tables** (`CREATE TABLE ... AS SELECT`) so downstream
  scripts don't recompute the same CTEs repeatedly

**Engine note**: this project uses **SQLite** rather than PostgreSQL/MySQL
so the whole pipeline runs with zero server setup — clone the repo, run
one script, done. Every technique used (CTEs, `NTILE`, `RANK`, `CASE`,
window functions) is standard ANSI SQL supported identically in
PostgreSQL and MySQL 8+; porting `sql/*.sql` over needs only trivial
syntax swaps (`JULIANDAY`/`DATE()` → `DATEDIFF`/`CURRENT_DATE`,
`AUTOINCREMENT` → `SERIAL`/`AUTO_INCREMENT`).

## Customer Segmentation

Thresholds were set after inspecting the actual quintile distribution
(each of R/F/M splits the 5,878 customers into 5 near-equal groups of
~1,175), so "score 4-5" genuinely means "top 40%":

| Segment | Rule | Meaning |
|---|---|---|
| **High Value** | R≥4, F≥4, M≥4 | Recent, frequent, big spenders — protect these |
| **Loyal Customer** | R≥3, F≥4, M≥3 | Frequent, strong spenders, still active |
| **Potential Loyalist** | R≥4, F 2-3 | Recent buyers building a habit |
| **New Customer** | R=5, F=1 | Just made their first purchase |
| **At Risk** | R≤2, F≥3 | Used to be good customers, gone quiet |
| **Churned** | R≤2, F≤2 | Long gone, and were never frequent buyers |
| **Low Value** | everything else | Infrequent, low spend, middling recency |

Resulting distribution (5,878 customers total):

| Segment | Customers | % of Customers | Revenue | % of Revenue |
|---|---|---|---|---|
| High Value | 1,341 | 22.8% | £11,924,494 | 68.6% |
| Churned | 1,532 | 26.1% | £543,073 | 3.1% |
| At Risk | 818 | 13.9% | £1,702,904 | 9.8% |
| Low Value | 783 | 13.3% | £518,694 | 3.0% |
| Potential Loyalist | 706 | 12.0% | £757,673 | 4.4% |
| Loyal Customer | 641 | 10.9% | £1,915,834 | 11.0% |
| New Customer | 57 | 1.0% | £12,132 | 0.1% |

## Python Visualization

Implemented in [`python/rfm_visualization.py`](python/rfm_visualization.py), reading
directly from the SQL output (`outputs/customer_segments.csv`) — no numbers
are recomputed or invented in Python.

1. **`segment_distribution.png`** — bar chart of customer count per segment
2. **`revenue_by_segment.png`** — bar chart of total revenue per segment
3. **`recency_vs_monetary.png`** — scatter plot (log-scale monetary axis)
   showing how recency and spend relate, colored by segment

## Key Business Insights

Auto-generated from the actual data at `outputs/business_insights.md`
(regenerated every time `rfm_visualization.py` runs):

1. **High Value** customers are 22.8% of the customer base (1,341
   customers) but generate 68.6% of total revenue (£11,924,494) —
   classic 80/20-style concentration.
2. **At Risk** customers (818 customers, 13.9% of the base) have
   historically generated £1,702,904 in revenue (9.8% of total) with an
   average spend of £2,082 each, but haven't purchased in 367 days on
   average — the single highest-value group to target with a win-back
   campaign.
3. The top 10 customers by revenue alone contribute £2,787,079 (16.0% of
   total revenue), underscoring how concentrated this business's revenue
   is among a small number of accounts.
4. **Churned** customers are the largest single segment (1,532 customers,
   26.1%) but only 3.1% of revenue, with average recency of 459 days —
   most were low-value to begin with (avg spend £354), so win-back budget
   is better directed at **At Risk** than at this group.
5. **Recommendation**: prioritize retention offers for the 818 At Risk
   customers (high historical value, lapsing now) over broad campaigns
   aimed at the larger-but-lower-value Churned segment, and protect the
   High Value segment's experience since it drives most revenue from a
   minority of customers.

## Project Workflow

```text
Raw Data (online_retail.xlsx)
   ↓
Data Cleaning (python/data_cleaning.py)
   ↓
SQLite Database (sql/01_create_tables.sql)
   ↓
RFM Calculation (sql/03_rfm_analysis.sql — CTEs)
   ↓
RFM Scoring (sql/03_rfm_analysis.sql — NTILE)
   ↓
Customer Segmentation (sql/04_customer_segmentation.sql — CASE + RANK)
   ↓
Business Analysis (sql/05_business_analysis.sql)
   ↓
Python Visualization (python/rfm_visualization.py)
   ↓
Business Insights (outputs/business_insights.md)
```

## Project Structure

```text
ecommerce-rfm-customer-segmentation/
├── data/
│   ├── raw/                  # online_retail.xlsx (gitignored — see Dataset section)
│   └── processed/            # cleaned_transactions.csv (gitignored, reproducible)
├── python/
│   ├── data_cleaning.py
│   └── rfm_visualization.py
├── sql/
│   ├── 01_create_tables.sql
│   ├── 02_data_quality_checks.sql
│   ├── 03_rfm_analysis.sql
│   ├── 04_customer_segmentation.sql
│   └── 05_business_analysis.sql
├── outputs/
│   ├── customer_rfm.csv
│   ├── customer_segments.csv
│   ├── business_insights.md
│   └── charts/
│       ├── segment_distribution.png
│       ├── revenue_by_segment.png
│       └── recency_vs_monetary.png
├── README.md
├── requirements.txt
├── .gitignore
└── LICENSE
```

## Setup & Reproduction

```bash
# 1. Clone and install dependencies
git clone <your-repo-url>
cd ecommerce-rfm-customer-segmentation
pip install -r requirements.txt

# 2. Download the dataset and place it at data/raw/online_retail.xlsx
#    https://archive.ics.uci.edu/dataset/502/online+retail+ii

# 3. Clean the data
python python/data_cleaning.py

# 4. Build the SQLite database and load cleaned data
python3 -c "
import sqlite3, csv
conn = sqlite3.connect('outputs/ecommerce_rfm.db')
cur = conn.cursor()
cur.executescript(open('sql/01_create_tables.sql').read())
with open('data/processed/cleaned_transactions.csv') as f:
    reader = csv.reader(f); next(reader)
    cur.executemany('INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?,?)', list(reader))
conn.commit()
"

# 5. Run the RFM calculation, scoring, segmentation, and business queries
sqlite3 outputs/ecommerce_rfm.db < sql/03_rfm_analysis.sql
sqlite3 outputs/ecommerce_rfm.db < sql/04_customer_segmentation.sql
sqlite3 outputs/ecommerce_rfm.db < sql/05_business_analysis.sql

# 6. Export customer_rfm / customer_segments to outputs/*.csv, then:
python python/rfm_visualization.py
```

*(If you don't have the `sqlite3` CLI installed, every step above can run
through Python's built-in `sqlite3` module instead — see the inline
comments in each script.)*

## Skills Demonstrated

```text
SQL (SQLite, portable to PostgreSQL/MySQL)
CTEs (WITH clauses)
Window Functions — NTILE(), RANK()
CASE-based business segmentation
GROUP BY / HAVING aggregation
Date arithmetic (JULIANDAY, DATE)
Data Cleaning (Python/Pandas)
RFM Analysis / Customer Analytics
Python — Pandas, Matplotlib
Business Insight Generation
```

## License

MIT — see [LICENSE](LICENSE).
