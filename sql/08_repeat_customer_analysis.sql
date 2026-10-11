
-- Repeat-customer analysis
-- Customer identity: customer_unique_id
-- Scope: delivered orders with a known purchase timestamp

WITH customer_orders AS (
    SELECT
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS delivered_order_count
    FROM customers AS c
    INNER JOIN orders AS o
        ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp IS NOT NULL
      AND c.customer_unique_id IS NOT NULL
    GROUP BY c.customer_unique_id
),

customer_segments AS (
    SELECT
        customer_unique_id,
        delivered_order_count,
        CASE
            WHEN delivered_order_count >= 2 THEN 'Repeat'
            ELSE 'One-time'
        END AS customer_segment
    FROM customer_orders
)

SELECT
    customer_segment,
    COUNT(*) AS customer_count,
    ROUND(
        100.0 * COUNT(*)
        / NULLIF(SUM(COUNT(*)) OVER (), 0),
        2
    ) AS customer_percentage
FROM customer_segments
GROUP BY customer_segment
ORDER BY customer_count DESC;
