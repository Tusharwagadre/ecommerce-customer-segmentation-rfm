-- ============================================================
-- 03_rfm_analysis.sql
-- Calculates Recency, Frequency, Monetary (RFM) metrics per
-- customer, then scores each metric 1-5 with NTILE() and
-- materializes the result into a `customer_rfm` table that
-- 04_customer_segmentation.sql and 05_business_analysis.sql
-- build on.
--
-- Reference date = MAX(invoice_date) + 1 day, i.e. "as of the day
-- after the last transaction in the dataset". This is the standard
-- RFM convention so that even the most recent purchase has a
-- recency of at least 1 day (avoids a recency of 0).
-- ============================================================

DROP TABLE IF EXISTS customer_rfm;

CREATE TABLE customer_rfm AS

WITH reference_date AS (
    -- Single reference point every customer's recency is measured against
    SELECT DATE(MAX(invoice_date), '+1 day') AS ref_date
    FROM transactions
),

customer_orders AS (
    -- One row per customer: last purchase date, order count, total spend
    SELECT
        t.customer_id,
        MAX(t.invoice_date)                AS last_purchase_date,
        COUNT(DISTINCT t.invoice_no)        AS frequency,
        SUM(t.revenue)                      AS monetary
    FROM transactions t
    GROUP BY t.customer_id
),

rfm_base AS (
    -- Recency in whole days between last purchase and the reference date
    SELECT
        co.customer_id,
        CAST(JULIANDAY(rd.ref_date) - JULIANDAY(co.last_purchase_date) AS INTEGER) AS recency,
        co.frequency,
        ROUND(co.monetary, 2) AS monetary
    FROM customer_orders co
    CROSS JOIN reference_date rd
),

rfm_scored AS (
    -- NTILE(5) buckets each metric into quintiles across the whole
    -- customer base. Recency is scored in reverse (bucket 1 = most
    -- recent = highest score) because a LOWER recency is BETTER,
    -- while frequency and monetary are scored directly (bucket 5 =
    -- highest value = highest score) because HIGHER is BETTER.
    SELECT
        customer_id,
        recency,
        frequency,
        monetary,
        (6 - NTILE(5) OVER (ORDER BY recency ASC))   AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC)       AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC)        AS m_score
    FROM rfm_base
)

SELECT
    customer_id,
    recency,
    frequency,
    monetary,
    r_score,
    f_score,
    m_score,
    (r_score + f_score + m_score)                          AS rfm_score,
    (CAST(r_score AS TEXT) || CAST(f_score AS TEXT) || CAST(m_score AS TEXT)) AS rfm_segment_code
FROM rfm_scored;

CREATE INDEX idx_customer_rfm_customer_id ON customer_rfm (customer_id);

-- Quick sanity peek at the result
SELECT * FROM customer_rfm ORDER BY rfm_score DESC LIMIT 10;
