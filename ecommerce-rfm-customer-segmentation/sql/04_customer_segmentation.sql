-- ============================================================
-- 04_customer_segmentation.sql
-- Applies business-friendly segment labels to customer_rfm using
-- CASE logic on the individual R/F/M scores (not just the summed
-- rfm_score, since two customers can hit the same total score
-- through very different R/F/M combinations that mean different
-- things for the business).
--
-- Thresholds were chosen after inspecting the actual quintile
-- distribution in 03_rfm_analysis.sql (each of R/F/M splits the
-- 5,878 customers into 5 near-equal groups of ~1,175), so "4-5" is
-- genuinely "top 40%" and "1-2" is genuinely "bottom 40%" here.
-- ============================================================

DROP TABLE IF EXISTS customer_segments;

CREATE TABLE customer_segments AS
SELECT
    customer_id,
    recency,
    frequency,
    monetary,
    r_score,
    f_score,
    m_score,
    rfm_score,
    rfm_segment_code,
    CASE
        -- Bought recently, buy often, spend the most -> protect these
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4
            THEN 'High Value'

        -- Buy often and spend well, though not necessarily this week
        WHEN r_score >= 3 AND f_score >= 4 AND m_score >= 3
            THEN 'Loyal Customer'

        -- Recent buyers building a habit but not yet frequent/big spenders
        WHEN r_score >= 4 AND f_score BETWEEN 2 AND 3
            THEN 'Potential Loyalist'

        -- Single/very recent purchase, no track record yet
        WHEN r_score = 5 AND f_score = 1
            THEN 'New Customer'

        -- Used to be good customers (decent F/M) but haven't come back recently
        WHEN r_score <= 2 AND f_score >= 3
            THEN 'At Risk'

        -- Long gone AND never bought much/often to begin with
        WHEN r_score <= 2 AND f_score <= 2
            THEN 'Churned'

        -- Everyone else: infrequent, low spend, middling recency
        ELSE 'Low Value'
    END AS segment
FROM customer_rfm;

CREATE INDEX idx_customer_segments_segment ON customer_segments (segment);

-- ------------------------------------------------------------
-- Customer ranking (Section 9 of the brief)
-- ------------------------------------------------------------

-- Top customers by revenue, ranked with RANK() so ties share a rank
SELECT
    customer_id,
    monetary,
    RANK() OVER (ORDER BY monetary DESC) AS revenue_rank,
    segment
FROM customer_segments
ORDER BY revenue_rank
LIMIT 10;

-- Top customers by purchase frequency
SELECT
    customer_id,
    frequency,
    RANK() OVER (ORDER BY frequency DESC) AS frequency_rank,
    segment
FROM customer_segments
ORDER BY frequency_rank
LIMIT 10;

-- Customers with the highest RFM scores
SELECT
    customer_id,
    r_score,
    f_score,
    m_score,
    rfm_score,
    segment
FROM customer_segments
ORDER BY rfm_score DESC
LIMIT 10;

-- Segment distribution sanity check (how many customers landed in each bucket)
SELECT segment, COUNT(*) AS customers
FROM customer_segments
GROUP BY segment
ORDER BY customers DESC;
