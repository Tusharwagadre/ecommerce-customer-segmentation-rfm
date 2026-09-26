"""
data_cleaning.py
-----------------
Cleans the raw Online Retail II transaction data and produces a single,
analysis-ready CSV for SQL loading.

Cleaning rules applied (documented in README.md as well):
  1. Drop rows with missing Customer ID   -> RFM is customer-level; a
     transaction with no customer ID cannot be attributed to anyone.
  2. Drop rows with missing Description   -> not needed for RFM math, but
     removed for data-quality consistency since they usually accompany
     other bad rows (adjustments/testing entries).
  3. Drop cancelled invoices (Invoice starting with 'C') -> these are
     returns/refunds, not purchases, and would distort Frequency/Monetary.
  4. Drop rows with Quantity <= 0        -> negative or zero quantities are
     returns, adjustments, or data-entry errors, not real purchases.
  5. Drop rows with Price <= 0           -> free/zero-priced rows are
     stock adjustments, manual corrections, or bad data, not sales.
  6. Drop exact duplicate rows           -> duplicate scans/re-exports.
  7. Parse InvoiceDate to a proper datetime and drop unparsable rows.
  8. Compute Revenue = Quantity * Price.

Output: data/processed/cleaned_transactions.csv
"""

import pandas as pd
from pathlib import Path

RAW_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "online_retail.xlsx"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "cleaned_transactions.csv"


def load_raw(path: Path) -> pd.DataFrame:
    """Load and concatenate all sheets in the workbook (each sheet = one year)."""
    xl = pd.ExcelFile(path)
    frames = [pd.read_excel(xl, sheet_name=s) for s in xl.sheet_names]
    df = pd.concat(frames, ignore_index=True)
    df.columns = [c.strip() for c in df.columns]
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    start_rows = len(df)
    log = {"start_rows": start_rows}

    # Standardize column names
    df = df.rename(columns={
        "Invoice": "invoice_no",
        "StockCode": "stock_code",
        "Description": "description",
        "Quantity": "quantity",
        "InvoiceDate": "invoice_date",
        "Price": "unit_price",
        "Customer ID": "customer_id",
        "Country": "country",
    })

    # 1. Missing Customer ID
    df = df.dropna(subset=["customer_id"])
    log["after_drop_missing_customer_id"] = len(df)

    # 2. Missing description
    df = df.dropna(subset=["description"])
    log["after_drop_missing_description"] = len(df)

    # 3. Cancelled invoices (start with 'C')
    df = df[~df["invoice_no"].astype(str).str.upper().str.startswith("C")]
    log["after_drop_cancelled_invoices"] = len(df)

    # 4. Non-positive quantity
    df = df[df["quantity"] > 0]
    log["after_drop_non_positive_quantity"] = len(df)

    # 5. Non-positive price
    df = df[df["unit_price"] > 0]
    log["after_drop_non_positive_price"] = len(df)

    # 6. Exact duplicate rows
    before = len(df)
    df = df.drop_duplicates()
    log["duplicates_removed"] = before - len(df)
    log["after_drop_duplicates"] = len(df)

    # 7. Parse dates
    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")
    df = df.dropna(subset=["invoice_date"])
    log["after_drop_bad_dates"] = len(df)

    # Types
    df["customer_id"] = df["customer_id"].astype(int)
    df["quantity"] = df["quantity"].astype(int)
    df["unit_price"] = df["unit_price"].astype(float)

    # 8. Revenue
    df["revenue"] = df["quantity"] * df["unit_price"]

    df = df[[
        "invoice_no", "stock_code", "description", "quantity",
        "invoice_date", "unit_price", "customer_id", "country", "revenue",
    ]]

    log["end_rows"] = len(df)
    log["rows_removed_total"] = start_rows - len(df)
    log["pct_removed"] = round(100 * (start_rows - len(df)) / start_rows, 2)

    return df, log


def main():
    print(f"Loading raw data from {RAW_PATH} ...")
    raw = load_raw(RAW_PATH)
    print(f"Raw rows: {len(raw):,}")

    cleaned, log = clean(raw)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(OUT_PATH, index=False)

    print("\nCleaning summary:")
    for k, v in log.items():
        print(f"  {k}: {v:,}" if isinstance(v, int) else f"  {k}: {v}")

    print(f"\nCleaned dataset written to {OUT_PATH}")
    print(f"Date range: {cleaned['invoice_date'].min()} -> {cleaned['invoice_date'].max()}")
    print(f"Unique customers: {cleaned['customer_id'].nunique():,}")
    print(f"Unique invoices: {cleaned['invoice_no'].nunique():,}")


if __name__ == "__main__":
    main()
