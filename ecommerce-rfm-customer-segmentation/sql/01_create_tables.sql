-- ============================================================
-- 01_create_tables.sql
-- Creates the transactions table that holds the cleaned,
-- customer-level transaction data produced by
-- python/data_cleaning.py (data/processed/cleaned_transactions.csv).
--
-- Engine: SQLite (see README.md for why SQLite was chosen and how
-- these scripts port to PostgreSQL/MySQL with trivial syntax changes).
-- ============================================================

DROP TABLE IF EXISTS transactions;

CREATE TABLE transactions (
    invoice_no      TEXT    NOT NULL,
    stock_code      TEXT    NOT NULL,
    description     TEXT,
    quantity        INTEGER NOT NULL,
    invoice_date    TEXT    NOT NULL,   -- ISO-8601 'YYYY-MM-DD HH:MM:SS'
    unit_price      REAL    NOT NULL,
    customer_id     INTEGER NOT NULL,
    country         TEXT,
    revenue         REAL    NOT NULL
);

-- Indexes that matter for the RFM / ranking queries that follow:
-- most queries filter or group by customer_id, and window functions
-- over invoice_date benefit from an index on the date column too.
CREATE INDEX idx_transactions_customer_id   ON transactions (customer_id);
CREATE INDEX idx_transactions_invoice_date  ON transactions (invoice_date);
CREATE INDEX idx_transactions_invoice_no    ON transactions (invoice_no);
