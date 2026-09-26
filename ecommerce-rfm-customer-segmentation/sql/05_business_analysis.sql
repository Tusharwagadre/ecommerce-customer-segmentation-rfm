-- ============================================================
-- 05_business_analysis.sql
-- Ten business questions answered directly from customer_segments
-- (built in 04_customer_segmentation.sql) and transactions.
-- ============================================================

-- Q1: How many customers are in each segment?
SELECT segment, COUNT(*) AS customer_count
FROM customer_segments
GROUP BY segment
ORDER BY customer_count DESC;

-- Q2: What percentage of customers belong to each segment?
SELECT
    segment,
    COUNT(*) AS customer_count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM customer_segments), 2) AS pct_of_customers
FROM customer_segments
GROUP BY segment
ORDER BY pct_of_customers DESC;

-- Q3: Which segments generate the most revenue?
SELECT
    segment,
    ROUND(SUM(monetary), 2) AS total_revenue,
    ROUND(100.0 * SUM(monetary) / (SELECT SUM(monetary) FROM customer_segments), 2) AS pct_of_revenue
FROM customer_segments
GROUP BY segment
ORDER BY total_revenue DESC;

-- Q4: What is the average monetary value of each segment?
SELECT segment, ROUND(AVG(monetary), 2) AS avg_monetary
FROM customer_segments
GROUP BY segment
ORDER BY avg_monetary DESC;

-- Q5: What is the average frequency of each segment?
SELECT segment, ROUND(AVG(frequency), 2) AS avg_frequency
FROM customer_segments
GROUP BY segment
ORDER BY avg_frequency DESC;

-- Q6: What is the average recency of each segment?
SELECT segment, ROUND(AVG(recency), 1) AS avg_recency_days
FROM customer_segments
GROUP BY segment
ORDER BY avg_recency_days ASC;

-- Q7: Who are the top 10 customers by revenue?
SELECT customer_id, monetary AS total_revenue, segment
FROM customer_segments
ORDER BY monetary DESC
LIMIT 10;

-- Q8: Who are the top 10 customers by purchase frequency?
SELECT customer_id, frequency AS total_orders, segment
FROM customer_segments
ORDER BY frequency DESC
LIMIT 10;

-- Q9: Which customers are potentially at risk?
--     (At Risk segment, ordered by highest historical spend first --
--      i.e. the ones worth a retention campaign the most)
SELECT customer_id, recency, frequency, monetary, segment
FROM customer_segments
WHERE segment = 'At Risk'
ORDER BY monetary DESC
LIMIT 20;

-- Q10: Which customers have the highest RFM scores?
SELECT customer_id, r_score, f_score, m_score, rfm_score, segment
FROM customer_segments
ORDER BY rfm_score DESC, monetary DESC
LIMIT 20;
