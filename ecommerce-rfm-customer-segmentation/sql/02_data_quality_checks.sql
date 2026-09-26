-- ============================================================
-- 02_data_quality_checks.sql
-- Sanity checks run against the cleaned `transactions` table to
-- confirm the Python cleaning step worked as intended before any
-- RFM math is built on top of it.
-- ============================================================

-- 1. Row count and basic shape
SELECT COUNT(*)                    AS total_rows,
       COUNT(DISTINCT customer_id) AS unique_customers,
       COUNT(DISTINCT invoice_no)  AS unique_invoices,
       MIN(invoice_date)           AS earliest_invoice,
       MAX(invoice_date)           AS latest_invoice
FROM transactions;

-- 2. No nulls should remain in required columns
SELECT
    SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) AS null_customer_id,
    SUM(CASE WHEN invoice_no  IS NULL THEN 1 ELSE 0 END) AS null_invoice_no,
    SUM(CASE WHEN invoice_date IS NULL THEN 1 ELSE 0 END) AS null_invoice_date
FROM transactions;

-- 3. No non-positive quantity or price should remain
SELECT
    SUM(CASE WHEN quantity   <= 0 THEN 1 ELSE 0 END) AS bad_quantity_rows,
    SUM(CASE WHEN unit_price <= 0 THEN 1 ELSE 0 END) AS bad_price_rows
FROM transactions;

-- 4. No cancelled invoices (invoice numbers starting with 'C') should remain
SELECT COUNT(*) AS cancelled_invoices_remaining
FROM transactions
WHERE invoice_no LIKE 'C%';

-- 5. Revenue sanity check: revenue must equal quantity * unit_price for every row
SELECT COUNT(*) AS revenue_mismatch_rows
FROM transactions
WHERE ROUND(revenue, 2) <> ROUND(quantity * unit_price, 2);

-- 6. Distribution check: customers with only one invoice ever
--    (expected to be a meaningful share -> informs the "New Customer" segment)
SELECT COUNT(*) AS one_time_customers
FROM (
    SELECT customer_id
    FROM transactions
    GROUP BY customer_id
    HAVING COUNT(DISTINCT invoice_no) = 1
);
